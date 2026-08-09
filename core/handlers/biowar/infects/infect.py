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


async def infect(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar, redis: Redis, lock: Lock):
    async with lock:
        id = msg.from_user.id
        chat_id = msg.chat.id
        attacker_id = msg.from_user.id
    id = msg.from_user.id
    chat_id = msg.chat.id
    parts = msg.text.split() if msg.text else []
    victimer_id = getattr(msg, "_override_target_id", None) or func.reply_or_tag_geeter(msg)
    if not victimer_id and len(parts) > 1 and parts[1].isdigit():
        victimer_id = int(parts[1])
    
    if getattr(msg, "_override_target_id", None):
        spent_pathogens = 1
    else:
        spent_pathogens = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
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
    # Лимит убран
    # if spent_pathogens > 10: ...
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
            await redis.hset(victimer['id'], mapping={
                'pet_vuln_indicator': 100
                }
            )
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

    # Новая сетка шансов с капом 0.1%
    if difference >= 0:
        base_chance = 100.0
    else:
        table = {
            -1: 50.0, -2: 35.0, -3: 25.0, -4: 18.0, -5: 12.0,
            -6: 8.0,  -7: 5.0,  -8: 3.0,  -9: 2.0,  -10: 1.0,
            -11: 0.8, -12: 0.6, -13: 0.4, -14: 0.3, -15: 0.25,
            -16: 0.22, -17: 0.20, -18: 0.18, -19: 0.16, -20: 0.15,
            -21: 0.14, -22: 0.13, -23: 0.12, -24: 0.11, -25: 0.108,
            -26: 0.106, -27: 0.104, -28: 0.102, -29: 0.101
        }
        base_chance = table.get(difference, 0.10)

    # Ограничиваем количество патогенов в серии от 1 до 10
    try:
        spent_pathogens = int(spent_pathogens)
    except Exception:
        spent_pathogens = 1
    
    max_pathogens = min(10, max(1, spent_pathogens))
    available_pathogens = infecter.get("pathogens", 1)
    spent_pathogens = min(max_pathogens, available_pathogens)

    # Redis-бонус за прошлые нехиты
    redis_key = f"infect_accum_bonus:{infecter['id']}:{victimer['id']}"
    raw_accum = await redis.get(redis_key)
    accum_bonus = float(raw_accum) if raw_accum else 0.0

    step_add = 0.05 if difference <= -30 else base_chance / 2.0
    actual_spent = 0
    is_success = False

    for attempt in range(1, spent_pathogens + 1):
        actual_spent = attempt
        current_chance = min(100.0, base_chance + accum_bonus)
        
        if random.random() * 100 <= current_chance:
            is_success = True
            await redis.delete(redis_key)  # Сброс бонуса при успехе
            break
        else:
            accum_bonus += step_add
            await redis.set(redis_key, accum_bonus, ex=60)

    spent_pathogens = actual_spent
    infect_chance = min(100.0, base_chance + accum_bonus)

    if not is_success:
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

    # Логика суммирования горячки (максимум 60 минут)
    now_ts = int(datetime.now(timezone.utc).timestamp())
    
    # Универсальное считывание текущей горячки
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
    fever_time_ = fever_time  # Показываем только минуты текущего заражения
    
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

    # Запись в историю заражений для топа
    try:
        query_hist = "INSERT INTO biowar_infection_history (attacker_id, victim_id, week_str, month_str, infect_date) VALUES (%s, %s, DATE_FORMAT(NOW(), '%%x-%%V'), DATE_FORMAT(NOW(), '%%Y-%%m'), NOW());"
        await repo_biowar.cur.execute(query_hist, (infecter['id'], victimer['id']))
        await repo_biowar.conn.commit()
    except Exception as e:
        print("Error inserting infection history:", e)

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

    # 1. Выбор по номеру из топа (с реплаем на список)
    if message.reply_to_message and arg and arg.isdigit():
        requested_idx = int(arg)
        r = message.reply_to_message
        user_ids_in_order = []

        entities = r.entities or r.caption_entities or []
        for entity in entities:
            if entity.type == "text_link" and entity.url:
                if "user_id=" in entity.url:
                    try:
                        import re
                        uids = re.findall(r"\d+", entity.url)
                        if uids:
                            uid = int(uids[0])
                        if uid not in user_ids_in_order:
                            user_ids_in_order.append(uid)
                    except ValueError:
                        pass

        if not user_ids_in_order:
            r_text = r.text or r.caption or ""
            import re
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

    # 2. Получение ID из аргумента (ссылка tg://, числа или id) или реплая
    else:
        r_id = None
        import re

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

    # Ищем данные жертвы в базе
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
        InlineKeyboardButton(text="💥 Ебнуть", callback_data=f"hit_target:{target_id}")
    ]])
    await message.reply(response_text, parse_mode="HTML", reply_markup=kb)



