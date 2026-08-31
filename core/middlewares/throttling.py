from aiogram import BaseMiddleware
from aiogram.types import Update
from cachetools import TTLCache
from typing import Awaitable, Callable, Dict, Any

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, time_limit: float = 0.3) -> None:
        # Задержка 0.3 сек позволит нормально отправлять сообщения раз в 1 сек
        self.rate_limit = TTLCache(maxsize=10_000, ttl=time_limit)

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        chat = data.get('event_chat')
        user = data.get('event_from_user')

        # Работает только в ЛС
        if not user or not chat or chat.type != 'private':
            return await handler(event, data)

        if user.id in self.rate_limit:
            return  # Сбрасывает только если сообщения идут чаще, чем раз в 0.3 сек

        self.rate_limit[user.id] = True
        return await handler(event, data)
