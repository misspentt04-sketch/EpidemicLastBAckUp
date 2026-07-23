from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message

from core.settings import settings


class IsAdminNotChatFilter(BaseFilter):
    async def __call__(self, msg: Message) -> bool:
        if str(msg.from_user.id) in settings.bots.admin_id:
            return True
        else:
            return False