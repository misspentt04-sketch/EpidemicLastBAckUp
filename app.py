from core.handlers.idea import idea_router
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.enums.chat_type import ChatType

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.cryptopay import crypto
from redis.asyncio import Redis
from pytz import timezone

from core.middlewares import (
    DBPoolMiddleware, ThrottlingMiddleware, ThrottlingMiddlewareInline,
    UserRestrictMiddleware, ChatMemberUpdateMiddleware
)
from core.filters import IsNotBotFilter, IsNotForwardFilter, IsNotChannelFilter

from core.utils.db_api.settings_pool import db_pool, loop_tasks, scheduler_tasks
from core.utils.commands import set_commands, del_commands
from core.utils.db_api.create_database import db_settings_up
from core.utils.db_api.redis_initialize import redis_initialize

from core.handlers import (
    biowar_router,
    biowar_router2,
    chat_manage_router,
    story_router,
    biowar_global_router,
    suggestions_router
)
from core.handlers.startup import start

from core.settings import settings

import logging
import asyncio


logging.getLogger("asyncmy").setLevel(logging.ERROR)

async def run_tasks(pool, redis, bot, scheduler):
    asyncio.create_task(loop_tasks(pool, redis, bot))
    asyncio.create_task(scheduler_tasks(pool, redis, bot, scheduler))

async def main():
    logging.basicConfig(level=logging.INFO,
                        format = '%(asctime)s - [%(levelname)s] - %(name)s - '
                        '(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s')

    bot = Bot(settings.bots.bot_token, default = DefaultBotProperties(parse_mode=ParseMode.HTML))
    redis_db = Redis(host=settings.redis.ip, port=6379, db=0, decode_responses=True)
    storage = RedisStorage(redis=redis_db)
    
    dp = Dispatcher(storage=storage)
    pool = await db_pool.get_pool()
    scheduler = AsyncIOScheduler(timezone=timezone('Europe/Moscow'))
    lock = asyncio.Lock()
    
    await bot.delete_webhook(drop_pending_updates = True)
    
#     await db_settings_up(pool)
    
    await del_commands(bot)
    await set_commands(bot)
    
    await redis_initialize(pool, redis_db)

    # Middlewares
    
    dp.update.outer_middleware.register(DBPoolMiddleware(pool, redis_db, lock, bot, crypto))
    dp.message.middleware.register(ThrottlingMiddleware(1.5))
    dp.callback_query.middleware.register(ThrottlingMiddlewareInline(0.5))
    dp.chat_member.middleware.register(ChatMemberUpdateMiddleware())
    
    biowar_router.message.middleware.register(UserRestrictMiddleware(redis_db))
    biowar_router2.message.middleware.register(UserRestrictMiddleware(redis_db))

    
    #        # Start
    dp.message.register(start, CommandStart(ignore_case=True), F.chat.type == ChatType.PRIVATE)

    dp.include_routers(
    idea_router,
        biowar_router,
        biowar_router2,
        biowar_global_router,
        story_router,
        chat_manage_router,
        suggestions_router
    )

    # dp.message.filter(IsNotForwardFilter())
    # biowar_router.message.filter(IsNotBotFilter(), IsNotChannelFilter())
    # biowar_router2.message.filter(IsNotChannelFilter())

    await run_tasks(pool, redis_db, bot, scheduler)

    print('Started succesfully!')

    scheduler.start()
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown()
        await bot.session.close()
    
    
if __name__ == "__main__":
    asyncio.run(main())