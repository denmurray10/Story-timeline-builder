import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timeline_project.settings')
django.setup()

from django.template import Template, Context
t = Template("{% with b_id=7|stringformat:'s' %}{% with b_val='book-'|add:b_id %}{{ b_val }} and {% if sel == b_val %}YES{% endif %}{% endwith %}{% endwith %}")
print(repr(t.render(Context({'sel': 'book-7'}))))
