import psycopg2
import psycopg2.extras
from flask import request, session
from config import Config


def log_activity(action, details=None):
    try:
        db_url = (getattr(Config, 'DATABASE_URL', '') or getattr(Config, 'DEFAULT_DB_URL', '')).strip().replace('\r', '').replace('\n', '')
        conn = psycopg2.connect(db_url, sslmode='require')
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
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