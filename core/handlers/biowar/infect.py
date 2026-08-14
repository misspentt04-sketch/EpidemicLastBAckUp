import math
import random
from datetime import datetime, timedelta
from aiogram import types
from core.loader import dp, bot, db
from core.data.tricks.themes_data import get_theme_text

async def handle_infect(message: types.Message):
    attacker_id = message.from_user.id
    reply = message.reply_to_message

    if not reply or not reply.from_user:
        await message.reply("❌ Ответьте на сообщение пользователя, которого хотите заразить!")
        return

    target_id = reply.from_user.id
    if attacker_id == target_id:
        await message.reply("❌ Нельзя заразить самого себя!")
        return

    async with db.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT pathogen_name, pathogens, infect_lvl, fever_lvl, expire_days, bio_exp, bio_res FROM Users WHERE id = %s", (attacker_id,))
            attacker_data = await cur.fetchone()
            
            await cur.execute("SELECT immunity_lvl, sb_lvl FROM Users WHERE id = %s", (target_id,))
            target_data = await cur.fetchone()

            # Количество попыток против этой жертвы
            await cur.execute("SELECT COUNT(*) FROM AttackLogs WHERE attacker_id = %s AND target_id = %s", (attacker_id, target_id))
            attack_count_res = await cur.fetchone()
            try_count = (attack_count_res[0] if attack_count_res else 0) + 1

    if not attacker_data or not target_data:
        await message.reply("❌ Один из пользователей не зарегистрирован в системе!")
        return

    pathogen_name = attacker_data[0] or "Стандартный штамм"
    pathogens_left = attacker_data[1]
    infect_lvl = attacker_data[2] or 1
    fever_lvl = attacker_data[3] or 1
    expire_days = attacker_data[4] or 1
    immunity_lvl = target_data[0] or 1
    sb_lvl = target_data[1] or 0

    if pathogens_left <= 0:
        await message.reply("⚠️ У вас закончились патогены для атаки!")
        return

    penetration_chance = min(95, max(5, int((infect_lvl / (infect_lvl + immunity_lvl)) * 100)))
    success = random.randint(1, 100) <= penetration_chance

    # Форматирование имён и упоминаний
    attacker_mention = message.from_user.get_mention(as_html=True)
    target_mention = reply.from_user.get_mention(as_html=True)
    target_name = reply.from_user.first_name or f"Игрок {target_id}"

    success_template = await get_theme_text(db, attacker_id, "infect_success")
    fail_template = await get_theme_text(db, attacker_id, "infect_failed")
    sb_template = await get_theme_text(db, target_id, "sb_report")

    fever_time = fever_lvl * 10
    exp_gain = random.randint(3000, 70000) # Динамический опыт
    res_gain = exp_gain

    if success:
        # 1. Сообщение в чат об успешной атаке
        text_attack = success_template.format(
            attacker_mention=attacker_mention,
            target_mention=target_mention,
            pathogen_name=pathogen_name,
            fever_time=fever_time,
            expire_days=expire_days,
            exp_gain=f"{exp_gain:,}",
            res_gain=f"{res_gain:,}"
        )
        await message.reply(text_attack, parse_mode="HTML")

        # 2. Уведомление СБ жертве (если прокачана СБ)
        if sb_lvl > 0:
            try:
                text_sb = sb_template.format(
                    target_name=target_name,
                    try_count=try_count,
                    attacker_mention=attacker_mention
                )
                await bot.send_message(target_id, text_sb, parse_mode="HTML")
            except Exception:
                pass

    else:
        # Неуспешная атака
        text_attack = fail_template.format(
            target_name=target_name,
            attacker_mention=attacker_mention,
            target_mention=target_mention,
            pathogens_left=pathogens_left - 1,
            penetration_chance=penetration_chance
        )
        await message.reply(text_attack, parse_mode="HTML")
