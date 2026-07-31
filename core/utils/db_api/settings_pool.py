import asyncmy
import asyncio

from core.settings import settings

from core.services.loop_tasks import (
    victim_expire_check, victim_expire_kd_check, victim_fever_check,
    pathogens_refresh_check, corporation_stats_refresh, gave_victims_food,
    refresh_pets_vuln_indicator, game_mute_check, pet_the_pet_time_check,
    pet_happy_check
)
from core.services.top_reports import send_weekly_top_report, send_monthly_top_report

class DatabasePool:
    def __init__(self):
        self._pool = None

    async def create_pool(self):
        self._pool = await asyncmy.create_pool(
            host=settings.db.ip,
            user=settings.db.user,
            password=settings.db.password,
            db=settings.db.db,
            autocommit=True,
        )

    async def get_pool(self) -> asyncmy.Pool:
        if self._pool is None:
            await self.create_pool()
        return self._pool

    async def close_pool(self):
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None

db_pool = DatabasePool()

async def loop_tasks(pool, redis, bot):
    tasks = [
        victim_expire_check(pool),
        victim_expire_kd_check(pool),
        victim_fever_check(pool),
        pathogens_refresh_check(pool),
        corporation_stats_refresh(pool),
        refresh_pets_vuln_indicator(redis),
        game_mute_check(pool, redis, bot),
        pet_the_pet_time_check(pool, redis, bot),
        pet_happy_check(pool)
    ]
    await asyncio.gather(*tasks)

async def scheduler_tasks(pool, redis, bot, scheduler):
    # Кормление жертв
    scheduler.add_job(gave_victims_food, 'cron', hour='12,0', minute=0, args=(pool,))
    
    # Еженедельный отчет в воскресенье в 23:59
    scheduler.add_job(send_weekly_top_report, 'cron', day_of_week='sun', hour=23, minute=59, args=(bot,))
    
    # Ежемесячный отчет в последний день любого месяца в 23:59 (выражение 'last' для cron в APScheduler)
    scheduler.add_job(send_monthly_top_report, 'cron', day='last sun,last mon,last tue,last wed,last thu,last fri,last sat', hour=23, minute=59, args=(bot,))
