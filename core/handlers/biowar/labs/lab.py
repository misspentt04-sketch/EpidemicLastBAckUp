from asyncmy.cursors import Cursor
from redis.asyncio import Redis
from aiogram.types import Message
from aiogram import Bot, Router
from datetime import datetime, timedelta, timezone

from core.keyboards.inline.lab import lab_navigation, lab_confirm_upgrade
from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.texttriggers import deep_links
from core.data.icons import LabIco, OtherIco, PetIco
from core.data.tricks.tricks_biowar import tricks_biowar

from core import func

from humanize import intcomma

lab_main_router = Router()

@lab_main_router.message() # или ваш декоратор команды, если он здесь задается
async def get_lab(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar, redis: Redis):
    
    id = msg.from_user.id # not for using
    target_lab = func.reply_or_tag_geeter(msg)
    is_my_lab = not func.check_reply_or_tag(msg)
    
    lab_info = await repo_biowar.get_info_user_lab(target_lab) # always use lab_info['id']
    corp_info = await repo_biowar.get_corporation(target_lab)
    
    if lab_info is None:
        return await msg.answer(tricks_biowar['text']['not_info_about_user'])
    if target_lab and lab_info['lab_dossier'] == 0 and target_lab != id:
        return await msg.answer(tricks_biowar['lab']['lab_dossier_secret'])
    
    infected = await repo_biowar.get_my_infected(lab_info['id'])
    illnesses = await repo_biowar.get_my_illnesses(lab_info['id'])

    pet = await repo_biowar.get_my_pet(lab_info['id'])
    
    pet_vuln_indicator = 0
    if pet:
        pet_vuln_indicator = await redis.hget(lab_info['id'], 'pet_vuln_indicator')
        if not pet_vuln_indicator:
            pet_vuln_indicator = 100
    
    full_name = lab_info["full_name"]
    name_entity = func.entity_create_full_name(
        lab_info['id'], lab_info['full_name']
    )
    pathogen_name = lab_info["pathogen_name"] if lab_info["pathogen_name"] else 'засекречено'
    lab_name = lab_info['lab_name'] if lab_info['lab_name'] else full_name
    fever = func.fever_expire_difference_check(lab_info['fever']) if lab_info['fever'] else None
    if fever:
        fever = tricks_biowar['lab']['fever'].format(
            fever
        )
    
    fever_time = int(lab_info['lethality'] / 3)
    fever_time = (1 if fever_time == 0 else(60 if fever_time >= 180 else fever_time))
    
    refresh_pathogen_time = '\n'
    if lab_info["science_time"]:
        science_time = func.fever_expire_difference_check(lab_info["science_time"])
    if lab_info["science_time"]:
            refresh_pathogen_time = f'<i>{LabIco.sand_clock.value} Новый патоген через {science_time}</i>\n\n'
    
    if corp_info:
        corp_text = f'В составе Корпорации — «<a href="tg://openmessage?user_id={corp_info["leader_id"]}">{corp_info["name"]}</a>»\n\n'
    else:
        corp_text = '\n'
    
    pet_text = '✨ Питомец отсутствует\n'
    if pet:
        pets_info = tricks_biowar['pet']['pets_info'][pet['pet_name'].lower()]
        pet_text = (
            f'{pets_info["emoji"]} <b>Стихия:</b> {pets_info["element"]}\n'
            f'{pets_info["element_emoji"]} <b>Шкала пробития:</b> {pet_vuln_indicator}%\n'
        )
    
    custom_emoji = lab_info['customization_emoji'] if lab_info['customization_emoji'] else ''
    
    time_food = await repo_biowar.get_time_food()
    time_food_diff = datetime.utcfromtimestamp(time_food) - datetime.utcnow()
    get_food_text = func.convert_seconds_to_human(time_food_diff.total_seconds())

    infected_count = len(infected) if isinstance(infected, (list, tuple)) else infected
    illnesses_count = len(illnesses) if isinstance(illnesses, (list, tuple)) else illnesses

    lab_text = (
        f'<b>📩 Досье лаборатории {lab_name}:</b>\n'
        f'Руководитель — {name_entity} {custom_emoji}\n'
        f'{corp_text}'
        
        f'{LabIco.label.value} <b>Имя патогена:</b> {pathogen_name}\n'
        f'{LabIco.pathogens.value} <b>Готовых патогенов:</b> {lab_info["ready_pathogens"]}/{lab_info["pathogens"]}\n'
        f'{LabIco.science.value} <b>Квалификация учёных:</b> {lab_info["science"]} ур ({61 - lab_info["science"]} мин.)\n'
        f'{refresh_pathogen_time}'
        
        f'<blockquote><b>——[ Характеристика]——</b>\n'
        f'{LabIco.infect.value} Заразность: {lab_info["infect"]} ур\n'
        f'{LabIco.immunity.value} Иммунитет: {lab_info["immunity"]} ур\n'
        f'{LabIco.lethality.value} Летальность: {lab_info["lethality"]} ур ({fever_time} мин | {lab_info["lethality"]} дн)\n'
        f'{LabIco.security_service.value} Служба безопасности: {lab_info["security_service"]} ур</blockquote>\n'
        
        f'<b>——————————————</b>\n'
        f'ID лаборатории: <code>{lab_info["id"]}</code>\n'
        f'<b>——————————————</b>\n'
        
        f'<blockquote><b>—[Запасы — реагентов]—</b>\n'
        f'{LabIco.bio_experience.value} Опыт: {intcomma(lab_info["bio_experience"]).replace(",", " ")}\n'
        f'{LabIco.bio_resource.value} Ресурсы: {intcomma(lab_info["bio_resource"]).replace(",", " ")}\n'
        f'{LabIco.time.value} <i>Ежедневная премия через: Каждый день в 12.00 и 00.00</i>\n'
        f'{fever + "</blockquote>" if fever else "</blockquote>"}'
        
        f'{LabIco.infected.value} Заражённых: {infected_count}\n'
        f'{LabIco.illnesses.value} Своих болезней: {illnesses_count}\n\n'
    )
    
    await msg.answer(lab_text, disable_web_page_preview = True,
                     reply_markup = lab_navigation(id, is_my_lab))


