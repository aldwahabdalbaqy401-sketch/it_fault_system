import mysql.connector
from flask import request, session
from config import Config

def log_activity(action, details=None):
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            charset='utf8mb4',
            use_unicode=True
        )
        cursor = conn.cursor()
        user_id = session.get('user_id')
        ip = request.remote_addr if request else '0.0.0.0'
        
        cursor.execute(
            "INSERT INTO activity_log (user_id, action, details, ip_address) VALUES (%s, %s, %s, %s)",
            (user_id, action, details, ip)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ خطأ في تسجيل النشاط: {e}")