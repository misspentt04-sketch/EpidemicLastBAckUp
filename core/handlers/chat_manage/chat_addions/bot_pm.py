from aiogram.types import Message
import random

async def bot_pm(msg: Message):
    await msg.answer(text, disable_web_page_preview=True)
