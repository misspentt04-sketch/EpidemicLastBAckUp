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
        # Получаем список всех колонок таблицы users
        await cur.execute("DESCRIBE users;")
        cols = await cur.fetchall()
        print("--- КОЛОНКИ ТАБЛИЦЫ USERS ---")
        theme_cols = [c[0] for c in cols if 'theme' in c[0].lower()]
        print("Все колонки со словом 'theme':", theme_cols)
        
        # Запрашиваем данные по пользователю
        if theme_cols:
            cols_str = ", ".join(theme_cols)
            await cur.execute(f"SELECT user_id, {cols_str} FROM users WHERE user_id = 7972320837;")
            row = await cur.fetchone()
            print("Значения для вашей лабы:", row)
        else:
            print("Колонки со словом 'theme' не найдены! Все колонки:", [c[0] for c in cols])

asyncio.run(check())
