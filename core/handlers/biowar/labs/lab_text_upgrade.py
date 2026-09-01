from aiogram import Router, types, F
from asyncmy.cursors import Cursor
from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.tricks.tricks_biowar import tricks_biowar
from core.keyboards.inline.lab import lab_confirm_upgrade, lab_confirm_upgrade_extend
from core import func
from humanize import intcomma

text_upgrade_router = Router()

SKILL_MAP = {
    "зз": "infect",
    "заразность": "infect",
    "иммун": "immunity",
    "иммунитет": "immunity",
    "летал": "lethality",
    "летальность": "lethality",
    "сб": "security_service",
    "безопасность": "security_service",
    "пат": "pathogens",
    "патоген": "pathogens",
    "квала": "science",
    "разработка": "science"
}

async def handle_text_upgrade(msg: types.Message, db: Cursor, repo_biowar: RequestsRepoBiowar):
    text = msg.text.strip()
    
    plus_count = 0
    for char in text:
        if char == '+':
            plus_count += 1
        else:
            break

    clean_text = text[plus_count:].strip().lower()
    args = clean_text.split()
    
    if not args:
        return

    raw_skill = args[0]
    if raw_skill not in SKILL_MAP:
        return

    user_id = msg.from_user.id
    lab_info = await repo_biowar.get_info_user_lab(user_id)
    if not lab_info:
        return

    skill = SKILL_MAP[raw_skill]
    
    lvl = 1
    if len(args) > 1 and args[1].isdigit():
        lvl = int(args[1])
        if lvl < 1:
            lvl = 1
        if lvl > 5:
            lvl = 5

    from_lvl = lab_info[skill]
    to_lvl = from_lvl + lvl
    science_max_lvl = tricks_biowar['max']['skill']['science']

    if skill == 'science':
        if to_lvl > science_max_lvl:
            return await msg.reply(tricks_biowar['lab']['max_level_up_limit'].format(tricks_biowar['lvlup_en_to_ru'][skill]))
        science_minutes = science_max_lvl - to_lvl + 1
    else:
        science_minutes = to_lvl

    rebirth_lvl = lab_info.get("rebirth_level", 0) or 0
    discount = min(rebirth_lvl * 0.025, 0.10)
    price = int(func.lvl_up_calc(skill, from_lvl, to_lvl) * (1 - discount))

    # 1 плюс (+) — превью и кнопка подтверждения
    if plus_count == 1:
        text_resp = tricks_biowar['skills_lvl'][skill].format(lvl, science_minutes, intcomma(price), lvl)
        await msg.reply(text_resp, reply_markup=lab_confirm_upgrade(skill, lvl, user_id))
        return

    # 2 плюса (++) — моментальная прокачка с кнопками 1x/3x/5x
    bio_resource_remainder = lab_info['bio_resource'] - price

    if bio_resource_remainder >= 0:
        if skill == 'pathogens':
            await repo_biowar.update_lab_skill_val(user_id, 'ready_pathogens', lab_info['ready_pathogens'] + lvl)

        await repo_biowar.update_lab_lvlup(user_id, skill, to_lvl, bio_resource_remainder)
        text_resp = tricks_biowar['skills_lvl'][f'{skill}_complete'].format(lvl, science_minutes, intcomma(price))
        await msg.reply(text_resp, reply_markup=lab_confirm_upgrade_extend(skill, user_id))
    else:
        await msg.reply(tricks_biowar['text']['not_enough_resources'])

# ===== КОРОТКИЕ КОМАНДЫ ДЛЯ ПРОКАЧКИ =====
@text_upgrade_router.message(F.text.lower().startswith("+зз"))
async def cmd_upgrade_infect(msg: types.Message, db: Cursor, repo_biowar: RequestsRepoBiowar):
    await handle_upgrade(msg, db, repo_biowar, "infect")

@text_upgrade_router.message(F.text.lower().startswith("+иммун"))
async def cmd_upgrade_immunity(msg: types.Message, db: Cursor, repo_biowar: RequestsRepoBiowar):
    await handle_upgrade(msg, db, repo_biowar, "immunity")

@text_upgrade_router.message(F.text.lower().startswith("+летал"))
async def cmd_upgrade_lethality(msg: types.Message, db: Cursor, repo_biowar: RequestsRepoBiowar):
    await handle_upgrade(msg, db, repo_biowar, "lethality")

@text_upgrade_router.message(F.text.lower().startswith("+сб"))
async def cmd_upgrade_security(msg: types.Message, db: Cursor, repo_biowar: RequestsRepoBiowar):
    await handle_upgrade(msg, db, repo_biowar, "security_service")

