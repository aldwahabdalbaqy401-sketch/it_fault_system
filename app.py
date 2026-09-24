from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, send_from_directory, jsonify
from flask_mail import Mail, Message
import psycopg2
import psycopg2.extras
from config import Config
from flask_bcrypt import Bcrypt
from auth import login_required, role_required
from activity_logger import log_activity
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime, timedelta
import os
import time
import secrets
import random
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from flask_wtf import CSRFProtect
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill

app = Flask(__name__)
app.config.from_object(Config)

csrf = CSRFProtect(app)

bcrypt = Bcrypt(app)
mail = Mail(app)

# ===== تخزين الرموز مؤقتاً (في الذاكرة) =====
reset_codes = {}  # {email: {'code': '123456', 'expiry': datetime, 'user_id': id}}

# ===== إعدادات رفع الملفات =====
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'attachments')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ===== إنشاء مجلد الرفع بأمان =====
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
except FileExistsError:
    pass
except Exception as e:
    print(f"⚠️ خطأ في إنشاء مجلد الرفع: {e}")

# ========== إضافة اسم المشروع ==========
def translate_text(arabic_text, english_text=None):
    language = session.get('language', 'ar')
    if language == 'en':
        return english_text if english_text is not None else arabic_text
    return arabic_text

def localize_data(value):
    if value is None or session.get('language', 'ar') != 'en':
        return value
    translations = {
        'أجهزة': 'Hardware', 'برمجيات': 'Software', 'شبكات': 'Network',
        'قواعد بيانات': 'Database', 'إنترنت': 'Internet', 'أمني': 'Security', 'أخرى': 'Other',
        'كلية الطب': 'College of Medicine', 'كلية الهندسة': 'College of Engineering',
        'كلية العلوم': 'College of Science', 'كلية الآداب': 'College of Arts',
        'كلية الاقتصاد': 'College of Economics', 'كلية الحقوق': 'College of Law',
        'كلية التربية': 'College of Education', 'كلية الزراعة': 'College of Agriculture',
        'كلية الطب البيطري': 'College of Veterinary Medicine', 'كلية الصيدلة': 'College of Pharmacy',
        'كلية التمريض': 'College of Nursing', 'كلية علوم الحاسوب': 'College of Computer Science',
        'كلية الإعلام': 'College of Media', 'كلية الفنون': 'College of Arts and Design',
        'كلية التعليم الصناعي': 'College of Industrial Education', 'كلية الدراسات العليا': 'Graduate Studies',
        'عمادة القبول والتسجيل': 'Admissions and Registration', 'عمادة شؤون الطلاب': 'Student Affairs',
        'الإدارة العامة': 'General Administration', 'شبكة': 'Network', 'كيبل': 'Cable',
        'طابعة': 'Printer', 'حاسوب': 'Computer', 'إنترنت': 'Internet', 'اتصال': 'Connection',
        'غير محدد': 'Not specified', '-': '-'
    }
    return translations.get(value, value)

@app.context_processor
def inject_app_name():
    language = session.get('language', 'ar')
    is_english = language == 'en'
    return {
        'APP_NAME': getattr(Config, 'APP_NAME_EN', 'Technical Fault Management System') if is_english else getattr(Config, 'APP_NAME', 'نظام إدارة وتتبع الأعطال التقنية'),
        'APP_FULL_TITLE': getattr(Config, 'APP_FULL_TITLE_EN', 'Technical Fault Management System') if is_english else getattr(Config, 'APP_FULL_TITLE', 'نظام إدارة وتتبع الأعطال التقنية'),
        'APP_NAME_AR': Config.APP_NAME,
        'APP_NAME_EN': Config.APP_NAME_EN,
        'current_language': language,
        'is_english': is_english,
        'page_direction': 'ltr' if is_english else 'rtl',
        'page_lang': 'en' if is_english else 'ar',
        'translate': translate_text,
        'localize_data': localize_data
    }

@app.after_request
def add_cache_control_headers(response):
    if response.mimetype == 'text/html':
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

@app.route('/set-language/<language>')
def set_language(language):
    if language not in {'ar', 'en'}:
        language = 'ar'
    session['language'] = language
    referrer = request.referrer
    if referrer:
        parsed_referrer = urlparse(referrer)
        if parsed_referrer.netloc and parsed_referrer.netloc != request.host:
            referrer = None
    return redirect(referrer or url_for('login'))

# ========== مسارات PWA وتطبيق الويب التقدمي ==========
@app.route('/manifest.json')
def pwa_manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')

@app.route('/service-worker.js')
def pwa_service_worker():
    response = send_from_directory('static', 'service-worker.js', mimetype='application/javascript')
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/offline')
def pwa_offline():
    return render_template('offline.html')

# ========== دالة الاتصال بقاعدة البيانات ==========
last_db_error = ""

