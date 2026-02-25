import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timeline_project.settings')
django.setup()

from django.template import Template, Context
t = Template("{% if sel == 'book-'|add:val %}yes{% else %}{{ 'book-'|add:val_str }}{% endif %}")
print(t.render(Context({'sel': 'book-1', 'val': 1, 'val_str': '1'})))
