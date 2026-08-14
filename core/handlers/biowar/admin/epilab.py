import re
import time
import logging
from datetime import datetime, timedelta
from humanize import intcomma
from redis.asyncio import Redis

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core.middlewares.antispam import banned_users, user_timestamps
from core.settings import settings
from core import func
from core.data.icons import LabIco
from core.utils.db_api.repo_biowar import RequestsRepoBiowar

router = Router()
logger = logging.getLogger(__name__)

OWNER_LOG_ID = -1003688648228

class EpiLabAdminStates(StatesGroup):
    waiting_for_ac_reason = State()
    waiting_for_block_reason = State()
    waiting_for_transfer_target = State()

def parse_time_duration(text: str) -> tuple[int, int]:
    """Возвращает (expire_timestamp, duration_in_seconds)"""
    text = text.strip().lower()
    now_ts = int(time.time())

    if text in ['навсегда', 'forever', '0', 'perm', 'на вечно', 'всегда']:
        seconds = 3650 * 24 * 3600  # ~10 лет
        return now_ts + seconds, seconds

    match = re.match(r'^(\d+)\s*([мmhhdдч]?)$', text)
    if not match:
        return now_ts + 3600, 3600  # По умолчанию 1 час

    val, unit = match.groups()
    val = int(val)

    if unit in ['м', 'm']:
        seconds = val * 60
    elif unit in ['ч', 'h']:
        seconds = val * 3600
    elif unit in ['д', 'd']:
        seconds = val * 86400
    else:
        seconds = val * 60

    return now_ts + seconds, seconds

async def notify_owner_action(message_or_user, action_desc: str, target_id: int = None, bot: Bot = None):
    try:
        user = getattr(message_or_user, "from_user", message_or_user)
        bot_instance = bot or getattr(message_or_user, "bot", None)
        if not bot_instance:
            return

        admin_info = f"👤 Админ: {user.full_name} (@{user.username}, <code>{user.id}</code>)"
        target_info = f"🎯 Цель (ID): <code>{target_id}</code>\n" if target_id else ""
        log_text = (
            f"🔔 <b>Лог админ-действия:</b>\n"
            f"{admin_info}\n"
            f"{target_info}"
            f"🛠 Действие: {action_desc}"
        )
        await bot_instance.send_message(OWNER_LOG_ID, log_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to send admin action log: {e}")

async def resolve_lab_target(message: Message, query: str = None, repo_biowar: RequestsRepoBiowar = None):
    if message.reply_to_message and not query:
        replied_user = message.reply_to_message.from_user
        if replied_user:
            try:
                lab = await repo_biowar.get_info_user_lab(replied_user.id)
                if lab:
                    return lab
            except Exception:
                pass
            return {'id': replied_user.id}

    if not query:
        return None

    query = query.strip()
    if "user_id=" in query:
        match_uid = re.search(r'user_id=(\d+)', query)
        if match_uid:
            query = match_uid.group(1)

    target_user_id = None
    if query.isdigit():
        target_user_id = int(query)
    else:
        clean_query = query.lstrip('@')

        if hasattr(repo_biowar, 'get_id_by_username'):
            try:
                res = await repo_biowar.get_id_by_username(clean_query)
                if res:
                    target_user_id = res.get('user_id') or res.get('id') if isinstance(res, dict) else int(res)
            except Exception:
                pass

        if not target_user_id and hasattr(repo_biowar, 'get_user'):
            try:
                user = await repo_biowar.get_user(clean_query)
                if user:
                    target_user_id = user.get('user_id') or user.get('id')
            except Exception:
                pass

    if target_user_id:
        try:
            lab = await repo_biowar.get_info_user_lab(target_user_id)
            if lab:
                return lab
        except Exception:
            pass
        return {'id': target_user_id}

    return None

@router.message(F.text.regexp(r'^!(?:эпилаб|epilab)(?:\s+(.*))?', flags=re.IGNORECASE))
async def cmd_epi_lab(message: Message, state: FSMContext, repo_biowar: RequestsRepoBiowar):
    if str(message.from_user.id) not in settings.bots.admin_id:
        return
    await state.clear()
    match = re.match(r'^!(?:эпилаб|epilab)(?:\s+(.*))?', message.text, re.IGNORECASE)
    query = match.group(1) if match else None

    lab_data = await resolve_lab_target(message, query, repo_biowar)
    if not lab_data or 'id' not in lab_data:
        await message.answer("⚠️ Использование: !эпилаб <user_id, @username> или реплаем на сообщение игрока.")
        return

    target_id = lab_data['id']

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔬 Просмотр лаборатории", callback_data=f"epilab:view:{target_id}")],
        [InlineKeyboardButton(text="⛔ АС (Мут команд)", callback_data=f"epilab:ac:{target_id}")],
        [InlineKeyboardButton(text="🔒 Запрет смены имени/патогена", callback_data=f"epilab:blockname:{target_id}")],
        [InlineKeyboardButton(text="🔓 Снять ограничения", callback_data=f"epilab:unblock:{target_id}")],
        [InlineKeyboardButton(text="🔄 Перенос лаборатории", callback_data=f"epilab:transfer:{target_id}")],
        [InlineKeyboardButton(text="💣 Обнул", callback_data=f"epilab:reset:{target_id}")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="epilab:close")]
    ])

    await message.answer(f"🎛 <b>Управление лабораторией:</b> <code>{target_id}</code>", reply_markup=kb)

