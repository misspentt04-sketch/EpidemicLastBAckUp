from datetime import datetime
from asyncmy.pool import Pool
from core.settings import moscow_tz


def get_week_str() -> str:
    """Возвращает строку недели: '2026-38'"""
    now = datetime.now(moscow_tz)
    return now.strftime("%Y-%W")


async def add_activity_point(pool: Pool, user_id: int, source: str = "farm"):
    """Начисляет 1 очко активности за фарм или заражение"""
    week = get_week_str()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            if source == "farm":
                await cur.execute("""
                    INSERT INTO ActivityPoints (user_id, points, week_str, farm_count)
                    VALUES (%s, 1, %s, 1)
                    ON DUPLICATE KEY UPDATE
                        points = points + 1,
                        farm_count = farm_count + 1
                """, (user_id, week))
            else:  # infect
                await cur.execute("""
                    INSERT INTO ActivityPoints (user_id, points, week_str, infect_count)
                    VALUES (%s, 1, %s, 1)
                    ON DUPLICATE KEY UPDATE
                        points = points + 1,
                        infect_count = infect_count + 1
                """, (user_id, week))
