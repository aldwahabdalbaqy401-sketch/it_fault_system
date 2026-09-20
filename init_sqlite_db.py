import sqlite3
import os

def initialize_database():
    db_file = 'it_fault_db.db'
    
    if os.path.exists(db_file):
        print(f"Database {db_file} already exists.")
        return

    print("Initializing SQLite database with embedded schema...")
    
    schema = """
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(50) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        full_name VARCHAR(100),
        email VARCHAR(255) UNIQUE,
        phone VARCHAR(30),
        department VARCHAR(150),
        user_type VARCHAR(50),
        role VARCHAR(50) DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE faults (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(200) NOT NULL,
        description TEXT,
        fault_type VARCHAR(50),
        location VARCHAR(255),
        priority VARCHAR(50) DEFAULT 'medium',
        status VARCHAR(50) DEFAULT 'new',
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
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fault_id INT NOT NULL,
        sender_id INT NOT NULL,
        receiver_id INT NULL,
        message TEXT NOT NULL,
        image VARCHAR(255) NULL,
        is_read BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INT NOT NULL,
        fault_id INT NULL,
        message TEXT NOT NULL,
        is_read BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INT NULL,
        username VARCHAR(50),
        action VARCHAR(255),
        details TEXT,
        ip_address VARCHAR(45),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    INSERT INTO users (username, password, full_name, role) VALUES
    ('admin', '$2b$12$yDvDxul/CwhTR7tQQ.aBherTriSJSP3tNaHnqPDIAXbZDyh2GFjYe', 'مدير النظام', 'admin'),
    ('supervisor1', '$2b$12$yDvDxul/CwhTR7tQQ.aBherTriSJSP3tNaHnqPDIAXbZDyh2GFjYe', 'مشرف التقنية', 'supervisor'),
    ('tech1', '$2b$12$yDvDxul/CwhTR7tQQ.aBherTriSJSP3tNaHnqPDIAXbZDyh2GFjYe', 'أحمد محمد', 'technician'),
    ('tech2', '$2b$12$yDvDxul/CwhTR7tQQ.aBherTriSJSP3tNaHnqPDIAXbZDyh2GFjYe', 'خالد علي', 'technician');
    
    INSERT INTO faults (title, description, priority, status) VALUES
    ('شاشة سوداء', 'الجهاز لا يعمل والشاشة سوداء بالكامل، لا يوجد استجابة', 'critical', 'new'),
    ('بطء في النظام', 'الجهاز بطيء جداً في التشغيل ويستغرق دقائق لفتح البرامج', 'medium', 'in_progress'),
    ('مشكلة في الطابعة', 'الطابعة لا تطبع على الرغم من الاتصال والمحبرة جديدة', 'high', 'resolved'),
    ('انقطاع الإنترنت', 'الإنترنت مقطوع في قسم المالية منذ الصباح', 'critical', 'in_progress'),
    ('تعطل البريد الإلكتروني', 'لا يمكن إرسال أو استقبال البريد الإلكتروني', 'high', 'new'),
    ('مشكلة في برنامج المحاسبة', 'برنامج المحاسبة يظهر خطأ عند فتح التقارير', 'medium', 'resolved'),
    ('شاشة زرقاء', 'يظهر خطأ شاشة زرقاء عند تشغيل الجهاز', 'critical', 'new'),
    ('بطء في الشبكة', 'الشبكة الداخلية بطيئة جداً وتؤثر على العمل', 'high', 'in_progress'),
    ('تعطل السيرفر', 'السيرفر الرئيسي لا يعمل ولا يمكن الدخول للنظام', 'critical', 'resolved'),
    ('مشكلة في الصوت', 'الصوت لا يعمل على جهاز الاجتماعات', 'low', 'closed');
    """

    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Execute script
        cursor.executescript(schema)
        
        conn.commit()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    initialize_database()
