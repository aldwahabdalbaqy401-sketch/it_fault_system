// ===== تحديث عداد الإشعارات =====
function updateNotifCount() {
    fetch('/api/notifications/count')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('notif-count');
            if (badge) {
                badge.textContent = data.count || 0;
                badge.style.display = data.count > 0 ? 'inline-block' : 'none';
            }
        })
        .catch(err => console.log('⚠️ خطأ:', err));
}

// ===== إظهار إشعار منبثق (Toast) =====
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-body">
            <span>${message}</span>
            <button class="toast-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
        </div>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
}

// تشغيل عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    updateNotifCount();
    setInterval(updateNotifCount, 30000);
});