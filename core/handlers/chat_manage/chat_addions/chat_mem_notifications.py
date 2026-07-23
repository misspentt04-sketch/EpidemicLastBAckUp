from aiogram.types import Message
from asyncmy.cursors import Cursor
from aiogram import Bot
from aiogram.methods.get_chat_administrators import GetChatAdministrators
from datetime import datetime, timedelta

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.utils.db_api.repo_chat_manage import RequestsRepoChatManage
from core.data.texttriggers import deep_links
# from core.keyboards.inline.marriage import *
from core.data.tricks.tricks_chat_manage import tricks_cm
from core import func

async def include_hello_not(msg: Message, bot: Bot, db: Cursor, repo_cm: RequestsRepoChatManage, repo_biowar: RequestsRepoBiowar):
    chat_id = msg.chat.id
    chat = await repo_biowar.get_chat_by_id(chat_id)

    result = await func.get_admins_chat(bot, chat_id)
    admin_ids = [member.user.id for member in result]
    
    if msg.from_user.id not in admin_ids:
        return await msg.answer(tricks_cm['rules']['not_admin'].format(chat['title']))
    
    if '+' in msg.text:
        await repo_cm.include_off_notifications(chat_id, 0)
        await msg.answer(tricks_cm['chat_members']['new_members_include'].format(chat['title']))

    elif '-' in msg.text:
        await repo_cm.include_off_notifications(chat_id, 1)
        await msg.answer(tricks_cm['chat_members']['new_members_off'].format(chat['title']))


async def include_leave_not(msg: Message, bot: Bot, db: Cursor, repo_cm: RequestsRepoChatManage, repo_biowar: RequestsRepoBiowar):
    chat_id = msg.chat.id
    chat = await repo_biowar.get_chat_by_id(chat_id)

    result = await func.get_admins_chat(bot, chat_id)
    admin_ids = [member.user.id for member in result]
    
    if msg.from_user.id not in admin_ids:
        return await msg.answer(tricks_cm['rules']['not_admin'].format(chat['title']))

    if '+' in msg.text:
        await repo_cm.include_off_notifications(chat_id, 3)
        await msg.answer(tricks_cm['chat_members']['leave_members_include'].format(chat['title']))
        
    elif '-' in msg.text:
        await repo_cm.include_off_notifications(chat_id, 4)
        await msg.answer(tricks_cm['chat_members']['leave_members_off'].format(chat['title']))