async def lab_lvlup_skills(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):

    id = msg.from_user.id
    inline_mode = (False if msg.text[:2] == '++' else True)
    
    lvl = (int(msg.text.split(' ')[1]) if len(msg.text.split(' ')) > 1 else 1)
    
    if lvl > 5:
        text = tricks_biowar['text']['max_reached_skill_lvl']
        return await msg.answer(text)
    
    skill = msg.text.lower().split(' ')[0].strip('+')
    en_skill = tricks_biowar['lvlup_ru_to_en'][skill]
    
    lab_info = await repo_biowar.get_info_user_lab(id)
    
    from_lvl = lab_info[en_skill]
    lab_bio_resource = lab_info['bio_resource']
    
    to_lvl = from_lvl + lvl
    price = func.lvl_up_calc(en_skill, from_lvl, to_lvl)
    
    if en_skill == 'science' and to_lvl > tricks_biowar['max']['skill']['science']:
        return await msg.answer(tricks_biowar['lab']['max_level_up_limit'].format(skill))
    
    bio_resource_remainder = lab_bio_resource - price
    
    if bio_resource_remainder >= 0 or inline_mode:
        
        if en_skill == 'science':
            science_minutes = tricks_biowar['max']['skill']['science'] - to_lvl + 1
        
        text = tricks_biowar['skills_lvl'][en_skill].format(lvl, (science_minutes if en_skill=='science' else intcomma(to_lvl)), intcomma(price), lvl, to_lvl)
        
        if not inline_mode:
            text = tricks_biowar['skills_lvl'][f'{en_skill}_complete'].format(lvl, (science_minutes if en_skill=='science' else to_lvl), intcomma(price))
            await repo_biowar.update_lab_lvlup(id, en_skill, to_lvl, bio_resource_remainder)
            if en_skill == 'pathogens':
                await repo_biowar.update_lab_skill_val(id, 'ready_pathogens', lab_info['ready_pathogens'] + lvl)
        else:    
            return await msg.answer(text, reply_markup = lab_confirm_upgrade(en_skill, lvl, id))
    else:
        text = tricks_biowar['text']['not_enough_resources']
    

    await msg.answer(text)
