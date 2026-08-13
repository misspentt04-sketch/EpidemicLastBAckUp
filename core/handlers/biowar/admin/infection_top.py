from aiogram.filters import Command
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.text_decorations import html_decoration as hd
from core.utils.db_api.settings_pool import db_pool
from datetime import datetime, timedelta

router = Router()

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
                # Используем надежную фильтрацию по YEARWEEK (ISO 1 mode)
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

def get_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Неделя", callback_data="top_w"),
            InlineKeyboardButton(text="📅 Месяц", callback_data="top_m"),
            InlineKeyboardButton(text="⏳ Всё время", callback_data="top_a")
        ]
    ])

@router.message(F.text.regexp(r"(?i)^топ\s+зар$"))
async def cmd_top_zar(message: Message):
    text = await get_top_text("a")
    await message.answer(text, parse_mode="HTML", reply_markup=get_keyboard())

@router.callback_query(F.data.in_({"top_w", "top_m", "top_a"}))
async def top_callback(callback: CallbackQuery):
    p_type = callback.data.split("_")[1] # w, m, a
    text = await get_top_text(p_type)

    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_keyboard())
    except Exception:
        pass
    await callback.answer()


@router.message(Command("top_bio"))


@router.message(Command("top_bio"))


@router.message(Command("top_bio"))


@router.message(Command("top_bio"))


@router.message(Command("top_bio"))


@router.message(Command("top_bio"))


@router.message(Command("top_bio"))


@router.message(Command("top_bio"))


@router.message(Command("top_bio"))


@router.message(Command("top_bio"))


@router.message(Command("top_bio"))


@router.message(Command("top_bio"))


@router.message(Command("top_bio"))
@router.message(F.text.regexp(r"(?i)^(топ\\s+(био|биовойн[аы]))$"))
async def cmd_top_bio_tick(message: Message, **kwargs):
    query = """
        SELECT victims_owner_id, SUM(victim_bio_resource_earn) AS total_tick
        FROM Victims
        WHERE victims_owner_id != 8236324289
        GROUP BY victims_owner_id
        ORDER BY total_tick DESC
        LIMIT 10;
    """
    
    async with db_pool._pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query)
            rows = await cur.fetchall()

    if not rows:
        await message.answer("🧪 <b>ТОП ЛАБОРАТОРИЙ ПО ТИКУ</b>\n\n<i>Пока нет данных о жертвах.</i>", parse_mode="HTML")
        return

    medals = ["🥇", "🥈", "🥉"]
    lines = ["🧪 <b>ТОП ЛАБОРАТОРИЙ ПО ТИКУ</b>\n"]

    for idx, row in enumerate(rows, 1):
        if isinstance(row, dict):
            owner_id = row.get("victims_owner_id")
            total_tick = row.get("total_tick", 0) or 0
        else:
            owner_id = row[0]
            total_tick = row[1] if len(row) > 1 and row[1] is not None else 0

        prefix = medals[idx - 1] if idx <= 3 else f"{idx}."
        formatted_tick = f"{int(total_tick):,}".replace(",", " ")

        lines.append(f"{prefix} @{owner_id} — <code>+{formatted_tick}</code>/тик")

    await message.answer("\n".join(lines), parse_mode="HTML")
