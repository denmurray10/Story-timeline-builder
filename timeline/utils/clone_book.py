import logging
from django.db import transaction
from timeline.models import Book, Chapter, Character, Tag, Event, CharacterRelationship, WorldEntry, StoryScanStatus

logger = logging.getLogger(__name__)

@transaction.atomic
def clone_book_for_user(source_book_id, new_user):
    """
    Deep clones a Book and its related entities for a new user.
    """
    try:
        source_book = Book.objects.get(id=source_book_id)
    except Book.DoesNotExist:
        logger.error(f"Source book {source_book_id} not found.")
        return None

    char_map = {}
    tag_map = {}
    chapter_map = {}
    event_map = {}

    # 1. Clone Characters
    source_events = Event.objects.filter(book=source_book)
    source_characters = set()
    for ev in source_events:
        source_characters.update(ev.characters.all())
        if ev.pov_character:
            source_characters.add(ev.pov_character)
            
    source_characters.update(Character.objects.filter(introduction_book=source_book))

    for char in source_characters:
        new_char = Character.objects.get(id=char.id) # Fresh instance
        old_id = new_char.id
        new_char.pk = None
        new_char.user = new_user
        new_char.save()
        char_map[old_id] = new_char

    # 2. Clone Tags
    source_tags = set()
    for ev in source_events:
        source_tags.update(ev.tags.all())
            
    for tag in source_tags:
        new_tag = Tag.objects.get(id=tag.id)
        old_id = new_tag.id
        new_tag.pk = None
        new_tag.user = new_user
        
        # Handle unique constraint on Tag (user, name)
        # If the new user already has a tag with this name, use the existing one
        existing_tag = Tag.objects.filter(user=new_user, name=new_tag.name).first()
        if existing_tag:
            tag_map[old_id] = existing_tag
        else:
            new_tag.save()
            tag_map[old_id] = new_tag

    # 3. Clone Book
    new_book = Book.objects.get(id=source_book.id)
    new_book.pk = None
    new_book.user = new_user
    new_book.save()

    # 4. Clone Chapters
    for chap in Chapter.objects.filter(book=source_book):
        new_chap = Chapter.objects.get(id=chap.id)
        old_id = new_chap.id
        new_chap.pk = None
        new_chap.book = new_book
        new_chap.save()
        chapter_map[old_id] = new_chap

    # Fix Character introduction references
    for old_id, new_char in char_map.items():
        needs_save = False
        if new_char.introduction_book_id == source_book_id:
            new_char.introduction_book = new_book
            needs_save = True
        if new_char.introduction_chapter_id in chapter_map:
            new_char.introduction_chapter = chapter_map[new_char.introduction_chapter_id]
            needs_save = True
        if needs_save:
            new_char.save()

    # 5. Clone Events
    for ev in Event.objects.filter(book=source_book):
        old_ev = Event.objects.get(id=ev.id) # To access M2M and preserve state
        new_ev = Event.objects.get(id=ev.id)
        old_id = new_ev.id
        
        new_ev.pk = None
        new_ev.user = new_user
        new_ev.book = new_book
        if new_ev.chapter_id in chapter_map:
            new_ev.chapter = chapter_map[new_ev.chapter_id]
        if new_ev.pov_character_id in char_map:
            new_ev.pov_character = char_map[new_ev.pov_character_id]
            
        # We'll fix relative_to_event later
        new_ev.relative_to_event = None
        new_ev.save()
        event_map[old_id] = new_ev

        # Add M2M
        for c in old_ev.characters.all():
            if c.id in char_map:
                new_ev.characters.add(char_map[c.id])
        for t in old_ev.tags.all():
            if t.id in tag_map:
                new_ev.tags.add(tag_map[t.id])

    # Fix Event relative references
    for ev in Event.objects.filter(book=source_book):
        if ev.relative_to_event_id in event_map:
            new_ev = event_map[ev.id]
            new_ev.relative_to_event = event_map[ev.relative_to_event_id]
            new_ev.save()

    # 6. Clone Character Relationships
    # Only clone relationships where both characters were cloned
    for rel in CharacterRelationship.objects.filter(character_a__in=char_map.keys(), character_b__in=char_map.keys()):
        new_rel = CharacterRelationship.objects.get(id=rel.id)
        new_rel.pk = None
        new_rel.user = new_user
        new_rel.character_a = char_map[new_rel.character_a_id]
        new_rel.character_b = char_map[new_rel.character_b_id]
        if new_rel.starts_at_event_id in event_map:
            new_rel.starts_at_event = event_map[new_rel.starts_at_event_id]
        else:
            new_rel.starts_at_event = None
        new_rel.save()

    # 7. Clone World Entries
    for entry in WorldEntry.objects.filter(book=source_book):
        new_entry = WorldEntry.objects.get(id=entry.id)
        new_entry.pk = None
        new_entry.user = new_user
        new_entry.book = new_book
        new_entry.save()

    # 8. Clone Story Scan Status (just create a new one as completed)
    if hasattr(source_book, 'scan_status'):
        StoryScanStatus.objects.create(
            book=new_book,
            status=source_book.scan_status.status,
            progress_percentage=source_book.scan_status.progress_percentage
        )

    # 9. Clone caches (InteractionSummaryCache, RelationshipAnalysisCache)
    from timeline.models import InteractionSummaryCache, RelationshipAnalysisCache
    for isc in InteractionSummaryCache.objects.filter(book=source_book, character_a__in=char_map.keys(), character_b__in=char_map.keys()):
        new_isc = InteractionSummaryCache.objects.get(id=isc.id)
        new_isc.pk = None
        new_isc.book = new_book
        new_isc.character_a = char_map[new_isc.character_a_id]
        new_isc.character_b = char_map[new_isc.character_b_id]
        new_isc.save()

    for rac in RelationshipAnalysisCache.objects.filter(book=source_book, character_a__in=char_map.keys(), character_b__in=char_map.keys()):
        new_rac = RelationshipAnalysisCache.objects.get(id=rac.id)
        new_rac.pk = None
        new_rac.book = new_book
        new_rac.character_a = char_map[new_rac.character_a_id]
        new_rac.character_b = char_map[new_rac.character_b_id]
        new_rac.save()

    return new_book
