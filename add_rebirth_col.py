import asyncio
from core.database import db_pool

async def main():
    try:
        pool = await db_pool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("ALTER TABLE Lab ADD COLUMN rebirth_level INT DEFAULT 0;")
                print("✅ Столбец rebirth_level успешно добавлен в таблицу Lab!")
    except Exception as e:
        print(f"ℹ️ Статус колонки в БД: {e}")

if __name__ == "__main__":
    asyncio.run(main())
