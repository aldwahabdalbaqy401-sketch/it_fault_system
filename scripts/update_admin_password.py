import bcrypt
import mysql.connector

from config import Config


NEW_PASSWORD = "0120270"
ADMIN_USERNAME = "admin"


conn = mysql.connector.connect(
    host=Config.MYSQL_HOST,
    user=Config.MYSQL_USER,
    password=Config.MYSQL_PASSWORD,
    database=Config.MYSQL_DB,
)
cursor = conn.cursor()

try:
    cursor.execute(
        "SELECT id, username, role FROM users WHERE username = %s",
        (ADMIN_USERNAME,),
    )
    user = cursor.fetchone()
    if not user:
        print(f"User not found: {ADMIN_USERNAME}")
    else:
        hashed_password = bcrypt.hashpw(
            NEW_PASSWORD.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')
        cursor.execute(
            "UPDATE users SET password = %s WHERE username = %s",
            (hashed_password, ADMIN_USERNAME),
        )
        conn.commit()
        print(f"Updated password for {user[1]}: {cursor.rowcount} row(s)")
finally:
    cursor.close()
    conn.close()
