"""
سكريبت إنشاء قاعدة البيانات MySQL على PythonAnywhere
قم بتشغيله مرة واحدة فقط من Bash Console على PythonAnywhere
"""

import pymysql
from config import Config


def initialize_database():
    print("🔄 جاري الاتصال بقاعدة البيانات MySQL...")

    try:
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = conn.cursor()
        print("✅ تم الاتصال بنجاح!")
    except Exception as e:
        print(f"❌ فشل الاتصال: {e}")
        print("تأكد من:")
        print("  1. تعيين كلمة مرور MySQL في config.py")
        print("  2. إنشاء قاعدة البيانات من صفحة Databases في PythonAnywhere")
        return

    tables_sql = [
        # ===== جدول المستخدمين =====
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            full_name VARCHAR(100),
            email VARCHAR(255) UNIQUE,
            phone VARCHAR(30),
            department VARCHAR(150),
            user_type VARCHAR(50),
            role ENUM('admin', 'supervisor', 'technician', 'user') DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,

        # ===== جدول الأعطال =====
        """
        CREATE TABLE IF NOT EXISTS faults (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            fault_type VARCHAR(50),
            location VARCHAR(255),
            priority ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
            status ENUM('new', 'in_progress', 'resolved', 'closed') DEFAULT 'new',
            attachment VARCHAR(255),
            user_id INT,
            assigned_to INT,
            scheduled_date DATETIME NULL,
            received_at DATETIME NULL,
            started_at DATETIME NULL,
            completed_at DATETIME NULL,
            technician_notes TEXT,
            user_rating TINYINT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,

        # ===== جدول رسائل الشات =====
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            fault_id INT NOT NULL,
            sender_id INT NOT NULL,
            receiver_id INT NULL,
            message TEXT NOT NULL,
            image VARCHAR(255) NULL,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_chat_fault (fault_id),
            INDEX idx_chat_sender (sender_id),
            INDEX idx_chat_receiver (receiver_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,

        # ===== جدول الإشعارات =====
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            fault_id INT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_notifications_user (user_id),
            INDEX idx_notifications_fault (fault_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,

        # ===== جدول سجل النشاط =====
        """
        CREATE TABLE IF NOT EXISTS activity_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NULL,
            username VARCHAR(50),
            action VARCHAR(255),
            details TEXT,
            ip_address VARCHAR(45),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_activity_user (user_id),
            INDEX idx_activity_created (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
    ]

    # إنشاء الجداول
    for sql in tables_sql:
        try:
            cursor.execute(sql)
            conn.commit()
        except Exception as e:
            print(f"⚠️ تحذير عند إنشاء جدول: {e}")

    print("✅ تم إنشاء الجداول بنجاح!")

    # إضافة المستخدمين الافتراضيين
    users_data = [
        ('admin',       '$2b$12$yDvDxul/CwhTR7tQQ.aBherTriSJSP3tNaHnqPDIAXbZDyh2GFjYe', 'مدير النظام',   'admin'),
        ('supervisor1', '$2b$12$yDvDxul/CwhTR7tQQ.aBherTriSJSP3tNaHnqPDIAXbZDyh2GFjYe', 'مشرف التقنية', 'supervisor'),
        ('tech1',       '$2b$12$yDvDxul/CwhTR7tQQ.aBherTriSJSP3tNaHnqPDIAXbZDyh2GFjYe', 'أحمد محمد',    'technician'),
        ('tech2',       '$2b$12$yDvDxul/CwhTR7tQQ.aBherTriSJSP3tNaHnqPDIAXbZDyh2GFjYe', 'خالد علي',     'technician'),
    ]

    for username, password, full_name, role in users_data:
        try:
            cursor.execute(
                "INSERT IGNORE INTO users (username, password, full_name, role) VALUES (%s, %s, %s, %s)",
                (username, password, full_name, role)
            )
        except Exception as e:
            print(f"⚠️ تحذير عند إضافة مستخدم {username}: {e}")

    conn.commit()
    print("✅ تم إضافة المستخدمين الافتراضيين!")
    print()
    print("=" * 50)
    print("🎉 قاعدة البيانات جاهزة!")
    print("=" * 50)
    print("بيانات الدخول الافتراضية:")
    print("  المدير:    admin      | كلمة المرور: 123456")
    print("  المشرف:    supervisor1 | كلمة المرور: 123456")
    print("  الفني 1:   tech1      | كلمة المرور: 123456")
    print("  الفني 2:   tech2      | كلمة المرور: 123456")
    print("=" * 50)

    cursor.close()
    conn.close()


if __name__ == '__main__':
    initialize_database()
