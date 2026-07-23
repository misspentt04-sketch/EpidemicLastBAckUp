from aiogram.types import Message
from aiogram import Bot
from aiogram.utils.markdown import hlink

from asyncmy.cursors import Cursor

from core.utils.db_api.repo_chat_manage import RequestsRepoChatManage
from core.data.tricks.tricks_chat_manage import tricks_cm
from core.data.texttriggers import deep_links
from core import func

async def set_nickname(msg: Message, db: Cursor, repo_cm: RequestsRepoChatManage):

    nickname = ' '.join(msg.text.split()[1:])

    await repo_cm.set_nickname(msg.from_user.id, nickname)
    
    text = tricks_cm['nickname']['successful_changed'].format(nickname)
    
    await msg.answer(text)




