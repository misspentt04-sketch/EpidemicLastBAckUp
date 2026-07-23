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
        print("=== ТАБЛИЦА CASES ===")
        try:
            cursor.execute("SELECT * FROM cases LIMIT 5;")
            for row in cursor.fetchall():
                print(row)
        except Exception as e:
            print(f"Ошибка с таблицей cases: {e}")

        print("\n=== ТАБЛИЦА ПРОМОКОДОВ ===")
        promo_table_found = False
        for table_name in ["promocodes", "promo", "codes"]:
            try:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
                print(f"Найдена таблица: {table_name}")
                for row in cursor.fetchall():
                    print(row)
                promo_table_found = True
                break
            except Exception:
                continue
        
        if not promo_table_found:
            print("Таблица промокодов не найдена.")
finally:
    connection.close()
