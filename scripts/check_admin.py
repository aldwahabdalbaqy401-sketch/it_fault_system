import psycopg2
from config import Config

conn = psycopg2.connect(Config.DEFAULT_DB_URL, sslmode='require')
cur = conn.cursor()
cur.execute("SELECT id, username, role, password FROM users WHERE username = 'admin'")
row = cur.fetchone()
print("Admin in DB:", row[0], row[1], row[2], "hash prefix:", row[3][:25] if row and row[3] else None)
cur.close()
conn.close()