@text_upgrade_router.message(F.text.lower().startswith("+пат"))
async def cmd_upgrade_pathogens(msg: types.Message, db: Cursor, repo_biowar: RequestsRepoBiowar):
    await handle_upgrade(msg, db, repo_biowar, "pathogens")

@text_upgrade_router.message(F.text.lower().startswith("+квала"))
async def cmd_upgrade_science(msg: types.Message, db: Cursor, repo_biowar: RequestsRepoBiowar):
    await handle_upgrade(msg, db, repo_biowar, "science")

async def handle_upgrade(msg: types.Message, db: Cursor, repo_biowar: RequestsRepoBiowar, skill: str):
    user_id = msg.from_user.id
    lab_info = await repo_biowar.get_info_user_lab(user_id)
    if not lab_info:
        return

    # Парсим количество уровней
    text = msg.text.lower()
    parts = text.split()
    lvl = 1
    if len(parts) > 1 and parts[1].isdigit():
        lvl = int(parts[1])
        if lvl < 1:
            lvl = 1
        if lvl > 5:
            lvl = 5

    from_lvl = lab_info[skill]
    to_lvl = from_lvl + lvl
    science_max_lvl = tricks_biowar['max']['skill']['science']

    if skill == 'science':
        if to_lvl > science_max_lvl:
            return await msg.reply(tricks_biowar['lab']['max_level_up_limit'].format(tricks_biowar['lvlup_en_to_ru'][skill]))
        science_minutes = science_max_lvl - to_lvl + 1
    else:
        science_minutes = to_lvl

    rebirth_lvl = lab_info.get("rebirth_level", 0) or 0
    discount = min(rebirth_lvl * 0.025, 0.10)
    price = int(func.lvl_up_calc(skill, from_lvl, to_lvl) * (1 - discount))

    # Если 2 плюса (++зз) — моментальная прокачка
    if text.startswith("++"):
        bio_resource_remainder = lab_info['bio_resource'] - price
        if bio_resource_remainder >= 0:
            if skill == 'pathogens':
                await repo_biowar.update_lab_skill_val(user_id, 'ready_pathogens', lab_info['ready_pathogens'] + lvl)
            await repo_biowar.update_lab_lvlup(user_id, skill, to_lvl, bio_resource_remainder)
            text_resp = tricks_biowar['skills_lvl'][f'{skill}_complete'].format(lvl, science_minutes, intcomma(price))
            await msg.reply(text_resp, reply_markup=lab_confirm_upgrade_extend(skill, user_id))
        else:
            await msg.reply(tricks_biowar['text']['not_enough_resources'])
    else:
        # 1 плюс — превью и кнопка подтверждения
        text_resp = tricks_biowar['skills_lvl'][skill].format(lvl, science_minutes, intcomma(price), lvl)
        await msg.reply(text_resp, reply_markup=lab_confirm_upgrade(skill, lvl, user_id))

# ===== ПОЛНЫЕ КОМАНДЫ =====
@text_upgrade_router.message(F.text.lower().startswith("+заразность"))
async def cmd_upgrade_infect_full(msg: types.Message, db: Cursor, repo_biowar: RequestsRepoBiowar):
    await handle_upgrade(msg, db, repo_biowar, "infect")

@text_upgrade_router.message(F.text.lower().startswith("+иммунитет"))
async def cmd_upgrade_immunity_full(msg: types.Message, db: Cursor, repo_biowar: RequestsRepoBiowar):
    await handle_upgrade(msg, db, repo_biowar, "immunity")

@text_upgrade_router.message(F.text.lower().startswith("+летальность"))
async def cmd_upgrade_lethality_full(msg: types.Message, db: Cursor, repo_biowar: RequestsRepoBiowar):
    await handle_upgrade(msg, db, repo_biowar, "lethality")

@text_upgrade_router.message(F.text.lower().startswith("+безопасность"))
async def cmd_upgrade_security_full(msg: types.Message, db: Cursor, repo_biowar: RequestsRepoBiowar):
    await handle_upgrade(msg, db, repo_biowar, "security_service")

@text_upgrade_router.message(F.text.lower().startswith("+патоген"))
async def cmd_upgrade_pathogens_full(msg: types.Message, db: Cursor, repo_biowar: RequestsRepoBiowar):
    await handle_upgrade(msg, db, repo_biowar, "pathogens")

@text_upgrade_router.message(F.text.lower().startswith("+разработка"))
async def cmd_upgrade_science_full(msg: types.Message, db: Cursor, repo_biowar: RequestsRepoBiowar):
    await handle_upgrade(msg, db, repo_biowar, "science")
