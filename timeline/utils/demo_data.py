import logging
from django.db import transaction
from timeline.models import Series, Book, Chapter, Character, Event, Tag, CharacterRelationship

logger = logging.getLogger(__name__)

def clone_demo_data_for_user(target_user, source_book_id=1):
    """
    Clones the specified book (and all its related entities like characters, 
    events, relationships, and tags) to the target_user.
    This creates a perfect sandbox replica for a new user.
    """
    try:
        source_book = Book.objects.get(id=source_book_id)
    except Book.DoesNotExist:
        logger.error(f"Source book {source_book_id} does not exist.")
        return False

    # Check if user already has this book by title
    if Book.objects.filter(user=target_user, title=source_book.title).exists():
        return False

    with transaction.atomic():
        # 1. Clone Series if exists
        target_series = None
        if source_book.series:
            target_series, _ = Series.objects.get_or_create(
                user=target_user,
                title=source_book.series.title,
                defaults={'description': source_book.series.description}
            )

        # 2. Clone Book
        target_book = Book.objects.create(
            user=target_user,
            series=target_series,
            title=source_book.title,
            series_order=source_book.series_order,
            description=source_book.description,
            word_count_target=source_book.word_count_target,
            current_word_count=source_book.current_word_count,
            status=source_book.status,
            image=source_book.image
        )

        # 3. Clone Characters
        # We clone all characters associated with the source user. 
        # (Assuming the source user is Admin/Demo user and only has demo data)
        character_map = {}
        for char in Character.objects.filter(user=source_book.user):
            new_char = Character.objects.create(
                user=target_user,
                name=char.name,
                nickname=char.nickname,
                aliases=char.aliases,
                role=char.role,
                description=char.description,
                motivation=char.motivation,
                goals=char.goals,
                traits=char.traits,
                color_code=char.color_code,
                height=char.height,
                eyes=char.eyes,
                hair=char.hair,
                age=char.age,
                core_desire=char.core_desire,
                fatal_flaw=char.fatal_flaw,
                fears=char.fears,
                flaws=char.flaws,
                internal_conflicts=char.internal_conflicts,
                unfulfilled_desires=char.unfulfilled_desires,
                secrets=char.secrets,
                regrets=char.regrets,
                is_active=char.is_active,
                profile_image=char.profile_image,
                avatar_id=char.avatar_id,
            )
            character_map[char.id] = new_char

        # 4. Clone Chapters
        chapter_map = {}
        for chap in Chapter.objects.filter(book=source_book):
            new_chap = Chapter.objects.create(
                book=target_book,
                chapter_number=chap.chapter_number,
                title=chap.title,
                description=chap.description,
                word_count=chap.word_count,
                is_complete=chap.is_complete,
                content=chap.content
            )
            chapter_map[chap.id] = new_chap

        # Fix Character introductions now that chapters and book exist
        for old_id, new_char in character_map.items():
            old_char = Character.objects.get(id=old_id)
            save_needed = False
            if old_char.introduction_book_id == source_book.id:
                new_char.introduction_book = target_book
                save_needed = True
            if old_char.introduction_chapter_id in chapter_map:
                new_char.introduction_chapter = chapter_map[old_char.introduction_chapter_id]
                save_needed = True
            if save_needed:
                new_char.save()

        # 5. Clone Relationships
        for rel in CharacterRelationship.objects.filter(user=source_book.user):
            if rel.character_a_id in character_map and rel.character_b_id in character_map:
                new_rel = CharacterRelationship.objects.create(
                    user=target_user,
                    character_a=character_map[rel.character_a_id],
                    character_b=character_map[rel.character_b_id],
                    relationship_type=rel.relationship_type,
                    description=rel.description,
                    strength=rel.strength,
                    trust_level=rel.trust_level,
                    power_dynamic=rel.power_dynamic,
                    relationship_status=rel.relationship_status,
                    visibility=rel.visibility,
                    conflict_source=rel.conflict_source,
                    character_a_wants=rel.character_a_wants,
                    character_b_wants=rel.character_b_wants,
                    evolution=rel.evolution,
                    shared_secret=rel.shared_secret,
                    first_impression=rel.first_impression,
                    vulnerability=rel.vulnerability,
                    major_shared_moments=rel.major_shared_moments,
                    predictability=rel.predictability
                )

        # 6. Clone Tags
        tag_map = {}
        # Get tags used in the source book's events
        source_tags = Tag.objects.filter(events__book=source_book).distinct()
        for tag in source_tags:
            new_tag, _ = Tag.objects.get_or_create(
                user=target_user,
                name=tag.name,
                defaults={'category': tag.category, 'color': tag.color, 'description': tag.description}
            )
            tag_map[tag.id] = new_tag

        # 7. Clone Events
        event_map = {}
        for event in Event.objects.filter(book=source_book):
            new_event = Event.objects.create(
                user=target_user,
                title=event.title,
                description=event.description,
                content_json=event.content_json,
                content_html=event.content_html,
                book=target_book,
                chapter=chapter_map.get(event.chapter_id) if event.chapter_id else None,
                sequence_order=event.sequence_order,
                chronological_order=event.chronological_order,
                narrative_order=event.narrative_order,
                date_type=event.date_type,
                date=event.date,
                earliest_date=event.earliest_date,
                latest_date=event.latest_date,
                end_date=event.end_date,
                relative_description=event.relative_description,
                relative_days=event.relative_days,
                is_locked=event.is_locked,
                story_date=event.story_date,
                location=event.location,
                pov_character=character_map.get(event.pov_character_id) if event.pov_character_id else None,
                emotional_tone=event.emotional_tone,
                story_beat=event.story_beat,
                scene_type=event.scene_type,
                tension_level=event.tension_level,
                notes=event.notes,
                word_count=event.word_count,
                is_written=event.is_written
            )
            
            # Map many-to-many fields
            for old_char in event.characters.all():
                if old_char.id in character_map:
                    new_event.characters.add(character_map[old_char.id])
            
            for old_tag in event.tags.all():
                if old_tag.id in tag_map:
                    new_event.tags.add(tag_map[old_tag.id])
                    
            event_map[event.id] = new_event
            
        # Fix relative events (events dependent on other events)
        for old_id, new_event in event_map.items():
            old_event = Event.objects.get(id=old_id)
            if old_event.relative_to_event_id in event_map:
                new_event.relative_to_event = event_map[old_event.relative_to_event_id]
                new_event.save()
                
    return True
