from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message


class IsNotBotFilter(BaseFilter):
    async def __call__(self, msg: Message) -> bool:
        if msg.reply_to_message:
            return False if msg.reply_to_message.from_user.is_bot else True
        else:
            return True