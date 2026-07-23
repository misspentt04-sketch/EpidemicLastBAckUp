from aiogram import types, Bot
from aiogram.filters import CommandObject

from redis import Redis
from asyncmy.cursors import Cursor

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.utils.db_api.repo_chat_manage import RequestsRepoChatManage
from core.data.tricks.tricks_chat_manage import tricks_cm
from core import func
from core.settings import CHAT_LOGS

from humanize import intcomma
from datetime import datetime, timedelta

import asyncio
import sys


async def disable_biowar_chat(msg: types.Message, bot: Bot, repo_biowar: RequestsRepoBiowar, redis: Redis):

    chat = await repo_biowar.get_chat_by_id(msg.chat.id)

    result = await func.get_admins_chat(bot, chat['chat_id'])
    admin_ids = [member.user.id for member in result]
    
    if msg.from_user.id not in admin_ids:
        return await msg.answer(tricks_cm['rules']['not_admin'].format(chat['title']))

    mention = func.entity_create(chat['chat_id'], chat['title'])
    mute_time = (datetime.utcnow() + timedelta(days=9999)).timestamp()

    await repo_biowar.game_mute(chat['chat_id'], mute_time, msg.from_user.id, 'Отключение био-войн в чате')
    await redis.set(f'epidemic_gamemute:{chat["chat_id"]}', mute_time)

    text = (
        f'В чате {mention} была отключена игра «био-войны»'
    )
    
    await msg.answer(text)
    await asyncio.sleep(0.1)
    try:
        await bot.send_message(CHAT_LOGS, text, disable_web_page_preview=True)
    except:
        pass


async def disalbe_biowar_user(msg: types.Message, bot: Bot, repo_biowar: RequestsRepoBiowar, redis: Redis):

    user = await repo_biowar.get_user(msg.from_user.id)

    mention = func.entity_create(user['id'], user['full_name'])
    mute_time = (datetime.utcnow() + timedelta(days=9999)).timestamp()

    await repo_biowar.game_mute(user['id'], mute_time, user['id'], 'Выход из игры био-войн')
    await redis.set(f'epidemic_gamemute:{user["id"]}', mute_time)

    text = (
        f'Игрок {mention} вышел из игры «био-войны»'
    )
    
    await msg.answer(text)
    await asyncio.sleep(0.1)
    try:
        await bot.send_message(CHAT_LOGS, text, disable_web_page_preview=True)
    except:
        pass


async def enable_chat_biowar(msg: types.Message, bot: Bot, repo_biowar: RequestsRepoBiowar, redis: Redis):

    chat = await repo_biowar.get_chat_by_id(msg.chat.id)

    result = await func.get_admins_chat(bot, chat['chat_id'])
    admin_ids = [member.user.id for member in result]
    
    if msg.from_user.id not in admin_ids:
        return await msg.answer(tricks_cm['rules']['not_admin'].format(chat['title']))

    mention = func.entity_create(chat['chat_id'], chat['title'])

    await redis.delete(f'epidemic_gamemute:{chat["chat_id"]}')
    await repo_biowar.game_mute_cancel(chat['chat_id'])

    text = (
        f'В чате {mention} была включена игра «био-войны»'
    )
    
    await msg.answer(text)
    await asyncio.sleep(0.1)
    try:
        await bot.send_message(CHAT_LOGS, text, disable_web_page_preview=True)
    except:
        pass