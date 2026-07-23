from asyncmy.cursors import Cursor
from redis.asyncio import Redis
from aiogram.types import Message
from aiogram import Bot

from aiogram.utils.markdown import hlink

from asyncio import Lock

from humanize import intcomma
from datetime import datetime, timedelta

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.texttriggers import deep_links
from core import func

from core.data.tricks.tricks_biowar import tricks_biowar

from core.settings import settings

import re
import random
import asyncio


async def infect(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar, redis: Redis, lock: Lock):
  async with lock:
    id = msg.from_user.id
    chat_id = msg.chat.id
    victimer_id = func.reply_or_tag_geeter(msg)
    parts = msg.text.split()
    spent_pathogens = int(parts[1]) if parts[:2][-1].isdigit() else 1
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
        infecter = await repo_biowar.get_info_user_lab(id)
        if is_random:
            victimer = await repo_biowar.get_random_victim(id)
        else:
            if lower_exp is None:
                lower_exp = 0 if infecter['bio_experience'] / 2 < 0 else infecter['bio_experience'] / 1.5
            if higher_exp is None:
                higher_exp = 10 * 5 if infecter['bio_experience'] < 10 else infecter['bio_experience'] * 5
            victimer = await repo_biowar.get_victim_by_infect_range(id, lower_exp, higher_exp)
        if victimer is None:
            return await msg.answer(tricks_biowar['text']['victim_not_found'])
    else: # Normal infect
        infecter = await repo_biowar.get_info_user_lab(id)
        victimer = await repo_biowar.get_info_user_lab(victimer_id)
    
    
    if victimer_id == settings.bots.bot_id:
        return await msg.answer(tricks_biowar['infect']['impossible_to_infect_bot'])
    if victimer is None:
        return await msg.answer(tricks_biowar['text']['not_info_about_user'])
    if spent_pathogens > 10:
        return await msg.answer(tricks_biowar['infect']['pathogen_count_limit'].format(10))
    if spent_pathogens == 0:
        return await msg.answer(tricks_biowar['infect']['pathogen_count_zero'])
    if victimer['id'] == id:
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
            await redis.hset(victimer['id'], mapping={
                'pet_vuln_indicator': 100
                }
            )
        vic_pet_vuln_indicator = float(await redis.hget(victimer['id'], 'pet_vuln_indicator'))
    
    vic_user_chat = await repo_biowar.get_user_chat(victimer['id'])
    
    ss_detect = 1 if infecter['security_service'] < victimer['security_service'] else 0
    inf_infect = infecter['infect']
    vic_immunity = victimer['immunity']
    science_time = int((datetime.utcnow() + timedelta(minutes=(61-infecter['science']))).timestamp())
    
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
        vic_entity, spent_pathogens, inf_entity,
        vic_entity_sb
    )
    if inf_ready_pathogens_left < 0:
        if infecter['ready_pathogens'] >= 1:
            spent_pathogens = infecter['ready_pathogens']
            inf_ready_pathogens_left = 0
        else:
            return await msg.answer(tricks_biowar['infect']['pathogens_over'])
    
    difference = inf_infect - vic_immunity

    if difference >= 0:
        infect_chance = 100
    else:
        table = {-1:50,-2:35,-3:25,-4:18,-5:12,-6:9,-7:7,-8:5.5,-9:4.3,-10:3.5,-11:2.8,-12:2.2,-13:1.7,-14:1.3,-15:1.0,-16:0.9,-17:0.8,-18:0.7}
        infect_chance = table.get(difference,0.6)

    if random.random()*100 > infect_chance:
        await repo_biowar.subtract_pathogens(infecter['id'], spent_pathogens)

        if not infecter['science_time']:
            await repo_biowar.update_lab_skill_val(infecter['id'], 'science_time', science_time)

        if (
            ss_detect == 1
            and victimer['chat_setup_virus']
            and victimer['chat_setup_virus'] != chat_id
            and vic_user_chat
            and spent_pathogens >= 2
        ):
            await bot.send_message(victimer['chat_setup_virus'], sb_virus_detect_try_text)

        return await msg.answer(
            tricks_biowar['infect']['victim_immunity_fail'].format(
                vic_entity,
                inf_ready_pathogens_left,
                '',
                f'{infect_chance}%'
            )
        )

    inf_fev_time = tricks_biowar['max']['time']['infect_fever_time'] / 60
    fever_time = int(infecter['lethality'] / 3)
    fever_time = (1 if fever_time == 0 else fever_time)
    fever_time_ = fever_time
    if victimer['fever']:
        fev_minutes = (datetime.fromtimestamp(victimer['fever']) - datetime.utcnow()).total_seconds() / 60
        fever_time = round(inf_fev_time if fever_time + fev_minutes > inf_fev_time else fever_time + fev_minutes)
    fever_expire = int((datetime.utcnow() + timedelta(minutes=fever_time)).timestamp())
    
    lose_exp = int(round(victimer['bio_experience'] * tricks_biowar['max']['elements']['infect_claim_percent'], 0))
    earn_exp = int(round(
        victimer['bio_experience'] * (
        # tricks_biowar['max']['elements']['infect_claim_bonus_percent'] + \
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
    vic_exp = 0 if lose_exp < 0 else lose_exp
    
    vic_expire = int((datetime.utcnow() + timedelta(days=infecter["lethality"])).timestamp())
    vic_expire_kd = int((datetime.utcnow() + timedelta(seconds=tricks_biowar['max']['time']['victim_kd_expire'])).timestamp())
    vic_new = not await repo_biowar.select_one('SELECT victim_id FROM Victims WHERE victims_owner_id=%s AND victim_id=%s;', (infecter['id'], victimer['id']))
    infect_date = datetime.utcnow().timestamp()
    
    await redis.set(f'epidemic_pet_try_count_heal:{infecter["id"]}', 0)

    await repo_biowar.infect_setup(
        infecter['id'], victimer['id'], earn_exp, vic_exp,
        vic_expire_kd, inf_ready_pathogens_left,
        fever_expire, vic_expire,
        infect_date, pathogen_name, ss_detect,
        science_time, infecter['science_time'], pet_boost_exp
    )
    
    # if vic_new:
    #     await repo_biowar.add_lab_bio_currency(infecter['id'], earn_exp)
    
    text = tricks_biowar['infect']['infect'].format(
        inf_entity, pathogen_name, vic_entity, fever_time_,
        infecter["lethality"], intcomma(earn_exp), vic_username_entity_inv,
        tricks_biowar['text']['victim_new'].format(intcomma(earn_exp)) if vic_new else ''
    )
    
    sb_virus_detect_text = tricks_biowar['infect']['sb_virus_detect'].format(
        vic_entity, spent_pathogens, inf_entity,
        inf_entity, pathogen_name, vic_entity_sb, fever_time_,
        infecter["lethality"], intcomma(earn_exp),
        tricks_biowar['text']['victim_new'].format(intcomma(earn_exp)) if vic_new else ''
    )
    
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




import time
import re


import time
import re
from aiogram import Bot

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
    
    # 1. Если это tg:// ссылка с user_id
    if "user_id=" in arg:
        m = re.search(r"user_id=(\d+)", arg)
        if m:
            return int(m.group(1))
            
    # 2. Если это цифрический ID
    clean_arg = arg.lstrip("@")
    if clean_arg.isdigit():
        return int(clean_arg)
        
    # 3. Если это ссылка t.me/username или @username
    if "t.me/" in arg:
        clean_arg = arg.split("t.me/")[-1].split("/")[0].strip("@")
    elif arg.startswith("@"):
        clean_arg = arg[1:]
        
    # Пытаемся получить пользователя через Telegram API по юзернейму
    if clean_arg and not clean_arg.isdigit():
        try:
            chat_member = await bot.get_chat(clean_arg)
            return chat_member.id
        except Exception:
            pass
            
    return None

async def cmd_check_victim(message: Message, bot: Bot, repo_biowar: RequestsRepoBiowar):
    owner_id = message.from_user.id
    target_id = await extract_target_user_id(message, bot)
    if not target_id:
        await message.reply("❌ Укажите жертву реплаем, перешлите сообщение, укажите @username или ID.")
        return
    
    victims = await repo_biowar.get_victims(owner_id)
    victim_data = None
    if victims:
        for v in victims:
            if v.get('victim_id') == target_id:
                victim_data = v
                break
                
    if not victim_data:
        await message.reply("❌ Игрок не является жертвой владельца.")
        return
        
    bio_earn = victim_data.get('victim_bio_resource_earn', 0)
    expire_time = victim_data.get('victim_expire', 0)
    left_seconds = expire_time - int(time.time())
    
    if left_seconds <= 0:
        time_str = "Срок истек"
    else:
        d, rem = divmod(left_seconds, 86400)
        h, rem = divmod(rem, 3600)
        m = rem // 60
        parts = []
        if d > 0: parts.append(f"{d}д")
        if h > 0 or d > 0: parts.append(f"{h}ч")
        parts.append(f"{m}м")
        time_str = " ".join(parts)
        
    fbio = f"{bio_earn:,}".replace(",", " ")
    await message.reply(f"🧬 Жертва приносит {fbio} био-ресурсов.\n⏳ Осталось: {time_str}.")
