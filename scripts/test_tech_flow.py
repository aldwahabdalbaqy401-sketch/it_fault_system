import re
from app import app

with app.test_client() as client:
    res = client.get('/login')
    html = res.data.decode('utf-8')
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    csrf_token = match.group(1) if match else None
    print('CSRF token:', csrf_token[:15] if csrf_token else 'None')

    # Test tech1
    login_tech = client.post('/login', data={'username': 'tech1', 'password': 'password123', 'csrf_token': csrf_token}, follow_redirects=False)
    print('Tech1 login status:', login_tech.status_code, 'Redirect:', login_tech.headers.get('Location'))

    # Follow redirect to technician_support
    if login_tech.headers.get('Location') == '/technician_support':
        tech_page = client.get('/technician_support')
        print('Technician support page status:', tech_page.status_code)
