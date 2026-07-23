from redis import Redis

from aiogram import BaseMiddleware
from aiogram.types import Update
from aiogram.dispatcher.flags import get_flag

from typing import Awaitable, Callable, Dict, Any
from cachetools import TTLCache

from core.utils.db_api.repo_biowar import RequestsRepoBiowar

import random

class UserRestrictMiddleware(BaseMiddleware):

    def __init__(self, redis: Redis) -> None:
        self.redis: Redis = redis

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get('event_from_user')
        chat = data.get('event_chat')
        
        if chat:
            game_mute1 = await self.redis.get(f'epidemic_gamemute:{chat.id}')
            if game_mute1:
                return
        if user:
            game_mute = await self.redis.get(f'epidemic_gamemute:{user.id}')
            if game_mute:
                return
        
        return await handler(event, data)
        


