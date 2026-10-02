from aiogram.filters import Command
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.text_decorations import html_decoration as hd
from aiogram.exceptions import TelegramBadRequest
from core.utils.db_api.settings_pool import db_pool
from datetime import datetime, timedelta
import time

router = Router()

# Антиспам кэш (user_id: timestamp)
_user_cooldowns = {}

class TopCallback(CallbackData, prefix="top"):
    period: str
    owner_id: int

def get_next_sunday_reset():
    now = datetime.now()
    days_until_sunday = (6 - now.weekday()) % 7
    if days_until_sunday == 0 and (now.hour > 23 or (now.hour == 23 and now.minute >= 59)):
        days_until_sunday = 7
    next_sunday = now + timedelta(days=days_until_sunday)
    return next_sunday.strftime("%d.%m.%Y в 23:59:59")

def get_last_day_of_month_reset():
    now = datetime.now()
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)
    last_day = next_month - timedelta(days=1)
    return last_day.strftime("%d.%m.%Y в 23:59:59")

async def get_top_text(period_type):
    pool = await db_pool.get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            if period_type == "w":
                title = "Топ заражений (за неделю)"
                date_filter = "AND (YEARWEEK(h.infect_date, 1) = YEARWEEK(NOW(), 1) OR h.week_str = DATE_FORMAT(NOW(), '%G-%V'))"
                reset_date = get_next_sunday_reset()
                reset_info = f"🔄 <i>Сброс: {reset_date}</i>"
            elif period_type == "m":
                title = "Топ заражений (за месяц)"
                date_filter = "AND (DATE_FORMAT(h.infect_date, '%Y-%m') = DATE_FORMAT(NOW(), '%Y-%m') OR h.month_str = DATE_FORMAT(NOW(), '%Y-%m'))"
                reset_date = get_last_day_of_month_reset()
                reset_info = f"🔄 <i>Сброс: {reset_date}</i>"
            else:
                title = "Топ заражений (за всё время)"
                date_filter = ""
                reset_info = "⏳ <i>Статистика за всё время (не сбрасывается)</i>"

            query = f"""
                SELECT h.attacker_id, COUNT(h.id) as cnt
                FROM biowar_infection_history h
                WHERE h.attacker_id != 123456789 {date_filter}
                GROUP BY h.attacker_id
                ORDER BY cnt DESC
                LIMIT 10;
            """
            await cur.execute(query)
            rows = await cur.fetchall()

            text = f"🏆 <b>{title}</b>\n\n"
            if not rows:
                text += "Пока нет данных.\n\n"
            else:
                for idx, row in enumerate(rows, start=1):
                    attacker_id = row.get('attacker_id') if isinstance(row, dict) else row[0]
                    count = row.get('cnt', 0) if isinstance(row, dict) else row[1]

                    name = None
                    try:
                        await cur.execute('SELECT lab_name FROM Lab WHERE lab_id = %s;', (attacker_id,))
                        lab_row = await cur.fetchone()
                        if lab_row:
                            name = lab_row.get('lab_name') if isinstance(lab_row, dict) else lab_row[0]
                    except Exception:
                        pass

                    if not name:
                        try:
                            await cur.execute('SELECT username FROM Users WHERE id = %s;', (attacker_id,))
                            user_row = await cur.fetchone()
                            if user_row:
                                name = user_row.get('username') if isinstance(user_row, dict) else user_row[0]
                        except Exception:
                            pass

                    if not name:
                        name = f"Лаборатория {attacker_id}"

                    escaped_name = hd.quote(str(name))
                    user_display = f"<a href=\"tg://openmessage?user_id={attacker_id}\">{escaped_name}</a>"

                    text += f"<b>{idx}.</b> {user_display} — <code>{count}</code> заражений\n"

            text += f"\n{reset_info}"
            return text

def get_keyboard(owner_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Неделя", callback_data=TopCallback(period="w", owner_id=owner_id).pack()),
            InlineKeyboardButton(text="📅 Месяц", callback_data=TopCallback(period="m", owner_id=owner_id).pack()),
            InlineKeyboardButton(text="⏳ Всё время", callback_data=TopCallback(period="a", owner_id=owner_id).pack())
        ]
    ])

@router.message(F.text.regexp(r"(?i)^топ\s+зар$"))
async def cmd_top_zar(message: Message):
    text = await get_top_text("a")
    await message.answer(text, parse_mode="HTML", reply_markup=get_keyboard(message.from_user.id))

@router.callback_query(TopCallback.filter())
async def top_callback(callback: CallbackQuery, callback_data: TopCallback):
    user_id = callback.from_user.id

    if user_id != callback_data.owner_id:
        await callback.answer("❌ Вы не можете переключать чужое меню!", show_alert=True)
        return

    now = time.time()
    last_time = _user_cooldowns.get(user_id, 0)
    if now - last_time < 1.0:
        await callback.answer("⏳ Не так быстро! Подождите секунду.", show_alert=False)
        return

    _user_cooldowns[user_id] = now
    text = await get_top_text(callback_data.period)

    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_keyboard(callback_data.owner_id))
        await callback.answer()
    except TelegramBadRequest:
        await callback.answer()
    except Exception:
        await callback.answer()

# ===== Кэш топа =====
_top_bio_cache = {"text": None, "expires_at": 0}
_TOP_BIO_TTL = 300  # 5 минут


