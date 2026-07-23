from aiogram import BaseMiddleware
from aiogram.types import Update

from typing import Any, Awaitable, Callable
from cachetools import TTLCache

import asyncio

class ChatMemberUpdateMiddleware(BaseMiddleware):
    
    def __init__(self) -> None:
        self.time_limit = TTLCache(maxsize=10_000, ttl=3)
    
    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        chat = data.get('event_chat')
        
        if self.time_limit.get(chat.id):
            return
        
        self.time_limit[chat.id] = None
        
        return await handler(event, data)
