import psycopg2
import os
import dj_database_url

try:
    conn = psycopg2.connect(
        dj_database_url.config(default=os.getenv('DATABASE_URL'))
    )
    print("Подключение успешно!")
    conn.close()
except Exception as e:
    print(f"Ошибка: {e}")
