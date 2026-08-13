from aiogram import BaseMiddleware
from aiogram.types import Update
from cachetools import TTLCache
from typing import Awaitable, Callable, Dict, Any
from datetime import datetime, timedelta

import asyncio
import time

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(
        self,
        limit: int=2.0,
        per_chat_limit: int = 1500,
        time_window: int = 60,
        cmd_peer_second: int = 2,
        time_inteval_floodwait: int = 30
    )-> None:
        self.rate_limit = TTLCache(maxsize=1000_000, ttl=limit)
        # Лимит 20 сообщений в минуту на чат
        self.chat_limits = TTLCache(maxsize=1000_000, ttl=time_window)  # Хранит счетчики сообщений для чатов
        self.per_chat_limit = per_chat_limit  # Лимит сообщений в минуту для чата
        self.time_window = time_window  # Время в секундах (60 для минуты)
        self.cmd_peer_second = cmd_peer_second
        self.cmd_tracker = TTLCache(maxsize=10_000, ttl=1)
        self.interval_cmd = {}
        self.interval_cmd_tracker = TTLCache(maxsize=10_000, ttl=time_inteval_floodwait)

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        chat = data.get('event_chat')  # ID чата, откуда пришел запрос
        user = data.get('event_from_user')
        
        # if user.id in self.rate_limit:
        #     await event.delete()
        #     return
        # if user.id in self.interval_cmd_tracker:
        #     if self.interval_cmd_tracker[user.id] is None:
        #         await event.answer(f'❗️ Вам выдан флудвейт на 60 секунд в связи с цикличным таймером. Экспирементально.')
        #         self.interval_cmd_tracker[user.id] = True
        #     return
        
        # Ключ для отслеживания сообщений в этом чате
        chat_key = f"{chat.id}"
        
        # Инициализируем счетчик сообщений для чата, если его нет
        if chat_key not in self.chat_limits and chat.type != 'private':
            self.chat_limits[chat_key] = 0
        if chat_key not in self.cmd_tracker:
            self.cmd_tracker[chat_key] = set()
        # Interval anti ddos & mass attack
        if user.id not in self.interval_cmd:
            self.interval_cmd[user.id] = {}
        
        interval_key = self.interval_cmd[user.id]
        now = datetime.utcnow()
        if 'time0' not in interval_key:
            self.interval_cmd[user.id]['time0'] = now
        elif 'time1' not in interval_key:
            self.interval_cmd[user.id]['time1'] = now
        elif 'time2' not in interval_key:
            self.interval_cmd[user.id]['time2'] = now
        elif 'time3' not in interval_key:
            self.interval_cmd[user.id]['time3'] = now
            interval_key = self.interval_cmd[user.id]
            time1 = round((interval_key['time1'] - interval_key['time0']).total_seconds(), 1)
            time2 = round((interval_key['time2'] - interval_key['time1']).total_seconds(), 1)
            time3 = round((interval_key['time3'] - interval_key['time2']).total_seconds(), 1)
            if time1 == time2 == time3:
                self.interval_cmd_tracker[user.id] = None
            self.interval_cmd.pop(user.id)
        #   
        
        current_cmds = self.cmd_tracker[chat_key]
        
        # if len(current_cmds) >= self.cmd_peer_second:
        #     return
        
        # Проверяем лимит для чата
        if (
            chat.type != 'private' and self.chat_limits[chat_key] >= self.per_chat_limit
            and event.text
            and 'заразить' in event.text.lower()
        ):
            # Если лимит превышен, ждем до конца окна
            return
        
        # Увеличиваем счетчик сообщений для чата
        if chat.type != 'private':
            self.chat_limits[chat_key] += 1
        self.rate_limit[user.id] = None
        if user.id not in current_cmds:# and event.text and 'заразить' in event.text.lower():
            current_cmds.add(user.id)
            self.cmd_tracker[chat_key] = current_cmds

        return await handler(event, data)

