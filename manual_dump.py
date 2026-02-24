import os
import django
import json
from django.core import serializers

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timeline_project.settings')
django.setup()

from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from django.contrib.sites.models import Site
from timeline.models import Book, Chapter, Character, Event, Tag, CharacterRelationship, WorldEntry, AIFocusTask, ActivityLog

def custom_dump():
    models_to_dump = [
        User, Site, SocialApp, SocialAccount, SocialToken,
        Book, Chapter, Character, Event, Tag, CharacterRelationship, WorldEntry, AIFocusTask, ActivityLog
    ]
    all_data = []
    
    for model in models_to_dump:
        data = serializers.serialize("json", model.objects.all())
        all_data.extend(json.loads(data))
        
    with open('manual_backup.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2)
    print("Exported results to manual_backup.json")

if __name__ == "__main__":
    custom_dump()
