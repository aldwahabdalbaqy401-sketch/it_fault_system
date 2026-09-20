import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='it_fault_db'
    )
    print("✅ اتصال ناجح")
    conn.close()
except Exception as e:
    print(f"❌ فشل الاتصال: {e}")