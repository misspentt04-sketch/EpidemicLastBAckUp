import asyncio
import asyncmy

async def check():
    conn = await asyncmy.connect(
        host='localhost',
        port=3306,
        user='root',
        password='',
        database='epidemic'
    )
    async with conn.cursor() as cur:
        await cur.execute("SHOW TABLES LIKE '%theme%';")
        tables = await cur.fetchall()
        print("Таблицы тем:", tables)
        
        # Проверяем записи в найденных таблицах тем
        for t in tables:
            t_name = t[0]
            await cur.execute(f"SELECT * FROM {t_name} LIMIT 5;")
            rows = await cur.fetchall()
            print(f"Данные из {t_name}:", rows)

asyncio.run(check())
