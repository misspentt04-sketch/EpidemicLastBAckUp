from aiogram import Bot
from aiogram.types import CallbackQuery
from asyncmy.cursors import Cursor

from core.utils.callbackdata import Lab, LabLvlUpConfirm
from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.keyboards.inline.lab import lab_confirm_upgrade, lab_confirm_upgrade_extend

from core.data.tricks.tricks_biowar import tricks_biowar

from core import func

from humanize import intcomma

import random

async def lab_lvlup(call: CallbackQuery, bot: Bot, callback_data: Lab, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = call.from_user.id
    
    if id != callback_data.id or not callback_data.is_my_lab:
        return await call.answer(random.choice(tricks_biowar['inline']['not_your_button']))
    
    lab_info = await repo_biowar.get_info_user_lab(id)
    
    skill = callback_data.skill.split('lab_')[1]
    lvl = callback_data.lvl_up
    from_lvl = lab_info[skill]
    to_lvl = from_lvl + lvl
    price = func.lvl_up_calc(skill, from_lvl, to_lvl)
    science_max_lvl = tricks_biowar['max']['skill']['science']
    
    if skill == 'science':
        science_minutes =  tricks_biowar['max']['skill']['science'] - to_lvl + 1
    
    text = tricks_biowar['skills_lvl'][skill].format(lvl, (science_minutes if skill=='science' else to_lvl), intcomma(price), lvl)    
    
    await call.message.answer(text, reply_markup = lab_confirm_upgrade(skill, lvl, id))
    await call.answer()

async def lab_lvlup_confirm(call: CallbackQuery, bot: Bot, callback_data: LabLvlUpConfirm, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    user_id = call.from_user.id
    
    if user_id != callback_data.id:
        return await call.answer(random.choice(tricks_biowar['inline']['not_your_button']))
    
    lab_info = await repo_biowar.get_info_user_lab(user_id)
    
    skill = callback_data.skill.split('lab_confirm_')[1]
    lvl = callback_data.lvl_up
    from_lvl = lab_info[skill]
    to_lvl = from_lvl + lvl
    price = func.lvl_up_calc(skill, from_lvl, to_lvl)
    science_max_lvl = tricks_biowar['max']['skill']['science']
    
    if skill == 'science':
        if to_lvl > science_max_lvl:
            return await call.message.answer(tricks_biowar['lab']['max_level_up_limit'].format(tricks_biowar['lvlup_en_to_ru'][skill]))
        science_minutes = science_max_lvl - to_lvl + 1
    
    bio_resource_remainder = lab_info['bio_resource'] - price
    
    if bio_resource_remainder >= 0:
        
        if skill == 'pathogens':
            await repo_biowar.update_lab_skill_val(user_id, 'ready_pathogens', lab_info['ready_pathogens'] + lvl)
        
        await repo_biowar.update_lab_lvlup(user_id, skill, to_lvl, bio_resource_remainder)
        text = tricks_biowar['skills_lvl'][f'{skill}_complete'].format(lvl, (science_minutes if skill=='science' else to_lvl), intcomma(price))
    else:
        text = tricks_biowar['text']['not_enough_resources']
    
    await call.message.edit_text(text, reply_markup=lab_confirm_upgrade_extend(skill, user_id))
    await call.answer()


async def lab_lvl_up_confirm_extend(call: CallbackQuery, callback_data: LabLvlUpConfirm, repo_biowar: RequestsRepoBiowar):

    user_id = call.from_user.id

    if user_id != callback_data.user_id:
        return await call.answer(random.choice(tricks_biowar['inline']['not_your_button']))
    
    lab_info = await repo_biowar.get_info_user_lab(user_id)
    
    skill = callback_data.skill
    lvl = callback_data.lvl_up
    from_lvl = lab_info[skill]
    to_lvl = from_lvl + lvl
    price = func.lvl_up_calc(skill, from_lvl, to_lvl)
    science_max_lvl = tricks_biowar['max']['skill']['science']
    
    if skill == 'science':
        if to_lvl > science_max_lvl:
            return await call.message.answer(tricks_biowar['lab']['max_level_up_limit'].format(tricks_biowar['lvlup_en_to_ru'][skill]))
        science_minutes = science_max_lvl - to_lvl + 1
    
    bio_resource_remainder = lab_info['bio_resource'] - price
    
    if bio_resource_remainder >= 0:
        
        if skill == 'pathogens':
            await repo_biowar.update_lab_skill_val(user_id, 'ready_pathogens', lab_info['ready_pathogens'] + lvl)
        
        await repo_biowar.update_lab_lvlup(user_id, skill, to_lvl, bio_resource_remainder)
        text = tricks_biowar['skills_lvl'][f'{skill}_complete'].format(lvl, (science_minutes if skill=='science' else to_lvl), intcomma(price))
    else:
        text = tricks_biowar['text']['not_enough_resources']
        await call.message.answer(text)
        return await call.answer()
    
    await call.message.edit_text(text, reply_markup=lab_confirm_upgrade_extend(skill, user_id))
    await call.answer(f'Улучшение на {lvl} уровней')

