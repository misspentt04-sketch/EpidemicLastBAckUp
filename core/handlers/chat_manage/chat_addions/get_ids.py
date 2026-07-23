from aiogram.types import Message
from aiogram import Bot
from aiogram.utils.markdown import hlink

from asyncmy.cursors import Cursor

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.tricks.tricks_chat_manage import tricks_cm
from core.data.texttriggers import deep_links
from core import func

async def get_user_id(msg: Message, db: Cursor, repo_biowar: RequestsRepoBiowar):

    user = await repo_biowar.get_user(func.reply_or_tag_geeter(msg))
    
    if not user:
        return await msg.answer(tricks_cm['get_id']['result_not_found'])
    
    entity = func.entity_create_consider_username(user)
    
    text = tricks_cm['get_id']['result_id'].format(user['id'], entity)
    
    await msg.answer(text, disable_web_page_preview=True)


async def get_chat_id(msg: Message, repo_biowar: RequestsRepoBiowar):

    chat = await repo_biowar.get_chat_by_id(msg.chat.id)
    
    text = tricks_cm['get_id']['get_chat_id'].format(chat['title'], chat['chat_id'])
    
    await msg.answer(text)