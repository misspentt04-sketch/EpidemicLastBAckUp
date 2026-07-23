from aiogram.types import Message
from aiogram import Bot

async def get_pet(msg: Message, bot: Bot, *args, **kwargs):
    await msg.answer("✨ Система питомцев была полностью отключена.")
