from aiogram import BaseMiddleware
from aiogram.types import Message
import time


class ActivityMiddleware(BaseMiddleware):
    """Считает команды каждого юзера за последние 10 минут"""

    def __init__(self, redis):
        self.redis = redis

    async def __call__(self, handler, event, data):
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
            key = f"activity:{user_id}"
            try:
                await self.redis.incr(key)
                await self.redis.expire(key, 600)  # 10 минут
            except Exception as e:
                print(f"[ACTIVITY] Redis error: {e}")
        return await handler(event, data)
