import mysql.connector
from mysql.connector import Error
from pathlib import Path

# إعدادات الاتصال
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': ''
}

# قراءة ملف SQL وتنفيذه
def run_sql_file(file_path):
    try:
        # الاتصال بـ MySQL بدون تحديد قاعدة
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # قراءة محتوى الملف
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # تقسيم الأوامر
        sql_commands = sql_script.split(';')
        
        for command in sql_commands:
            command = command.strip()
            if command:
                try:
                    cursor.execute(command)
                    if command.upper().startswith('SELECT'):
                        results = cursor.fetchall()
                        for row in results:
                            print(row)
                except Error as e:
                    print(f"⚠️ خطأ في الأمر: {command[:50]}...")
                    print(f"🔴 {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ تم إنشاء قاعدة البيانات والجداول بنجاح!")
        
    except Error as e:
        print(f"❌ خطأ في الاتصال: {e}")

if __name__ == '__main__':
    project_root = Path(__file__).resolve().parents[1]
    run_sql_file(project_root / 'database' / 'it_fault_db.sql')