# -*- coding: utf-8 -*-
import re
from app import app

def run_tests():
    with app.test_client() as client:
        # Step 1: Login page CSRF and technician login
        res = client.get('/login')
        assert res.status_code == 200, f"Login GET failed: {res.status_code}"
        match = re.search(r'name="csrf_token" value="([^"]+)"', res.data.decode('utf-8'))
        csrf_token = match.group(1) if match else None
        assert csrf_token, "No CSRF token found"

        # Step 2: Tech1 login
        tech_login = client.post('/login', data={'username': 'tech1', 'password': 'password123', 'csrf_token': csrf_token}, follow_redirects=False)
        print("1. Tech1 login status:", tech_login.status_code, "Redirect:", tech_login.headers.get('Location'))
        assert tech_login.status_code == 302
        assert tech_login.headers.get('Location') == '/technician_support'

        # Step 3: Access /technician_support as technician
        tech_page = client.get('/technician_support')
        print("2. Tech page status:", tech_page.status_code)
        assert tech_page.status_code == 200
        assert "مركز العمليات" in tech_page.data.decode('utf-8') or "لوحة إسناد ومتابعة الفنيين" in tech_page.data.decode('utf-8')

        # Step 4: Logout
        client.get('/logout')

        # Step 5: Admin login
        res = client.get('/login')
        match = re.search(r'name="csrf_token" value="([^"]+)"', res.data.decode('utf-8'))
        csrf_token = match.group(1) if match else None

        admin_login = client.post('/login', data={'username': 'admin', 'password': 'admin123', 'csrf_token': csrf_token}, follow_redirects=False)
        print("3. Admin login status:", admin_login.status_code, "Redirect:", admin_login.headers.get('Location'))
        assert admin_login.status_code == 302
        assert admin_login.headers.get('Location') == '/dashboard'

        # Step 6: Admin opens /technician_support
        admin_tech_page = client.get('/technician_support')
        print("4. Admin viewing /technician_support status:", admin_tech_page.status_code)
        assert admin_tech_page.status_code == 200
        html = admin_tech_page.data.decode('utf-8')
        assert "تصفية حسب الفني" in html

        # Step 7: Admin opens /assign_fault/1
        assign_page = client.get('/assign_fault/1')
        print("5. Admin viewing /assign_fault/1 status:", assign_page.status_code)
        assert assign_page.status_code == 200
        html_assign = assign_page.data.decode('utf-8')
        assert "م. أحمد محمد" in html_assign or "tech1" in html_assign
        assert "م. سارة علي" in html_assign or "tech2" in html_assign

        # Step 8: Admin assigns fault 1 to tech1
        match = re.search(r'name="csrf_token" value="([^"]+)"', html_assign)
        assign_csrf = match.group(1) if match else None
        assign_post = client.post('/assign_fault/1', data={
            'assigned_to': '5',  # tech1 id
            'assign_note': 'يرجى مراجعة الكيبل في الدور الأرضي',
            'csrf_token': assign_csrf
        }, follow_redirects=False)
        print("6. Admin assigned fault 1 status:", assign_post.status_code, "Redirect:", assign_post.headers.get('Location'))
        assert assign_post.status_code == 302

        # Step 9: Re-verify tech1 can see assigned fault and test receiving it
        client.get('/logout')
        res = client.get('/login')
        match = re.search(r'name="csrf_token" value="([^"]+)"', res.data.decode('utf-8'))
        csrf_token = match.group(1) if match else None
        client.post('/login', data={'username': 'tech1', 'password': 'password123', 'csrf_token': csrf_token}, follow_redirects=False)

        tech_page2 = client.get('/technician_support')
        html_tech2 = tech_page2.data.decode('utf-8')
        assert "#1" in html_tech2
        print("7. Tech1 successfully sees assigned fault #1!")

        print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY! No 500 errors!")

if __name__ == '__main__':
    run_tests()
