import pymysql

connection = pymysql.connect(
    host="localhost",
    user="root",
    password="1603",
    database="epidemic",
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor
)

try:
    with connection.cursor() as cursor:
        for table in ["Promos", "promo_code", "Admins"]:
            print(f"\n=== ТАБЛИЦА: {table} ===")
            try:
                cursor.execute(f"SELECT * FROM {table} LIMIT 10;")
                rows = cursor.fetchall()
                if not rows:
                    print("(пусто)")
                for r in rows:
                    print(r)
            except Exception as e:
                print(f"Ошибка: {e}")
finally:
    connection.close()
