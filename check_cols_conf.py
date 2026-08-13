import asyncio
import asyncmy

# Импортируем конфиг проекта
try:
    from core.config import MYSQL_CONFIG
except ImportError:
    try:
        from config import MYSQL_CONFIG
    except ImportError:
        MYSQL_CONFIG = {"host": "localhost", "user": "root", "password": "", "database": "epidemic"}

async def check():
    print(f"Подключаемся к БД '{MYSQL_CONFIG.get('database')}' под пользователем '{MYSQL_CONFIG.get('user')}'...")
    conn = await asyncmy.connect(
        host=MYSQL_CONFIG.get('host', 'localhost'),
        port=MYSQL_CONFIG.get('port', 3306),
        user=MYSQL_CONFIG.get('user', 'root'),
        password=MYSQL_CONFIG.get('password', ''),
        database=MYSQL_CONFIG.get('database', 'epidemic')
    )
    async with conn.cursor() as cur:
        # 1. Смотрим все таблицы
        await cur.execute("SHOW TABLES;")
        tables = await cur.fetchall()
        print("Таблицы в БД:", [t[0] for t in tables])

        # 2. Ищем колонки со словом theme в users
        await cur.execute("DESCRIBE users;")
        cols = await cur.fetchall()
        theme_cols = [c[0] for c in cols if 'theme' in c[0].lower()]
        print("Колонки со словом 'theme' в users:", theme_cols)

        # 3. Смотрим данные вашего ID (7972320837)
        if theme_cols:
            cols_str = ", ".join(theme_cols)
            await cur.execute(f"SELECT user_id, {cols_str} FROM users WHERE user_id = 7972320837;")
            print("Ваши значения темы:", await cur.fetchone())

asyncio.run(check())
