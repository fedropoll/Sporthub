import psycopg2

try:
    conn = psycopg2.connect(
        dbname="sporthub_db",
        user="admin",
        password="admin",
        host="localhost",
        port="5432"
    )
    print("Подключение успешно!")
    conn.close()
except Exception as e:
    print(f"Ошибка: {e}")