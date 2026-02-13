import os
import django
import json

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timeline_project.settings')
django.setup()

from timeline.models import RelationshipAnalysisCache, CharacterRelationship

def sync_all():
    caches = RelationshipAnalysisCache.objects.all()
    print(f"Found {caches.count()} cached relationship analyses.")
    count = 0
    for cache in caches:
        data = cache.full_json
        if not data or not isinstance(data, dict):
            continue
            
        # HANDLE NESTING: If data contains an 'analysis' key, use that
        if 'analysis' in data and isinstance(data['analysis'], dict):
            data = data['analysis']
            
        # Mirror to permanent record
        rel, created = CharacterRelationship.objects.get_or_create(
            user=cache.character_a.user,
            character_a=cache.character_a,
            character_b=cache.character_b,
        )
        
        # Pull AI insights into permanent fields
        ai_strength = data.get('strength', 5)
        
        # We update the fields
        rel.relationship_type = data.get('type', 'neutral')
        rel.description = data.get('description', '')
        rel.strength = ai_strength
        rel.trust_level = data.get('trust_level', 5)
        rel.power_dynamic = data.get('power_dynamic', 'balanced')
        rel.relationship_status = data.get('relationship_status', 'active')
        rel.visibility = data.get('visibility', 'public')
        
        rel.conflict_source = data.get('conflict_source', '')
        rel.character_a_wants = data.get('character_a_wants', '')
        rel.character_b_wants = data.get('character_b_wants', '')
        rel.evolution = data.get('evolution', '')
        rel.shared_secret = data.get('shared_secret', '')
        rel.first_impression = data.get('first_impression', '')
        rel.vulnerability = data.get('vulnerability', '')
        rel.major_shared_moments = data.get('major_shared_moments', '')
        rel.predictability = data.get('predictability', 5)
        
        rel.save()
        count += 1
        print(f"[{count}] Fixed & Synced: {cache.character_a.name} <-> {cache.character_b.name} (Type: {rel.relationship_type})")

if __name__ == "__main__":
    sync_all()
    print("Done!")
