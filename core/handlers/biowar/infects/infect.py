from core.handlers.tricks.themes import get_user_theme
from core.data.tricks.themes_data import get_theme_text
import re
from core.data.tricks.themes_data import get_theme_text
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from asyncmy.cursors import Cursor
from redis.asyncio import Redis
from aiogram.types import Message
from aiogram import Bot

from aiogram.utils.markdown import hlink

from asyncio import Lock

from humanize import intcomma
from datetime import datetime, timedelta, timezone

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.texttriggers import deep_links
from core import func

from core.data.tricks.tricks_biowar import tricks_biowar

from core.settings import settings

import re
import random
import asyncio
import time


async def infect(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar, redis: Redis, lock: Lock):
    if await redis.get(f"epidemic_infect_cooldown:{msg.from_user.id}"):
        return
    await redis.set(f"epidemic_infect_cooldown:{msg.from_user.id}", "1", px=200)
    async with lock:
        id = msg.from_user.id
        chat_id = msg.chat.id
        attacker_id = msg.from_user.id
    id = msg.from_user.id
    chat_id = msg.chat.id
    parts = msg.text.split() if msg.text else []
    victimer_id = getattr(msg, "_override_target_id", None) or func.reply_or_tag_geeter(msg)
    digits = [int(p) for p in parts if p.isdigit()]
    if not victimer_id and len(parts) > 1 and parts[1].isdigit() and len(parts[1]) > 5:
        victimer_id = int(parts[1])

    if getattr(msg, "_override_target_id", None):
        spent_pathogens = 1
    else:
        raw_p = digits[-1] if digits else 1
        spent_pathogens = min(10, max(1, raw_p))
    is_tag = func.check_if_tag(msg)
    sb_answer = True
    pet_boost_exp = False

    # Random infect
    if not is_tag and re.findall(r'заразить (-|=|\+|слаб(ее|ый|ого)|равн(ее|ый|ого)|сильн(ее|ый|ого)|рандом|р)(|\s\d{1,2})', msg.text.lower()):
        lower_exp = higher_exp = None
        is_random = False
        if re.findall(r'заразить (-|слаб(ее|ый|ого))(|\s\d{1,2})', msg.text.lower()):
            lower_exp = 0
            higher_exp = 10
            sb_answer = False
        if re.findall(r'заразить (\+|сильн(ее|ый|ого))(|\s\d{1,2})', msg.text.lower()):
            higher_exp = 999999999999999
        if re.findall(r'заразить (рандом|р)(|\s\d{1,2})', msg.text.lower()):
            is_random = True
        attacker_id = msg.from_user.id
        infecter = await repo_biowar.get_info_user_lab(attacker_id)
        if is_random:
            victimer = await repo_biowar.get_random_victim(attacker_id)
        else:
            if lower_exp is None:
                lower_exp = 0 if infecter['bio_experience'] / 2 < 0 else infecter['bio_experience'] / 1.5
            if higher_exp is None:
                higher_exp = 10 * 5 if infecter['bio_experience'] < 10 else infecter['bio_experience'] * 5
            victimer = await repo_biowar.get_victim_by_infect_range(attacker_id, lower_exp, higher_exp)
        if victimer is None:
            return await msg.answer(tricks_biowar['text']['victim_not_found'])
    else: # Normal infect
        attacker_id = msg.from_user.id
        infecter = await repo_biowar.get_info_user_lab(attacker_id)
        victimer = await repo_biowar.get_info_user_lab(victimer_id)

    if victimer_id == settings.bots.bot_id:
        return await msg.answer(tricks_biowar['infect']['impossible_to_infect_bot'])
    if victimer is None:
        return await msg.answer(tricks_biowar['text']['not_info_about_user'])
    if spent_pathogens == 0:
        return await msg.answer(tricks_biowar['infect']['pathogen_count_zero'])
    if victimer['id'] == attacker_id:
        return await msg.answer(tricks_biowar['infect']['self_infect'])

    fever = func.fever_expire_difference_check(infecter['fever']) if infecter['fever'] else None
    pathogen_name = ('«' + infecter['pathogen_name'] + '»' if infecter['pathogen_name'] else 'неизвестным патогеном')
    fever_pathogen_name = (infecter['fever_pathogen_name'] if infecter['fever_pathogen_name'] else 'неизвестным патогеном')

    infecter_pet = await repo_biowar.get_my_pet(infecter['id'])

    if fever:
        try_heal_count = await redis.get(f'epidemic_pet_try_count_heal:{infecter["id"]}')
        if infecter_pet and infecter_pet['current_pet'] in ['Байлу'] and (try_heal_count == '0' or try_heal_count is None):
            await redis.set(f'epidemic_pet_try_count_heal:{infecter["id"]}', 1)
            try_heal_count = await redis.get(f'epidemic_pet_try_count_heal:{infecter["id"]}')
            if random.randint(1, 10) <= 4:
                await redis.set(f'epidemic_pet_try_count_heal:{infecter["id"]}', 0)
                await repo_biowar.buy_vaccine(0, infecter['id'])
                return await msg.answer(tricks_biowar['pet']['pet_skills_text']['байлу']['heal_fever'])
        return await msg.answer(tricks_biowar['infect']['fever'].format(
            fever_pathogen_name, fever
        ))


    victim_expire_kd_check = await repo_biowar.check_victim_expire(infecter['id'], victimer['id'])
    if victim_expire_kd_check != 0:
        return await msg.answer(tricks_biowar['text']['victim_expire_yes'].format(
            func.victim_expire_difference_check(victim_expire_kd_check)
        ))

    victimer_pet = await repo_biowar.get_my_pet(victimer['id'])

    vic_pet_vuln_indicator = 0
    if victimer_pet:
        if await redis.hget(victimer['id'], 'pet_vuln_indicator') is None:
            await redis.hset(victimer['id'], mapping={'pet_vuln_indicator': 100})
        vic_pet_vuln_indicator = float(await redis.hget(victimer['id'], 'pet_vuln_indicator'))

    vic_user_chat = await repo_biowar.get_user_chat(victimer['id'])

    ss_detect = 1 if infecter['security_service'] < victimer['security_service'] else 0
    inf_infect = infecter['infect']
    vic_immunity = victimer['immunity']
    science_time = int(time.time()) + (61 - infecter['science']) * 60

    inf_ready_pathogens_left = infecter['ready_pathogens'] - spent_pathogens

    inf_entity = func.entity_create(
        infecter['id'], infecter['full_name']
    )
    vic_entity_sb = hlink(victimer['full_name'], f'tg://user?id={victimer["id"]}')
    vic_entity = func.entity_create(
        victimer['id'], victimer['full_name']
    )
    vic_username_entity_inv = func.entity_create(
        (victimer['username'] if victimer['username'] else victimer['id']), '‎ ',
        (deep_links['link'] if victimer['username'] else deep_links['mention'])
    )

    sb_virus_detect_try_text = tricks_biowar['infect']['sb_virus_detect_try_text'].format(
        vic_entity, spent_pathogens, inf_entity, vic_entity_sb
    )
    if inf_ready_pathogens_left < 0:
        if infecter['ready_pathogens'] >= 1:
            spent_pathogens = infecter['ready_pathogens']
            inf_ready_pathogens_left = 0
        else:
            return await msg.answer(tricks_biowar['infect']['pathogens_over'])

    difference = inf_infect - vic_immunity
    if difference <= -222:
        return await msg.answer(
            f'❌ Вы не можете пробить, ведь у вас большая разница ({abs(difference)}).\n'
            f'Бить сможете, когда разница будет меньше 222.'
        )

    logging.info(f"[INFECT DEBUG] inf_infect={inf_infect}, vic_immunity={vic_immunity}, diff={difference}")
    CHANCES_GRID = {0: 100.0, -1: 75.0, -2: 50.0, -3: 40.0, -4: 25.0, -5: 15.0, -6: 13.2, -7: 11.4, -8: 9.6, -9: 7.8, -10: 6.0, -11: 5.87, -12: 5.75, -13: 5.62, -14: 5.5, -15: 5.37, -16: 5.25, -17: 5.12, -18: 5.0, -19: 4.87, -20: 4.75, -21: 4.62, -22: 4.5, -23: 4.37, -24: 4.25, -25: 4.12, -26: 4.0, -27: 3.87, -28: 3.75, -29: 3.62, -30: 3.5, -31: 3.37, -32: 3.25, -33: 3.12, -34: 3.0, -35: 2.87, -36: 2.75, -37: 2.62, -38: 2.5, -39: 2.37, -40: 2.25, -41: 2.12, -42: 2.0, -43: 1.87, -44: 1.75, -45: 1.62, -46: 1.5, -47: 1.37, -48: 1.25, -49: 1.12, -50: 1.0, -51: 0.982, -52: 0.964, -53: 0.946, -54: 0.928, -55: 0.91, -56: 0.892, -57: 0.874, -58: 0.856, -59: 0.838, -60: 0.82, -61: 0.802, -62: 0.784, -63: 0.766, -64: 0.748, -65: 0.73, -66: 0.712, -67: 0.694, -68: 0.676, -69: 0.658, -70: 0.64, -71: 0.622, -72: 0.604, -73: 0.586, -74: 0.568, -75: 0.55, -76: 0.532, -77: 0.514, -78: 0.496, -79: 0.478, -80: 0.46, -81: 0.442, -82: 0.424, -83: 0.406, -84: 0.388, -85: 0.37, -86: 0.352, -87: 0.334, -88: 0.316, -89: 0.298, -90: 0.28, -91: 0.262, -92: 0.244, -93: 0.226, -94: 0.208, -95: 0.19, -96: 0.172, -97: 0.154, -98: 0.136, -99: 0.118, -100: 0.1, -101: 0.095, -102: 0.091, -103: 0.086, -104: 0.082, -105: 0.078, -106: 0.074, -107: 0.07, -108: 0.067, -109: 0.063, -110: 0.06, -111: 0.057, -112: 0.054, -113: 0.052, -114: 0.049, -115: 0.047, -116: 0.044, -117: 0.042, -118: 0.04, -119: 0.038, -120: 0.036, -121: 0.034, -122: 0.033, -123: 0.031, -124: 0.029, -125: 0.028, -126: 0.027, -127: 0.025, -128: 0.024, -129: 0.023, -130: 0.022, -131: 0.021, -132: 0.02, -133: 0.019, -134: 0.018, -135: 0.017, -136: 0.016, -137: 0.015, -138: 0.014, -139: 0.014, -140: 0.013, -141: 0.012, -142: 0.012, -143: 0.011, -144: 0.011, -145: 0.01, -146: 0.0098, -147: 0.0093, -148: 0.0088, -149: 0.0084, -150: 0.008, -151: 0.0076, -152: 0.0072, -153: 0.0068, -154: 0.0065, -155: 0.0062, -156: 0.0059, -157: 0.0056, -158: 0.0053, -159: 0.005, -160: 0.0048, -161: 0.0045, -162: 0.0043, -163: 0.0041, -164: 0.0039, -165: 0.0037, -166: 0.0035, -167: 0.0033, -168: 0.0032, -169: 0.003, -170: 0.0029, -171: 0.0027, -172: 0.0026, -173: 0.0025, -174: 0.0023, -175: 0.0022, -176: 0.0021, -177: 0.002, -178: 0.0019, -179: 0.0018, -180: 0.0017, -181: 0.0016, -182: 0.0015, -183: 0.0015, -184: 0.0014, -185: 0.0013, -186: 0.0013, -187: 0.0012, -188: 0.0012, -189: 0.0011, -190: 0.0011, -191: 0.001, -192: 0.001, -193: 0.001, -194: 0.001, -195: 0.001, -196: 0.001, -197: 0.001, -198: 0.001, -199: 0.001, -200: 0.001}

    if difference >= 0:
        base_chance = 100.0
    elif difference in CHANCES_GRID:
        base_chance = CHANCES_GRID[difference]
    elif difference < -200:
        base_chance = 0.001
    else:
        base_chance = 1.0

    redis_key = f"infect_accum_bonus:{infecter['id']}:{victimer['id']}"
    accumulated_chance = await redis.get(redis_key)
    p_count = int(spent_pathogens) if spent_pathogens else 1
    step_multiplier = (1.0 + (p_count - 1) * 0.2722)

    if accumulated_chance is not None:
        add_step = (base_chance / 4.0) * step_multiplier
        raw_val = accumulated_chance.decode() if isinstance(accumulated_chance, bytes) else accumulated_chance
        total_chance = float(raw_val) + add_step
    else:
        total_chance = base_chance * step_multiplier

    await redis.set(redis_key, str(total_chance), ex=60)

    is_success = False
    actual_spent = spent_pathogens
    if random.uniform(0, 100) <= total_chance:
        is_success = True
        await redis.delete(redis_key)

    infect_chance = total_chance
    display_chance_str = f"{infect_chance:.4f}"
    if display_chance_str == "" or display_chance_str == "0":
        display_chance_str = f"{infect_chance:.10f}"

    if not is_success:
        await repo_biowar.subtract_pathogens(infecter['id'], spent_pathogens)

        if not infecter['science_time']:
            await repo_biowar.update_lab_skill_val(infecter['id'], 'science_time', science_time)

        if (
            ss_detect == 1
            and victimer['chat_setup_virus']
            and victimer['chat_setup_virus'] != chat_id
            and vic_user_chat
            and spent_pathogens >= 1
        ):
            await bot.send_message(victimer['chat_setup_virus'], sb_virus_detect_try_text)

        default_fail_msg = tricks_biowar['infect']['victim_immunity_fail'].format(
            vic_entity,
            inf_ready_pathogens_left,
            '',
            f'{display_chance_str}% '
        )
        custom_fail_template = await get_theme_text(repo_biowar, msg.from_user.id, 'infect_failed')
        if custom_fail_template:
            fail_text = custom_fail_template.format(
                target_name=vic_entity_sb, target_mention=vic_entity,
                pathogens_left=inf_ready_pathogens_left,
                penetration_chance=display_chance_str
            )
        else:
            fail_text = default_fail_msg

        return await msg.answer(fail_text)

    inf_fev_time = tricks_biowar['max']['time']['infect_fever_time'] / 60
    fever_time = int(infecter['lethality'] / 3)
    fever_time = (1 if fever_time == 0 else fever_time)

    now_ts = int(datetime.now(timezone.utc).timestamp())

    raw_fever = victimer.get('fever_expire') or victimer.get('fever') or 0
    if hasattr(raw_fever, 'timestamp'):
        current_fever = int(raw_fever.timestamp())
    elif isinstance(raw_fever, (int, float)):
        current_fever = int(raw_fever)
    else:
        current_fever = 0

    rem_seconds = max(0, current_fever - now_ts)

    add_seconds = fever_time * 60
    total_seconds = min(3600, rem_seconds + add_seconds)

    fever_expire = now_ts + total_seconds
    fever_time_ = fever_time

    lose_exp = int(round(victimer['bio_experience'] * tricks_biowar['max']['elements']['infect_claim_percent'], 0))
    earn_exp = int(round(
        victimer['bio_experience'] * (
        tricks_biowar['max']['elements']['infect_claim_percent']
        ), 0)
    )

    inf_pets_info = None
    if infecter_pet:
        inf_pets_info = tricks_biowar['pet']['pets_info'][infecter_pet['current_pet'].lower()]

    if infecter_pet and infecter_pet['current_pet'].lower() == 'первопроходец':
        pet_boost_exp = int(round(
            victimer['bio_experience'] * inf_pets_info['skill_val'],
        0))
        await repo_biowar.update_pet_boost_exp(infecter['id'], infecter['pet_boost_exp']+pet_boost_exp)
    if infecter_pet and infecter_pet['current_pet'].lower() == 'ам-ням':
        skill_val_rand = (0.03 if random.randint(1, 100) <= 5 else inf_pets_info['skill_val'])
        pet_boost_exp = int(round(
            victimer['bio_experience'] * skill_val_rand,
        0))
        await repo_biowar.update_pet_boost_exp(infecter['id'], infecter['pet_boost_exp']+pet_boost_exp)

    earn_exp = int(round(earn_exp / (1+(vic_immunity-inf_infect)/10/10) if vic_immunity > inf_infect else earn_exp, 0))
    lose_exp = int(round(lose_exp / (1+(vic_immunity-inf_infect)/10/10) if vic_immunity > inf_infect else lose_exp, 0))
    lose_exp = victimer['bio_experience'] - lose_exp

    earn_exp = 1 if earn_exp <= 0 else earn_exp
    earn_exp = max(1, int(earn_exp))
    vic_exp = 0 if lose_exp < 0 else lose_exp

    vic_expire = int((datetime.utcnow() + timedelta(days=infecter["lethality"])).timestamp())
    vic_expire_kd = int((datetime.utcnow() + timedelta(seconds=tricks_biowar['max']['time']['victim_kd_expire'])).timestamp())
    
    # Сначала ПРОВЕРЯЕМ, была ли жертва в базе ДО ВЫЗОВА infect_setup:
    check_victim = await repo_biowar.select_one(
        'SELECT victim_id FROM Victims WHERE victims_owner_id=%s AND victim_id=%s;',
        (infecter['id'], victimer['id'])
    )
    vic_new = (check_victim is None)
    
    infect_date = datetime.utcnow().timestamp()

    await redis.set(f'epidemic_pet_try_count_heal:{infecter["id"]}', 0)

    try:
        query_hist = "INSERT INTO biowar_infection_history (attacker_id, victim_id, week_str, month_str, infect_date) VALUES (%s, %s, DATE_FORMAT(NOW(), '%%x-%%V'), DATE_FORMAT(NOW(), '%%Y-%%m'), NOW());"
        await repo_biowar.cur.execute(query_hist, (infecter['id'], victimer['id']))
    except Exception as ex:
        print("Error inserting infection history:", ex)

    # И только ТЕПЕРЬ перезаписываем запись в базе
    # Сохраняем сколько опыта получили с этой жертвы
    await repo_biowar.execute(
        "UPDATE Victims SET last_earn_exp = %s WHERE victims_owner_id = %s AND victim_id = %s;",
        earn_exp, infecter['id'], victimer['id']
    )
    
    # Сохраняем предыдущий опыт в Redis перед обновлением
    await redis.set(f"last_earn:{infecter['id']}:{victimer['id']}", earn_exp)
    
    # Блокировка от дупа
    lock_key = f"epidemic_infect_lock:{victimer_id}"
    if await redis.get(lock_key):
        return await msg.answer("⏳ Жертва уже заражена другим игроком! Попробуйте позже.")
    await redis.set(lock_key, "1", ex=2)  # Блокировка на 2 секунды
    
    # Проверяем, не заражена ли жертва уже кем-то другим
    
    
    # Если всё ок — закрепляем блокировку
    await redis.set(lock_key, "1", ex=2)
    await repo_biowar.infect_setup(
        infecter['id'], victimer['id'], earn_exp, vic_exp,
        vic_expire_kd, inf_ready_pathogens_left,
        fever_expire, vic_expire,
        infect_date, pathogen_name, ss_detect,
        science_time, infecter['science_time'], pet_boost_exp
    )

    # Формируем текст
    default_success_msg = tricks_biowar['infect']['infect'].format(
        inf_entity, pathogen_name, vic_entity, fever_time_,
        infecter["lethality"], intcomma(earn_exp), vic_username_entity_inv,
        tricks_biowar['text']['victim_new'].format(intcomma(earn_exp)) if vic_new else ''
    )

    custom_success_template = await get_theme_text(repo_biowar, msg.from_user.id, 'infect_success')
    print(f"[TEXT DEBUG] custom_success_template: {repr(custom_success_template)}")
    if custom_success_template:
        p_name = pathogen_name if pathogen_name else "Неизвестный патоген"
        try:
            if not vic_new:
                t_lines = custom_success_template.splitlines()
                t_lines = [l for l in t_lines if not l.strip().startswith("✨")]
                template_to_use = chr(10).join(t_lines)
            else:
                template_to_use = custom_success_template

            text = template_to_use.format(
                attacker_mention=inf_entity,
                target_name=vic_entity_sb,
                target_mention=vic_entity,
                pathogen_name=p_name,
                fever_time=fever_time_,
                expire_days=infecter["lethality"],
                exp_gain=intcomma(earn_exp)
            )
        except Exception as e:
            print(f"[INFECT SUCCESS FORMAT ERROR] {e}")
            text = default_success_msg
    else:
        text = default_success_msg
    sb_virus_detect_text = tricks_biowar['infect']['sb_virus_detect'].format(
        vic_entity, spent_pathogens, inf_entity,
        inf_entity, pathogen_name, vic_entity_sb, fever_time_,
        infecter["lethality"], intcomma(earn_exp),
        tricks_biowar['text']['victim_new'].format(intcomma(earn_exp)) if vic_new else ''
    )

    inf_sb = infecter.get('security_service', 0)
    vic_sb = victimer.get('security_service', 0)
    display_attacker = "<b>Неизвестная лаборатория</b> 🕵️‍♂️" if inf_sb > vic_sb else inf_entity

    custom_infected_you_template = await get_theme_text(repo_biowar, victimer.get('user_id', victimer.get('id')), 'infected_you')
    if custom_infected_you_template:
        sb_virus_not_detect_text = custom_infected_you_template.format(
            attacker_mention=display_attacker,
            
            fever_time=fever_time_,
            expire_days=infecter["lethality"],
            pathogen_name=infecter.get("pathogen_name", "вирус")
        )
    else:
        sb_virus_not_detect_text = tricks_biowar['infect']['sb_virus_not_detect_text'].format(
            pathogen_name, vic_entity_sb, fever_time_, infecter["lethality"]
        )

    await msg.answer(text, disable_web_page_preview=True)
    try:
        if (
            sb_answer is True
            and
            victimer['chat_setup_virus'] and victimer['chat_setup_virus'] != chat_id
            and
            (vic_user_chat if victimer['chat_setup_virus'] == victimer['id'] else True)
        ):
            await asyncio.sleep(0.1)
            await bot.send_message(
                victimer['chat_setup_virus'],
                sb_virus_detect_text if ss_detect == 1 else sb_virus_not_detect_text
            )
    except:
        pass


