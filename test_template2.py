import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timeline_project.settings')
django.setup()

from django.template import Template, Context
t = Template("{% with val_str=val|stringformat:'s' %}{% with expected='book-'|add:val_str %}{{ expected }}{% if sel == expected %}yes{% endif %}{% endwith %}{% endwith %}")
print(t.render(Context({'sel': 'book-1', 'val': 1})))