async def hit_target_callback(callback: CallbackQuery, bot: Bot, db, repo_biowar: RequestsRepoBiowar, redis: Redis, lock: Lock):
    # Анти-спам замок в Redis
    click_key = f"hit_cb_lock:{callback.from_user.id}:{callback.message.message_id}"
    if await redis.get(click_key):
        return await callback.answer('⏳ Подожди немного...', show_alert=False)
    await redis.set(click_key, '1', ex=2)

    data_parts = callback.data.split(':')
    target_id = int(data_parts[1])
    
    owner_id = int(data_parts[2]) if len(data_parts) > 2 and data_parts[2].isdigit() else None

    if not owner_id and callback.message.reply_to_message and callback.message.reply_to_message.from_user:
        owner_id = callback.message.reply_to_message.from_user.id

    # Проверка на админа через БД / repo
    is_admin = False
    try:
        user_data = await repo_biowar.get_user(callback.from_user.id)
        if user_data and (getattr(user_data, 'is_admin', False) or getattr(user_data, 'role', '') in ['admin', 'owner', 'creator']):
            is_admin = True
    except Exception:
        pass

    # Если в config прописан
    try:
        from core.config import settings
        if callback.from_user.id in getattr(settings.bots, 'admin_ids', []) or callback.from_user.id == getattr(settings.bots, 'admin_id', None):
            is_admin = True
    except Exception:
        pass

    # Обычным игрокам запрещаем чужие кнопки, АДМИНАМ РАЗРЕШАЕМ ВСЁ!
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

    await callback.answer('🚀 Запуск атаки...', show_alert=False)
    await infect(msg=fake_message, bot=bot, db=db, repo_biowar=repo_biowar, redis=redis, lock=lock)

    data_parts = callback.data.split(':')
    target_id = int(data_parts[1])
    
    owner_id = int(data_parts[2]) if len(data_parts) > 2 and data_parts[2].isdigit() else None

    if not owner_id and callback.message.reply_to_message and callback.message.reply_to_message.from_user:
        owner_id = callback.message.reply_to_message.from_user.id

    # Проверяем, является ли нажимающий администратором
    from core.config import settings
    admin_ids = getattr(settings.bots, 'admin_ids', [])
    if not isinstance(admin_ids, (list, tuple, set)):
        admin_ids = [admin_ids]
    
    is_admin = callback.from_user.id in admin_ids or callback.from_user.id in getattr(settings.bots, 'admin_id_list', [])

    # Обычным пользователям запрещаем чужие кнопки, админам — разрешаем!
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

    await callback.answer('🚀 Запуск атаки...', show_alert=False)
    await infect(msg=fake_message, bot=bot, db=db, repo_biowar=repo_biowar, redis=redis, lock=lock)

    data_parts = callback.data.split(':')
    target_id = int(data_parts[1])
    
    # 1. Проверяем owner_id из callback_data
    owner_id = int(data_parts[2]) if len(data_parts) > 2 and data_parts[2].isdigit() else None

    # 2. Проверяем owner_id из reply_to_message
    if not owner_id and callback.message.reply_to_message and callback.message.reply_to_message.from_user:
        owner_id = callback.message.reply_to_message.from_user.id

    # Блокировка чужих кликов
    if owner_id and callback.from_user.id != owner_id:
        return await callback.answer('❌ Это не твоя кнопка!', show_alert=True)

    # Запрет атаки самого себя
    if callback.from_user.id == target_id:
        return await callback.answer('❌ Нельзя атаковать самого себя!', show_alert=True)

    fake_message = callback.message.model_copy(update={
        'from_user': callback.from_user,
        'text': f'заразить {target_id} 1',
        'reply_to_message': None
    })
    
    setattr(fake_message, '_override_target_id', target_id)

    await callback.answer('🚀 Запуск атаки...', show_alert=False)
    await infect(msg=fake_message, bot=bot, db=db, repo_biowar=repo_biowar, redis=redis, lock=lock)

    # 2. Если в callback_data нет owner_id, пытаемся узнать владельца через reply_to_message
    if not owner_id and callback.message.reply_to_message and callback.message.reply_to_message.from_user:
        owner_id = callback.message.reply_to_message.from_user.id

    # 3. Блокируем чужие клики, если удалось определить владельца
    if owner_id and callback.from_user.id != owner_id:
        return await callback.answer('❌ Это не твоя кнопка!', show_alert=True)

    # 4. Запрет на атаку самого себя
    if callback.from_user.id == target_id:
        return await callback.answer('❌ Нельзя атаковать самого себя!', show_alert=True)

    fake_message = callback.message.model_copy(update={
        'from_user': callback.from_user,
        'text': f'заразить {target_id} 1',
        'reply_to_message': None
    })
    
    setattr(fake_message, '_override_target_id', target_id)

    await callback.answer('🚀 Запуск атаки...', show_alert=False)
    await infect(msg=fake_message, bot=bot, db=db, repo_biowar=repo_biowar, redis=redis, lock=lock)

    # Проверка: если кнопку нажимает не тот, кто её вызвал
    if owner_id and callback.from_user.id != owner_id:
        return await callback.answer('❌ Это не твоя кнопка!', show_alert=True)

    if callback.from_user.id == target_id:
        return await callback.answer('❌ Нельзя атаковать самого себя!', show_alert=True)

    fake_message = callback.message.model_copy(update={
        'from_user': callback.from_user,
        'text': f'заразить {target_id} 1',
        'reply_to_message': None
    })
    
    setattr(fake_message, '_override_target_id', target_id)

    await callback.answer('🚀 Запуск атаки...', show_alert=False)
    await infect(msg=fake_message, bot=bot, db=db, repo_biowar=repo_biowar, redis=redis, lock=lock)

    fake_message = callback.message.model_copy(update={
        'from_user': callback.from_user,
        'text': f'заразить {target_id} 1',
        'reply_to_message': None
    })
    
    # Передаем явно ID целевого игрока
    setattr(fake_message, '_override_target_id', target_id)

    await callback.answer('🚀 Запуск атаки...', show_alert=False)
    await infect(msg=fake_message, bot=bot, db=db, repo_biowar=repo_biowar, redis=redis, lock=lock)

    await callback.answer("🚀 Запуск заражения...", show_alert=False)
    
    await infect(msg=fake_message, bot=bot, db=db, repo_biowar=repo_biowar, redis=redis, lock=lock)
