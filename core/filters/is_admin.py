from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message

from core.settings import settings
from core.settings import CHAT_ADMINS


class IsAdminFilter(BaseFilter):
    async def __call__(self, msg: Message) -> bool:
        if str(msg.from_user.id) in settings.bots.admin_id and msg.chat.id == CHAT_ADMINS:
            return True
        else:
            return False
