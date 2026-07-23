from aiogram.types import Message
from asyncmy.cursors import Cursor
from aiogram import Bot

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.tricks.tricks_biowar import tricks_biowar
from core.data.tricks.tricks_genai import tricks_genai
from core.utils.genai import gpt_thinks
from core.settings import CHAT_LOGS
from core import func

from datetime import datetime

import emoji
import asyncio

async def pathogen_name_change(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    msgt = msg.text
    pathogen_name = ' '.join(msgt.split(' ')[2:])
    max_pathogen_len = tricks_biowar['max']['elements']['pathogen_name_len']
    
    pathogen_check = await repo_biowar.select_all('SELECT pathogen_name FROM Lab WHERE pathogen_name=%s', pathogen_name)
    bio_mute = await repo_biowar.get_user_bio_mute(id)
    
    # errors
    if bio_mute:
        bio_mute_days = (datetime.fromtimestamp(bio_mute['time_expire']) - datetime.utcnow()).days
        return await msg.answer(tricks_biowar['epidemic_admins']['bio_muted'].format(bio_mute_days))
    if len(pathogen_name) >= max_pathogen_len:
        return await msg.answer(tricks_biowar['lab']['pathogen_name_change_max_len'].format(max_pathogen_len))
    if pathogen_check:
        return await msg.answer(tricks_biowar['lab']['pathogen_name_already_exists'])
    
    user = await repo_biowar.get_user(id)
    mention = func.entity_create_consider_username(user)
    
    if msg.text[0] == '-':
        pathogen_name = None
        text = tricks_biowar['lab']['delete_pathogen_name']
    else:
        text = tricks_biowar['lab']['pathogen_name_change'].format(pathogen_name)
    
    text_to_moders = f'Игрок {mention} поменял имя патогена на «{pathogen_name}»'
    
    await repo_biowar.pathogen_name_change(pathogen_name, id)
    await msg.answer(text)
    await asyncio.sleep(1)
    
    is_mat = gpt_thinks(tricks_genai['prompts']['anti_mat'].format(pathogen_name))
    
    if int(is_mat) == 1:
        try:
            await bot.send_message(CHAT_LOGS, text_to_moders, disable_web_page_preview=True)
        except:
            pass

async def lab_dossier(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    dossier_val = 1
    
    user = await repo_biowar.get_user(id)
    user_entity = func.entity_create_consider_username(user)
    
    if msg.text[0] == '-':
        dossier_val = 0
        text = tricks_biowar['lab']['hide_lab_dossier'].format(user_entity)
    else:
        text = tricks_biowar['lab']['show_lab_dossier'].format(user_entity)
    
    await repo_biowar.update_lab_dossier(dossier_val, id)
    
    await msg.answer(text, disable_web_page_preview=True)

async def customization_emoji(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    emoji_text = msg.text.split(' ')[-1]
    
    lab_info = await repo_biowar.get_info_user_lab(id)
    
    if msg.text[0] == '-' and not lab_info['customization_emoji']:
        return await msg.answer(tricks_biowar['lab']['hasnt_emoji_customization'])
    if msg.text[0] != '-' and not emoji.is_emoji(emoji_text):
        return await msg.answer(tricks_biowar['lab']['wrong_emoji_customization'])
    
    if msg.text[0] == '-':
        emoji_text = None
        text = tricks_biowar['lab']['remove_emoji_customization'].format(lab_info['customization_emoji'])
    else:
        text = tricks_biowar['lab']['customization_emoji'].format(emoji_text)
    
    await msg.answer(text)
    await repo_biowar.set_lab_customization_emoji(id, emoji_text)

async def change_lab_name(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    lab_name = ' '.join(msg.text.split(' ')[2:])
    max_lab_len = tricks_biowar['max']['elements']['pathogen_name_len']
    
    lab_check = await repo_biowar.select_all('SELECT lab_name FROM Lab WHERE lab_name=%s', lab_name)
    user = await repo_biowar.get_user(id)
    mention = func.entity_create_consider_username(user)
    
    bio_mute = await repo_biowar.get_user_bio_mute(id)
    
    # errors
    if bio_mute:
        bio_mute_days = (datetime.fromtimestamp(bio_mute['time_expire']) - datetime.utcnow()).days
        return await msg.answer(tricks_biowar['epidemic_admins']['bio_muted'].format(bio_mute_days))
    
    if msg.text[0] != '-':
        if len(lab_name) >= max_lab_len:
            return await msg.answer(tricks_biowar['lab']['lab_name_max_len'].format(max_lab_len))
        if lab_check:
            return await msg.answer(tricks_biowar['lab']['lab_name_already_exists'])
    
    if msg.text[0] == '-':
        lab_name = 'лаб ' + user['full_name']
        text = tricks_biowar['lab']['remove_lab_name'].format(lab_name)
    else:
        text = tricks_biowar['lab']['change_lab_name'].format(lab_name)
    
    text_to_moders = f'Игрок {mention} поменял имя лабы на «{lab_name}»'
    
    await repo_biowar.lab_name_change(lab_name, id)
    
    await msg.answer(text)
    await asyncio.sleep(1)
    is_mat = gpt_thinks(tricks_genai['prompts']['anti_mat'].format(lab_name))
    if int(is_mat) == 1:
        try:
            await bot.send_message(CHAT_LOGS, text_to_moders, disable_web_page_preview=True)
        except:
            pass