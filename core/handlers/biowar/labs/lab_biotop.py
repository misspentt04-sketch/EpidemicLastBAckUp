from aiogram.types import Message
from asyncmy.cursors import Cursor
from aiogram import Bot

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.texttriggers import deep_links
from core.data.tricks.tricks_biowar import tricks_biowar

from core import func

from humanize import intcomma

async def biotop(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    
    biotop = await repo_biowar.get_lab_biotop()
    
    biotop_list = func.get_biotop_lab(biotop)
    
    text = (
        tricks_biowar['biotops']['lab'].format(
            '\n'.join(biotop_list[0]), intcomma(biotop_list[1][0])
        )
    )
    
    await msg.answer(text)


async def biotop_chat(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    
    query = ''
    
    biotop = await repo_biowar.get_lab_biotop_chat(msg.chat.id)
    
    chat_biotop_list = func.get_biotop_lab(biotop)
    
    text = (
        tricks_biowar['biotops']['lab_chat'].format(
            '\n'.join(chat_biotop_list[0]), intcomma(chat_biotop_list[1][0])
        )
    )
    
    await msg.answer(text)

