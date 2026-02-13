import os
import django
import hashlib
from collections import defaultdict

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timeline_project.settings')
django.setup()

from timeline.models import InteractionSummaryCache, Character, Book, CharacterRelationship
from timeline.views import _perform_relationship_analysis

def high_precision_sync():
    # 1. Group summaries by character pair
    print("Collecting cached interaction summaries...")
    all_summaries = InteractionSummaryCache.objects.all().order_by('batch_index')
    groups = defaultdict(list)
    
    for s in all_summaries:
        key = (s.book_id, s.character_a_id, s.character_b_id)
        groups[key].append(s)
        
    print(f"Found {len(groups)} character pairs with available scene summaries.")
    
    count = 0
    for (book_id, char_a_id, char_b_id), summaries in groups.items():
        # Get objects
        try:
            char_a = Character.objects.get(id=char_a_id)
            char_b = Character.objects.get(id=char_b_id)
            book = Book.objects.get(id=book_id)
        except Exception as e:
            print(f"Skipping group due to missing objects: {e}")
            continue
            
        # Prepare inputs for _perform_relationship_analysis
        summary_texts = [s.summary_text for s in summaries]
        batch_hashes = [s.content_hash for s in summaries]
        snapshots_hash = "|".join(batch_hashes)
        
        char_a_data = f"{char_a.traits}|{char_a.motivation}|{char_a.role}"
        char_b_data = f"{char_b.traits}|{char_b.motivation}|{char_b.role}"
        h_a = hashlib.sha256(char_a_data.encode()).hexdigest()
        h_b = hashlib.sha256(char_b_data.encode()).hexdigest()
        
        print(f"\n[{count+1}/{len(groups)}] Analyzing: {char_a.name} & {char_b.name}...")
        
        # Trigger High-Precision AI Pass
        try:
            result = _perform_relationship_analysis(
                char_a, char_b, book,
                summary_texts, snapshots_hash, h_a, h_b
            )
            if result:
                print(f"  -> SUCCESS. Type: {result.get('type')}, Secret: {result.get('shared_secret')[:30]}...")
            else:
                print("  -> AI returned no result.")
        except Exception as e:
            print(f"  -> ERROR: {e}")
            
        count += 1

    print("\nHigh-Precision Sync Completed!")

if __name__ == "__main__":
    high_precision_sync()
