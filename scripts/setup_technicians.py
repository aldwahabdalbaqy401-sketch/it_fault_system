import psycopg2
from config import Config
from werkzeug.security import generate_password_hash

conn = psycopg2.connect(Config.DEFAULT_DB_URL, sslmode='require')
cur = conn.cursor()

pwd_hash = generate_password_hash('password123')

cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users'")
cols = [r[0] for r in cur.fetchall()]
print("Users columns:", cols)

pwd_col = 'password' if 'password' in cols else 'password_hash'
cur.execute(f"UPDATE users SET role = 'technician', {pwd_col} = %s WHERE username = 'tech1'", (pwd_hash,))
if cur.rowcount == 0:
    cur.execute(f"""
        INSERT INTO users (username, {pwd_col}, full_name, email, role, phone, department)
        VALUES ('tech1', %s, 'م. أحمد محمد (فني شبكات)', 'tech1@whitenile.edu.sd', 'technician', '0123456789', 'تقنية المعلومات')
    """, (pwd_hash,))

cur.execute("SELECT id FROM users WHERE username = 'tech2'")
if not cur.fetchone():
    cur.execute(f"""
        INSERT INTO users (username, {pwd_col}, full_name, email, role, phone, department)
        VALUES ('tech2', %s, 'م. سارة علي (فني صيانة)', 'tech2@whitenile.edu.sd', 'technician', '0987654321', 'تقنية المعلومات')
    """, (pwd_hash,))

conn.commit()

cur.execute("SELECT id, username, full_name, role FROM users WHERE role = 'technician'")
print('Technicians in DB:', cur.fetchall())
cur.close()
conn.close()
