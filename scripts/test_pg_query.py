import psycopg2
from config import Config

conn = psycopg2.connect(Config.DEFAULT_DB_URL, sslmode='require')
cur = conn.cursor()
try:
    cur.execute('SELECT COUNT(*) as pending FROM faults WHERE assigned_to IS NOT NULL AND status IN ("new", "in_progress")')
    print("Double quotes worked")
except Exception as e:
    print("Postgres double quotes ERROR:", e)

try:
    cur.execute("SELECT COUNT(*) as pending FROM faults WHERE assigned_to IS NOT NULL AND status IN ('new', 'in_progress')")
    print("Single quotes worked successfully! Count:", cur.fetchone())
except Exception as e:
    print("Single quotes error:", e)

cur.close()
conn.close()
