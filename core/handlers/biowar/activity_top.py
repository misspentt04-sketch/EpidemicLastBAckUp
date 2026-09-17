from aiogram import Router, F
from aiogram.types import Message
from asyncmy.pool import Pool
from asyncmy.cursors import DictCursor
from humanize import intcomma

from core.utils.activity import get_week_str

router = Router()


async def get_top_activity(pool: Pool, week: str = None, limit: int = 10):
    if not week:
        week = get_week_str()

    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute("""
                SELECT ap.user_id, ap.points, ap.farm_count, ap.infect_count,
                       u.full_name, u.username, l.lab_name
                FROM ActivityPoints ap
                LEFT JOIN Users u ON u.id = ap.user_id
                LEFT JOIN Lab l ON l.lab_id = ap.user_id
                WHERE ap.week_str = %s
                ORDER BY ap.points DESC
                LIMIT %s
            """, (week, limit))
            return await cur.fetchall()


def format_top(rows: list) -> str:
    from datetime import datetime, timedelta
    from core.settings import moscow_tz

    now = datetime.now(moscow_tz)
    # Ближайший понедельник 00:00
    days_until_monday = (7 - now.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    next_monday = (now + timedelta(days=days_until_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    reset_str = next_monday.strftime("%d.%m в 00:00")

    if not rows:
        return (
            "╔══════════════════════╗\n"
            "   📊 <b>ТОП АКТИВНОСТИ</b>\n"
            "╚══════════════════════╝\n\n"
            "<i>Пока нет данных за эту неделю.</i>\n\n"
            f"🔄 <i>Сброс: {reset_str}</i>"
        )

    text = (
        "╔══════════════════════╗\n"
        "   🏆 <b>ТОП АКТИВНОСТИ</b>\n"
        "╚══════════════════════╝\n\n"
        f"📅 <i>Неделя • сброс {reset_str}</i>\n\n"
    )

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    for i, row in enumerate(rows):
        uid = row["user_id"]
        name = row.get("lab_name") or row.get("full_name") or f"ID {uid}"
        username = row.get("username")
        points = row["points"] or 0
        farms = row.get("farm_count", 0) or 0
        infects = row.get("infect_count", 0) or 0

        if username:
            display = f'<a href="https://t.me/{username}">{name}</a>'
        else:
            display = f'<a href="tg://user?id={uid}">{name}</a>'

        medal = medals[i] if i < len(medals) else f"{i+1}."

        text += (
            f"{medal} {display} — <b>{intcomma(points)}</b> очк.\n"
        )

    text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    text += "🎁 <b>Награды топ-5:</b>\n"
    text += "🥇 2 💎  •  🥈 1 💎  •  🥉 1000 🪙\n"
    text += "4️⃣ 1 📦  •  5️⃣ 1 📦"

    return text


@router.message(F.text.lower() == "!топы")
async def cmd_top_activity(msg: Message, pool: Pool):
    try:
        week = get_week_str()
        rows = await get_top_activity(pool, week)
        text = format_top(rows)
        await msg.reply(text, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        print(f"[ACTIVITY TOP ERROR] {e}")
        await msg.reply(f"❌ Ошибка: {e}")
