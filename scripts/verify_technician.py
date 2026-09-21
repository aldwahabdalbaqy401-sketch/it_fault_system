import psycopg2, psycopg2.extras
from config import Config

conn = psycopg2.connect(Config.DEFAULT_DB_URL, sslmode='require', cursor_factory=psycopg2.extras.RealDictCursor)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) as pending FROM faults WHERE assigned_to IS NOT NULL AND status IN ('new', 'in_progress')")
res1 = cur.fetchone()
print("Pending query success:", res1)

cur.execute("SELECT COUNT(*) as resolved FROM faults WHERE assigned_to IS NOT NULL AND status = 'resolved'")
res2 = cur.fetchone()
print("Resolved query success:", res2)

cur.close()
conn.close()
print("ALL TECHNICIAN QUERIES WORK 100%!")
