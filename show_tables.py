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
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print("=== СПИСОК ТАБЛИЦ В БАЗЕ ===")
        for t in tables:
            for key, val in t.items():
                print(val)
finally:
    connection.close()
