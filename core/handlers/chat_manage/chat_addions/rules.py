from aiogram.types import Message
from asyncmy.cursors import Cursor
from aiogram import Bot
from aiogram.methods.get_chat_administrators import GetChatAdministrators

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.utils.db_api.repo_chat_manage import RequestsRepoChatManage

from core.data.texttriggers import deep_links
from core.data.tricks.tricks_chat_manage import tricks_cm
from core.data.tg_ban_words import words as tg_ban_words
from core import func

async def add_rules(msg: Message, bot: Bot, db: Cursor, repo_cm: RequestsRepoChatManage, repo_biowar: RequestsRepoBiowar):
    
    id = msg.chat
    chat = await repo_biowar.get_chat_by_id(id.id)

    result = await func.get_admins_chat(bot, id.id)
    admin_ids = [member.user.id for member in result]
    
    if msg.from_user.id not in admin_ids:
        await msg.answer(tricks_cm['rules']['not_admin'].format(chat['title']))
        return
    
    rules_text = msg.html_text[9:]

    if len(rules_text) < 5:
        await msg.answer(tricks_cm['rules']['rules_short'].format(chat['title']))
        return
    
    await repo_cm.add_rules_chat(id.id, rules_text)

    await msg.answer(tricks_cm['rules']['rules_added'].format(chat['title']))

async def get_rules(msg: Message, bot: Bot, db: Cursor, repo_cm: RequestsRepoChatManage, repo_biowar: RequestsRepoBiowar):

    id = msg.chat

    chat = await repo_biowar.get_chat_by_id(id.id)
    rules = await repo_cm.get_rules_chat(id.id)

    if rules:
        await msg.answer(tricks_cm['rules']['show_rules'].format(chat['title'], rules['text']))
        return

    await msg.answer(tricks_cm['rules']['rules_not_found'].format(chat['title']))

async def del_rules(msg: Message, bot: Bot, db: Cursor, repo_cm: RequestsRepoChatManage, repo_biowar: RequestsRepoBiowar):

    id = msg.chat
    chat = await repo_biowar.get_chat_by_id(id.id)

    result = await func.get_admins_chat(bot, id.id)
    admin_ids = [member.user.id for member in result]
    
    if msg.from_user.id not in admin_ids:
        await msg.answer(tricks_cm['rules']['not_admin'].format(chat['title']))
        return
    
    await repo_cm.del_rules_chat(id.id)

    await msg.answer(tricks_cm['rules']['rules_del'].format(chat['title']))