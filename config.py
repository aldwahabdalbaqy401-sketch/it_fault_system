import os


class Config:
    # ===== إعدادات قاعدة البيانات =====
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'it_fault_db'
    MYSQL_CHARSET = 'utf8mb4'
    MYSQL_USE_UNICODE = True

    # ===== إعدادات الأمان =====
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-only-change-this-secret-key')

    # ===== إعدادات CSRF (Flask-WTF) =====
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TRUSTED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

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
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

    # ===== اسم المشروع =====
    APP_NAME = 'نظام إدارة وتتبع الأعطال التقنية – بالتطبيق على جامعة النيل الأبيض'
    APP_NAME_EN = 'Technical Fault Management and Tracking System – Applied at White Nile University'
