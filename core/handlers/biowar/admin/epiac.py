"""
Команда .ас — выдача игрового мута (АС) + обнуление.
Собственный router, собственный FSM, собственные callback'и.
Не пересекается с epilab.py.
"""
import re
import time
import logging
from datetime import datetime, timedelta

from redis.asyncio import Redis
from humanize import intcomma

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core import func
from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.utils.db_api.settings_pool import db_pool
from core.settings import settings

router = Router()
logger = logging.getLogger(__name__)

OWNER_LOG_ID = -1003688648228  # тот же лог, что в epilab

MIN_SECONDS = 86400                       # 1 день
MAX_SECONDS = 1000 * 365 * 86400          # 1000 лет


# ===== FSM =====

class ACEpiStates(StatesGroup):
    waiting_for_reason = State()         # причина АС
    waiting_for_time = State()           # срок АС
    waiting_for_delcorp_reason = State() # причина удаления корпы


# ===== ХЕЛПЕРЫ =====

def _is_admin(user_id: int) -> bool:
    admin_cfg = getattr(settings.bots, "admin_ids", getattr(settings.bots, "admin_id", []))
    if isinstance(admin_cfg, (int, str)):
        admin_cfg = [int(admin_cfg)]
    elif isinstance(admin_cfg, (list, tuple, set)):
        admin_cfg = [int(a) for a in admin_cfg if a is not None]
    else:
        admin_cfg = []
    return user_id in set(admin_cfg)


def _parse_time(text: str) -> tuple[int, int, str]:
    """
    Возвращает (expire_ts, duration_sec, error_message).
    Форматы: 1d, 1y, 999d, 123123y, 0 (навсегда), 1ч, 30м.
    """
    text = (text or "").strip().lower()
    now = int(time.time())

    if text in {"0", "навсегда", "forever", "perm", "∞", "всегда"}:
        return now + MAX_SECONDS, MAX_SECONDS, ""

    m = re.match(r'^(\d+)\s*(y|г|год|года|лет|d|д|дн|дней|дня|h|ч|час|часов|m|м|мин|минут|минуты)?$', text)
    if not m:
        return 0, 0, "❌ Неверный формат. Примеры: 1d, 1y, 999d, 0 (навсегда)"

    val = int(m.group(1))
    unit = (m.group(2) or "").lower()

    if unit in {"y", "г", "год", "года", "лет"}:
        seconds = val * 365 * 86400
    elif unit in {"d", "д", "дн", "дней", "дня"}:
        seconds = val * 86400
    elif unit in {"h", "ч", "час", "часов"}:
        seconds = val * 3600
    elif unit in {"m", "м", "мин", "минут", "минуты"}:
        seconds = val * 60
    else:
        # без единицы — считаем днями
        seconds = val * 86400

    if seconds < MIN_SECONDS:
        return 0, 0, "❌ Минимум 1 день."
    if seconds > MAX_SECONDS:
        seconds = MAX_SECONDS

    return now + seconds, seconds, ""


def _duration_text(seconds: int) -> str:
    if seconds >= 365 * 86400:
        years = seconds // (365 * 86400)
        return f"{years} г."
    if seconds >= 86400:
        return f"{seconds // 86400} д."
    if seconds >= 3600:
        return f"{seconds // 3600} ч."
    return f"{seconds // 60} мин."


async def _log(admin_user, action: str, target_id: int, bot: Bot):
    try:
        text = (
            f"🔔 <b>АС-панель</b>\n"
            f"👤 Админ: {admin_user.full_name} (@{admin_user.username}, <code>{admin_user.id}</code>)\n"
            f"🎯 Цель: <code>{target_id}</code>\n"
            f"🛠 {action}"
        )
        await bot.send_message(OWNER_LOG_ID, text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"AC log failed: {e}")


async def _resolve_target(message: Message, query: str, repo: RequestsRepoBiowar) -> int | None:
    """Ищем игрока по ID, @username или reply."""
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id
    if not query:
        return None
    q = query.strip()
    if "user_id=" in q:
        mm = re.search(r'user_id=(\d+)', q)
        if mm:
            q = mm.group(1)
    if q.isdigit():
        return int(q)
    # @username
    clean = q.lstrip('@')
    try:
        user = await repo.get_user(clean)
        if user:
            return user.get('id') if isinstance(user, dict) else int(user)
    except Exception:
        pass
    return None


