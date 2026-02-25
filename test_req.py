import sys, os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timeline_project.settings')
django.setup()
from django.test import Client
from django.contrib.auth.models import User
c = Client(SERVER_NAME='localhost')
u = User.objects.first()
c.force_login(u)
r = c.get('/characters/')
if r.status_code == 200:
    html = r.content.decode('utf-8')
    lines = html.split('\n')
    for idx, line in enumerate(lines):
        if 'select id="bookFilter"' in line:
            for j in range(idx, idx+25):
                print(f"{j+1}: {lines[j]}")
            break
else:
    print(r.status_code)
