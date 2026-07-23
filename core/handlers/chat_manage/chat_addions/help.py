from aiogram.types import Message
from asyncmy.cursors import Cursor
from aiogram import Bot

from redis import Redis

from core.utils.db_api.repo_chat_manage import RequestsRepoChatManage
from core.data.texttriggers import deep_links
from core.data.tricks.tricks_chat_manage import tricks_cm
from core.data.tg_ban_words import words as tg_ban_words

from core.keyboards.inline.tutorial_begin import help_kb

from core import func

async def help(msg: Message, bot: Bot, redis: Redis, repo_cm: RequestsRepoChatManage):
    
    admin_list = tricks_cm['start']['menu_admin_list']
    online = []
    offline = []
    
    for key, val in admin_list.items():
        admin = await redis.get(f'epidemic_help_admin_status:{key}')
        if admin:
            online.append(val)
        else:
            offline.append(val)
    
    text = tricks_cm['start']['menu'].format(
        '\n'.join(online),
        '\n'.join(offline)
    )
    
    await msg.answer(text, reply_markup=help_kb(), disable_web_page_preview=True)
    