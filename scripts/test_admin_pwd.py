from app import app, bcrypt
import psycopg2
from config import Config

conn = psycopg2.connect(Config.DEFAULT_DB_URL, sslmode='require')
cur = conn.cursor()
cur.execute("SELECT password FROM users WHERE username = 'admin'")
row = cur.fetchone()
stored_pwd = row[0] if row else None
print("Stored hash:", stored_pwd)

with app.app_context():
    for test_p in ['123456', 'password123', 'admin', 'admin123', 'password']:
        try:
            res = bcrypt.check_password_hash(stored_pwd, test_p)
            print(f"Password '{test_p}' matches: {res}")
            if res:
                break
        except Exception as e:
            print(f"Error checking '{test_p}':", e)

cur.close()
conn.close()