def _main_menu(uid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚫 Заблокировать в боте", callback_data=f"acm:block:{uid}")],
        [
            InlineKeyboardButton(text="🧪 Обнулить опыт", callback_data=f"acm:rexp:{uid}"),
            InlineKeyboardButton(text="💰 Обнулить ресурсы", callback_data=f"acm:rres:{uid}"),
        ],
        [
            InlineKeyboardButton(text="📦 Обнулить кейсы", callback_data=f"acm:rcase:{uid}"),
            InlineKeyboardButton(text="💎 Обнулить коины", callback_data=f"acm:rcoin:{uid}"),
        ],
        [InlineKeyboardButton(text="🔬 Обнулить лабораторию", callback_data=f"acm:rlab:{uid}")],
        [InlineKeyboardButton(text="🏛 Удалить корпу игрока", callback_data=f"acm:delcorp:{uid}")],
        [InlineKeyboardButton(text="🔓 Снять АС", callback_data=f"acm:unban:{uid}")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="acm:close")],
    ])


# ===== КОМАНДА .ас =====

@router.message(F.text.lower().regexp(r'^[.!\/]?ас\s*(.*)$'))
async def cmd_ac(message: Message, state: FSMContext, repo_biowar: RequestsRepoBiowar):
    if not _is_admin(message.from_user.id):
        return

    # Достаём аргумент
    m = re.match(r'^[.!\/]?ас\s*(.*)$', message.text, re.IGNORECASE)
    query = (m.group(1) or "").strip() if m else ""

    if not query and not message.reply_to_message:
        return await message.answer(
            "ℹ️ Использование: <code>.ас &lt;user_id&gt;</code>, "
            "<code>.ас @username</code> или реплаем на сообщение.",
            parse_mode="HTML",
        )

    target_id = await _resolve_target(message, query, repo_biowar)
    if not target_id:
        return await message.answer("⚠️ Не удалось найти игрока.")

    await state.clear()

    await message.answer(
        f"🎛 <b>АС-панель:</b> <code>{target_id}</code>",
        reply_markup=_main_menu(target_id),
        parse_mode="HTML",
    )


# ===== CALLBACK'И =====

