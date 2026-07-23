from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message
from redis import Redis


class IsReplyPetNotifyMsgFilter(BaseFilter):
    async def __call__(self, msg: Message, redis: Redis) -> bool:
        if msg.reply_to_message and msg.reply_to_message.from_user.bot:
            is_pet_notify_msg = await redis.get(f'epidemic_pet_msg:{msg.chat.id}:{msg.reply_to_message.message_id}')
            if is_pet_notify_msg and is_pet_notify_msg.partition(':')[0] == str(msg.from_user.id):
                return True
            else:
                return False
        return False

