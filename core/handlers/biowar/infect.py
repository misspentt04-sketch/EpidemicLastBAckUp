import math
import random
from datetime import datetime, timedelta
from aiogram import types
from aiogram import Bot
from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.tricks.themes_data import get_theme_text

async def handle_infect(message: types.Message, bot: Bot, repo_biowar: RequestsRepoBiowar):
    attacker_id = message.from_user.id
    reply = message.reply_to_message

    if not reply or not reply.from_user:
        await message.reply("❌ Ответьте на сообщение пользователя, которого хотите заразить!")
        return

    target_id = reply.from_user.id
    if attacker_id == target_id:
        await message.reply("❌ Нельзя заразить самого себя!")
        return

    # Получаем данные через repo_biowar
    attacker_data = await repo_biowar.get_info_user_lab(attacker_id)
    target_data = await repo_biowar.get_info_user_lab(target_id)

    if not attacker_data or not target_data:
        await message.reply("❌ Один из пользователей не зарегистрирован в системе!")
        return

    pathogen_name = attacker_data.get('pathogen_name', "Стандартный штамм")
    pathogens_left = attacker_data.get('pathogens', 0)
    infect_lvl = attacker_data.get('infect', 1)
    fever_lvl = attacker_data.get('fever_lvl', 1)
    expire_days = attacker_data.get('expire_days', 1)
    immunity_lvl = target_data.get('immunity', 1)
    sb_lvl = target_data.get('sb_lvl', 0)

    # Количество попыток (можно добавить в repo_biowar)
    try_count = 1  # упрощенно

    if pathogens_left <= 0:
        await message.reply("⚠️ У вас закончились патогены для атаки!")
        return

    penetration_chance = min(95, max(5, int((infect_lvl / (infect_lvl + immunity_lvl)) * 100)))
    success = random.randint(1, 100) <= penetration_chance

    attacker_mention = message.from_user.get_mention(as_html=True)
    target_mention = reply.from_user.get_mention(as_html=True)
    target_name = reply.from_user.first_name or f"Игрок {target_id}"

    success_template = await get_theme_text(repo_biowar, attacker_id, "infect_success")
    fail_template = await get_theme_text(repo_biowar, attacker_id, "infect_failed")
    sb_template = await get_theme_text(repo_biowar, target_id, "sb_report")

    fever_time = fever_lvl * 10
    exp_gain = random.randint(3000, 70000)

    if success:
        # Списываем патогены
        await repo_biowar.execute_query(
            "UPDATE Lab SET pathogens = pathogens - 1 WHERE lab_id = %s;",
            attacker_id
        )

        text_attack = success_template.format(
            attacker_mention=attacker_mention,
            target_mention=target_mention,
            pathogen_name=pathogen_name,
            fever_time=fever_time,
            expire_days=expire_days,
            exp_gain=f"{exp_gain:,}"
        )
        await message.reply(text_attack, parse_mode="HTML")

        if sb_lvl > 0:
            try:
                text_sb = sb_template.format(
                    target_name=target_name,
                    attempts_count=try_count,
                    attacker_mention=attacker_mention
                )
                await bot.send_message(target_id, text_sb, parse_mode="HTML")
            except Exception:
                pass

    else:
        text_attack = fail_template.format(
            target_name=target_name,
            attacker_mention=attacker_mention,
            target_mention=target_mention,
            pathogens_left=pathogens_left - 1,
            penetration_chance=penetration_chance
        )
        await message.reply(text_attack, parse_mode="HTML")