@router.callback_query(F.data.startswith('acm:'))
async def acm_callback(call: CallbackQuery, state: FSMContext, repo_biowar: RequestsRepoBiowar, redis: Redis, bot: Bot):
    if not _is_admin(call.from_user.id):
        return await call.answer("❌ Нет доступа", show_alert=True)

    parts = call.data.split(':')
    action = parts[1]
    uid = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None

    # ----- Закрыть -----
    if action == 'close':
        await state.clear()
        try:
            await call.message.delete()
        except Exception:
            pass
        return await call.answer()

    # ----- Заблокировать в боте -----
    if action == 'block':
        if not uid:
            return await call.answer("❌ Неверный ID", show_alert=True)
        await state.update_data(ac_target=uid)
        await state.set_state(ACEpiStates.waiting_for_reason)
        await call.message.answer("✍️ Введите причину блокировки:")
        return await call.answer()

    # ----- Снять АС -----
    if action == 'unban':
        if not uid:
            return await call.answer("❌ Неверный ID", show_alert=True)
        try:
            await repo_biowar.game_mute_cancel(uid)
        except Exception:
            pass
        # чистка Redis
        for p in ("epidemic_gamemute:", "gamemute:"):
            try:
                await redis.delete(f"{p}{uid}")
            except Exception:
                pass
        # чистка памяти
        try:
            from core.middlewares.antispam import banned_users
            banned_users.pop(int(uid), None)
        except Exception:
            pass

        await _log(call.from_user, f"🔓 Снятие АС", uid, bot)
        try:
            await call.message.edit_text(f"✅ АС снят с <code>{uid}</code>", parse_mode="HTML")
        except Exception:
            await call.message.answer(f"✅ АС снят с <code>{uid}</code>", parse_mode="HTML")
        return await call.answer()

    # ----- Удалить корпу -----
    if action == 'delcorp':
        if not uid:
            return await call.answer("❌ Неверный ID", show_alert=True)
        # Проверим, есть ли корпа у игрока
        async with db_pool._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT corporation_code FROM CorporationMembers WHERE member_id=%s LIMIT 1;",
                    (uid,),
                )
                row = await cur.fetchone()
                if not row:
                    return await call.answer("❌ Игрок не состоит в корпорации", show_alert=True)
                corp_code = row[0] if isinstance(row, (list, tuple)) else row.get('corporation_code')

        await state.update_data(delcorp_target=uid, delcorp_code=corp_code)
        await state.set_state(ACEpiStates.waiting_for_delcorp_reason)
        await call.message.answer(
            f"🏛 <b>Удаление корпорации</b>\n\n"
            f"👤 Игрок: <code>{uid}</code>\n"
            f"🏛 Корпа: <code>{corp_code}</code>\n\n"
            f"✍️ Введите <b>причину</b> удаления:",
            parse_mode="HTML",
        )
        return await call.answer()

    # ----- Обнуления -----
    if action in ('rexp', 'rres', 'rcase', 'rcoin', 'rlab'):
        if not uid:
            return await call.answer("❌ Неверный ID", show_alert=True)
        try:
            if action == 'rexp':
                await repo_biowar.update_lab_skill_val(uid, 'bio_experience', 0)
                label = "🧪 Опыт обнулён"
            elif action == 'rres':
                await repo_biowar.update_lab_skill_val(uid, 'bio_resource', 0)
                label = "💰 Ресурсы обнулены"
            elif action == 'rcase':
                # Кейсы: Lab.case1, Lab.case2 (если есть поле case3 — добавь)
                for field in ('case1', 'case2'):
                    try:
                        await repo_biowar.update_lab_skill_val(uid, field, 0)
                    except Exception:
                        pass
                label = "📦 Кейсы обнулены"
            elif action == 'rcoin':
                await repo_biowar.update_lab_skill_val(uid, 'epicoins', 0)
                label = "💎 Коины обнулены"
            elif action == 'rlab':
                for field, val in [
                    ('infect', 1), ('immunity', 1), ('lethality', 1),
                    ('security_service', 1), ('science', 1),
                    ('pathogens', 4), ('ready_pathogens', 0),
                    ('bio_experience', 1000), ('bio_resource', 15000),
                ]:
                    try:
                        await repo_biowar.update_lab_skill_val(uid, field, val)
                    except Exception:
                        pass
                try:
                    await repo_biowar.pathogen_name_change(None, uid)
                    await repo_biowar.lab_name_change(None, uid)
                    await repo_biowar.execute_query(
                        "DELETE FROM Victims WHERE victims_owner_id = %s;", uid
                    )
                except Exception:
                    pass
                label = "🔬 Лаборатория сброшена"

            await _log(call.from_user, label, uid, bot)
            await call.answer(f"✅ {label}", show_alert=True)
        except Exception as e:
            logger.error(f"AC reset error ({action}, {uid}): {e}")
            await call.answer(f"❌ Ошибка: {e}", show_alert=True)
        return


# ===== FSM: ПРИЧИНА =====

