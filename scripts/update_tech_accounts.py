# -*- coding: utf-8 -*-
import sys
import psycopg2
from config import Config
from flask_bcrypt import Bcrypt
from flask import Flask

app = Flask(__name__)
bcrypt = Bcrypt(app)

conn = psycopg2.connect(Config.DEFAULT_DB_URL, sslmode='require')
cur = conn.cursor()
hashed = bcrypt.generate_password_hash('password123').decode('utf-8')

# Ensure tech1 exists and has technician role
cur.execute("SELECT id FROM users WHERE username = 'tech1'")
if cur.fetchone():
    cur.execute("UPDATE users SET role = 'technician', password = %s, full_name = 'م. أحمد محمد (فني شبكات)' WHERE username = 'tech1'", (hashed,))
else:
    cur.execute("INSERT INTO users (username, password, full_name, email, role, phone, department, user_type) VALUES ('tech1', %s, 'م. أحمد محمد (فني شبكات)', 'tech1@whitenile.edu.sd', 'technician', '0123456789', 'تقنية المعلومات', 'staff')", (hashed,))

# Ensure tech2 exists and has technician role
cur.execute("SELECT id FROM users WHERE username = 'tech2'")
if cur.fetchone():
    cur.execute("UPDATE users SET role = 'technician', password = %s, full_name = 'م. سارة علي (فني صيانة ودعم)' WHERE username = 'tech2'", (hashed,))
else:
    cur.execute("INSERT INTO users (username, password, full_name, email, role, phone, department, user_type) VALUES ('tech2', %s, 'م. سارة علي (فني صيانة ودعم)', 'tech2@whitenile.edu.sd', 'technician', '0987654321', 'تقنية المعلومات', 'staff')", (hashed,))

conn.commit()

cur.execute("SELECT id, username, role FROM users WHERE role = 'technician'")
rows = cur.fetchall()
print("Success! Technicians updated:")
for r in rows:
    print(f"ID={r[0]}, Username={r[1]}, Role={r[2]}")

cur.close()
conn.close()