@router.message(F.text.regexp(r'^!(?:асы|aclist|списокм)', flags=re.IGNORECASE))
async def cmd_list_aces(message: Message, repo_biowar: RequestsRepoBiowar):
    game_mutes = await repo_biowar.get_gamemute_list() if hasattr(repo_biowar, 'get_gamemute_list') else []
    bio_mutes = await repo_biowar.get_biomute_list() if hasattr(repo_biowar, 'get_biomute_list') else []

    now_ts = int(time.time())
    text_lines = ["<b>📋 Список активных ограничений (АС и запретов):</b>\n"]

    active_game_mutes = [m for m in (game_mutes or []) if not m.get('expire') or m.get('expire') > now_ts]
    active_bio_mutes = [m for m in (bio_mutes or []) if not m.get('expire') or m.get('expire') > now_ts]

    if active_game_mutes:
        text_lines.append("<b>⛔ АС (Муты команд):</b>")
        for m in active_game_mutes:
            uid = m.get('user_id') or m.get('id')
            admin_id = m.get('admin_id') or m.get('admin') or '?'
            reason = m.get('reason', 'не указана')
            expire = m.get('expire') or m.get('time_expire') or 0
            expire_str = datetime.fromtimestamp(expire).strftime('%Y-%m-%d %H:%M') if expire else 'навсегда'
            text_lines.append(f"• Игрок: <code>{uid}</code> | Админ: <code>{admin_id}</code>\n  Причина: {reason} | До: {expire_str}")
        text_lines.append("")

    if active_bio_mutes:
        text_lines.append("<b>🔒 Запреты смены имени/патогена:</b>")
        for m in active_bio_mutes:
            uid = m.get('user_id') or m.get('id')
            admin_id = m.get('admin_id') or m.get('admin') or '?'
            reason = m.get('reason', 'не указана')
            expire = m.get('expire') or m.get('time_expire') or 0
            expire_str = datetime.fromtimestamp(expire).strftime('%Y-%m-%d %H:%M') if expire else 'навсегда'
            text_lines.append(f"• Игрок: <code>{uid}</code> | Админ: <code>{admin_id}</code>\n  Причина: {reason} | До: {expire_str}")

    if not active_game_mutes and not active_bio_mutes:
        text_lines.append("<i>Активных ограничений в базе данных не найдено.</i>")

    await message.answer("\n".join(text_lines), disable_web_page_preview=True)