@router.message(ACEpiStates.waiting_for_reason)
async def ac_reason(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    reason = (message.text or "").strip()
    if not reason:
        return await message.answer("❌ Причина не может быть пустой.")

    await state.update_data(ac_reason=reason)
    await state.set_state(ACEpiStates.waiting_for_time)
    await message.answer(
        f"📝 Причина: <b>{reason}</b>\n\n"
        f"⏳ Введите срок:\n"
        f"• <code>1d</code> — 1 день\n"
        f"• <code>7d</code> — 7 дней\n"
        f"• <code>1y</code> — 1 год\n"
        f"• <code>999d</code>, <code>123123y</code>\n"
        f"• <code>0</code> — навсегда\n\n"
        f"<i>Минимум 1 день. Максимум 1000 лет.</i>",
        parse_mode="HTML",
    )


# ===== FSM: СРОК + ВЫДАЧА =====

@router.message(ACEpiStates.waiting_for_time)
async def ac_time(message: Message, state: FSMContext, repo_biowar: RequestsRepoBiowar, redis: Redis, bot: Bot):
    if not _is_admin(message.from_user.id):
        return

    data = await state.get_data()
    target_id = data.get('ac_target')
    reason = data.get('ac_reason', 'Не указана')
    await state.clear()

    if not target_id:
        return await message.answer("❌ Сессия истекла, повторите <code>.ас</code>.")

    expire_ts, duration, err = _parse_time(message.text or "")
    if err:
        return await message.answer(err)

    try:
        # 1. Записать в БД
        await repo_biowar.game_mute_add(target_id, message.from_user.id, reason, expire_ts)

        # 2. Redis
        try:
            await redis.set(
                f"epidemic_gamemute:{target_id}",
                f"{reason}:{expire_ts}",
                ex=duration,
            )
        except Exception:
            pass

        # 3. Память
        try:
            from core.middlewares.antispam import banned_users
            banned_users[int(target_id)] = expire_ts
        except Exception:
            pass

        # 4. ЛС игроку
        dur_text = "навсегда" if duration >= MAX_SECONDS else _duration_text(duration)
        until_text = (
            "навсегда" if duration >= MAX_SECONDS
            else datetime.fromtimestamp(expire_ts).strftime('%d.%m.%Y %H:%M МСК')
        )

        user_text = (
            f"🚫 <b>Вы заблокированы в боте.</b>\n\n"
            f"<b>Причина:</b> {reason}\n"
            f"<b>Срок:</b> {dur_text}\n"
            f"<b>До:</b> {until_text}\n\n"
            f"<i>Игровые команды не будут отвечать до окончания срока.</i>"
        )
        try:
            await bot.send_message(target_id, user_text, parse_mode="HTML")
            sent = "✅"
        except Exception as e:
            logger.warning(f"Cannot send AC notification to {target_id}: {e}")
            sent = "⚠️ ЛС не отправлено"

        # 5. Лог
        await _log(message.from_user, f"🚫 Блокировка (Причина: {reason}, Срок: {dur_text})", target_id, bot)

        await message.answer(
            f"✅ АС выдан игроку <code>{target_id}</code>\n"
            f"<b>Причина:</b> {reason}\n"
            f"<b>Срок:</b> {dur_text}\n"
            f"<b>До:</b> {until_text}\n"
            f"{sent}",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"AC apply error: {e}")
        await message.answer(f"❌ Ошибка: {e}")




# ===== СПИСОК АС (.лист) =====

@router.message(F.text.lower().regexp(r'^[.!\/]?(лист|aclist|асы|список ас)\s*$'))
async def cmd_ac_list(message: Message, repo_biowar: RequestsRepoBiowar):
    if not _is_admin(message.from_user.id):
        return

    mutes = await repo_biowar.get_gamemute_list()
    now = int(time.time())

    # Оставляем только активные
    active = [m for m in (mutes or []) if int(m.get('time_expire') or 0) > now]

    if not active:
        return await message.answer("✅ Активных АС нет.", parse_mode="HTML")

    # Сортируем: кто ближе к разбану — вверху
    active.sort(key=lambda m: int(m.get('time_expire') or 0))

    lines = [
        "🚫 <b>АКТИВНЫЕ АС</b>",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}

    for i, m in enumerate(active, 1):
        uid = int(m.get('user_id'))
        expire = int(m.get('time_expire') or 0)
        admin_id = m.get('admin')
        reason = (m.get('reason') or "Не указана").strip()
        full_name = m.get('full_name') or m.get('username') or f"ID {uid}"

        until = datetime.fromtimestamp(expire).strftime('%d.%m.%Y %H:%M')
        left_sec = max(0, expire - now)
        left_text = _duration_text(left_sec) if left_sec > 0 else "истекает"

        prefix = medals.get(i, f"<b>{i}.</b>")
        name_link = f'<a href="tg://openmessage?user_id={uid}">{full_name}</a>'

        lines.append(
            f"{prefix} {name_link}\n"
            f"   📋 {reason}\n"
            f"   ⏳ до <b>{until}</b> (осталось {left_text})\n"
            f"   👮 <code>{admin_id}</code>\n"
        )

    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"📊 Всего в АС: <b>{len(active)}</b>",
    ]

    await message.answer(
        "\n".join(lines),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


# ===== ПРИЧИНА АС ДЛЯ ИГРОКА (.причина) =====

@router.message(F.text.lower().regexp(r'^[.!\/]?(причина|reason)\s*(.*)$'))
async def cmd_ac_reason(message: Message, repo_biowar: RequestsRepoBiowar):
    if not _is_admin(message.from_user.id):
        return

    m = re.match(r'^[.!\/]?(?:причина|reason)\s*(.*)$', message.text, re.IGNORECASE)
    query = (m.group(1) or "").strip() if m else ""

    target_id = await _resolve_target(message, query, repo_biowar)
    if not target_id:
        return await message.answer(
            "ℹ️ Использование: <code>.причина &lt;user_id&gt;</code>, "
            "<code>.причина @username</code> или реплаем на сообщение.",
            parse_mode="HTML",
        )

    # Ищем активный АС
    mutes = await repo_biowar.get_gamemute_list()
    now = int(time.time())
    active = [x for x in (mutes or []) if int(x.get('user_id') or 0) == int(target_id)
              and int(x.get('time_expire') or 0) > now]

    if not active:
        return await message.answer(
            f"✅ Игрок <code>{target_id}</code> не в бане.",
            parse_mode="HTML",
        )

    m = active[0]
    expire = int(m.get('time_expire') or 0)
    admin_id = m.get('admin')
    reason = (m.get('reason') or "Не указана").strip()
    full_name = m.get('full_name') or m.get('username') or f"ID {target_id}"

    until = datetime.fromtimestamp(expire).strftime('%d.%m.%Y %H:%M')
    left_sec = max(0, expire - now)
    left_text = _duration_text(left_sec) if left_sec > 0 else "истекает"

    name_link = f'<a href="tg://openmessage?user_id={target_id}">{full_name}</a>'

    text = (
        f"🚫 <b>АС ИГРОКА</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 {name_link}\n"
        f"🆔 <code>{target_id}</code>\n\n"
        f"📋 <b>Причина:</b> {reason}\n"
        f"⏳ <b>Выдан до:</b> {until}\n"
        f"⌛️ <b>Осталось:</b> {left_text}\n"
        f"👮 <b>Админ:</b> <code>{admin_id}</code>"
    )

    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)


