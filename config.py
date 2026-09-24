import os
from dotenv import load_dotenv

load_dotenv()  # تحميل متغيرات .env تلقائياً


class Config:
    # ===== قاعدة بيانات Supabase (PostgreSQL) =====
    DEFAULT_DB_URL = 'postgresql://postgres.sgsshggrhegoytypqslt:gedo0904613916@aws-1-eu-west-1.pooler.supabase.com:5432/postgres'
    DATABASE_URL = (os.getenv('DATABASE_URL') or DEFAULT_DB_URL).strip().replace('\r', '').replace('\n', '').strip("'").strip('"')

    # ===== إعدادات الأمان =====
    SECRET_KEY = os.getenv('SECRET_KEY', 'aldwahab-super-secret-key-2026')

    # ===== إعدادات CSRF (Flask-WTF) =====
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TRUSTED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0',
                               'aldwahabdalbaqy.pythonanywhere.com',
                               'it-fault-system.onrender.com',
                               '.onrender.com']

    # ===== إعدادات الجلسة والقوالب =====
    TEMPLATES_AUTO_RELOAD = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = True

    # ===== إعدادات البريد الإلكتروني =====
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER') or os.getenv('MAIL_USERNAME') or 'noreply@whitenile.edu.sd'

    # ===== اسم المشروع =====
    APP_NAME       = 'نظام إدارة وتتبع الأعطال التقنية'
    APP_NAME_EN    = 'Technical Fault Management System'
    APP_FULL_TITLE = 'نظام إدارة وتتبع الأعطال التقنية'
    APP_FULL_TITLE_EN = 'Technical Fault Management System'