async def extract_target_user_id(message, bot: Bot):
    if message.reply_to_message:
        r = message.reply_to_message
        if r.from_user:
            return r.from_user.id
        if r.forward_from:
            return r.forward_from.id

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return None

    arg = args[1].strip()

    if "user_id=" in arg:
        m = re.search(r"user_id=(\d+)", arg)
        if m:
            return int(m.group(1))

    clean_arg = arg.lstrip("@")
    if clean_arg.isdigit():
        return int(clean_arg)

    if "t.me/" in arg:
        clean_arg = arg.split("t.me/")[-1].split("/")[0].strip("@")
    elif arg.startswith("@"):
        clean_arg = arg[1:]

    if clean_arg and not clean_arg.isdigit():
        try:
            chat_member = await bot.get_chat(clean_arg)
            return chat_member.id
        except Exception:
            pass

    return None

async def cmd_check_victim(message: Message, bot: Bot, repo_biowar: RequestsRepoBiowar):
    text_clean = message.text.strip()
    parts = text_clean.split()

    arg = parts[1] if len(parts) >= 2 else None

    if arg and arg.isdigit() and not message.reply_to_message:
        return

    target_id = None
    requested_idx = None
    victim_data = None
    owner_id = message.from_user.id
    victims = await repo_biowar.get_victims(owner_id)

    if message.reply_to_message and arg and arg.isdigit():
        requested_idx = int(arg)
        r = message.reply_to_message
        user_ids_in_order = []

        entities = r.entities or r.caption_entities or []
        for entity in entities:
            if entity.type == "text_link" and entity.url:
                if "user_id=" in entity.url:
                    try:
                        uids = re.findall(r"\d+", entity.url)
                        if uids:
                            uid = int(uids[0])
                        if uid not in user_ids_in_order:
                            user_ids_in_order.append(uid)
                    except ValueError:
                        pass

        if not user_ids_in_order:
            r_text = r.text or r.caption or ""
            found_links = re.findall(r"user_id=(\d+)", r_text)
            for uid_str in found_links:
                uid = int(uid_str)
                if uid not in user_ids_in_order:
                    user_ids_in_order.append(uid)

        idx = requested_idx - 1
        if 0 <= idx < len(user_ids_in_order):
            target_id = user_ids_in_order[idx]
        else:
            await message.reply(f"❌ Игрок под номером {requested_idx} не найден в этом списке.")
            return

    else:
        r_id = None

        if arg:
            found_ids = re.findall(r"\d{7,}", arg)
            if found_ids:
                r_id = int(found_ids[0])
            elif arg.isdigit():
                r_id = int(arg)

        if not r_id and message.reply_to_message:
            r = message.reply_to_message
            if r.from_user:
                r_id = r.from_user.id
            elif r.forward_from:
                r_id = r.forward_from.id
            else:
                r_text = r.text or r.caption or ""
                found_ids = re.findall(r"\d{7,}", r_text)
                if found_ids:
                    r_id = int(found_ids[0])

        target_id = r_id

    if not target_id:
        return

    if victims:
        keys_to_check = ["victim_id", "user_id", "id"]
        for v in victims:
            for key in keys_to_check:
                v_id = v.get(key)
                if v_id is not None and int(v_id) == target_id:
                    victim_data = v
                    break
            if victim_data:
                break

    if not victim_data:
        try:
            lab_info = await repo_biowar.get_lab(target_id)
            if lab_info:
                victim_data = {
                    "victim_id": target_id,
                    "victim_bio_resource_earn": 0,
                    "victim_expire": 0,
                    **lab_info
                }
        except Exception as e:
            print(f"[DEBUG] Could not fetch lab directly: {e}")

    if not victim_data:
        victim_data = {
            "victim_id": target_id,
            "victim_bio_resource_earn": 0,
            "victim_expire": 0
        }

    bio_earn = victim_data.get("victim_bio_resource_earn", 0)
    expire_time = victim_data.get("victim_expire", 0)
    left_seconds = expire_time - int(time.time())

    if left_seconds <= 0:
        time_str = "Срок истек или не заражен"
    else:
        d, rem = divmod(left_seconds, 86400)
        h, rem = divmod(rem, 3600)
        m = rem // 60
        parts_time = []
        if d > 0: parts_time.append(f"{d}д")
        if h > 0 or d > 0: parts_time.append(f"{h}ч")
        parts_time.append(f"{m}м")
        time_str = " ".join(parts_time)

    fbio = f"{bio_earn:,}".replace(",", " ")

    header_info = f"Жертва (#{requested_idx})" if requested_idx else "Жертва"
    link_url = f"tg://openmessage?user_id={target_id}"
    response_text = f"🧬 {header_info}: <a href='{link_url}'>ссылка на игрока</a>\n💰 Приносит: {fbio} био-ресурсов.\n⏳ Осталось: {time_str}."

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="💥 Ебнуть", callback_data=f"hit_target:{target_id}:{owner_id}")
    ]])
    await message.reply(response_text, parse_mode="HTML", reply_markup=kb)


