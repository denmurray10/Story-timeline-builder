import sys, os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timeline_project.settings')
django.setup()
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from timeline.models import Series, Book, Character
u = User.objects.first()
ctx = {
    'series_list': Series.objects.filter(user=u).prefetch_related('books'),
    'standalone_books': Book.objects.filter(user=u, series__isnull=True),
    'selected_book': 'series-1'
}
s = render_to_string('timeline/character_list.html', ctx)
lines = s.split('\n')
for idx, line in enumerate(lines):
    if 'select id="bookFilter"' in line:
        for j in range(idx, min(idx + 30, len(lines))):
            print(f"{j+1}: {lines[j]}")
        break
