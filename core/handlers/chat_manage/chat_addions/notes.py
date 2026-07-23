from aiogram.types import Message
from asyncmy.cursors import Cursor
from aiogram import Bot
from datetime import datetime
from zoneinfo import ZoneInfo

from core.utils.db_api.repo_chat_manage import RequestsRepoChatManage
from core.data.texttriggers import deep_links
from core.data.tricks.tricks_chat_manage import tricks_cm
from core.data.tg_ban_words import words as tg_ban_words

from core import func

import re

async def show_notes(msg: Message, bot: Bot, db: Cursor, repo_cm: RequestsRepoChatManage):
    
    id = msg.from_user.id
    chat_id = msg.chat.id
    
    notes = await repo_cm.get_notes(chat_id)
    
    if not notes:
        return await msg.answer(tricks_cm['notes']['show_notes_not'])
    
    notes_text_list = func.get_notes_list(notes)
    text = tricks_cm['notes']['show_notes'].format('\n'.join(notes_text_list))
    
    await msg.answer(text)

async def show_note(msg: Message, bot: Bot, db: Cursor, repo_cm: RequestsRepoChatManage):
    
    id = msg.from_user.id
    chat_id = msg.chat.id
    note_title = msg.text[8:]
    
    note = await repo_cm.get_note(chat_id, note_title)
    
    if not note:
        return await msg.answer(tricks_cm['notes']['note_not_found'])
    
    dt_match = re.search(r'(\d{4}\.\d{2}\.\d{2})', note['text'].splitlines()[-1]).group(0)
    note_text = '\n'.join(note['text'].splitlines()[:-2]) + f'\n\n🕒 <i>{dt_match}</i>'
    
    text = tricks_cm['notes']['show_note'].format(note['title'], note_text)
    
    await msg.answer(text, disable_web_page_preview=True)

async def add_note(msg: Message, bot: Bot, db: Cursor, repo_cm: RequestsRepoChatManage):
    
    id = msg.from_user.id
    chat_id = msg.chat.id
    note_title = msg.text.splitlines()[0][9:]
    note_text = msg.html_text.splitlines()[1:]
    
    note = await repo_cm.get_note(chat_id, note_title)
    
    if note:
        return await msg.answer(tricks_cm['notes']['note_already_exist'])
    elif not note_text:
        return await msg.answer(tricks_cm['notes']['note_not_has_text'])
    
    notes_count = await repo_cm.get_notes_count(chat_id)
    
    text = tricks_cm['notes']['add_note'].format(note_title)

    now = datetime.now(ZoneInfo("Europe/Moscow"))
    time_create = now.strftime("%Y.%m.%d")
    note_text = '\n'.join(note_text) + f'\n\n🕒 <b>Создана:</b> <i>{time_create}</i>'
    
    await msg.answer(text)
    await repo_cm.add_note(chat_id, notes_count+1, note_title, note_text)


async def del_note(msg: Message, bot: Bot, db: Cursor, repo_cm: RequestsRepoChatManage):
    
    id = msg.from_user.id
    chat_id = msg.chat.id
    note_title = msg.text[9:]
    
    note = await repo_cm.get_note(chat_id, note_title)
    
    if not note:
        return await msg.answer(tricks_cm['notes']['note_not_found'])
    
    text = tricks_cm['notes']['del_note'].format(note['title'])
    
    await msg.answer(text)
    await repo_cm.del_note(chat_id, note['note_id'])


