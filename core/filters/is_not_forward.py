from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message


class IsNotForwardFilter(BaseFilter):
    async def __call__(self, msg: Message) -> bool:
        return False if msg.forward_origin else True