async def hit_target_callback(callback: CallbackQuery, bot: Bot, db, repo_biowar: RequestsRepoBiowar, redis: Redis, lock: Lock):
    try:
        await callback.answer()
    except Exception:
        pass

    lock_key = f"strict_hit_lock:{callback.message.chat.id}:{callback.message.message_id}"
    if await redis.get(lock_key):
        return
    await redis.set(lock_key, "1", ex=30)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    data_parts = callback.data.split(':')
    if len(data_parts) < 2:
        return

    try:
        target_id = int(data_parts[1])
    except ValueError:
        return

    owner_id = int(data_parts[2]) if len(data_parts) > 2 and data_parts[2].isdigit() else None

    if not owner_id and callback.message.reply_to_message and callback.message.reply_to_message.from_user:
        owner_id = callback.message.reply_to_message.from_user.id

    is_admin = False
    try:
        user_data = await repo_biowar.get_user(callback.from_user.id)
        if user_data and (getattr(user_data, 'is_admin', False) or getattr(user_data, 'role', '') in ['admin', 'owner', 'creator']):
            is_admin = True
    except Exception:
        pass

    try:
        from core.settings import settings
        admin_ids = getattr(settings.bots, 'admin_ids', [])
        if not isinstance(admin_ids, (list, tuple, set)):
            admin_ids = [admin_ids]
        if callback.from_user.id in admin_ids or callback.from_user.id == getattr(settings.bots, 'admin_id', None):
            is_admin = True
    except Exception:
        pass

    if owner_id and callback.from_user.id != owner_id and not is_admin:
        return await callback.answer('❌ Это не твоя кнопка!', show_alert=True)

    if callback.from_user.id == target_id:
        return await callback.answer('❌ Нельзя атаковать самого себя!', show_alert=True)

    fake_message = callback.message.model_copy(update={
        'from_user': callback.from_user,
        'text': f'заразить {target_id} 1',
        'reply_to_message': None
    })
    setattr(fake_message, '_override_target_id', target_id)

    await infect(msg=fake_message, bot=bot, db=db, repo_biowar=repo_biowar, redis=redis, lock=lock)

# ===== ПРОВЕРКА БУСТЕРА =====
