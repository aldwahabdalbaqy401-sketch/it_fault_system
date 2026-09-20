-- =============================================
-- نظام إدارة وتتبع الأعطال التقنية
-- ملف قاعدة البيانات (جاهز للتنفيذ)
-- =============================================

-- حذف القاعدة لو موجودة
DROP DATABASE IF EXISTS it_fault_db;

-- إنشاء القاعدة
CREATE DATABASE it_fault_db;

-- استخدام القاعدة
USE it_fault_db;

-- =============================================
-- 1. جدول المستخدمين
-- =============================================
CREATE TABLE users (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================
-- 2. جدول الأعطال
-- =============================================
CREATE TABLE faults (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================
-- 3. إضافة مستخدمين افتراضيين
-- =============================================
INSERT INTO users (username, password, full_name, role) VALUES
('admin', '$2b$12$yDvDxul/CwhTR7tQQ.aBherTriSJSP3tNaHnqPDIAXbZDyh2GFjYe', 'مدير النظام', 'admin'),
('supervisor1', '$2b$12$yDvDxul/CwhTR7tQQ.aBherTriSJSP3tNaHnqPDIAXbZDyh2GFjYe', 'مشرف التقنية', 'supervisor'),
('tech1', '$2b$12$yDvDxul/CwhTR7tQQ.aBherTriSJSP3tNaHnqPDIAXbZDyh2GFjYe', 'أحمد محمد', 'technician'),
('tech2', '$2b$12$yDvDxul/CwhTR7tQQ.aBherTriSJSP3tNaHnqPDIAXbZDyh2GFjYe', 'خالد علي', 'technician');

-- =============================================
-- 4. إضافة أعطال تجريبية
-- =============================================
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

-- =============================================
-- 5. عرض البيانات للتأكد
-- =============================================
SELECT '✅ تم إنشاء قاعدة البيانات بنجاح' AS 'رسالة';
SELECT COUNT(*) AS 'عدد المستخدمين' FROM users;
SELECT COUNT(*) AS 'عدد الأعطال' FROM faults;

-- عرض المستخدمين
SELECT * FROM users;

-- عرض الأعطال
SELECT * FROM faults;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ضمان حفظ رسائل الشات العربية في الجداول المنشأة مسبقاً
ALTER TABLE chat_messages
    CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    fault_id INT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_notifications_user (user_id),
    INDEX idx_notifications_fault (fault_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;