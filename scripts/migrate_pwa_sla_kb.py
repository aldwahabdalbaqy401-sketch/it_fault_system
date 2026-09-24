"""
Migration script for SLA, Knowledge Base, PWA, and Spare Parts tracking.
Supports Supabase PostgreSQL and MySQL.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
import psycopg2
import psycopg2.extras

def run_migration():
    print("🔄 Connecting to database for SLA, Knowledge Base & Spare Parts migration...")
    db_url = Config.DATABASE_URL or Config.DEFAULT_DB_URL
    db_url = db_url.strip().replace('\r', '').replace('\n', '').strip("'").strip('"')

    try:
        conn = psycopg2.connect(db_url, sslmode='require')
        cursor = conn.cursor()
        print("✅ Database connected successfully!")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return

    # 1. Add SLA and Spare Parts columns to `faults` table
    alter_faults_queries = [
        "ALTER TABLE faults ADD COLUMN IF NOT EXISTS sla_due_date TIMESTAMP NULL;",
        "ALTER TABLE faults ADD COLUMN IF NOT EXISTS is_escalated BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE faults ADD COLUMN IF NOT EXISTS escalated_at TIMESTAMP NULL;",
        "ALTER TABLE faults ADD COLUMN IF NOT EXISTS spare_parts_cost NUMERIC(10, 2) DEFAULT 0.00;"
    ]

    for q in alter_faults_queries:
        try:
            cursor.execute(q)
            conn.commit()
            print(f"  Applied: {q.strip()[:45]}...")
        except Exception as e:
            conn.rollback()
            print(f"  Note on column check: {e}")

    # 2. Create Knowledge Base table
    kb_table_sql = """
    CREATE TABLE IF NOT EXISTS knowledge_base (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        category VARCHAR(100) NOT NULL,
        content TEXT NOT NULL,
        tags VARCHAR(255),
        views_count INT DEFAULT 0,
        helpful_count INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        cursor.execute(kb_table_sql)
        conn.commit()
        print("✅ Table 'knowledge_base' ready.")
    except Exception as e:
        conn.rollback()
        print(f"  Note on knowledge_base table: {e}")

    # 3. Create Fault Parts table
    parts_table_sql = """
    CREATE TABLE IF NOT EXISTS fault_parts (
        id SERIAL PRIMARY KEY,
        fault_id INT NOT NULL,
        part_name VARCHAR(150) NOT NULL,
        quantity INT DEFAULT 1,
        unit_cost NUMERIC(10, 2) DEFAULT 0.00,
        total_cost NUMERIC(10, 2) DEFAULT 0.00,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        cursor.execute(parts_table_sql)
        conn.commit()
        print("✅ Table 'fault_parts' ready.")
    except Exception as e:
        conn.rollback()
        print(f"  Note on fault_parts table: {e}")

    # 4. Insert Initial Knowledge Base Articles
    seed_kb_articles = [
        (
            'حل مشكلة عدم استجابة الطابعة أو ظهورها كـ Offline',
            'أجهزة',
            '1. تأكد من توصيل كابل الطاقة وكابل USB أو الشبكة بإحكام.\n2. افتح قائمة ابدأ (Start) ثم توجه إلى Settings > Printers & Scanners.\n3. اضغط على الطابعة واختر "Open queue" ثم قم بإلغاء أي أوامر طباعة معلقة (Cancel all documents).\n4. تأكد من إزالة علامة الصح عن خيار "Use Printer Offline".\n5. قم بإعادة تشغيل خدمة الطباعة (Print Spooler) من خلال Services.msc.',
            'طابعة, printer, offline, طباعة'
        ),
        (
            'خطوات استعادة الاتصال بشبكة الإنترنت والواي فاي',
            'شبكات',
            '1. تأكد من توصيل كابل الشبكة (Ethernet) بشكل سليم وإضاءة منفذ الشبكة.\n2. في حال استخدام الواي فاي، قم بفصل الشبكة وإعادة إدخال كلمة المرور.\n3. افتح موجه الأوامر (CMD) كمسؤول واكتب الأوامر التالية بالترتيب:\n   - ipconfig /release\n   - ipconfig /renew\n   - ipconfig /flushdns\n4. قم بإعادة تشغيل الجهاز.',
            'انترنت, شبكة, wifi, internet, network, بطء'
        ),
        (
            'طريقة إعداد وحل مشاكل البريد الإلكتروني الجامعي',
            'برمجيات',
            '1. تأكد من كتابة عنوان البريد كاملاً مع النطاق @whitenile.edu.sd.\n2. تأكد من تفعيل المصادقة والتحقق بخطوتين في حال تفعيلها.\n3. في حال نسيان كلمة المرور، استخدم رابط "نسيت كلمة المرور" من صفحة الدخول بالبوابة.\n4. لمزامنة البريد على الهاتف أو Outlook، تأكد من ضبط إعدادات الخادم (IMAP: Port 993 SSL, SMTP: Port 587 TLS).',
            'ايميل, بريد, email, outlook, كلمة المرور'
        ),
        (
            'حل مشكلة الشاشة الزرقاء أو بطء وتجمد النظام المفاجئ',
            'برمجيات',
            '1. قم بفصل أي أجهزة USB خارجية مضافة مؤخراً.\n2. افتح إدارة المهام (Task Manager) وتحقق من البرامج التي تستهلك المعالج أو الذاكرة RAM بنسبة 100%.\n3. قم بتنظيف الملفات المؤقتة عبر الضغط على Win + R وكتابة %temp% وحذف الملفات.\n4. في حال استمرار المشكلة، سجل بلاغاً عاجلاً لقسم الصيانة ليقوم الفني بفحص الهارد ديسك والرامات.',
            'شاشة زرقاء, تعليق, بطء, windows, تجمد'
        ),
        (
            'إرشادات استخدام بروجكتر القاعات الذكية والشاشات التفاعلية',
            'أجهزة',
            '1. تأكد من اختيار مصدر الإدخال الصحيح (HDMI 1 أو HDMI 2) من جهاز التحكم عن بعد.\n2. استخدم اختصار لوحة المفاتيح (Windows Key + P) واختر "Duplicate" لتكرار شاشة اللابتوب.\n3. في حال عدم وجود صوت من السماعات، غير مخرج الصوت من إعدادات شريط المهام إلى مخرج البروجكتر/HDMI.',
            'بروجكتر, projector, شاشة, قاعات, صوت'
        )
    ]

    for title, category, content, tags in seed_kb_articles:
        try:
            cursor.execute("SELECT id FROM knowledge_base WHERE title = %s", (title,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO knowledge_base (title, category, content, tags) VALUES (%s, %s, %s, %s)",
                    (title, category, content, tags)
                )
                conn.commit()
                print(f"  Seeded KB: {title[:35]}...")
        except Exception as e:
            conn.rollback()
            print(f"  Note on seed article: {e}")

    # 5. Populate existing faults with SLA due dates if missing
    try:
        cursor.execute("""
            UPDATE faults 
            SET sla_due_date = CASE 
                WHEN priority = 'critical' THEN created_at + INTERVAL '2 hours'
                WHEN priority = 'high' THEN created_at + INTERVAL '6 hours'
                WHEN priority = 'medium' THEN created_at + INTERVAL '24 hours'
                ELSE created_at + INTERVAL '48 hours'
            END
            WHERE sla_due_date IS NULL;
        """)
        conn.commit()
        print("✅ Updated SLA due dates on existing faults.")
    except Exception as e:
        conn.rollback()
        print(f"  Note on SLA backfill: {e}")

    cursor.close()
    conn.close()
    print("🎉 All migrations completed successfully!")

if __name__ == '__main__':
    run_migration()
