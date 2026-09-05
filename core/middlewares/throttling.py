from aiogram import BaseMiddleware
from aiogram.types import Update
from cachetools import TTLCache
from typing import Awaitable, Callable, Dict, Any

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, time_limit: float = 0.3) -> None:
        # Задержка 0.3 сек между сообщениями
        self.rate_limit = TTLCache(maxsize=10_000, ttl=time_limit)

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get('event_from_user')
        chat = data.get('event_chat')

        # Работает во всех чатах (не только в ЛС)
        if not user:
            return await handler(event, data)

        # Ключ = user_id + chat_id (разные чаты — разные задержки)
        key = f"{user.id}:{chat.id if chat else 'global'}"

        if key in self.rate_limit:
            return  # Пропускаем если сообщение чаще чем раз в 0.3 сек

        self.rate_limit[key] = True
        return await handler(event, data)