# ===== ХЭНДЛЕРЫ ВВОДА ДЛЯ FSM (АС, Запрет имени, Перенос) =====

@router.message(EpiLabAdminStates.waiting_for_ac_reason)
async def process_ac_reason(message: Message, state: FSMContext, repo_biowar: RequestsRepoBiowar, redis: Redis):
    data = await state.get_data()
    target_id = data.get('target_id')
    await state.clear()

    if not target_id:
        return await message.answer("❌ Сессия истёкла, повторите команду заново.")

    text = message.text.strip()
    parts = text.rsplit(' ', 1)
    reason = text
    expire_ts, duration_sec = parse_time_duration("3600")

    if len(parts) == 2:
        re_match = re.match(r'^(\d+)\s*([мmhhdдч]?)$', parts[1].lower()) or parts[1].lower() in ['навсегда', 'forever', '0', 'perm', 'всегда']
        if re_match:
            reason = parts[0]
            expire_ts, duration_sec = parse_time_duration(parts[1])

    try:
        if hasattr(repo_biowar, 'game_mute_add'):
            await repo_biowar.game_mute_add(target_id, message.from_user.id, reason, expire_ts)
        
        banned_users[int(target_id)] = expire_ts
        for prefix in ["epidemic_gamemute:", "gamemute:"]:
            try:
                await redis.set(f"{prefix}{target_id}", f"{reason}:{expire_ts}", ex=duration_sec)
            except Exception:
                pass

        await notify_owner_action(message.from_user, f"⛔ Выдача АС (Причина: {reason}, До: {datetime.fromtimestamp(expire_ts).strftime('%d.%m.%Y %H:%M')})", target_id, bot=message.bot)
        await message.answer(f"✅ АС успешно выдан игроку <code>{target_id}</code>!\n<b>Причина:</b> {reason}")
    except Exception as e:
        logger.error(f"Error applying AC for {target_id}: {e}")
        await message.answer(f"❌ Ошибка при выдаче АС: {e}")

@router.message(EpiLabAdminStates.waiting_for_block_reason)
async def process_block_reason(message: Message, state: FSMContext, repo_biowar: RequestsRepoBiowar, redis: Redis):
    data = await state.get_data()
    target_id = data.get('target_id')
    await state.clear()

    if not target_id:
        return await message.answer("❌ Сессия истёкла, повторите команду заново.")

    text = message.text.strip()
    parts = text.rsplit(' ', 1)
    reason = text
    expire_ts, duration_sec = parse_time_duration("3600")

    if len(parts) == 2:
        re_match = re.match(r'^(\d+)\s*([мmhhdдч]?)$', parts[1].lower()) or parts[1].lower() in ['навсегда', 'forever', '0', 'perm', 'всегда']
        if re_match:
            reason = parts[0]
            expire_ts, duration_sec = parse_time_duration(parts[1])

    try:
        if hasattr(repo_biowar, 'bio_mute_add'):
            await repo_biowar.bio_mute_add(target_id, message.from_user.id, reason, expire_ts)

        if hasattr(repo_biowar, 'pathogen_name_change'):
            await repo_biowar.pathogen_name_change(None, target_id)
        if hasattr(repo_biowar, 'lab_name_change'):
            await repo_biowar.lab_name_change(None, target_id)

        for prefix in ["biomute:", "epidemic_biomute:"]:
            try:
                await redis.set(f"{prefix}{target_id}", f"{reason}:{expire_ts}", ex=duration_sec)
            except Exception:
                pass

        await notify_owner_action(message.from_user, f"🔒 Запрет смены имени/патогена (Причина: {reason})", target_id, bot=message.bot)
        await message.answer(f"✅ Запрет смены имени/патогена у игрока <code>{target_id}</code> установлен!\n<b>Причина:</b> {reason}")
    except Exception as e:
        await message.answer(f"❌ Ошибка при установке запрета: {e}")

