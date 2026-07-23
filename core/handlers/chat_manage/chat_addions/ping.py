from aiogram.types import Message
from asyncmy.cursors import Cursor
from aiogram import Bot

from core.utils.db_api.repo_chat_manage import RequestsRepoChatManage
from core.utils.genai import gpt_thinks
from core.data.texttriggers import deep_links
from core.data.tricks.tricks_biowar import tricks_biowar
from core.data.tricks.tricks_genai import tricks_genai

from core import func

import random

async def ping(msg: Message, bot: Bot, db: Cursor, repo_cm: RequestsRepoChatManage):
    
    msgt = msg.text.lower().replace('.', '').replace('/', '').replace('!', '')
    
    text = tricks_biowar['ping'][msgt]
    if isinstance(text, list):
        text = random.choice(text)
    
    await msg.answer(text)