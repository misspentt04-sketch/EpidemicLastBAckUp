import logging
import asyncmy
import asyncio

from core.settings import settings

from core.services.loop_tasks import (
    victim_expire_check, victim_expire_kd_check, victim_fever_check,
    pathogens_refresh_check, corporation_stats_refresh, gave_victims_food,
    refresh_pets_vuln_indicator, game_mute_check, pet_the_pet_time_check,
    pet_happy_check,
    student_income_loop,
    weekly_exp_grant
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
            minsize=10,
            maxsize=100,
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
    logging.info("DEBUG loop_tasks started")
    
    # Запускаем все задачи через create_task, чтобы они не блокировали друг друга
    try:
        asyncio.create_task(weekly_exp_grant(pool))
        asyncio.create_task(victim_expire_check(pool))
        asyncio.create_task(victim_expire_kd_check(pool))
        asyncio.create_task(victim_fever_check(pool))
        asyncio.create_task(pathogens_refresh_check(pool))
        asyncio.create_task(corporation_stats_refresh(pool))
        asyncio.create_task(refresh_pets_vuln_indicator(redis))
        asyncio.create_task(game_mute_check(pool, redis, bot))
        asyncio.create_task(pet_the_pet_time_check(pool, redis, bot))
        asyncio.create_task(pet_happy_check(pool))
        print("✅ [SETTINGS_POOL] Все задачи запущены, включая student_income_loop!")
    except Exception as e:
        print(f"[LOOP] ОШИБКА: {e}")
    
    # Держим функцию активной, чтобы задачи не завершились
    while True:
        await asyncio.sleep(3600)

async def scheduler_tasks(pool, redis, bot, scheduler):
    # Кормление жертв
    scheduler.add_job(gave_victims_food, 'cron', hour='12,0', minute=0, args=(pool,))

    # Еженедельный отчет в воскресенье в 23:59
    scheduler.add_job(send_weekly_top_report, 'cron', day_of_week='sun', hour=23, minute=59, args=(bot,))

    # Ежемесячный отчет в последний день любого месяца в 23:59
    scheduler.add_job(send_monthly_top_report, 'cron', day='last sun,last mon,last tue,last wed,last thu,last fri,last sat', hour=23, minute=59, args=(bot,))

    # ===== АВТОЗАПУСК БОССА В 20:00 МСК =====
    from core.services.scheduler_tasks import auto_start_boss, finish_boss
    scheduler.add_job(auto_start_boss, 'cron', hour=20, minute=0, args=(pool, redis, bot))
    scheduler.add_job(finish_boss, 'interval', minutes=1, args=(pool, redis, bot))
    print("[SCHEDULER] Автозапуск босса запланирован на 20:00 МСК")

# ===== ПРОВЕРКА КРЕДИТОВ ДОБАВЛЕНА В loop_tasks =====
# check_expired_credits запускается каждые 24 часа