async def process_transfer_target(message: Message, state: FSMContext, repo_biowar: RequestsRepoBiowar):
    data = await state.get_data()
    from_id = data.get('target_id')
    await state.clear()

    if not from_id:
        return await message.answer("❌ Сессия истёкла, повторите команду заново.")

    query = message.text
    dest_lab = await resolve_lab_target(message, query, repo_biowar)
    if not dest_lab or 'id' not in dest_lab:
        return await message.answer("⚠️ Не удалось найти второго игрока для переноса!")

    to_id = dest_lab['id']
    if int(from_id) == int(to_id):
        return await message.answer("❌ Перенос на того же пользователя невозможен!")

    try:
        if hasattr(repo_biowar, 'transfer_lab'):
            await repo_biowar.transfer_lab(from_id, to_id)
        elif hasattr(repo_biowar, 'transfer_user_lab'):
            await repo_biowar.transfer_user_lab(from_id, to_id)
        else:
            return await message.answer("⚠️ Метод переноса не найден в repo_biowar.")

        await notify_owner_action(message.from_user, f"🔄 Перенос лаборатории с {from_id} на {to_id}", from_id, bot=message.bot)
        await message.answer(f"✅ Лаборатория успешно перенесена с <code>{from_id}</code> на <code>{to_id}</code>!")
    except Exception as e:
        logger.error(f"Error transferring lab {from_id} -> {to_id}: {e}")
        await message.answer(f"❌ Ошибка при переносе лаборатории: {e}")

# ===== CALLBACK КНОПКИ ПАНЕЛИ =====

