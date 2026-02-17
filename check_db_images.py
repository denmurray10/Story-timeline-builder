import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timeline_project.settings')
django.setup()

from timeline.models import Book, Character, WorldEntry

print(f"Books: {Book.objects.count()}")
print(f"Books with images: {Book.objects.exclude(image='').count()}")
print(f"Characters: {Character.objects.count()}")
print(f"Characters with images: {Character.objects.exclude(profile_image='').count()}")
print(f"World Entries: {WorldEntry.objects.count()}")
print(f"World Entries with images: {WorldEntry.objects.exclude(image='').count()}")
