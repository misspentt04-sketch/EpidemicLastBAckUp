from asyncmy.cursors import DictCursor
from asyncmy.pool import Pool
from redis.asyncio import Redis
from aiocryptopay import AioCryptoPay
from datetime import datetime

from aiogram import BaseMiddleware, Bot
from aiogram.types import Update
from aiogram import html
from aiogram.dispatcher.flags import get_flag

from typing import Awaitable, Callable, Dict, Any
from asyncio import Lock

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.utils.db_api.repo_chat_manage import RequestsRepoChatManage

from core.func import clear_name_universal
from core.settings import settings


class DBPoolMiddleware(BaseMiddleware):

    def __init__(self, pool: Pool, redis: Redis, lock: Lock, bot: Bot, crypto: AioCryptoPay) -> None:
        self.pool: Pool = pool
        self.redis: Redis = redis
        self.lock: Lock = lock
        self.bot: Bot = bot
        self.crypto: AioCryptoPay = crypto

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        db_status = get_flag(data, 'db_status')

        if db_status or event.pre_checkout_query:
            return await handler(event, data)

        user = data.get('event_from_user')
        chat = data.get('event_chat')

        # Если событие не связано с конкретным пользователем, прокидываем дальше
        if not user:
            return await handler(event, data)

        async with self.pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                repo_biowar = RequestsRepoBiowar(cur)
                repo_chat_manage = RequestsRepoChatManage(cur)

                clear_name = clear_name_universal(user.full_name, user.username, user.id)

                await repo_biowar.add_data_user(
                    user.id,
                    clear_name,
                    user.username
                )
                await repo_biowar.add_data_user_lower(
                    user.id,
                    clear_name,
                    user.username
                )

                if chat:
                    if not event.chat_member or (event.chat_member and event.chat_member.new_chat_member.status != 'left'):
                        await repo_biowar.add_data_chat(
                            chat.id,
                            (chat.title if chat.type != 'private' else html.quote(chat.full_name or "")),
                            user.id,
                            chat.type == 'private'
                        )
                    if chat.type != 'private':
                        await repo_chat_manage.include_off_notifications(chat.id, 2)
                        marriage = await repo_chat_manage.get_marry(chat.id, user.id)

                        if marriage:
                            await repo_chat_manage.add_sms_marriages(chat.id, marriage['husband_id'])

                if not user.is_bot:
                    lab_time_created = datetime.utcnow().timestamp()
                    await repo_biowar.add_data_lab(user.id, clear_name, lab_time_created)
                    await repo_biowar.add_bag(user.id)
                    await repo_biowar.add_data_donate(user.id)
                    await repo_biowar.add_reputation_data(user.id)
                    if not event.callback_query and event.message:
                        await repo_biowar.insert_user_last_message(user.id, event_update=event)

                if str(user.id) in settings.bots.admin_id:
                    await self.redis.set(f'epidemic_help_admin_status:{user.id}', 'online', ex=15*60)

                data['redis'] = self.redis
                data['db'] = cur
                data['repo_biowar'] = repo_biowar
                data['repo_cm'] = repo_chat_manage
                data['lock'] = self.lock
                data['crypto'] = self.crypto

                result = await handler(event, data)
                await conn.commit()
                return result
