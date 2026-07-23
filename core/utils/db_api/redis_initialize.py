from asyncmy.cursors import DictCursor, Cursor
from asyncmy.pool import Pool
from redis import Redis

import asyncio


async def load_restrict_bot_users(cur: Cursor, redis: Redis):
    query = 'SELECT * FROM GameMute;'
    await cur.execute(query)
    users = await cur.fetchall()
    async with redis.pipeline() as pipe:
        for user in users:
            pipe.set(f'epidemic_gamemute:{user["user_id"]}', user['time_expire'])
        await pipe.execute()


async def redis_initialize(pool: Pool, redis: Redis):
    
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            tasks = [
                load_restrict_bot_users(cur, redis)
            ]
            await asyncio.gather(*tasks)
            