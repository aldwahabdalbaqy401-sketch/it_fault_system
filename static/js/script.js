// ============================================================
// script.js - نظام إدارة وتتبع الأعطال التقنية
// جميع الحقوق محفوظة © 2026
// ============================================================

// ===== تحديث عداد الإشعارات =====
function updateNotifCount() {
    fetch('/api/notifications/count')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('notif-count');
            if (badge) {
                const count = data.count || 0;
                badge.textContent = count;
                badge.style.display = count > 0 ? 'inline-block' : 'none';
            }
        })
        .catch(err => console.log('⚠️ خطأ في جلب الإشعارات:', err));
}

// ===== إشعارات منبثقة (Toast) =====
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) {
        // إنشاء الحاوية إذا لم تكن موجودة
        const newContainer = document.createElement('div');
        newContainer.id = 'toast-container';
        newContainer.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 400px;
            width: 100%;
        `;
        document.body.appendChild(newContainer);
    }

    const toastContainer = document.getElementById('toast-container');
    
    const colors = {
        success: { bg: '#10b981', border: '#059669' },
        danger: { bg: '#ef4444', border: '#dc2626' },
        warning: { bg: '#f59e0b', border: '#d97706' },
        info: { bg: '#3b82f6', border: '#2563eb' }
    };

    const icons = {
        success: '✅',
        danger: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.style.cssText = `
        background: ${colors[type]?.bg || '#1e293b'};
        color: white;
        padding: 14px 20px;
        border-radius: 12px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.2);
        border-right: 4px solid ${colors[type]?.border || '#475569'};
        animation: slideUp 0.4s ease;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        font-size: 14px;
        font-weight: 500;
        direction: rtl;
        min-width: 250px;
    `;

    toast.innerHTML = `
        <span>${icons[type] || 'ℹ️'} ${message}</span>
        <button onclick="this.parentElement.remove()" style="
            background: none;
            border: none;
            color: white;
            font-size: 20px;
            cursor: pointer;
            opacity: 0.7;
            padding: 0 4px;
        ">&times;</button>
    `;

    toastContainer.appendChild(toast);

    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(30px)';
            toast.style.transition = 'all 0.4s ease';
            setTimeout(() => toast.remove(), 400);
        }
    }, 5000);
}

// ===== تأكيد الحذف =====
function confirmDelete(message = 'هل أنت متأكد من الحذف؟') {
    return confirm(message);
}

// ===== إظهار/إخفاء كلمة المرور =====
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    
    if (input.type === 'password') {
        input.type = 'text';
    } else {
        input.type = 'password';
    }
}

// ===== تحميل تلقائي عند فتح الصفحة =====
document.addEventListener('DOMContentLoaded', function() {
    // تحديث عداد الإشعارات
    updateNotifCount();
    
    // تحديث كل 30 ثانية
    setInterval(updateNotifCount, 30000);
    
    // إغلاق التنبيهات تلقائياً
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-20px)';
            setTimeout(function() {
                alert.style.display = 'none';
            }, 400);
        }, 5000);
    });
});

// ===== إضافة تأثيرات CSS للـ Toast =====
const style = document.createElement('style');
style.textContent = `
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(style);