def get_db_connection():
    global last_db_error
    try:
        db_url = Config.DATABASE_URL
        if not db_url:
            db_url = Config.DEFAULT_DB_URL
        db_url = db_url.strip().replace('\r', '').replace('\n', '').strip("'").strip('"')
        conn = psycopg2.connect(db_url, sslmode='require', cursor_factory=psycopg2.extras.RealDictCursor)
        last_db_error = ""
        return conn
    except Exception as e:
        last_db_error = str(e)
        print(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
        # محاولة أخيرة بالرابط الافتراضي النظيف إذا كان مختلفاً
        try:
            if db_url != Config.DEFAULT_DB_URL:
                conn = psycopg2.connect(Config.DEFAULT_DB_URL, sslmode='require', cursor_factory=psycopg2.extras.RealDictCursor)
                last_db_error = ""
                return conn
        except Exception:
            pass
        return None

def get_cursor(conn):
    """إرجاع cursor يُرجع نتائج كـ dict"""
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# ========== دالة إرسال الإشعار الداخلي ==========
def send_notification(title, description):
    try:
        sender = app.config.get('MAIL_DEFAULT_SENDER') or 'noreply@whitenile.edu.sd'
        msg = Message(
            subject=f'🔔 عطل جديد: {title}',
            sender=sender,
            recipients=['admin@example.com'],
            body=f'تم إضافة عطل جديد:\n\nالعنوان: {title}\nالوصف: {description}'
        )
        mail.send(msg)
    except Exception as e:
        print(f"Notification send info: {e}")

# ========== دالة إرسال الإشعار الإلكتروني ==========
def send_email_notification(recipient, subject, body):
    if not recipient:
        return
    try:
        sender = app.config.get('MAIL_DEFAULT_SENDER') or 'noreply@whitenile.edu.sd'
        msg = Message(
            subject=subject,
            sender=sender,
            recipients=[recipient],
            body=body
        )
        mail.send(msg)
    except Exception as e:
        print(f"Email send info: {e}")

# ========== دوال مساعدة لجلب البريد الإلكتروني ==========
def get_user_email(user_id):
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    cursor.execute('SELECT email FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user['email'] if user else None

def get_user_email_by_fault(fault_id):
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    cursor.execute('SELECT u.email FROM faults f JOIN users u ON f.user_id = u.id WHERE f.id = %s', (fault_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user['email'] if user else None

def get_admin_emails():
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM users WHERE role = 'admin'")
    admins = cursor.fetchall()
    cursor.close()
    conn.close()
    return [admin['email'] for admin in admins if admin['email']]

# ========== دوال الإشعارات الداخلية ==========

def add_notification(user_id, fault_id, message):
    """إضافة إشعار جديد للمستخدم"""
    try:
        conn = get_db_connection()
        if not conn:
            return
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO notifications (user_id, fault_id, message) VALUES (%s, %s, %s)",
            (user_id, fault_id, message)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ خطأ في إضافة الإشعار: {e}")

def notify_new_fault(fault_id, title, user_id):
    """إرسال إشعارات عند إضافة عطل جديد"""
    # للمستخدم صاحب البلاغ
    add_notification(user_id, fault_id, f"📌 تم إضافة عطل جديد: {title}")
    
    # للمديرين
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE role = 'admin'")
        admins = cursor.fetchall()
        cursor.close()
        conn.close()
        
        for admin in admins:
            add_notification(admin['id'], fault_id, f"📌 عطل جديد من المستخدم: {title}")

def notify_status_change(fault_id, new_status, user_id):
    """إرسال إشعار عند تغيير حالة العطل"""
    add_notification(user_id, fault_id, f"📊 تم تحديث حالة البلاغ إلى: {new_status}")

# ========== الصفحات ==========

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/admin/add_user', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_add_user():
    return register()

@app.route('/register', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])  # ← فقط الأدمن يقدر يدخل
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        department = request.form.get('department')
        user_type = request.form.get('user_type')
        role = request.form.get('role', 'user')  # ← الصلاحية
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # ===== التحقق من البيانات =====
        if not all([full_name, username, email, phone, department, user_type, password, confirm_password]):
            flash('جميع الحقول مطلوبة', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('كلمة المرور غير متطابقة', 'danger')
            return render_template('register.html')

        if '@' not in email or '.' not in email:
            flash('البريد الإلكتروني غير صحيح', 'danger')
            return render_template('register.html')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = get_db_connection()
        if not conn:
            flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
            return render_template('register.html')

        cursor = conn.cursor()
        try:
            cursor.execute(
                '''INSERT INTO users 
                (username, password, full_name, email, phone, department, user_type, role) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                (username, hashed_password, full_name, email, phone, department, user_type, role)
            )
            conn.commit()
            log_activity('إنشاء حساب', f'المستخدم: {username} بواسطة {session["username"]}')
            flash('✅ تم إنشاء الحساب بنجاح', 'success')
            return redirect(url_for('admin_users'))
        except psycopg2.errors.UniqueViolation as e:
            conn.rollback()
            if 'username' in str(e):
                flash('اسم المستخدم موجود بالفعل', 'danger')
            elif 'email' in str(e):
                flash('البريد الإلكتروني موجود بالفعل', 'danger')
            else:
                flash('حدث خطأ في قاعدة البيانات', 'danger')
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('يرجى ملء جميع الحقول', 'danger')
            return render_template('login.html')

        conn = get_db_connection()
        if not conn:
            flash(f'مشكلة في الاتصال بقاعدة البيانات: {last_db_error}', 'danger')
            return render_template('login.html')

        cursor = conn.cursor()
        cursor.execute(
            '''SELECT * FROM users 
               WHERE LOWER(TRIM(username)) = LOWER(%s) 
                  OR (email IS NOT NULL AND LOWER(TRIM(email)) = LOWER(%s))''',
            (username, username)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            # التحقق الآمن من كلمة المرور
            password_matches = False
            user_pwd = user.get('password') or ''
            try:
                if bcrypt.check_password_hash(user_pwd, password):
                    password_matches = True
            except Exception:
                try:
                    import bcrypt as pybcrypt
                    if pybcrypt.checkpw(password.encode('utf-8'), user_pwd.encode('utf-8')):
                        password_matches = True
                except Exception:
                    pass

            if password_matches:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['user_role'] = user['role']
                session['full_name'] = user['full_name']
                session['email'] = user.get('email', '')
                session['phone'] = user.get('phone', '')
                session['department'] = user.get('department', '')
                session['user_type'] = user.get('user_type', '')
                log_activity('تسجيل دخول', f'المستخدم: {username}')
                flash(f'مرحباً {user["full_name"]}', 'success')

                # ===== توجيه حسب الصلاحية =====
                if user['role'] == 'admin':
                    return redirect(url_for('dashboard'))
                elif user['role'] == 'technician':
                    return redirect(url_for('technician_support'))
                elif user['role'] == 'supervisor':
                    return redirect(url_for('dashboard'))
                else:
                    return redirect(url_for('user_dashboard'))
            else:
                flash('كلمة المرور خطأ', 'danger')
        else:
            flash('اسم المستخدم غير موجود', 'danger')

        return render_template('login.html')

    return render_template('login.html')

# ===== دالة لإنشاء الأدمن لأول مرة (مؤقتة) =====
@app.route('/create_admin')
def create_admin():
    conn = get_db_connection()
    if not conn:
        return "Database connection failed"
    cursor = conn.cursor()
    hashed_password = bcrypt.generate_password_hash('123456').decode('utf-8')
    try:
        cursor.execute(
            '''INSERT INTO users (username, password, full_name, email, role, user_type) 
               VALUES (%s, %s, %s, %s, %s, %s)''',
            ('admin', hashed_password, 'مدير النظام', 'admin@example.com', 'admin', 'staff')
        )
        conn.commit()
        return "تم إنشاء الحساب بنجاح! اسم المستخدم: admin | كلمة المرور: 123456"
    except Exception as e:
        return f"Error: {e}"
    finally:
        cursor.close()
        conn.close()

# ===== نسيت كلمة المرور (نظام رمز التحقق) =====

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')

        if not email:
            flash('يرجى إدخال البريد الإلكتروني', 'danger')
            return render_template('forgot_password.html')

        conn = get_db_connection()
        if not conn:
            flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
            return render_template('forgot_password.html')

        cursor = conn.cursor()

        try:
            cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
            user = cursor.fetchone()
            
            # ===== استهلاك أي نتائج متبقية =====
            try:
                cursor.fetchall()
            except:
                pass
                
        except Exception as e:
            print(f"❌ خطأ في الاستعلام: {e}")
            cursor.close()
            conn.close()
            flash('حدث خطأ في قاعدة البيانات', 'danger')
            return render_template('forgot_password.html')

        cursor.close()

        if not user:
            conn.close()
            flash('البريد الإلكتروني غير مسجل', 'danger')
            return render_template('forgot_password.html')

        # ===== إنشاء رمز تحقق عشوائي (6 أرقام) =====
        code = str(random.randint(100000, 999999))
        expiry = datetime.now() + timedelta(minutes=10)

        # ===== تخزين الرمز مع user_id =====
        reset_codes[email] = {
            'code': code,
            'expiry': expiry,
            'user_id': user['id']  # ← نخزن user_id مع الرمز
        }

        body = f"""مرحباً,

لقد طلبت إعادة تعيين كلمة المرور الخاصة بك.

🔑 رمز التحقق الخاص بك هو: **{code}**

هذا الرمز صالح لمدة 10 دقائق.

إذا لم تطلب هذا، يرجى تجاهل هذه الرسالة.

تحياتنا,
{Config.APP_NAME}
"""

        send_email_notification(
            recipient=email,
            subject='🔑 رمز إعادة تعيين كلمة المرور',
            body=body
        )

        flash('✅ تم إرسال رمز التحقق إلى بريدك الإلكتروني', 'success')
        conn.close()
        return render_template('verify_code.html', email=email)

    return render_template('forgot_password.html')


@app.route('/verify_code', methods=['POST'])
def verify_code():
    email = request.form.get('email')
    code = request.form.get('code')

    if not email or not code:
        flash('يرجى إدخال الرمز', 'danger')
        return render_template('verify_code.html', email=email)

    # التحقق من الرمز
    if email not in reset_codes:
        flash('الرمز غير صحيح أو منتهي الصلاحية', 'danger')
        return render_template('verify_code.html', email=email)

    stored = reset_codes[email]
    if stored['code'] != code:
        flash('الرمز غير صحيح', 'danger')
        return render_template('verify_code.html', email=email)

    if datetime.now() > stored['expiry']:
        del reset_codes[email]
        flash('الرمز منتهي الصلاحية', 'danger')
        return render_template('verify_code.html', email=email)

    # ===== الرمز صحيح → نمرر user_id مع الإيميل =====
    return render_template('reset_password.html', email=email, user_id=stored['user_id'])


@app.route('/reset_password', methods=['POST'])
def reset_password():
    email = request.form.get('email')
    user_id = request.form.get('user_id')  # ← نجيب user_id من الفورم
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    stored = reset_codes.get(email)
    if not email or not user_id or not password or not confirm_password:
        flash('جميع الحقول مطلوبة', 'danger')
        return render_template('reset_password.html', email=email, user_id=user_id)

    if not stored or str(stored['user_id']) != str(user_id):
        flash('جلسة إعادة التعيين غير صالحة، اطلب رمزًا جديدًا', 'danger')
        return redirect(url_for('forgot_password'))

    if password != confirm_password:
        flash('كلمة المرور غير متطابقة', 'danger')
        return render_template('reset_password.html', email=email, user_id=user_id)

    if len(password) < 6:
        flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل', 'danger')
        return render_template('reset_password.html', email=email, user_id=user_id)

    conn = get_db_connection()
    if not conn:
        flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
        return render_template('reset_password.html', email=email, user_id=user_id)

    cursor = conn.cursor()
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    cursor.execute(
        'UPDATE users SET password = %s WHERE id = %s AND email = %s',
        (hashed_password, user_id, email)
    )
    updated = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()

    if updated != 1:
        flash('تعذر تحديث كلمة المرور، تحقق من بيانات الحساب واطلب رمزًا جديدًا', 'danger')
        return render_template('reset_password.html', email=email, user_id=user_id)

    # حذف الرمز بعد الاستخدام
    if email in reset_codes:
        del reset_codes[email]

    flash('✅ تم تحديث كلمة المرور بنجاح، يمكنك تسجيل الدخول الآن', 'success')
    return redirect(url_for('login'))

@app.route('/user_dashboard')
@login_required
def user_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM faults WHERE user_id = %s", (session['user_id'],))
    total_faults = cursor.fetchone()['total'] or 0

    cursor.execute("SELECT COUNT(*) as resolved FROM faults WHERE user_id = %s AND status IN ('resolved', 'closed')", (session['user_id'],))
    resolved_faults = cursor.fetchone()['resolved'] or 0

    cursor.execute("SELECT COUNT(*) as pending FROM faults WHERE user_id = %s AND status IN ('new', 'in_progress')", (session['user_id'],))
    pending_faults = cursor.fetchone()['pending'] or 0

    resolved_percent = round((resolved_faults / total_faults) * 100, 1) if total_faults else 0
    pending_percent = round((pending_faults / total_faults) * 100, 1) if total_faults else 0

    cursor.execute("""
        SELECT n.id, n.fault_id, n.message, n.is_read, n.created_at, f.title as fault_title 
        FROM notifications n
        LEFT JOIN faults f ON n.fault_id = f.id
        WHERE n.user_id = %s 
        ORDER BY n.created_at DESC LIMIT 5
    """, (session['user_id'],))
    recent_notifications = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'user_dashboard.html',
        total_faults=total_faults,
        resolved_faults=resolved_faults,
        pending_faults=pending_faults,
        resolved_percent=resolved_percent,
        pending_percent=pending_percent,
        recent_notifications=recent_notifications
    )

@app.route('/api/user/dashboard-stats')
@login_required
def user_dashboard_stats():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False}), 503

    cursor = conn.cursor()
    user_id = session['user_id']
    cursor.execute("SELECT COUNT(*) as total FROM faults WHERE user_id = %s", (user_id,))
    total_faults = cursor.fetchone()['total'] or 0
    cursor.execute("SELECT COUNT(*) as resolved FROM faults WHERE user_id = %s AND status IN ('resolved', 'closed')", (user_id,))
    resolved_faults = cursor.fetchone()['resolved'] or 0
    cursor.execute("SELECT COUNT(*) as pending FROM faults WHERE user_id = %s AND status IN ('new', 'in_progress')", (user_id,))
    pending_faults = cursor.fetchone()['pending'] or 0
    cursor.close()
    conn.close()

    return jsonify({
        'success': True,
        'total_faults': total_faults,
        'resolved_faults': resolved_faults,
        'pending_faults': pending_faults,
        'resolved_percent': round((resolved_faults / total_faults) * 100, 1) if total_faults else 0,
        'pending_percent': round((pending_faults / total_faults) * 100, 1) if total_faults else 0
    })

@app.route('/dashboard')
@login_required
@role_required(['admin', 'supervisor', 'technician'])
def dashboard():
    conn = get_db_connection()
    if not conn:
        flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
        return render_template('dashboard.html')

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM faults")
    total_faults = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as pending FROM faults WHERE status = 'new' OR status = 'in_progress'")
    pending_faults = cursor.fetchone()['pending']

    cursor.execute("SELECT COUNT(*) as resolved FROM faults WHERE status = 'resolved' OR status = 'closed'")
    resolved_faults = cursor.fetchone()['resolved']

    cursor.execute("SELECT COUNT(*) as critical FROM faults WHERE priority = 'critical'")
    critical_faults = cursor.fetchone()['critical']

    # ===== جلب المواعيد القريبة (خلال 3 أيام) =====
    cursor.execute("""
        SELECT id, title, scheduled_date, 
               EXTRACT(DAY FROM (scheduled_date - NOW())) as days_until
        FROM faults 
        WHERE scheduled_date IS NOT NULL 
          AND scheduled_date BETWEEN NOW() AND NOW() + INTERVAL '3 days'
          AND status NOT IN ('resolved', 'closed')
        ORDER BY scheduled_date ASC
    """)
    upcoming_appointments = cursor.fetchall()
    # ===== جلب آخر الإشعارات للمستخدم =====
    cursor.execute("""
        SELECT n.id, n.fault_id, n.message, n.is_read, n.created_at, f.title as fault_title 
        FROM notifications n
        LEFT JOIN faults f ON n.fault_id = f.id
        WHERE n.user_id = %s 
        ORDER BY n.created_at DESC LIMIT 6
    """, (session['user_id'],))
    recent_notifications = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'dashboard.html',
        total_faults=total_faults,
        pending_faults=pending_faults,
        resolved_faults=resolved_faults,
        critical_faults=critical_faults,
        upcoming_appointments=upcoming_appointments,
        recent_notifications=recent_notifications
    )

@app.route('/add_fault', methods=['GET', 'POST'])
@login_required
def add_fault():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        fault_type = request.form['fault_type']
        location = request.form['location']
        priority = request.form['priority']
        status = request.form['status']
        if session.get('user_role') == 'user':
            status = 'new'
        scheduled_date = request.form.get('scheduled_date')  # ===== حقل الموعد =====

        file = request.files.get('attachment')
        filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            # ===== حساب مهلة اتفاقية مستوى الخدمة (SLA Due Date) تلقائياً =====
            now = datetime.now()
            if priority == 'critical':
                sla_due_date = now + timedelta(hours=2)
            elif priority == 'high':
                sla_due_date = now + timedelta(hours=6)
            elif priority == 'medium':
                sla_due_date = now + timedelta(hours=24)
            else:
                sla_due_date = now + timedelta(hours=48)

            # ===== إضافة الموعد إذا كان موجوداً =====
            if scheduled_date:
                cursor.execute(
                    '''INSERT INTO faults 
                    (title, description, fault_type, location, priority, status, attachment, user_id, scheduled_date, sla_due_date) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id''',
                    (title, description, fault_type, location, priority, status, filename, session['user_id'], scheduled_date, sla_due_date)
                )
            else:
                cursor.execute(
                    '''INSERT INTO faults 
                    (title, description, fault_type, location, priority, status, attachment, user_id, sla_due_date) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id''',
                    (title, description, fault_type, location, priority, status, filename, session['user_id'], sla_due_date)
                )
            
            inserted_row = cursor.fetchone()
            fault_id = inserted_row['id'] if inserted_row and 'id' in inserted_row else cursor.lastrowid
            conn.commit()
            
            # ===== إضافة إشعارات =====
            notify_new_fault(fault_id, title, session['user_id'])
            
            cursor.close()
            conn.close()
            log_activity('إضافة عطل', f'العنوان: {title}')
            
            admin_emails = get_admin_emails()
            for admin_email in admin_emails:
                send_email_notification(
                    recipient=admin_email,
                    subject=f'🔔 عطل جديد: {title}',
                    body=f'تم إضافة عطل جديد:\n\nالعنوان: {title}\nالوصف: {description}'
                )
            
            flash('تم إضافة العطل بنجاح', 'success')
            if session.get('user_role') == 'user':
                return redirect(url_for('my_faults'))
            return redirect(url_for('view_faults'))
        else:
            flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
            return render_template('add_fault.html')

    return render_template('add_fault.html')

@app.route('/view_faults')
@login_required
@role_required(['admin', 'supervisor', 'technician'])
def view_faults():
    conn = get_db_connection()
    faults = []
    total_pages = 0
    current_page = 1
    per_page = 10
    
    # جلب رقم الصفحة
    try:
        current_page = int(request.args.get('page', 1))
        if current_page < 1:
            current_page = 1
    except:
        current_page = 1
    
    # ===== جلب معاملات الفلتر =====
    search_title = request.args.get('search_title', '').strip()
    fault_type = request.args.get('fault_type', '').strip()
    priority = request.args.get('priority', '').strip()
    status = request.args.get('status', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    
    if conn:
        cursor = conn.cursor()
        
        # ===== بناء الاستعلام مع الفلاتر =====
        query = "SELECT * FROM faults WHERE 1=1"
        count_query = "SELECT COUNT(*) as total FROM faults WHERE 1=1"
        params = []
        
        # فلتر البحث بالعنوان
        if search_title:
            query += " AND title LIKE %s"
            count_query += " AND title LIKE %s"
            params.append(f"%{search_title}%")
        
        # فلتر النوع
        if fault_type:
            query += " AND fault_type = %s"
            count_query += " AND fault_type = %s"
            params.append(fault_type)
        
        # فلتر الأولوية
        if priority:
            query += " AND priority = %s"
            count_query += " AND priority = %s"
            params.append(priority)
        
        # فلتر الحالة
        if status:
            query += " AND status = %s"
            count_query += " AND status = %s"
            params.append(status)
        
        # فلتر التاريخ (من)
        if date_from:
            query += " AND DATE(created_at) >= %s"
            count_query += " AND DATE(created_at) >= %s"
            params.append(date_from)
        
        # فلتر التاريخ (إلى)
        if date_to:
            query += " AND DATE(created_at) <= %s"
            count_query += " AND DATE(created_at) <= %s"
            params.append(date_to)
        
        # ===== جلب العدد الإجمالي =====
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()['total']
        total_pages = (total_count + per_page - 1) // per_page
        
        # ===== حساب الإزاحة =====
        offset = (current_page - 1) * per_page
        query += " ORDER BY id ASC, created_at ASC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        faults = cursor.fetchall()
        cursor.close()
        conn.close()
    
    return render_template(
        'view_faults.html',
        faults=faults,
        current_page=current_page,
        total_pages=total_pages,
        search_title=search_title,
        fault_type=fault_type,
        priority=priority,
        status=status,
        date_from=date_from,
        date_to=date_to
    )

@app.route('/edit_fault/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'supervisor'])
def edit_fault(id):
    conn = get_db_connection()
    if not conn:
        flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
        return redirect(url_for('view_faults'))

    cursor = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        fault_type = request.form['fault_type']
        location = request.form['location']
        priority = request.form['priority']
        status = request.form['status']
        scheduled_date = request.form.get('scheduled_date')

        if scheduled_date:
            cursor.execute(
                '''UPDATE faults SET 
                title=%s, description=%s, fault_type=%s, location=%s, priority=%s, status=%s, scheduled_date=%s 
                WHERE id=%s''',
                (title, description, fault_type, location, priority, status, scheduled_date, id)
            )
        else:
            cursor.execute(
                '''UPDATE faults SET 
                title=%s, description=%s, fault_type=%s, location=%s, priority=%s, status=%s, scheduled_date=NULL 
                WHERE id=%s''',
                (title, description, fault_type, location, priority, status, id)
            )
        conn.commit()
        cursor.close()
        conn.close()
        log_activity('تعديل عطل', f'ID: {id}')
        flash('تم تحديث العطل بنجاح', 'success')
        return redirect(url_for('view_faults'))

    cursor.execute('SELECT * FROM faults WHERE id = %s', (id,))
    fault = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit_fault.html', fault=fault)

@app.route('/delete_fault/<int:id>', methods=['POST'])
@login_required
@role_required(['admin'])
def delete_fault(id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM faults WHERE id = %s', (id,))
        conn.commit()
        cursor.close()
        conn.close()
        log_activity('حذف عطل', f'ID: {id}')
        flash('تم حذف العطل بنجاح', 'success')
    else:
        flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
    return redirect(url_for('view_faults'))

@app.route('/fault_details/<int:id>')
@login_required
def fault_details(id):
    conn = get_db_connection()
    if not conn:
        flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
        return redirect(url_for('view_faults'))

    cursor = conn.cursor()
    cursor.execute('''
        SELECT f.*, 
               u.full_name as user_full_name, u.email as user_email, u.phone as user_phone, u.department as user_dept,
               t.full_name as assigned_technician_name, t.email as assigned_technician_email, t.phone as assigned_technician_phone
        FROM faults f
        LEFT JOIN users u ON f.user_id = u.id
        LEFT JOIN users t ON f.assigned_to = t.id
        WHERE f.id = %s
    ''', (id,))
    fault = cursor.fetchone()

    parts = []
    try:
        cursor.execute('SELECT * FROM fault_parts WHERE fault_id = %s ORDER BY id ASC', (id,))
        parts = cursor.fetchall()
    except Exception:
        pass

    cursor.close()
    conn.close()

    if not fault:
        flash('البلاغ غير موجود', 'danger')
        return redirect(url_for('user_dashboard') if session.get('user_role') == 'user' else url_for('view_faults'))

    if session.get('user_role') == 'user' and fault['user_id'] != session['user_id']:
        flash('غير مصرح لك بالوصول إلى هذا البلاغ', 'danger')
        return redirect(url_for('my_faults'))

    return render_template('fault_details.html', fault=fault, parts=parts, now=datetime.now())

# ==========================================
# ========== مسارات قاعدة المعرفة ==========
# ==========================================

@app.route('/knowledge_base')
def knowledge_base():
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    
    conn = get_db_connection()
    articles = []
    if conn:
        cursor = conn.cursor()
        query_sql = "SELECT * FROM knowledge_base WHERE 1=1"
        params = []
        
        if category:
            query_sql += " AND category = %s"
            params.append(category)
            
        if q:
            query_sql += " AND (title ILIKE %s OR content ILIKE %s OR tags ILIKE %s)"
            search_param = f"%{q}%"
            params.extend([search_param, search_param, search_param])
            
        query_sql += " ORDER BY id DESC"
        cursor.execute(query_sql, tuple(params))
        articles = cursor.fetchall()
        cursor.close()
        conn.close()
        
    return render_template('knowledge_base.html', articles=articles, query=q, active_category=category)

@app.route('/api/knowledge_base/view/<int:id>', methods=['POST'])
def api_kb_view(id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE knowledge_base SET views_count = views_count + 1 WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    return jsonify({'success': False}), 500

@app.route('/api/knowledge_base/helpful/<int:id>', methods=['POST'])
def api_kb_helpful(id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE knowledge_base SET helpful_count = helpful_count + 1 WHERE id = %s RETURNING helpful_count", (id,))
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'helpful_count': row['helpful_count'] if row else 1})
    return jsonify({'success': False}), 500

@app.route('/api/knowledge_base/suggest')
def api_kb_suggest():
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        return jsonify({'suggestions': []})
        
    conn = get_db_connection()
    suggestions = []
    if conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, category, content FROM knowledge_base WHERE title ILIKE %s OR tags ILIKE %s OR content ILIKE %s LIMIT 3",
            (f"%{q}%", f"%{q}%", f"%{q}%")
        )
        suggestions = cursor.fetchall()
        cursor.close()
        conn.close()
        
    return jsonify({'suggestions': suggestions})

@app.route('/admin/knowledge_base/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'supervisor'])
def admin_add_kb():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        content = request.form.get('content', '').strip()
        tags = request.form.get('tags', '').strip()
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO knowledge_base (title, category, content, tags) VALUES (%s, %s, %s, %s)",
                (title, category, content, tags)
            )
            conn.commit()
            cursor.close()
            conn.close()
            log_activity('إضافة مقال معرفي', f'العنوان: {title}')
            flash('تمت إضافة المقال بنجاح إلى قاعدة المعرفة', 'success')
            return redirect(url_for('knowledge_base'))
        else:
            flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
            
    return render_template('admin_kb_form.html', article=None)

@app.route('/admin/knowledge_base/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'supervisor'])
def admin_edit_kb(id):
    conn = get_db_connection()
    if not conn:
        flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
        return redirect(url_for('knowledge_base'))
        
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM knowledge_base WHERE id = %s", (id,))
    article = cursor.fetchone()
    
    if not article:
        cursor.close()
        conn.close()
        flash('المقال غير موجود', 'danger')
        return redirect(url_for('knowledge_base'))
        
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        content = request.form.get('content', '').strip()
        tags = request.form.get('tags', '').strip()
        
        cursor.execute(
            "UPDATE knowledge_base SET title = %s, category = %s, content = %s, tags = %s, updated_at = NOW() WHERE id = %s",
            (title, category, content, tags, id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        log_activity('تعديل مقال معرفي', f'ID: {id}')
        flash('تم تحديث المقال بنجاح', 'success')
        return redirect(url_for('knowledge_base'))
        
    cursor.close()
    conn.close()
    return render_template('admin_kb_form.html', article=article)

@app.route('/admin/knowledge_base/delete/<int:id>', methods=['POST'])
@login_required
@role_required(['admin', 'supervisor'])
def admin_delete_kb(id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM knowledge_base WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        log_activity('حذف مقال معرفي', f'ID: {id}')
        flash('تم حذف المقال بنجاح', 'success')
    else:
        flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
    return redirect(url_for('knowledge_base'))

@app.route('/dashboard_stats')
@login_required
@role_required(['admin', 'supervisor'])
def dashboard_stats():
    conn = get_db_connection()
    if not conn:
        flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
        return redirect(url_for('dashboard'))

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM faults")
    total_faults = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as resolved FROM faults WHERE status = 'resolved' OR status = 'closed'")
    resolved_faults = cursor.fetchone()['resolved']

    cursor.execute("SELECT COUNT(*) as critical FROM faults WHERE priority = 'critical'")
    critical_faults = cursor.fetchone()['critical']

    cursor.execute("SELECT priority, COUNT(*) as count FROM faults GROUP BY priority")
    priority_rows = cursor.fetchall()
    priority_counts = {row['priority']: row['count'] for row in priority_rows}
    priority_definitions = [
        ('critical', 'حرجة'),
        ('high', 'عالية'),
        ('medium', 'متوسطة'),
        ('low', 'منخفضة')
    ]
    priority_stats = [
        {
            'priority': key,
            'label': label,
            'count': priority_counts.get(key, 0),
            'percent': round((priority_counts.get(key, 0) / total_faults * 100), 1) if total_faults else 0
        }
        for key, label in priority_definitions
    ]

    cursor.execute("SELECT status, COUNT(*) as count FROM faults GROUP BY status")
    status_rows = cursor.fetchall()
    status_counts = {row['status']: row['count'] for row in status_rows}
    status_definitions = [
        ('new', 'جديد'),
        ('in_progress', 'قيد المعالجة'),
        ('resolved', 'تم الحل'),
        ('closed', 'مغلق')
    ]
    status_stats = [
        {
            'status': key,
            'label': label,
            'count': status_counts.get(key, 0),
            'percent': round((status_counts.get(key, 0) / total_faults * 100), 1) if total_faults else 0
        }
        for key, label in status_definitions
    ]

    cursor.execute("""
        SELECT DATE(created_at) as date, COUNT(*) as count 
        FROM faults 
        WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY DATE(created_at)
        ORDER BY date ASC
    """)
    weekly_stats = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'dashboard_stats.html',
        total_faults=total_faults,
        resolved_faults=resolved_faults,
        critical_faults=critical_faults,
        priority_stats=priority_stats,
        status_stats=status_stats,
        weekly_stats=weekly_stats
    )

@app.route('/logout')
def logout():
    username = session.get('username', 'مستخدم')
    log_activity('تسجيل خروج', f'المستخدم: {username}')
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('login'))

@app.route('/export_pdf')
@login_required
def export_pdf():
    conn = get_db_connection()
    if not conn:
        flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
        return redirect(url_for('view_faults'))

    cursor = conn.cursor()
    cursor.execute('SELECT id, title, fault_type, location, priority, status, created_at FROM faults ORDER BY id ASC, created_at ASC')
    faults = cursor.fetchall()
    cursor.close()
    conn.close()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18,
                                  textColor=colors.HexColor('#1a1a3e'), alignment=1, spaceAfter=20)
    elements.append(Paragraph("📋 تقرير الأعطال التقنية", title_style))
    elements.append(Spacer(1, 0.2 * inch))

    date_style = ParagraphStyle('DateStyle', parent=styles['Normal'], fontSize=12,
                                textColor=colors.grey, alignment=2)
    elements.append(Paragraph(f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}", date_style))
    elements.append(Spacer(1, 0.3 * inch))

    data = [['#', 'العنوان', 'النوع', 'المكان', 'الأولوية', 'الحالة', 'التاريخ']]
    for fault in faults:
        data.append([
            str(fault['id']),
            fault['title'],
            fault['fault_type'] or 'غير محدد',
            fault['location'] or 'غير محدد',
            fault['priority'],
            fault['status'],
            fault['created_at'].strftime('%Y-%m-%d') if fault['created_at'] else ''
        ])

    table = Table(data, colWidths=[0.5 * inch, 2.5 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a3e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    elements.append(table)

    elements.append(Spacer(1, 0.5 * inch))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=10,
                                  textColor=colors.grey, alignment=1)
    elements.append(Paragraph(f"{Config.APP_NAME} - جميع الحقوق محفوظة © 2026", footer_style))

    doc.build(elements)
    buffer.seek(0)

    log_activity('تصدير تقرير PDF', f'عدد الأعطال: {len(faults)}')
    return send_file(buffer, as_attachment=True, download_name='faults_report.pdf', mimetype='application/pdf')

# ========== تصدير تقرير Excel ==========
@app.route('/export_excel')
@login_required
def export_excel():
    conn = get_db_connection()
    if not conn:
        flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
        return redirect(url_for('view_faults'))

    cursor = conn.cursor()
    cursor.execute('SELECT id, title, fault_type, location, priority, status, created_at FROM faults ORDER BY id ASC, created_at ASC')
    faults = cursor.fetchall()
    cursor.close()
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "الأعطال"

    headers = ['#', 'العنوان', 'النوع', 'المكان', 'الأولوية', 'الحالة', 'التاريخ']
    ws.append(headers)

    for col in range(1, 8):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="1a1a3e", end_color="1a1a3e", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")

    for fault in faults:
        ws.append([
            fault['id'],
            fault['title'],
            fault['fault_type'] or 'غير محدد',
            fault['location'] or 'غير محدد',
            fault['priority'],
            fault['status'],
            fault['created_at'].strftime('%Y-%m-%d %H:%M') if fault['created_at'] else ''
        ])

    for col in range(1, 8):
        ws.column_dimensions[chr(64 + col)].width = 18

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    log_activity('تصدير تقرير Excel', f'عدد الأعطال: {len(faults)}')
    return send_file(output, as_attachment=True, download_name='faults_report.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# ========== دعم الفنيين ==========
@app.route('/technician_support')
@login_required
@role_required(['technician', 'admin', 'supervisor'])
def technician_support():
    conn = get_db_connection()
    if not conn:
        flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
        return redirect(url_for('dashboard'))
    
    cursor = conn.cursor()
    
    # Filter by technician if admin/supervisor selected one
    tech_filter = request.args.get('tech_id')
    status_filter = request.args.get('status')
    
    query_conditions = []
    query_params = []
    
    if session['user_role'] in ['admin', 'supervisor']:
        if tech_filter and tech_filter.isdigit():
            query_conditions.append('f.assigned_to = %s')
            query_params.append(int(tech_filter))
        else:
            query_conditions.append('f.assigned_to IS NOT NULL')
    else:
        query_conditions.append('f.assigned_to = %s')
        query_params.append(session['user_id'])
        
    if status_filter and status_filter in ['new', 'in_progress', 'resolved', 'closed']:
        query_conditions.append('f.status = %s')
        query_params.append(status_filter)
        
    where_clause = " WHERE " + " AND ".join(query_conditions) if query_conditions else ""
    
    cursor.execute(
        f'''SELECT f.*, u.full_name as technician_name, u.username as technician_username,
                  reporter.full_name as reporter_name, reporter.phone as reporter_phone
        FROM faults f
        LEFT JOIN users u ON f.assigned_to = u.id
        LEFT JOIN users reporter ON f.user_id = reporter.id
        {where_clause}
        ORDER BY f.id DESC''',
        tuple(query_params)
    )
    assigned_faults = cursor.fetchall()
    
    # Calculate stats according to view perspective (individual technician or admin view)
    if session['user_role'] in ['admin', 'supervisor'] and not tech_filter:
        cursor.execute('SELECT COUNT(*) as total FROM faults WHERE assigned_to IS NOT NULL')
        total_assigned = cursor.fetchone()['total'] or 0
        
        cursor.execute("SELECT COUNT(*) as pending FROM faults WHERE assigned_to IS NOT NULL AND status IN ('new', 'in_progress')")
        pending_assigned = cursor.fetchone()['pending'] or 0
        
        cursor.execute("SELECT COUNT(*) as resolved FROM faults WHERE assigned_to IS NOT NULL AND status = 'resolved'")
        resolved_assigned = cursor.fetchone()['resolved'] or 0
    else:
        target_tech_id = int(tech_filter) if (session['user_role'] in ['admin', 'supervisor'] and tech_filter and tech_filter.isdigit()) else session['user_id']
        cursor.execute('SELECT COUNT(*) as total FROM faults WHERE assigned_to = %s', (target_tech_id,))
        total_assigned = cursor.fetchone()['total'] or 0
        
        cursor.execute("SELECT COUNT(*) as pending FROM faults WHERE assigned_to = %s AND status IN ('new', 'in_progress')", (target_tech_id,))
        pending_assigned = cursor.fetchone()['pending'] or 0
        
        cursor.execute("SELECT COUNT(*) as resolved FROM faults WHERE assigned_to = %s AND status = 'resolved'", (target_tech_id,))
        resolved_assigned = cursor.fetchone()['resolved'] or 0

    # Technicians list for admin filter dropdown
    technicians_list = []
    if session['user_role'] in ['admin', 'supervisor']:
        cursor.execute("SELECT id, username, full_name FROM users WHERE role = 'technician' ORDER BY full_name ASC")
        technicians_list = cursor.fetchall()

    cursor.close()
    conn.close()
    
    return render_template(
        'technician_support.html',
        assigned_faults=assigned_faults,
        total_assigned=total_assigned,
        pending_assigned=pending_assigned,
        resolved_assigned=resolved_assigned,
        technicians_list=technicians_list,
        selected_tech=tech_filter or '',
        selected_status=status_filter or ''
    )

# ========== إسناد البلاغ ==========
@app.route('/assign_fault/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'supervisor'])
def assign_fault(id):
    conn = get_db_connection()
    if not conn:
        flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
        return redirect(url_for('view_faults'))
    
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT f.*, u.full_name as assigned_name, reporter.full_name as reporter_name
        FROM faults f
        LEFT JOIN users u ON f.assigned_to = u.id
        LEFT JOIN users reporter ON f.user_id = reporter.id
        WHERE f.id = %s
    ''', (id,))
    fault = cursor.fetchone()
    
    if not fault:
        flash('البلاغ غير موجود', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('view_faults'))
    
    # Query all technicians with their current active fault load
    cursor.execute("""
        SELECT u.id, u.username, u.full_name, u.email, u.phone, u.department,
               COUNT(CASE WHEN f.status IN ('new', 'in_progress') THEN 1 END) as active_faults_count
        FROM users u
        LEFT JOIN faults f ON u.id = f.assigned_to
        WHERE u.role = 'technician'
        GROUP BY u.id, u.username, u.full_name, u.email, u.phone, u.department
        ORDER BY active_faults_count ASC, u.full_name ASC
    """)
    technicians = cursor.fetchall()
    
    if request.method == 'POST':
        assigned_to = request.form.get('assigned_to')
        assign_note = request.form.get('assign_note', '').strip()
        
        if assigned_to == 'unassign':
            cursor.execute(
                'UPDATE faults SET assigned_to = NULL WHERE id = %s',
                (id,)
            )
            conn.commit()
            log_activity('إلغاء إسناد بلاغ', f'ID: {id}')
            flash('ℹ️ تم إلغاء إسناد البلاغ بنجاح', 'info')
        elif assigned_to and assigned_to.isdigit():
            assigned_to = int(assigned_to)
            cursor.execute(
                'UPDATE faults SET assigned_to = %s WHERE id = %s',
                (assigned_to, id)
            )
            conn.commit()
            log_activity('إسناد بلاغ', f'ID: {id} إلى فني ID: {assigned_to}')
            
            # ===== إشعارات عند الإسناد =====
            if fault.get('user_id'):
                add_notification(
                    fault['user_id'],
                    id,
                    f"🔧 تم إسناد بلاغك إلى أحد فنيي الدعم"
                )
            add_notification(
                assigned_to,
                id,
                f"📌 تم إسناد بلاغ جديد إليك: {fault['title']}"
            )
            
            tech_email = get_user_email(assigned_to)
            if tech_email:
                note_text = f"\nملاحظات المشرف: {assign_note}" if assign_note else ""
                send_email_notification(
                    recipient=tech_email,
                    subject=f'🔧 تم إسناد بلاغ إليك - {fault["title"]}',
                    body=f'تم إسناد البلاغ "{fault["title"]}" إليك.\n\nالوصف: {fault["description"]}{note_text}'
                )
            
            flash('✅ تم إسناد البلاغ للفني بنجاح', 'success')
        else:
            flash('الرجاء اختيار فني صالح', 'danger')
            cursor.close()
            conn.close()
            return render_template('assign_fault.html', fault=fault, technicians=technicians)
        
        cursor.close()
        conn.close()
        next_page = request.args.get('next')
        if next_page == 'technician_support':
            return redirect(url_for('technician_support'))
        return redirect(url_for('view_faults'))
    
    cursor.close()
    conn.close()
    
    return render_template('assign_fault.html', fault=fault, technicians=technicians)

# ========== دورة حياة البلاغ ==========

@app.route('/receive_fault/<int:id>', methods=['POST'])
@login_required
@role_required(['technician', 'admin', 'supervisor'])
def receive_fault(id):
    conn = get_db_connection()
    if not conn:
        flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
        return redirect(url_for('technician_support'))
    
    cursor = conn.cursor()
    # If admin/supervisor, they can receive for the assigned technician or auto-assign to themselves if not assigned
    if session['user_role'] in ['admin', 'supervisor']:
        cursor.execute(
            "UPDATE faults SET status = 'in_progress', received_at = NOW() WHERE id = %s",
            (id,)
        )
    else:
        cursor.execute(
            "UPDATE faults SET status = 'in_progress', received_at = NOW() WHERE id = %s AND assigned_to = %s",
            (id, session['user_id'])
        )
    conn.commit()
    cursor.close()
    conn.close()
    
    log_activity('استلام بلاغ', f'ID: {id}')
    flash('✅ تم استلام البلاغ بنجاح، جاري العمل عليه', 'success')
    return redirect(request.referrer or url_for('technician_support'))

@app.route('/start_fault/<int:id>', methods=['POST'])
@login_required
@role_required(['technician', 'admin', 'supervisor'])
def start_fault(id):
    conn = get_db_connection()
    if not conn:
        flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
        return redirect(url_for('technician_support'))
    
    cursor = conn.cursor()
    if session['user_role'] in ['admin', 'supervisor']:
        cursor.execute(
            "UPDATE faults SET status = 'in_progress', started_at = NOW() WHERE id = %s",
            (id,)
        )
    else:
        cursor.execute(
            "UPDATE faults SET status = 'in_progress', started_at = NOW() WHERE id = %s AND assigned_to = %s",
            (id, session['user_id'])
        )
    conn.commit()
    cursor.close()
    conn.close()
    
    log_activity('بدء حل البلاغ', f'ID: {id}')
    flash('⏳ جاري العمل على حل المشكلة...', 'info')
    return redirect(request.referrer or url_for('technician_support'))

@app.route('/resolve_fault/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(['technician', 'admin', 'supervisor'])
def resolve_fault(id):
    conn = get_db_connection()
    if not conn:
        flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
        return redirect(url_for('technician_support'))
    
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM faults WHERE id = %s', (id,))
    fault = cursor.fetchone()
    
    try:
        cursor.fetchall()
    except Exception:
        pass
    cursor.close()
    
    if not fault:
        flash('البلاغ غير موجود', 'danger')
        conn.close()
        return redirect(url_for('technician_support'))
    
    if request.method == 'POST':
        notes = request.form.get('technician_notes', '').strip()
        cursor = conn.cursor()
        
        if session['user_role'] in ['admin', 'supervisor']:
            cursor.execute(
                "UPDATE faults SET status = 'resolved', completed_at = NOW(), technician_notes = %s WHERE id = %s",
                (notes, id)
            )
        else:
            cursor.execute(
                "UPDATE faults SET status = 'resolved', completed_at = NOW(), technician_notes = %s WHERE id = %s AND assigned_to = %s",
                (notes, id, session['user_id'])
            )

        # ===== تسجيل قطع الغيار المستهلكة إن وجدت =====
        part_name = request.form.get('part_name', '').strip()
        if part_name:
            try:
                part_qty = int(request.form.get('part_qty', 1) or 1)
            except Exception:
                part_qty = 1
            try:
                part_cost = float(request.form.get('part_cost', 0) or 0)
            except Exception:
                part_cost = 0.0

            total_cost = round(part_qty * part_cost, 2)
            try:
                cursor.execute(
                    "INSERT INTO fault_parts (fault_id, part_name, quantity, unit_cost, total_cost) VALUES (%s, %s, %s, %s, %s)",
                    (id, part_name, part_qty, part_cost, total_cost)
                )
                cursor.execute(
                    "UPDATE faults SET spare_parts_cost = COALESCE(spare_parts_cost, 0) + %s WHERE id = %s",
                    (total_cost, id)
                )
            except Exception as e:
                print(f"Error saving spare parts: {e}")

        conn.commit()
        
        # ===== إشعار عند حل العطل =====
        user_email = get_user_email_by_fault(id)
        if user_email:
            conn2 = get_db_connection()
            cursor2 = conn2.cursor()
            cursor2.execute("SELECT id FROM users WHERE email = %s", (user_email,))
            user = cursor2.fetchone()
            
            try:
                cursor2.fetchall()
            except Exception:
                pass
            cursor2.close()
            conn2.close()
            
            if user:
                add_notification(
                    user['id'],
                    id,
                    f"✅ تم حل البلاغ: {fault['title']}"
                )
        
        cursor.close()
        conn.close()
        
        log_activity('حل البلاغ', f'ID: {id}')
        flash('✅ تم حل المشكلة بنجاح وتسجيل الملاحظات', 'success')
        return redirect(url_for('technician_support'))
    
    conn.close()
    return render_template('resolve_fault.html', fault=fault)

@app.route('/close_fault/<int:id>', methods=['POST'])
@login_required
@role_required(['admin', 'supervisor'])
def close_fault(id):
    conn = get_db_connection()
    if not conn:
        flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
        return redirect(url_for('view_faults'))
    
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE faults SET status = 'closed' WHERE id = %s",
        (id,)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    log_activity('إغلاق البلاغ', f'ID: {id}')
    flash('🔒 تم إغلاق البلاغ', 'success')
    return redirect(url_for('view_faults'))

@app.route('/update_fault_status', methods=['POST'])
@login_required
@role_required(['technician', 'admin', 'supervisor'])
def update_fault_status():
    fault_id = request.form.get('fault_id')
    new_status = request.form.get('new_status')
    note = request.form.get('note', '')
    
    if not fault_id or not new_status:
        flash('بيانات غير مكتملة', 'danger')
        return redirect(request.referrer or url_for('technician_support'))
    
    conn = get_db_connection()
    if not conn:
        flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
        return redirect(request.referrer or url_for('technician_support'))
    
    cursor = conn.cursor()
    try:
        cursor.execute(
            'UPDATE faults SET status = %s WHERE id = %s',
            (new_status, fault_id)
        )
        conn.commit()
        
        log_activity('تحديث حالة البلاغ', f'ID: {fault_id} -> {new_status}')
        
        # ===== إشعار تغيير الحالة =====
        user_email = get_user_email_by_fault(fault_id)
        if user_email:
            conn2 = get_db_connection()
            cursor2 = conn2.cursor()
            cursor2.execute("SELECT id FROM users WHERE email = %s", (user_email,))
            user = cursor2.fetchone()
            
            try:
                cursor2.fetchall()
            except:
                pass
            cursor2.close()
            conn2.close()
            
            if user:
                notify_status_change(fault_id, new_status, user['id'])
        
        if user_email:
            send_email_notification(
                recipient=user_email,
                subject=f'📊 تحديث حالة البلاغ #{fault_id}',
                body=f'تم تحديث حالة البلاغ إلى: {new_status}'
            )
        
        if note:
            pass
        
        flash('✅ تم تحديث حالة البلاغ بنجاح', 'success')
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(request.referrer or url_for('technician_support'))

@app.route('/rate_fault/<int:id>', methods=['POST'])
@login_required
def rate_fault(id):
    rating = request.form.get('rating')

    try:
        rating_value = int(rating)
    except (TypeError, ValueError):
        rating_value = 0

    if rating_value < 1 or rating_value > 5:
        flash('تقييم غير صحيح', 'danger')
        return redirect(url_for('fault_details', id=id))
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, status FROM faults WHERE id = %s', (id,))
        fault = cursor.fetchone()
        if not fault or (session.get('user_role') == 'user' and fault['user_id'] != session['user_id']):
            cursor.close()
            conn.close()
            flash('غير مصرح لك بتقييم هذا البلاغ', 'danger')
            return redirect(url_for('my_faults'))
        if fault['status'] != 'closed':
            cursor.close()
            conn.close()
            flash('يمكن تقييم البلاغ بعد إغلاقه', 'warning')
            return redirect(url_for('fault_details', id=id))
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE faults SET user_rating = %s WHERE id = %s',
            (rating_value, id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity('تقييم البلاغ', f'ID: {id} - التقييم: {rating_value}')
        flash('✅ شكراً لتقييمك!', 'success')
    
    return redirect(url_for('fault_details', id=id))

# ========== نظام الشات (المحادثات) ==========

@app.route('/chat/<int:fault_id>')
@login_required
def chat(fault_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM faults WHERE id = %s', (fault_id,))
    fault = cursor.fetchone()
    
    try:
        cursor.fetchall()
    except:
        pass
    cursor.close()
    
    if not fault:
        flash('البلاغ غير موجود', 'danger')
        conn.close()
        return redirect(url_for('view_faults'))
    
    user_id = session['user_id']
    user_role = session['user_role']
    
    if user_role not in ['admin', 'supervisor']:
        if fault['user_id'] != user_id and fault['assigned_to'] != user_id:
            flash('غير مصرح لك بالوصول لهذه المحادثة', 'danger')
            conn.close()
            return redirect(url_for('my_faults') if user_role == 'user' else url_for('dashboard'))
    
    if user_role in ['admin', 'supervisor']:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, full_name, username, role FROM users WHERE id <> %s ORDER BY full_name, username",
            (user_id,)
        )
    else:
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT id, full_name, username, role FROM users
               WHERE id <> %s AND (id IN (%s, %s) OR role IN ('admin', 'supervisor'))
               ORDER BY full_name, username''',
            (user_id, fault['user_id'], fault['assigned_to'] or 0)
        )
    chat_users = cursor.fetchall()
    cursor.close()

    cursor = conn.cursor()
    cursor.execute(
        'UPDATE chat_messages SET is_read = TRUE WHERE fault_id = %s AND receiver_id = %s AND is_read = FALSE',
        (fault_id, user_id)
    )
    conn.commit()
    cursor.execute(
        '''SELECT cm.*, u.full_name as sender_name 
        FROM chat_messages cm
        JOIN users u ON cm.sender_id = u.id
        WHERE cm.fault_id = %s 
        ORDER BY cm.created_at ASC''',
        (fault_id,)
    )
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('chat.html', fault=fault, messages=messages, chat_users=chat_users)

@app.route('/send_message/<int:fault_id>', methods=['POST'])
@login_required
def send_message(fault_id):
    message = request.form.get('message', '').strip()
    receiver_id = request.form.get('receiver_id')
    image = request.files.get('image')
    image_filename = None

    # ===== معالجة الصورة =====
    if image and image.filename:
        allowed = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if '.' in image.filename and image.filename.rsplit('.', 1)[1].lower() in allowed:
            image_filename = secure_filename(image.filename)
            name_parts = image_filename.rsplit('.', 1)
            image_filename = f"{name_parts[0]}_{int(time.time())}.{name_parts[1]}"
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            if message:
                message = f"{message}\n📷 [صورة]"
            else:
                message = "📷 [صورة]"

    if not message:
        flash('الرسالة فارغة', 'danger')
        return redirect(url_for('chat', fault_id=fault_id))

    if not receiver_id:
        flash('يرجى اختيار المستلم', 'danger')
        return redirect(url_for('chat', fault_id=fault_id))

    conn = get_db_connection()
    if not conn:
        flash('مشكلة في الاتصال بقاعدة البيانات', 'danger')
        return redirect(url_for('user_dashboard'))
    cursor = conn.cursor()

    cursor.execute('SELECT user_id, assigned_to FROM faults WHERE id = %s', (fault_id,))
    fault_access = cursor.fetchone()
    if not fault_access or (
        session.get('user_role') == 'user'
        and fault_access['user_id'] != session['user_id']
        and fault_access['assigned_to'] != session['user_id']
    ):
        cursor.close()
        conn.close()
        flash('غير مصرح لك بإرسال رسالة في هذا البلاغ', 'danger')
        return redirect(url_for('my_faults'))

    if session.get('user_role') in ['admin', 'supervisor']:
        cursor.execute('SELECT id FROM users WHERE id = %s AND id <> %s', (receiver_id, session['user_id']))
    else:
        cursor.execute(
            '''SELECT id FROM users WHERE id = %s AND id <> %s
               AND (id IN (%s, %s) OR role IN ('admin', 'supervisor'))''',
            (receiver_id, session['user_id'], fault_access['user_id'], fault_access['assigned_to'] or 0)
        )

    # التأكد من وجود المستلم
    receiver = cursor.fetchone()

    if not receiver:
        flash('المستلم غير موجود', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('chat', fault_id=fault_id))

    cursor.close()

    # إرسال الرسالة مع اسم الصورة
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO chat_messages (fault_id, sender_id, receiver_id, message, image) 
        VALUES (%s, %s, %s, %s, %s)''',
        (fault_id, session['user_id'], receiver_id, message, image_filename)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('chat', fault_id=fault_id))

@app.route('/api/chat/unread')
@login_required
def unread_chat_messages():
    conn = get_db_connection()
    if not conn:
        return {'count': 0, 'latest': None}
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT COUNT(*) AS count FROM chat_messages
           WHERE receiver_id = %s AND is_read = FALSE''',
        (session['user_id'],)
    )
    unread_count = cursor.fetchone()['count'] or 0
    cursor.execute(
        '''SELECT cm.fault_id, f.title, cm.sender_id, u.full_name, u.username
           FROM chat_messages cm
           JOIN faults f ON f.id = cm.fault_id
           JOIN users u ON u.id = cm.sender_id
           WHERE cm.receiver_id = %s AND cm.is_read = FALSE
           ORDER BY cm.created_at DESC LIMIT 1''',
        (session['user_id'],)
    )
    latest = cursor.fetchone()
    cursor.close()
    conn.close()
    return {'count': unread_count, 'latest': latest}

# ========== نظام الإشعارات ==========

@app.route('/notifications')
@login_required
def notifications():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        '''SELECT n.*, f.title as fault_title 
        FROM notifications n
        JOIN faults f ON n.fault_id = f.id
        WHERE n.user_id = %s 
        ORDER BY n.created_at DESC''',
        (session['user_id'],)
    )
    notifs = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('notifications.html', notifications=notifs)

@app.route('/api/notifications/count')
@login_required
def notif_count():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT COUNT(*) as count FROM notifications WHERE user_id = %s AND is_read = FALSE',
        (session['user_id'],)
    )
    count = cursor.fetchone()['count']
    cursor.close()
    conn.close()
    return {'count': count}

@app.route('/api/notifications/latest')
@login_required
def notif_latest():
    conn = get_db_connection()
    if not conn:
        return {'notifications': []}
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT n.id, n.fault_id, n.message, n.is_read, n.created_at, f.title as fault_title 
        FROM notifications n
        LEFT JOIN faults f ON n.fault_id = f.id
        WHERE n.user_id = %s 
        ORDER BY n.created_at DESC LIMIT 5''',
        (session['user_id'],)
    )
    notifs = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Format the dates as string for JSON response
    for notif in notifs:
        if notif['created_at']:
            notif['created_at'] = notif['created_at'].strftime('%Y-%m-%d %H:%M')
            
    return {'notifications': notifs}

@app.route('/api/notifications/mark_read', methods=['POST'])
@login_required
def notif_mark_read():
    conn = get_db_connection()
    if not conn:
        return {'success': False, 'message': 'فشل الاتصال بقاعدة البيانات'}
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE notifications SET is_read = TRUE WHERE user_id = %s AND is_read = FALSE',
            (session['user_id'],)
        )
        conn.commit()
        cursor.close()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'message': str(e)}
    finally:
        conn.close()

@app.route('/api/notifications/delete/<int:notif_id>', methods=['POST'])
@login_required
def notif_delete_one(notif_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'فشل الاتصال بقاعدة البيانات'})
    try:
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM notifications WHERE id = %s AND user_id = %s',
            (notif_id, session['user_id'])
        )
        conn.commit()
        deleted = cursor.rowcount
        cursor.close()
        return jsonify({'success': deleted > 0})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