@router.callback_query(F.data.startswith('epilab:'))
async def epilab_callback(callback: CallbackQuery, state: FSMContext, repo_biowar: RequestsRepoBiowar, redis: Redis):
    admin_cfg = getattr(settings.bots, "admin_ids", getattr(settings.bots, "admin_id", []))
    if not isinstance(admin_cfg, (list, tuple, set)): 
        admin_cfg = [admin_cfg]
    
    is_admin = callback.from_user.id in admin_cfg or str(callback.from_user.id) in map(str, admin_cfg)
    if not is_admin:
        try:
            u = await repo_biowar.get_user(callback.from_user.id)
            if u and (getattr(u, "is_admin", False) or getattr(u, "role", "") in ["admin", "owner", "creator"]): 
                is_admin = True
        except Exception: 
            pass

    if not is_admin:
        return await callback.answer("❌ У вас нет доступа к управлению этой панелью!", show_alert=True)

    parts = callback.data.split(':')
    action = parts[1] if len(parts) > 1 else None

    if action == 'close':
        await state.clear()
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.answer()
        return

    target_id = int(parts[2]) if len(parts) > 2 else None

    if action == 'view':
        try:
            lab_info = await repo_biowar.get_info_user_lab(target_id)
            if not lab_info:
                return await callback.answer("Лаборатория не найдена в БД!", show_alert=True)

            corp_info = await repo_biowar.get_corporation(target_id) if hasattr(repo_biowar, 'get_corporation') else None
            infected = await repo_biowar.get_my_infected(lab_info.get('id', target_id)) if hasattr(repo_biowar, 'get_my_infected') else 0
            illnesses = await repo_biowar.get_my_illnesses(lab_info.get('id', target_id)) if hasattr(repo_biowar, 'get_my_illnesses') else 0

            full_name = lab_info.get("full_name", "Неизвестно")
            name_entity = func.entity_create_full_name(lab_info.get('id', target_id), full_name) if hasattr(func, 'entity_create_full_name') else full_name
            pathogen_name = lab_info.get("pathogen_name") or 'засекречено'
            lab_name = lab_info.get('lab_name') or full_name

            fever = func.fever_expire_difference_check(lab_info.get('fever')) if lab_info.get('fever') and hasattr(func, 'fever_expire_difference_check') else None
            fever_str = f"⏳ Лихорадка активна до: {fever}\n" if fever else ""

            lethality = lab_info.get('lethality', 1)
            fever_time = int(lethality / 3)
            fever_time = (1 if fever_time == 0 else (60 if fever_time >= 180 else fever_time))

            refresh_pathogen_time = '\n'
            if lab_info.get("science_time") and hasattr(func, 'fever_expire_difference_check'):
                science_time = func.fever_expire_difference_check(lab_info["science_time"])
                refresh_pathogen_time = f'<i>{LabIco.sand_clock.value} Новый патоген через {science_time}</i>\n\n'

            if corp_info and isinstance(corp_info, dict):
                corp_text = f'В составе Корпорации — «<a href="tg://openmessage?user_id={corp_info.get("leader_id")}">{corp_info.get("name")}</a>»\n\n'
            else:
                corp_text = '\n'

            custom_emoji = lab_info.get('customization_emoji') or ''

            now_msk = datetime.utcnow() + timedelta(hours=3)
            next_award = now_msk.replace(minute=0, second=0, microsecond=0)
            if now_msk.hour < 12:
                next_award = next_award.replace(hour=12)
            else:
                next_award = (next_award + timedelta(days=1)).replace(hour=0)
            seconds_left = (next_award - now_msk).total_seconds()
            get_food_text = func.convert_seconds_to_human(seconds_left) if hasattr(func, 'convert_seconds_to_human') else "скоро"

            bio_exp = lab_info.get("bio_experience", 0)
            bio_res = lab_info.get("bio_resource", 0)

            lab_text = (
                f'<b>📩 Досье лаборатории {lab_name}:</b>\n'
                f'Руководитель — {name_entity} {custom_emoji}\n'
                f'{corp_text}'
                f'{LabIco.label.value} <b>Имя патогена:</b> {pathogen_name}\n'
                f'{LabIco.pathogens.value} <b>Готовых патогенов:</b> {lab_info.get("ready_pathogens", 0)}/{lab_info.get("pathogens", 0)}\n'
                f'{LabIco.science.value} <b>Квалификация учёных:</b> {lab_info.get("science", 1)} ур ({61 - lab_info.get("science", 1)} мин.)\n'
                f'{refresh_pathogen_time}'
                f'<blockquote><b>——[ Характеристика]——</b>\n'
                f'{LabIco.infect.value} Заразность: {lab_info.get("infect", 1)} ур\n'
                f'{LabIco.immunity.value} Иммунитет: {lab_info.get("immunity", 1)} ур\n'
                f'{LabIco.lethality.value} Летальность: {lethality} ур ({fever_time} мин | {lethality} дн)\n'
                f'{LabIco.security_service.value} Служба безопасности: {lab_info.get("security_service", 1)} ур</blockquote>\n'
                f'<b>ID лаборатории:</b> {lab_info.get("id", target_id)}\n'
                '<b>——————————————</b>\n'
                '<blockquote><b>—[Запасы — реагентов]—</b>\n'
                f'{LabIco.bio_experience.value} Опыт: {intcomma(bio_exp).replace(",", " ")}\n'
                f'{LabIco.bio_resource.value} Ресурсы: {intcomma(bio_res).replace(",", " ")}\n'
                f'{LabIco.time.value} <i>Ежедневная премия через: {get_food_text}</i>\n'
                f'{fever_str}</blockquote>\n'
                f'{LabIco.infected.value} Заражённых: {infected}\n'
                f'{LabIco.illnesses.value} Своих болезней: {illnesses}\n'
            )

            back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад к управлению", callback_data=f"epilab:main:{target_id}")]
            ])

            await callback.message.edit_text(lab_text, disable_web_page_preview=True, reply_markup=back_keyboard)
            await callback.answer()
        except Exception as e:
            logger.error(f"Error in epilab:view for {target_id}: {e}", exc_info=True)
            await callback.answer(f"❌ Ошибка загрузки лабы: {e}", show_alert=True)

    elif action == 'main':
        back_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔬 Просмотр лаборатории", callback_data=f"epilab:view:{target_id}")],
            [InlineKeyboardButton(text="⛔ АС (Мут команд)", callback_data=f"epilab:ac:{target_id}")],
            [InlineKeyboardButton(text="🔒 Запрет смены имени/патогена", callback_data=f"epilab:blockname:{target_id}")],
            [InlineKeyboardButton(text="🔓 Снять ограничения", callback_data=f"epilab:unblock:{target_id}")],
            [InlineKeyboardButton(text="🔄 Перенос лаборатории", callback_data=f"epilab:transfer:{target_id}")],
            [InlineKeyboardButton(text="💣 Обнул", callback_data=f"epilab:reset:{target_id}")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="epilab:close")]
        ])
        await callback.message.edit_text(f"🎛 <b>Управление лабораторией:</b> <code>{target_id}</code>", reply_markup=back_kb)
        await callback.answer()

    elif action == 'ac':
        await state.update_data(target_id=target_id)
        await state.set_state(EpiLabAdminStates.waiting_for_ac_reason)
        await callback.message.answer("✍️ Введите причину и время для АС (например: <code>спам 10м</code> или <code>нарушение навсегда</code>):")
        await callback.answer()

    elif action == 'blockname':
        await state.update_data(target_id=target_id)
        await state.set_state(EpiLabAdminStates.waiting_for_block_reason)
        await callback.message.answer("✍️ Введите причину и время для запрета смены имени/патогена (например: <code>недопустимое имя 2ч</code>):")
        await callback.answer()

    elif action == 'unblock':
        if hasattr(repo_biowar, 'game_mute_cancel'):
            await repo_biowar.game_mute_cancel(target_id)
        if hasattr(repo_biowar, 'bio_mute_cancel'):
            await repo_biowar.bio_mute_cancel(target_id)
        banned_users.pop(int(target_id), None)
        user_timestamps.pop(int(target_id), None)
        for prefix in ["epidemic_gamemute:", "gamemute:", "biomute:", "epidemic_biomute:"]:
            try:
                await redis.delete(f"{prefix}{target_id}")
            except Exception:
                pass
        await notify_owner_action(callback.from_user, "🔓 Снятие всех ограничений / АС", target_id, bot=callback.bot)
        await callback.answer(f"✅ Все ограничения и АС для {target_id} сняты!", show_alert=True)

    elif action == 'transfer':
        await state.update_data(target_id=target_id)
        await state.set_state(EpiLabAdminStates.waiting_for_transfer_target)
        await callback.message.answer("🔄 Введите <code>user_id</code>, <code>@username</code> или отправьте реплаем сообщение второго игрока для переноса лаборатории:")
        await callback.answer()

    elif action == 'reset':
        try:
            await repo_biowar.update_lab_skill_val(target_id, 'infect', 1)
            await repo_biowar.update_lab_skill_val(target_id, 'immunity', 1)
            await repo_biowar.update_lab_skill_val(target_id, 'lethality', 1)
            await repo_biowar.update_lab_skill_val(target_id, 'security_service', 1)
            await repo_biowar.update_lab_skill_val(target_id, 'science', 1)
            await repo_biowar.update_lab_skill_val(target_id, 'pathogens', 4)
            await repo_biowar.update_lab_skill_val(target_id, 'ready_pathogens', 0)
            await repo_biowar.update_lab_skill_val(target_id, 'bio_experience', 1000)
            await repo_biowar.update_lab_skill_val(target_id, 'bio_resource', 15000)

            await repo_biowar.pathogen_name_change(None, target_id)
            await repo_biowar.lab_name_change(None, target_id)

            await notify_owner_action(callback.from_user, "💣 Сброс параметров лаборатории (Обнул)", target_id, bot=callback.bot)
            await callback.answer("💣 Лаборатория успешно сброшена до начального уровня!", show_alert=True)
        except Exception as e:
            logger.error(f"Error reset lab {target_id}: {e}")
            await callback.answer("❌ Ошибка при сбросе лаборатории!", show_alert=True)
