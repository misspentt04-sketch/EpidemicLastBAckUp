from asyncmy.cursors import DictCursor
from asyncmy.pool import Pool

from aiogram import BaseMiddleware
from aiogram.types import Update
from aiogram.dispatcher.flags import get_flag

from typing import Awaitable, Callable, Dict, Any
from cachetools import TTLCache
from datetime import datetime, timedelta

from core.data.whitelist_users import whitelist

import random

class ThrottlingMiddlewareInline(BaseMiddleware):

    def __init__(self, delay: int=2.5) -> None:
        self.delay = TTLCache(maxsize=10_000, ttl=delay)

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get('event_from_user')
        
        if (
            event.message.date.replace(tzinfo=None) <
            datetime.utcnow() - timedelta(days=1)
        ):
            return await event.answer('Кнопка устарела(')
        
        if user.id in self.delay:
            await event.answer(
                random.choice([
                    'Ты слишком горяч! Дай кнопке передохнуть(',
                    'Не насилуй кнопку, она итак даст'
                ]))
            return
        
        self.delay[user.id] = None
        return await handler(event, data)
        


