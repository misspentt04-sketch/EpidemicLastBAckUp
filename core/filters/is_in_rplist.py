from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message

from core.data.tricks.tricks_chat_manage import tricks_cm


class IsRPFilter(BaseFilter):
    async def __call__(self, msg: Message) -> bool:
        if msg.text:
            msg_text_clean = msg.text.lower().replace('.', '').replace('/', '').replace('!', '').split()
            if len(msg_text_clean) >= 1 and msg_text_clean[0] in tricks_cm['rp']:
                return True
            else:
                return False
        else:
            return False
