from flask import Flask
from flask_mail import Mail, Message
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

mail = Mail(app)

with app.app_context():
    try:
        msg = Message(
            subject='📧 اختبار الإشعارات',
            sender=Config.MAIL_USERNAME,
            recipients=['aldwahabdalbaqy@gmail.com'],  # بريدك الصحيح
            body='هذه رسالة اختبار من نظام إدارة الأعطال'
        )
        mail.send(msg)
        print("✅ تم إرسال البريد بنجاح!")
    except Exception as e:
        print(f"❌ فشل إرسال البريد: {e}")