# ========== إدارة المستخدمين (للأدمن فقط) ==========

@app.route('/admin/users')
@login_required
@role_required(['admin'])
def admin_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, full_name, email, role, user_type, created_at FROM users ORDER BY id DESC')
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_users2.html', users=users)

@app.route('/admin/edit_user/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_edit_user(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        role = request.form.get('role')
        user_type = request.form.get('user_type')

        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '')
        if password and len(password) < 6:
            cursor.close()
            conn.close()
            flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل', 'danger')
            return redirect(url_for('admin_edit_user', id=id))
        if password != confirm_password:
            cursor.close()
            conn.close()
            flash('كلمة المرور غير متطابقة', 'danger')
            return redirect(url_for('admin_edit_user', id=id))

        if password:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            cursor.execute(
                'UPDATE users SET role = %s, user_type = %s, password = %s WHERE id = %s',
                (role, user_type, hashed_password, id)
            )
        else:
            cursor.execute(
                'UPDATE users SET role = %s, user_type = %s WHERE id = %s',
                (role, user_type, id)
            )
        conn.commit()
        cursor.close()
        conn.close()
        flash('✅ تم تحديث بيانات المستخدم', 'success')
        return redirect(url_for('admin_users'))
    
    cursor.execute('SELECT * FROM users WHERE id = %s', (id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user:
        flash('المستخدم غير موجود', 'danger')
        return redirect(url_for('admin_users'))
    
    return render_template('admin_edit_user.html', user=user)

@app.route('/admin/delete_user/<int:id>', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_delete_user(id):
    if id == session['user_id']:
        flash('لا يمكنك حذف حسابك بنفسك', 'danger')
        return redirect(url_for('admin_users'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = %s', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('✅ تم حذف المستخدم', 'success')
    return redirect(url_for('admin_users'))

# ===== صفحة أعطالي للمستخدم =====
@app.route('/my_faults')
@login_required
def my_faults():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM faults WHERE user_id = %s ORDER BY id ASC, created_at ASC',
        (session['user_id'],)
    )
    faults = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # ===== تمرير جميع المتغيرات المطلوبة في القالب =====
    return render_template(
        'view_faults.html',
        faults=faults,
        current_page=1,
        total_pages=1,
        search_title='',
        fault_type='',
        priority='',
        status='',
        date_from='',
        date_to=''
        ,is_my_faults=True
    )

# ========== معالجة أخطاء HTTP ==========

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    import traceback
    error_details = traceback.format_exc()
    try:
        print("500 ERROR OCCURRED:\n", error_details)
    except Exception:
        pass
    return render_template('500.html', error_details=error_details), 500

@app.errorhandler(403)
def forbidden(e):
    flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
    return redirect(url_for('dashboard')), 403

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', '').lower() in {'1', 'true', 'yes'})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)