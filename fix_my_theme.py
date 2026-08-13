import asyncio
import asyncmy
import json
from core.config import settings

async def run():
    db_cfg = settings.db
    conn = await asyncmy.connect(
        host=db_cfg.host,
        port=db_cfg.port,
        user=db_cfg.user,
        password=db_cfg.password,
        database=db_cfg.database
    )
    async with conn.cursor() as cur:
        user_id = 7972320837
        bought = ["default", "admin"]
        await cur.execute("UPDATE Users SET active_theme = 'admin', bought_themes = %s WHERE id = %s", (json.dumps(bought), user_id))
        await conn.commit()
        print("✅ Админ-тема успешно прописана в БД для вашего ID!")

asyncio.run(run())