@router.message(Command("top_bio"))
@router.message(F.text.regexp(r"(?i)^(топ\s+био)$"))
async def cmd_top_bio_tick(message: Message, **kwargs):
    now = time.time()

    # Кэш — если валиден, отдаём моментально
    if _top_bio_cache["text"] and _top_bio_cache["expires_at"] > now:
        return await message.answer(_top_bio_cache["text"], parse_mode="HTML", disable_web_page_preview=True)

    # === Шаг 1. Лёгкая агрегация по Victims (быстро, индекс) ===
    base_query = """
        SELECT victims_owner_id, SUM(victim_bio_resource_earn) AS base_tick
        FROM Victims
        WHERE victims_owner_id != 8236324289
        GROUP BY victims_owner_id
        ORDER BY base_tick DESC
        LIMIT 50;
    """

    async with db_pool._pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(base_query)
            rows = await cur.fetchall()

    if not rows:
        text = "🧪 <b>ТОП ПО БИО-ТИКУ</b>\n\n<i>Пока нет данных о жертвах.</i>"
        _top_bio_cache["text"] = text
        _top_bio_cache["expires_at"] = now + _TOP_BIO_TTL
        return await message.answer(text, parse_mode="HTML")

    # Собираем ID
    ids = []
    base_map = {}
    for r in rows:
        if isinstance(r, dict):
            uid = r.get("victims_owner_id")
            base = int(r.get("base_tick") or 0)
        else:
            uid = r[0]
            base = int(r[1] or 0)
        if uid:
            ids.append(uid)
            base_map[uid] = base

    if not ids:
        return await message.answer("🧪 <b>ТОП ПО БИО-ТИКУ</b>\n\n<i>Пусто.</i>", parse_mode="HTML")

    placeholders = ",".join(["%s"] * len(ids))

    async with db_pool._pool.acquire() as conn:
        async with conn.cursor() as cur:
            # === Шаг 2. Забираем rebirth_level, level корпы, hidden ===
            await cur.execute(
                f'SELECT lab_id, COALESCE(rebirth_level, 0) AS rl FROM Lab WHERE lab_id IN ({placeholders});',
                tuple(ids),
            )
            rl_rows = await cur.fetchall()
            rebirth_map = {}
            for r in rl_rows:
                if isinstance(r, dict):
                    rebirth_map[r["lab_id"]] = int(r.get("rl") or 0)
                else:
                    rebirth_map[r[0]] = int(r[1] or 0)

            await cur.execute(
                f'SELECT cm.member_id, COALESCE(c.level, 0) AS lvl '
                f'FROM CorporationMembers cm '
                f'LEFT JOIN Corporation c ON c.invitation_code = cm.corporation_code '
                f'WHERE cm.member_id IN ({placeholders});',
                tuple(ids),
            )
            corp_rows = await cur.fetchall()
            corp_map = {}
            for r in corp_rows:
                if isinstance(r, dict):
                    corp_map[r["member_id"]] = int(r.get("lvl") or 0)
                else:
                    corp_map[r[0]] = int(r[1] or 0)

            await cur.execute(
                f'SELECT lab_id FROM HiddenPlayers WHERE lab_id IN ({placeholders});',
                tuple(ids),
            )
            hidden_rows = await cur.fetchall()
            hidden_set = set()
            for r in hidden_rows:
                if isinstance(r, dict):
                    hidden_set.add(r["lab_id"])
                else:
                    hidden_set.add(r[0])

            # === Шаг 3. Забираем имена одним запросом ===
            await cur.execute(
                f'SELECT id, full_name FROM Users WHERE id IN ({placeholders});',
                tuple(ids),
            )
            user_rows = await cur.fetchall()
            name_map = {}
            for r in user_rows:
                if isinstance(r, dict):
                    name_map[r["id"]] = r.get("full_name")
                else:
                    name_map[r[0]] = r[1]

    # === Считаем итог и сортируем ===
    results = []
    for uid in ids:
        if uid in hidden_set:
            continue

        base = base_map.get(uid, 0)
        rl = rebirth_map.get(uid, 0)
        lvl = corp_map.get(uid, 0)

        # Бонус корпы
        if lvl >= 5:
            corp_bonus = 0.20
        elif lvl >= 4:
            corp_bonus = 0.10
        elif lvl >= 2:
            corp_bonus = 0.05
        else:
            corp_bonus = 0.0

        total = int(base * (1 + rl * 0.10) * (1 + corp_bonus))
        results.append((uid, total))

    results.sort(key=lambda x: x[1], reverse=True)
    results = results[:10]

    if not results:
        text = "🧪 <b>ТОП ПО БИО-ТИКУ</b>\n\n<i>Пусто.</i>"
        _top_bio_cache["text"] = text
        _top_bio_cache["expires_at"] = now + _TOP_BIO_TTL
        return await message.answer(text, parse_mode="HTML")

    # === Формируем текст ===
    medals = ["🥇", "🥈", "🥉"]
    lines = ["🧪 <b>ТОП ПО БИО-ТИКУ</b>\n"]

    for idx, (uid, total) in enumerate(results, 1):
        name = name_map.get(uid) or f"ID {uid}"
        prefix = medals[idx - 1] if idx <= 3 else f"{idx}."
        formatted = f"{total:,}".replace(",", " ")
        user_display = f'<a href="tg://openmessage?user_id={uid}">{name}</a>'
        lines.append(f"{prefix} {user_display} — <code>+{formatted}</code>/тик")

    text = "\n".join(lines)
    _top_bio_cache["text"] = text
    _top_bio_cache["expires_at"] = now + _TOP_BIO_TTL

    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)