# ===== FSM: ПРИЧИНА УДАЛЕНИЯ КОРПЫ + УДАЛЕНИЕ =====

@router.message(ACEpiStates.waiting_for_delcorp_reason)
async def ac_delcorp_reason(message: Message, state: FSMContext, repo_biowar: RequestsRepoBiowar, bot: Bot):
    if not _is_admin(message.from_user.id):
        return

    reason = (message.text or "").strip()
    if not reason:
        return await message.answer("❌ Причина не может быть пустой.")

    data = await state.get_data()
    await state.clear()

    target_id = data.get('delcorp_target')
    corp_code = data.get('delcorp_code')

    if not target_id or not corp_code:
        return await message.answer("❌ Сессия истекла, повторите <code>.ас</code>.")

    async with db_pool._pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Данные корпы
            await cur.execute(
                "SELECT invitation_code, name, leader_id, members FROM Corporation WHERE invitation_code=%s;",
                (corp_code,),
            )
            corp = await cur.fetchone()

            if not corp:
                return await message.answer(f"❌ Корпа <code>{corp_code}</code> уже не существует.")

            corp_name = corp[1]
            leader_id = int(corp[2])
            members_count = int(corp[3] or 0)

            # Удаляем
            await cur.execute("DELETE FROM CorporationMembers WHERE corporation_code=%s;", (corp_code,))
            await cur.execute("DELETE FROM CorporationInviteList WHERE corporation_code=%s;", (corp_code,))
            await cur.execute("DELETE FROM CorpTreasuryLog WHERE corp_code=%s;", (corp_code,))
            await cur.execute("DELETE FROM CorpUpgrades WHERE corp_code=%s;", (corp_code,))
            await cur.execute("DELETE FROM Corporation WHERE invitation_code=%s;", (corp_code,))

    # ЛС лидеру
    leader_text = (
        f"🏛 Корпорация «{corp_name}» была удалена администрацией.\n\n"
        f"Все участники выведены из корпы.\n"
        f"Инвайт-код освобождён.\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📋 Причина: {reason}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Если считаешь это ошибкой — напиши в поддержку."
    )
    leader_status = "✅ отправлено"
    try:
        await bot.send_message(leader_id, leader_text, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        leader_status = f"⚠️ ЛС не доставлено ({type(e).__name__})"
        logger.warning(f"Cannot send to leader {leader_id}: {e}")

    # Лог
    try:
        log_text = (
            f"🗑 <b>[УДАЛЕНИЕ КОРПЫ через .ас]</b>\n"
            f"👤 Админ: {message.from_user.full_name} (@{message.from_user.username}, <code>{message.from_user.id}</code>)\n"
            f"🏛 Корпа: <b>«{corp_name}»</b> (<code>{corp_code}</code>)\n"
            f"👑 Лидер: <code>{leader_id}</code>\n"
            f"👥 Участников: <b>{members_count}</b>\n"
            f"📋 Причина: {reason}\n"
            f"📨 Лидеру: {leader_status}"
        )
        await bot.send_message(OWNER_LOG_ID, log_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Log error: {e}")

    await message.answer(
        f"✅ Корпа <b>«{corp_name}»</b> (<code>{corp_code}</code>) удалена.\n\n"
        f"👥 Участников выведено: <b>{members_count}</b>\n"
        f"👑 Лидер: <code>{leader_id}</code>\n"
        f"📨 Лидеру: {leader_status}",
        parse_mode="HTML",
    )
