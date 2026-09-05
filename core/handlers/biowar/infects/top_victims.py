from aiogram import Router, F
from aiogram.types import Message
from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from datetime import datetime

router = Router()

@router.message(F.text.lower().in_(["мж топ", "топ мж", "жертвы топ"]))
async def cmd_top_victims(msg: Message, repo_biowar: RequestsRepoBiowar):
    user_id = msg.from_user.id

    query = """
        SELECT victim_id, victim_bio_resource_earn, victim_expire
        FROM Victims
        WHERE victims_owner_id = %s AND victim_bio_resource_earn > 0
        ORDER BY victim_bio_resource_earn DESC
        LIMIT 20;
    """
    await repo_biowar.cur.execute(query, (user_id,))
    victims = await repo_biowar.cur.fetchall()

    if not victims:
        await msg.answer("📭 У вас нет жертв, которые приносят доход!")
        return

    lines = ["📊 <b>ТОП ЖЕРТВ ПО ДОХОДУ</b>\n"]

    for idx, victim in enumerate(victims, 1):
        if isinstance(victim, dict):
            victim_id = victim.get('victim_id')
            bio_earn = victim.get('victim_bio_resource_earn', 0) or 0
            victim_expire = victim.get('victim_expire', 0) or 0
        else:
            victim_id = victim[0]
            bio_earn = victim[1] or 0
            victim_expire = victim[2] or 0

        try:
            victim_info = await repo_biowar.get_info_user_lab(victim_id)
            if victim_info:
                victim_name = victim_info.get('full_name', f"ID {victim_id}")
            else:
                victim_name = f"ID {victim_id}"
        except:
            victim_name = f"ID {victim_id}"

        time_left = victim_expire - int(datetime.now().timestamp())
        if time_left <= 0:
            expire_str = "⚠️"
        elif time_left < 86400:
            hours = time_left // 3600
            minutes = (time_left % 3600) // 60
            expire_str = f"⏳ {hours}ч {minutes}м"
        else:
            days = time_left // 86400
            expire_str = f"⏳ {days}д"

        link = f'<a href="tg://openmessage?user_id={victim_id}">{victim_name}</a>'
        medals = ["🥇", "🥈", "🥉"]
        prefix = medals[idx - 1] if idx <= 3 else f"{idx}."

        lines.append(f"{prefix} {link} — <b>{bio_earn:,}</b> био/тик {expire_str}")

    await msg.answer("\n".join(lines), parse_mode="HTML")
