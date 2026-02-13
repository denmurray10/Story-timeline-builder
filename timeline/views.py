"""
Views for the Timeline app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
import docx2txt
import io
import os
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.views.decorators.http import require_POST
import json
import re
import hashlib
import time
import threading
import math
from itertools import combinations
from django.utils import timezone
import google.generativeai as genai
from openai import OpenAI
from django.conf import settings
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile

from .models import Book, Chapter, Character, Event, Tag, CharacterRelationship, AIFocusTask, ActivityLog, WorldEntry, InteractionSummaryCache, RelationshipAnalysisCache, StoryScanStatus
from .forms import (
    UserRegisterForm, BookForm, ChapterForm, CharacterForm, 
    EventForm, TagForm, UserAccountForm, CharacterRelationshipForm, WorldEntryForm
)
from .utils.ai_context import ContextResolver
# ============== Authentication Views ==============

@login_required
def account(request):
    """View and edit user account details."""
    if request.method == 'POST':
        form = UserAccountForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account details updated successfully!')
            return redirect('account')
    else:
        form = UserAccountForm(instance=request.user)
    return render(request, 'timeline/account.html', {'form': form})


# ============== Authentication Views ==============

def register(request):
    """User registration view."""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Account created for {user.username}!')
            return redirect('timeline_home')
    else:
        form = UserRegisterForm()
    return render(request, 'timeline/register.html', {'form': form})


# ============== Home & Dashboard ==============

def home(request):
    """Landing page - redirects to dashboard if logged in."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'timeline/home.html')


def home_preview(request):
    """Preview page for the new homepage design."""
    return render(request, 'timeline/home_preview.html')


@login_required
def dashboard(request):
    """Main dashboard showing overview of all projects."""
    books = Book.objects.filter(user=request.user).annotate(
        chapter_count=Count('chapters', distinct=True),
        event_count=Count('events', distinct=True),
        book_character_count=Count('events__characters', distinct=True)
    )
    
    characters = Character.objects.filter(user=request.user, is_active=True)
    total_events = Event.objects.filter(user=request.user).count()
    events_written = Event.objects.filter(user=request.user, is_written=True).count()
    
    # Recent activity logs (last 5)
    recent_activity = ActivityLog.objects.filter(user=request.user).order_by('-timestamp')[:5]
    
    today = timezone.localdate()
    
    chapters_completed = Chapter.objects.filter(
        book__user=request.user
    ).count()

    print(f"DEBUG: User={request.user}, Completed Chapters={chapters_completed}")
    focus_tasks = AIFocusTask.objects.filter(user=request.user, created_at__date=today)
    
    if not focus_tasks.exists():
        # Generate new tasks if none exist for today
        generate_daily_focus_tasks(request.user)
        focus_tasks = AIFocusTask.objects.filter(user=request.user, created_at__date=today)
    else:
        # Auto-sense if tasks have been completed
        auto_sense_focus_tasks(request.user, focus_tasks)
    
    # Character Spotlight (Daily Random)
    import random
    spotlight_character = None
    if characters.exists():
        # Use date as seed for daily consistency
        seed_value = int(today.strftime('%Y%m%d'))
        random.seed(seed_value)
        spotlight_character = random.choice(list(characters))
        # Reset seed to avoid affecting other random calls
        random.seed()
    
    # Relationship Sparkline (Latest/Strongest)
    top_relationships = CharacterRelationship.objects.filter(user=request.user).order_by('-strength')[:4]
    
    # Inspiration Mood Board (Random Elements)
    import random
    mood_elements = []
    
    # 1. Random Tag (Theme or Location)
    random_tag = Tag.objects.filter(user=request.user).order_by('?').first()
    if random_tag:
        mood_elements.append({'type': 'tag', 'content': random_tag.name, 'color': random_tag.color})
    
    # 2. Random Key Event
    random_event = Event.objects.filter(user=request.user, tension_level__gte=7).order_by('?').first()
    if random_event:
        mood_elements.append({'type': 'event', 'content': random_event.title})
        
    # 3. Random Character Motivation
    random_char_motivation = Character.objects.filter(user=request.user).exclude(motivation='').order_by('?').first()
    if random_char_motivation:
        mood_elements.append({'type': 'motivation', 'content': random_char_motivation.motivation, 'char': random_char_motivation.name})

    context = {
        'books': books,
        'character_count': characters.count(),
        'total_events': total_events,
        'events_written': events_written,
        'chapters_completed': chapters_completed,
        'recent_activity': recent_activity,
        'focus_tasks': focus_tasks,
        'spotlight_character': spotlight_character,
        'top_relationships': top_relationships,
        'mood_elements': mood_elements,
    }
    return render(request, 'timeline/dashboard.html', context)


def generate_daily_focus_tasks(user):
    """Helper to generate 3 focus tasks for the user using AI."""
    # 1. Gather context
    books = Book.objects.filter(user=user)
    chapters_without_content = Chapter.objects.filter(book__user=user, content='', chapter_file='').count()
    events_not_written = Event.objects.filter(user=user, is_written=False).count()
    characters = Character.objects.filter(user=user).count()
    
    context = f"The user is writing a story. Stats: {books.count()} books, {characters} characters. "
    context += f"They have {chapters_without_content} empty chapters and {events_not_written} unwritten events planned."
    context += "\nGenerate 3 short, actionable writing tasks for today. Return ONLY the tasks as a bulleted list."

    try:
        if settings.DEEPSEEK_API_KEY:
            client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful story writing coach. Give 3 short daily focus tasks."},
                    {"role": "user", "content": context},
                ],
                stream=False
            )
            tasks_text = response.choices[0].message.content
        elif settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-3-flash-preview')
            response = model.generate_content(context)
            tasks_text = response.text
        else:
            tasks_text = "- Add a new scene to your current book.\n- Flesh out a secondary character.\n- Review your last chapter."

        # Parse tasks (stripping bullet points like *, -, 1.)
        import re
        lines = [re.sub(r'^\d+[\.\)]\s*|^\*\s*|^-\s*', '', line).strip() for line in tasks_text.split('\n') if line.strip()]
        
        for text in lines[:3]:
            if text:
                AIFocusTask.objects.create(user=user, task_text=text)
    except Exception as e:
        print(f"Error generating tasks: {e}")
        # Fallback
        for text in ["Write 500 words", "Outline a new scene", "Develop a character trait"]:
            AIFocusTask.objects.create(user=user, task_text=text)


def auto_sense_focus_tasks(user, focus_tasks):
    """Automatically sense completion based on user activity since task creation."""
    if not focus_tasks.exists():
        return

    # Get activity since the earliest task was created today
    start_time = focus_tasks.order_by('created_at').first().created_at
    
    # Check for activity
    has_new_content = Chapter.objects.filter(book__user=user, updated_at__gte=start_time).exclude(content='', chapter_file='').exists()
    has_written_events = Event.objects.filter(user=user, updated_at__gte=start_time, is_written=True).exists()
    has_new_characters = Character.objects.filter(user=user, created_at__gte=start_time).exists()
    has_new_events = Event.objects.filter(user=user, created_at__gte=start_time).exists()

    for task in focus_tasks:
        if task.is_completed:
            continue
            
        text = task.task_text.lower()
        if ("chapter" in text or "write" in text or "content" in text) and has_new_content:
            task.is_completed = True
            task.save()
        elif ("event" in text or "scene" in text) and (has_new_events or has_written_events):
            task.is_completed = True
            task.save()
        elif "character" in text and has_new_characters:
            task.is_completed = True
            task.save()
        elif "flesh out" in text or "develop" in text:
            # Check for any update activity
            if has_new_content or has_written_events or has_new_characters:
                task.is_completed = True
                task.save()


@login_required
@require_POST
def api_toggle_focus_task(request, pk):
    """Toggle completion status of a focus task."""
    task = get_object_or_404(AIFocusTask, pk=pk, user=request.user)
    task.is_completed = not task.is_completed
    task.save()
    return JsonResponse({'status': 'success', 'is_completed': task.is_completed})


# ============== Book Views ==============

@login_required
def book_list(request):
    """List all books for the current user."""
    books = Book.objects.filter(user=request.user).annotate(
        chapter_count=Count('chapters'),
        event_count=Count('events'),
        character_count=Count('events__characters', distinct=True)
    )
    return render(request, 'timeline/book_list.html', {'books': books})


@login_required
def book_detail(request, pk):
    """Detail view for a single book."""
    book = get_object_or_404(Book, pk=pk, user=request.user)
    chapters = book.chapters.all().annotate(event_count=Count('events')).order_by('chapter_number')
    events = book.events.all().order_by('sequence_order')
    
    context = {
        'book': book,
        'chapters': chapters,
        'events': events,
    }
    return render(request, 'timeline/book_detail.html', context)


@login_required
def book_create(request):
    """Create a new book."""
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.user = request.user
            book.save()
            messages.success(request, f'Book "{book.title}" created successfully!')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm()
    return render(request, 'timeline/book_form.html', {'form': form, 'action': 'Create'})


@login_required
def book_edit(request, pk):
    """Edit an existing book."""
    book = get_object_or_404(Book, pk=pk, user=request.user)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, f'Book "{book.title}" updated successfully!')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm(instance=book)
    return render(request, 'timeline/book_form.html', {'form': form, 'action': 'Edit', 'book': book})


@login_required
def book_import(request):
    """Start a book import process in the background."""
    if request.method == 'POST' and request.FILES.get('book_file'):
        book_file = request.FILES['book_file']
        title = request.POST.get('title', 'Imported Book')
        
        # 1. Create the Book
        last_book = Book.objects.filter(user=request.user).order_by('-series_order').first()
        series_order = (last_book.series_order + 1) if last_book else 1
        
        book = Book.objects.create(
            user=request.user, 
            title=title, 
            series_order=series_order,
            status='importing',
            import_progress=5,
            import_status_message="Extracting manuscript text..."
        )
        
        # 2. Extract text immediately (before request context/file is lost)
        content = extract_text_from_file(book_file)
        if not content:
            book.delete()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Could not extract text.'})
            messages.error(request, "Could not extract text from file.")
            return redirect('book_list')

        # 3. Start background thread
        thread = threading.Thread(
            target=run_background_book_import,
            args=(book.id, content, request.user.id)
        )
        thread.start()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'book_id': book.id})
            
        return redirect('book_list')

    return render(request, 'timeline/book_import.html')


def run_background_book_import(book_id, content, user_id):
    """Heavy lifting AI analysis run in a background thread."""
    from django.contrib.auth.models import User
    import django
    django.db.connections.close_all()
    
    new_chapters = 0
    new_events = 0
    skipped_batches = 0
    
    try:
        book = Book.objects.get(id=book_id)
        user = User.objects.get(id=user_id)
        
        # 3. Global Character Pass
        book.import_progress = 15
        book.import_status_message = "Deep-scanning manuscript for characters..."
        book.save()
        
        char_context = content[:80000]
        char_data = analyze_characters_with_ai(char_context)
        
        # Pre-populate char_map with ALL existing characters for this user
        # Map both primary names AND aliases to the same character object
        char_map = {}
        for existing_char in Character.objects.filter(user=user):
            char_map[existing_char.name.lower()] = existing_char
            if existing_char.nickname:
                char_map[existing_char.nickname.lower()] = existing_char
            if existing_char.aliases:
                for alias in existing_char.aliases.split(','):
                    alias = alias.strip().lower()
                    if alias:
                        char_map[alias] = existing_char
        
        if char_data:
            for char_info in char_data.get('characters', []):
                try:
                    name = char_info.get('name')
                    if not name:
                        continue
                    
                    # Check if character already exists (case-insensitive, including aliases)
                    existing = char_map.get(name.lower())
                    
                    # Also check if any of the AI-detected aliases match an existing character
                    ai_aliases = char_info.get('aliases', [])
                    if not existing and ai_aliases:
                        for ai_alias in ai_aliases:
                            existing = char_map.get(ai_alias.lower().strip())
                            if existing:
                                break
                    
                    if existing:
                        # Update sparse fields on the existing character if AI provided richer data
                        updated = False
                        if not existing.description and char_info.get('description'):
                            existing.description = char_info['description']
                            updated = True
                        if not existing.motivation and char_info.get('motivation'):
                            existing.motivation = char_info['motivation']
                            updated = True
                        if not existing.goals and char_info.get('goals'):
                            existing.goals = char_info['goals']
                            updated = True
                        if not existing.traits and char_info.get('traits'):
                            existing.traits = char_info['traits']
                            updated = True
                        # Auto-set introduction book/chapter if not already set
                        if not existing.introduction_book:
                            existing.introduction_book = book
                            first_ch_num = char_info.get('first_chapter')
                            if first_ch_num:
                                intro_chapter = book.chapters.filter(chapter_number=first_ch_num).first()
                                if intro_chapter:
                                    existing.introduction_chapter = intro_chapter
                            updated = True
                        # Merge new aliases into existing ones
                        if ai_aliases:
                            current_aliases = set(
                                a.strip().lower() for a in (existing.aliases or '').split(',') if a.strip()
                            )
                            for a in ai_aliases:
                                current_aliases.add(a.strip().lower())
                            # Remove the primary name from aliases if present
                            current_aliases.discard(existing.name.lower())
                            if current_aliases:
                                existing.aliases = ', '.join(sorted(current_aliases))
                                updated = True
                        if updated:
                            existing.save()
                        # Register this name in char_map too (in case AI used a different name)
                        char_map[name.lower()] = existing
                    else:
                        aliases_str = ', '.join(ai_aliases) if ai_aliases else ''
                        # Determine introduction chapter
                        intro_chapter = None
                        first_ch_num = char_info.get('first_chapter')
                        if first_ch_num:
                            intro_chapter = book.chapters.filter(chapter_number=first_ch_num).first()
                        char = Character.objects.create(
                            user=user,
                            name=name,
                            aliases=aliases_str,
                            role=char_info.get('role', 'supporting')[:100],
                            description=char_info.get('description', ''),
                            motivation=char_info.get('motivation', ''),
                            goals=char_info.get('goals', ''),
                            traits=char_info.get('traits', ''),
                            introduction_book=book,
                            introduction_chapter=intro_chapter,
                        )
                        char_map[name.lower()] = char
                        # Also register all aliases in the map
                        for a in ai_aliases:
                            char_map[a.strip().lower()] = char
                except Exception as e:
                    print(f"Error creating character: {e}")

        # 4. Chapter Splitting
        book.import_progress = 25
        book.import_status_message = f"Splitting manuscript into chapters... ({len(char_map)} characters found)"
        book.save()
        
        chapter_regex = re.compile(
            r'(?:^|\n)(?:(?:Chapter|Section|Part|Book)\s+|[0-9]+[\.\-\s]+|[#*]{1,3}\s+)(?:[0-9A-Za-z]+)', 
            re.IGNORECASE
        )
        chapters_found = list(chapter_regex.finditer(content))
        
        chunks = []
        if chapters_found:
            for i in range(len(chapters_found)):
                start = chapters_found[i].start()
                end = chapters_found[i+1].start() if i+1 < len(chapters_found) else len(content)
                chunk_text = content[start:end].strip()
                if len(chunk_text) > 100:
                    chunks.append(chunk_text)
        
        if not chunks or len(chunks) < 2:
            chunks = [content[i:i+12000] for i in range(0, len(content), 12000)]

        # 5. Iterative Content Parsing — smaller batches for reliability
        total_chunks = len(chunks)
        batch_size = 2  # Reduced from 4 to avoid token limits
        
        for i in range(0, len(chunks), batch_size):
            batch_num = (i // batch_size) + 1
            total_batches = (total_chunks + batch_size - 1) // batch_size
            progress_chunk = int(25 + ((i / total_chunks) * 70))
            book.import_progress = progress_chunk
            book.import_status_message = f"Analyzing batch {batch_num}/{total_batches}... ({new_chapters} chapters, {new_events} events so far)"
            book.save()
            
            try:
                # Keep original full chunks for content storage
                original_batch = chunks[i:i+batch_size]
                # Truncate for AI analysis only
                batch = [chunk[:10000] for chunk in original_batch]
                batch_text = "\n\n--- SECTION BOUNDARY ---\n\n".join(batch)
                
                ai_data = analyze_book_content_batch_with_ai(batch_text)
                if not ai_data:
                    skipped_batches += 1
                    print(f"Batch {batch_num} returned no data, skipping.")
                    continue
                    
                ai_chapters = ai_data.get('chapters', [])
                for idx, chap_info in enumerate(ai_chapters):
                    try:
                        # Map chapter content from the original chunk if available
                        chapter_content = ''
                        if idx < len(original_batch):
                            chapter_content = original_batch[idx]
                        elif len(original_batch) == 1:
                            chapter_content = original_batch[0]
                        
                        chapter = Chapter.objects.create(
                            book=book,
                            chapter_number=chap_info.get('number', new_chapters + 1),
                            title=chap_info.get('title', f"Chapter {new_chapters + 1}")[:200],
                            description=chap_info.get('summary', '')[:5000],
                            content=chapter_content,
                            word_count=len(chapter_content.split()) if chapter_content else 0
                        )
                        new_chapters += 1
                        
                        for event_info in ai_data.get('events', []):
                            if event_info.get('chapter_number') == chapter.chapter_number:
                                try:
                                    pov_name = event_info.get('pov_character', '').lower()
                                    pov_char = char_map.get(pov_name)
                                    
                                    tension = event_info.get('tension', 5)
                                    if not isinstance(tension, int) or tension < 1:
                                        tension = 5
                                    if tension > 10:
                                        tension = 10
                                    
                                    event = Event.objects.create(
                                        user=user,
                                        book=book,
                                        chapter=chapter,
                                        title=event_info.get('title', f"Event {new_events + 1}")[:200],
                                        description=event_info.get('summary', '')[:5000],
                                        pov_character=pov_char,
                                        emotional_tone=event_info.get('tone', 'neutral')[:100],
                                        story_beat=event_info.get('beat', '')[:100],
                                        tension_level=tension,
                                        sequence_order=new_events + 1
                                    )
                                    
                                    for c_name in event_info.get('involved_characters', []):
                                        c_obj = char_map.get(c_name.lower())
                                        if c_obj:
                                            event.characters.add(c_obj)
                                    new_events += 1
                                except Exception as e:
                                    print(f"Error creating event: {e}")
                    except Exception as e:
                        print(f"Error creating chapter: {e}")
                        
            except Exception as e:
                skipped_batches += 1
                print(f"Batch {batch_num} failed: {e}")
                continue

        # 6. Mark as Live
        book.import_progress = 100
        status_parts = [f"{new_chapters} chapters, {new_events} events imported"]
        if skipped_batches > 0:
            status_parts.append(f"{skipped_batches} batch(es) skipped due to errors")
        book.import_status_message = "Import complete! " + ", ".join(status_parts)
        book.status = 'drafting'
        book.save()
        
    except Exception as e:
        print(f"Error in background import: {e}")
        try:
            book = Book.objects.get(id=book_id)
            book.import_status_message = f"Error: {str(e)[:200]}. Imported {new_chapters} chapters, {new_events} events before failure."
            book.status = 'drafting'  # Allow user to see partial results
            book.import_progress = 100
            book.save()
        except:
            pass


@login_required
def api_book_progress(request, pk):
    """API endpoint to get the import progress of a book with stall detection."""
    book = get_object_or_404(Book, pk=pk, user=request.user)
    
    is_stalled = False
    if book.status == 'importing':
        # If no update in 5 minutes, consider it stalled
        time_diff = timezone.now() - book.last_import_update
        if time_diff.total_seconds() > 300:
            is_stalled = True
            
    return JsonResponse({
        'status': book.status,
        'progress': book.import_progress,
        'message': book.import_status_message,
        'is_stalled': is_stalled
    })


@login_required
def book_delete(request, pk):
    """Delete a book."""
    book = get_object_or_404(Book, pk=pk, user=request.user)
    if request.method == 'POST':
        book_title = book.title
        
        # Enhanced cleanup: Find characters that were introduced in this book
        # and delete them if they aren't used in any other books.
        orphan_candidates = Character.objects.filter(introduction_book=book, user=request.user)
        for char in orphan_candidates:
            # Check if character has events (either as POV or listed character)
            # in any other book besides the one being deleted.
            is_used_elsewhere = Event.objects.filter(
                Q(characters=char) | Q(pov_character=char)
            ).exclude(book=book).exists()
            
            if not is_used_elsewhere:
                char.delete()

        book.delete()
        messages.success(request, f'Book "{book_title}" deleted successfully!')
        return redirect('book_list')
    return render(request, 'timeline/book_confirm_delete.html', {'book': book})


@login_required
def export_story_bible(request, pk):
    """View to export a professional Story Bible for a book."""
    book = get_object_or_404(Book, pk=pk, user=request.user)
    
    # Gather data
    characters = Character.objects.filter(user=request.user).order_by('role', 'name')
    events = Event.objects.filter(book=book, user=request.user).order_by('chronological_order', 'sequence_order')
    tags = Tag.objects.filter(user=request.user).order_by('category', 'name')
    
    context = {
        'book': book,
        'characters': characters,
        'events': events,
        'tags': tags,
        'now': timezone.now(),
    }
    return render(request, 'timeline/story_bible_export.html', context)



@login_required
def relationship_list(request):
    """List all character relationships."""
    relationships = CharacterRelationship.objects.filter(user=request.user)
    return render(request, 'timeline/relationship_list.html', {'relationships': relationships})


@login_required
def relationship_create(request):
    """Create a new character relationship."""
    if request.method == 'POST':
        form = CharacterRelationshipForm(request.POST, user=request.user)
        if form.is_valid():
            rel = form.save(commit=False)
            rel.user = request.user
            rel.save()
            messages.success(request, 'Relationship created successfully!')
            return redirect('relationship_list')
    else:
        form = CharacterRelationshipForm(user=request.user)
    return render(request, 'timeline/relationship_form.html', {'form': form, 'action': 'Create'})


@login_required
def relationship_edit(request, pk):
    """Edit an existing relationship."""
    rel = get_object_or_404(CharacterRelationship, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CharacterRelationshipForm(request.POST, instance=rel, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Relationship updated successfully!')
            return redirect('relationship_list')
    else:
        form = CharacterRelationshipForm(instance=rel, user=request.user)
    return render(request, 'timeline/relationship_form.html', {'form': form, 'action': 'Edit', 'relationship': rel})


@login_required
def relationship_delete(request, pk):
    """Delete a relationship."""
    rel = get_object_or_404(CharacterRelationship, pk=pk, user=request.user)
    if request.method == 'POST':
        rel.delete()
        messages.success(request, 'Relationship deleted.')
        return redirect('relationship_list')
    return render(request, 'timeline/relationship_confirm_delete.html', {'relationship': rel})


@login_required
def relationship_map(request):
    """View the interactive relationship graph."""
    characters = Character.objects.filter(user=request.user, is_active=True)
    return render(request, 'timeline/relationship_map.html', {'characters': characters})


@login_required
def api_relationship_data(request):
    """API endpoint for the relationship graph data."""
    characters = Character.objects.filter(user=request.user, is_active=True)
    relationships = CharacterRelationship.objects.filter(user=request.user)
    
    nodes = []
    for char in characters:
        # Determine color based on role
        color = char.color_code
        if not color:
            if char.role == 'protagonist': color = '#6366f1' # Indigo
            elif char.role == 'antagonist': color = '#ef4444' # Red
            else: color = '#94a3b8' # Gray
            
        nodes.append({
            'id': char.id,
            'label': char.name,
            'title': f"{char.name} ({char.get_role_display()})",
            'color': color,
            'image': char.profile_pic_url if char.profile_pic_url else "",
            'shape': 'circularImage' if char.profile_pic_url else 'dot',
            'description': char.description[:100] + "..." if char.description else ""
        })
        
    edges = []
    for rel in relationships:
        # Map strength to width
        width = max(1, rel.strength / 2)
        
        # Style based on type
        color = '#94a3b8'  # Gray (Default)
        if rel.relationship_type == 'romantic': color = '#ff2d55'
        elif rel.relationship_type == 'enemy': color = '#d00e00'
        elif rel.relationship_type == 'nemesis': color = '#450a0a'
        elif rel.relationship_type == 'rival': color = '#f97316'
        elif rel.relationship_type == 'ally': color = '#10b981'
        elif rel.relationship_type == 'friend': color = '#0ea5e9'
        elif rel.relationship_type == 'mentor': color = '#f5b60b'
        elif rel.relationship_type == 'protege': color = '#22d3ee'
        elif rel.relationship_type == 'family': color = '#8b5cf6'
        elif rel.relationship_type == 'professional': color = '#475569'
        elif rel.relationship_type == 'acquaintance': color = '#2dd4bf'
        elif rel.relationship_type == 'complicated': color = '#d946ef'
        
        edges.append({
            'id': rel.id,
            'from': rel.character_a.id,
            'to': rel.character_b.id,
            'label': rel.get_relationship_type_display(),
            'type_key': rel.relationship_type,
            'title': rel.description,
            'width': width,
            'color': color,
            'strength': rel.strength,
            'trust_level': rel.trust_level,
            'power_dynamic': rel.power_dynamic,
            'status': rel.relationship_status,
            'visibility': rel.visibility,
            'conflict_source': rel.conflict_source,
            'character_a_wants': rel.character_a_wants,
            'character_b_wants': rel.character_b_wants,
            'evolution': rel.evolution,
            'shared_secret': rel.shared_secret,
            'first_impression': rel.first_impression,
            'vulnerability': rel.vulnerability,
            'major_shared_moments': rel.major_shared_moments,
            'predictability': rel.predictability,
            'arrows': 'to' # Or none if mutual
        })
        
    data = {
        'nodes': nodes,
        'edges': edges
    }
    return JsonResponse(data)


@login_required
@require_POST
def api_manage_relationship(request):
    """AJAX view to create, update, or delete relationships."""
    try:
        data = json.loads(request.body)
        rel_id = data.get('id')
        action = data.get('action', 'save') # 'save' or 'delete'

        if action == 'delete' and rel_id:
            rel = get_object_or_404(CharacterRelationship, id=rel_id, user=request.user)
            # Invalidate Cache on Delete
            RelationshipAnalysisCache.objects.filter(character_a=rel.character_a, character_b=rel.character_b).delete()
            rel.delete()
            return JsonResponse({'status': 'success', 'message': 'Relationship deleted'})

        # Handle Create/Update
        if rel_id:
            rel = get_object_or_404(CharacterRelationship, id=rel_id, user=request.user)
            form = CharacterRelationshipForm(data, instance=rel, user=request.user)
        else:
            form = CharacterRelationshipForm(data, user=request.user)

        if form.is_valid():
            rel = form.save(commit=False)
            rel.user = request.user
            rel.save()
            
            # Invalidate Cache on Save (Manual edits override AI suggestions)
            RelationshipAnalysisCache.objects.filter(character_a=rel.character_a, character_b=rel.character_b).delete()
            
            return JsonResponse({
                'status': 'success', 
                'message': 'Relationship saved',
                'id': rel.id
            })
        else:
            print(f"Relationship Save Form Errors: {form.errors}")
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

    except Exception as e:
        print(f"Relationship Save API Exception: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ============== Helper Functions ==============

def get_file_word_count(file):
    """Calculate word count from an uploaded file (.docx or .txt)."""
    text = extract_text_from_file(file)
    if text:
        return len(text.split())
    return 0

def extract_text_from_file(file):
    """Extract string content from .docx, .txt, or .epub files, preserving paragraph spacing and styling."""
    filename = file.name.lower()
    text = ""
    try:
        if filename.endswith('.docx'):
            try:
                from docx import Document
                file.seek(0)
                doc = Document(file)
                paragraphs = []
                for para in doc.paragraphs:
                    para_text = para.text.strip()
                    if not para_text:
                        # Preserve blank lines (scene breaks / spacing)
                        paragraphs.append('')
                        continue
                    
                    # Check for heading styles
                    style_name = para.style.name.lower() if para.style else ''
                    if 'heading' in style_name or 'title' in style_name:
                        para_text = f'**{para_text}**'
                    
                    paragraphs.append(para_text)
                
                text = '\n\n'.join(paragraphs)
            except ImportError:
                # Fall back to docx2txt if python-docx not available
                file.seek(0)
                text = docx2txt.process(file)
        elif filename.endswith('.txt'):
            file.seek(0)
            raw = file.read()
            if isinstance(raw, bytes):
                text = raw.decode('utf-8', errors='ignore')
            else:
                text = raw
        elif filename.endswith('.epub'):
            # Create a temporary file to store the EPUB content
            # since EbookLib.epub.read_epub often requires a real file path
            fd, tmp_path = tempfile.mkstemp(suffix='.epub')
            try:
                with os.fdopen(fd, 'wb') as tmp:
                    file.seek(0)
                    tmp.write(file.read())
                
                book = epub.read_epub(tmp_path)
                chapters = []
                
                # Iterate through items, look for documents
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        # Parse HTML content
                        content = item.get_content()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Get clean text with double newlines for paragraphs
                        chapter_content = soup.get_text(separator='\n\n').strip()
                        if chapter_content:
                            chapters.append(chapter_content)
                
                text = '\n\n'.join(chapters)
            except Exception as epub_error:
                print(f"EPUB processing error: {epub_error}")
                text = ""
            finally:
                # Always clean up the temporary file
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except:
                        pass
    except Exception as e:
        print(f"Error processing file: {e}")
    return text

def _call_ai_json(prompt, system_message="You are a professional literary analyst. Always respond with valid JSON.", max_retries=3, deepseek_model="deepseek-chat", prefer_gemini=False):
    """Helper to call AI and return parsed JSON with retry logic."""
    if not settings.DEEPSEEK_API_KEY and not settings.GEMINI_API_KEY:
        return None
    
    for attempt in range(max_retries):
        try:
            # Use Gemini if preferred or if DeepSeek key is missing
            # BUT if deepseek_model is 'deepseek-reasoner', we override prefer_gemini
            should_use_gemini = (prefer_gemini and settings.GEMINI_API_KEY) or not settings.DEEPSEEK_API_KEY
            if deepseek_model == 'deepseek-reasoner':
                should_use_gemini = False if settings.DEEPSEEK_API_KEY else True

            if should_use_gemini:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                # If we were forced to Gemini but wanted reasoner, use pro
                model_name = 'gemini-1.5-pro' if deepseek_model == 'deepseek-reasoner' else 'gemini-1.5-flash'
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(f"{system_message}\n\nTask:\n{prompt}")
                content = response.text
            else:
                client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
                response = client.chat.completions.create(
                    model=deepseek_model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt},
                    ],
                    stream=False,
                    timeout=60
                )
                content = response.choices[0].message.content

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return json.loads(content)
        except Exception as e:
            print(f"AI Call Error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
            else:
                return None

def analyze_characters_with_ai(text):
    """Initial pass to identify characters and roles from a large chunk of text."""
    prompt = f"""
    Identify all significant characters in the following text. 
    IMPORTANT: Characters may be referred to by multiple names, titles, or family terms 
    (e.g. "Mum", "Sarah", "Mrs. Smith" might all be the same person). 
    Merge these into a SINGLE character entry and list all alternate names as aliases.
    
    IMPORTANT: Use British English (UK English) for all spelling and grammar.
    
    For each character, provide:
    - Name (use their most common/full name as the primary name)
    - Aliases (list of OTHER names they go by: nicknames, titles, family terms like "Mum", "Dad", etc.)
    - Role (protagonist, antagonist, or supporting)
    - Description: Write a DETAILED multi-paragraph description covering their physical appearance, 
      personality, background, and significance to the story. Be thorough and specific.
    - Motivation: What fundamentally drives this character? Their deepest desires, fears, and internal conflicts.
    - Goals: Their specific short-term and long-term objectives in the story.
    - Personality traits and quirks
    - first_chapter: The chapter number where this character FIRST appears or is first mentioned

    Return ONLY a JSON object:
    {{
      "characters": [
        {{ 
          "name": "Sarah Smith", 
          "aliases": ["Mum", "Mrs. Smith"], 
          "role": "protagonist", 
          "description": "A detailed multi-paragraph description...", 
          "motivation": "What drives this character...",
          "goals": "Their objectives...", 
          "traits": "Key personality traits...",
          "first_chapter": 1
        }}
      ]
    }}

    Text Content:
    {text}
    """
    return _call_ai_json(prompt, deepseek_model="deepseek-reasoner")

def analyze_book_content_batch_with_ai(text):
    """Analyze a batch of chapters to extract summaries and events."""
    prompt = f"""
    Analyze the following chapters and extract:
    1. Chapter details (number, title, summary)
    2. Key Events (title, summary, pov_character, tone, beat, tension level 1-10, involved characters)

    The events MUST be linked to a specific chapter_number.

    Return ONLY a JSON object:
    {{
      "chapters": [
        {{ "number": 1, "title": "...", "summary": "..." }}
      ],
      "events": [
        {{ 
          "chapter_number": 1, 
          "title": "...", 
          "summary": "...", 
          "pov_character": "...", 
          "tone": "...", 
          "beat": "...", 
          "tension": 7, 
          "involved_characters": ["Name1", "Name2"] 
        }}
      ]
    }}

    Text Content:
    {text}
    """
    return _call_ai_json(prompt, deepseek_model="deepseek-reasoner")

def analyze_book_content_with_ai(text):
    """Legacy compatibility: calls the batch analyzer for a single block."""
    return analyze_book_content_batch_with_ai(text)


# ============== AI Scene Outline ==============

@login_required
@require_POST
def api_scene_outline(request, pk):
    """Generate an AI scene outline for a chapter."""
    chapter = get_object_or_404(Chapter, pk=pk, book__user=request.user)
    
    # Gather context
    events = chapter.events.all().order_by('sequence_order')
    characters = set()
    for ev in events:
        for c in ev.characters.all():
            characters.add(c.name)
        if ev.pov_character:
            characters.add(ev.pov_character.name)
    
    context_parts = [f"Book: {chapter.book.title}", f"Chapter {chapter.chapter_number}: {chapter.title}"]
    if chapter.description:
        context_parts.append(f"Summary: {chapter.description}")
    if chapter.content:
        context_parts.append(f"Content (first 5000 chars): {chapter.content[:5000]}")
    if characters:
        context_parts.append(f"Characters present: {', '.join(characters)}")
    if events.exists():
        event_list = [f"- {e.title}: {e.description[:100]}" for e in events[:20]]
        context_parts.append("Events:\n" + "\n".join(event_list))
    
    prompt = "\n".join(context_parts) + """

Based on the above chapter information, generate a detailed scene outline. Return valid JSON with this structure:
{
    "scenes": [
        {
            "scene_number": 1,
            "title": "Scene title",
            "setting": "Where/when this scene takes place",
            "characters": ["Character names involved"],
            "objective": "What this scene accomplishes for the story",
            "beats": ["Beat 1: description", "Beat 2: description"],
            "emotional_arc": "How the emotional tone shifts in this scene",
            "tension_level": 5
        }
    ],
    "pacing_notes": "Overall chapter pacing advice",
    "chapter_arc": "How this chapter contributes to the larger story arc"
}
Generate 3-6 scenes depending on chapter complexity."""

    data = _call_ai_json(prompt, system_message="You are a professional story structure analyst. Generate detailed scene outlines. Always respond with valid JSON.")
    
    if data:
        return JsonResponse({'status': 'success', 'outline': data})
    return JsonResponse({'status': 'error', 'message': 'AI could not generate an outline. Please try again.'})


@login_required
@require_POST
def api_chapter_summary(request, pk):
    """Generate an AI summary for a chapter from its content."""
    chapter = get_object_or_404(Chapter, pk=pk, book__user=request.user)
    
    if not chapter.content:
        return JsonResponse({'status': 'error', 'message': 'No chapter content available to summarize.'})
    
    prompt = f"""
    Write a concise but comprehensive summary of the following chapter from a novel.
    The summary should capture the key plot points, character developments, 
    and any important revelations or turning points.
    Write 2-4 separate paragraphs.
    
    IMPORTANT: Use British English (UK English) for all spelling, grammar, and formatting 
    (e.g. "colour" not "color", "realise" not "realize", "travelled" not "traveled").

    Book: {chapter.book.title}
    Chapter {chapter.chapter_number}: {chapter.title}

    Chapter Content:
    {chapter.content[:15000]}

    Return ONLY a JSON object with paragraphs as a list:
    {{
        "paragraphs": [
            "First paragraph of the summary...",
            "Second paragraph of the summary...",
            "Third paragraph of the summary..."
        ]
    }}
    """
    
    data = _call_ai_json(prompt, system_message="You are a professional literary analyst. Write clear, engaging chapter summaries in British English. Always respond with valid JSON.")
    
    if data and data.get('paragraphs'):
        summary_text = '\n\n'.join(data['paragraphs'])
        chapter.description = summary_text
        chapter.save()
        return JsonResponse({'status': 'success', 'summary': summary_text})
    # Fallback: handle old format where summary is a single string
    if data and data.get('summary'):
        chapter.description = data['summary']
        chapter.save()
        return JsonResponse({'status': 'success', 'summary': data['summary']})
    return JsonResponse({'status': 'error', 'message': 'AI could not generate a summary. Please try again.'})


# ============== Chapter Views ==============

@login_required
def chapter_list(request):
    """View to list all chapters grouped by book."""
    books = Book.objects.filter(user=request.user).prefetch_related('chapters').order_by('-series_order')
    return render(request, 'timeline/chapter_list.html', {'books': books})


@login_required
def chapter_create(request, book_pk):
    """Create a new chapter in a book."""
    book = get_object_or_404(Book, pk=book_pk, user=request.user)
    if request.method == 'POST':
        form = ChapterForm(request.POST, request.FILES)
        if form.is_valid():
            chapter = form.save(commit=False)
            chapter.book = book
            
            # Auto-calculate word count
            if 'chapter_file' in request.FILES:
                chapter.word_count = get_file_word_count(request.FILES['chapter_file'])
            elif chapter.content:
                # Calculate word count from pasted content
                chapter.word_count = len(chapter.content.split())
            
            chapter.save()
            messages.success(request, f'Chapter "{chapter.title}" created successfully! (Word count: {chapter.word_count})')
            return redirect('book_detail', pk=book.pk)
    else:
        # Auto-suggest next chapter number
        last_chapter = book.chapters.order_by('-chapter_number').first()
        initial_chapter_number = (last_chapter.chapter_number + 1) if last_chapter else 1
        form = ChapterForm(initial={'chapter_number': initial_chapter_number})
    
    return render(request, 'timeline/chapter_form.html', {
        'form': form,
        'book': book,
        'action': 'Create'
    })


@login_required
def chapter_detail(request, pk):
    """View a single chapter's content."""
    chapter = get_object_or_404(Chapter, pk=pk, book__user=request.user)
    events = chapter.events.all().order_by('sequence_order')
    # Get all characters who appear in this chapter's events
    chapter_characters = Character.objects.filter(
        events__chapter=chapter
    ).distinct().order_by('name')
    return render(request, 'timeline/chapter_detail.html', {
        'chapter': chapter,
        'events': events,
        'chapter_characters': chapter_characters,
    })


@login_required
def chapter_edit(request, pk):
    """Edit an existing chapter."""
    chapter = get_object_or_404(Chapter, pk=pk, book__user=request.user)
    if request.method == 'POST':
        form = ChapterForm(request.POST, request.FILES, instance=chapter)
        if form.is_valid():
            # Update word count
            if 'chapter_file' in request.FILES:
                chapter.word_count = get_file_word_count(request.FILES['chapter_file'])
            elif 'content' in form.changed_data and chapter.content:
                chapter.word_count = len(chapter.content.split())
            
            form.save()
            messages.success(request, f'Chapter "{chapter.title}" updated successfully! (Word count: {chapter.word_count})')
            return redirect('book_detail', pk=chapter.book.pk)
    else:
        form = ChapterForm(instance=chapter)
    
    return render(request, 'timeline/chapter_form.html', {
        'form': form,
        'chapter': chapter,
        'book': chapter.book,
        'action': 'Edit'
    })


@login_required
def chapter_delete(request, pk):
    """Delete a chapter."""
    chapter = get_object_or_404(Chapter, pk=pk, book__user=request.user)
    book = chapter.book
    if request.method == 'POST':
        chapter_title = chapter.title
        chapter.delete()
        messages.success(request, f'Chapter "{chapter_title}" deleted successfully!')
        return redirect('book_detail', pk=book.pk)
    return render(request, 'timeline/chapter_confirm_delete.html', {'chapter': chapter})


@login_required
def chapter_bulk_upload(request, book_pk):
    """Bulk upload multiple chapter files."""
    book = get_object_or_404(Book, pk=book_pk, user=request.user)
    
    if request.method == 'POST':
        files = request.FILES.getlist('chapter_files')
        if not files:
            messages.error(request, 'No files were selected.')
            return redirect('chapter_bulk_upload', book_pk=book.pk)
            
        # Get starting chapter number
        last_chapter = book.chapters.order_by('-chapter_number').first()
        current_number = (last_chapter.chapter_number + 1) if last_chapter else 1
        
        chapters_created = 0
        for f in files:
            # Clean up filename for title
            filename = os.path.splitext(f.name)[0]
            title = filename.replace('_', ' ').replace('-', ' ').title()
            
            # Create chapter
            chapter = Chapter(
                book=book,
                chapter_number=current_number,
                title=title,
                chapter_file=f
            )
            
            # Calculate word count
            chapter.word_count = get_file_word_count(f)
            chapter.save()
            
            current_number += 1
            chapters_created += 1
            
        messages.success(request, f'Successfully uploaded {chapters_created} chapters!')
        return redirect('book_detail', pk=book.pk)
        
    # Get starting chapter number for the "Paste" tab
    last_chapter = book.chapters.order_by('-chapter_number').first()
    next_chapter_number = (last_chapter.chapter_number + 1) if last_chapter else 1
    
    return render(request, 'timeline/chapter_bulk_upload.html', {
        'book': book,
        'next_chapter_number': next_chapter_number
    })


# ============== Character Views ==============

@login_required
def character_list(request):
    """List all characters."""
    characters = Character.objects.filter(user=request.user).annotate(
        event_count=Count('events')
    )
    return render(request, 'timeline/character_list.html', {'characters': characters})


@login_required
def character_detail(request, pk):
    """Detail view for a single character."""
    character = get_object_or_404(Character, pk=pk, user=request.user)
    events = character.events.all().order_by('sequence_order')
    pov_events = character.pov_events.all().order_by('sequence_order')
    
    context = {
        'character': character,
        'events': events,
        'pov_events': pov_events,
    }
    return render(request, 'timeline/character_detail.html', context)


@login_required
def character_create(request):
    """Create a new character."""
    if request.method == 'POST':
        form = CharacterForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            character = form.save(commit=False)
            character.user = request.user
            character.save()
            messages.success(request, f'Character "{character.name}" created successfully!')
            return redirect('character_detail', pk=character.pk)
    else:
        form = CharacterForm(user=request.user)
    return render(request, 'timeline/character_form.html', {'form': form, 'action': 'Create'})


@login_required
def character_edit(request, pk):
    """Edit an existing character."""
    character = get_object_or_404(Character, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CharacterForm(request.POST, request.FILES, instance=character, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Character "{character.name}" updated successfully!')
            return redirect('character_detail', pk=character.pk)
    else:
        form = CharacterForm(instance=character, user=request.user)
    return render(request, 'timeline/character_form.html', {
        'form': form,
        'action': 'Edit',
        'character': character
    })


@login_required
def character_delete(request, pk):
    """Delete a character."""
    character = get_object_or_404(Character, pk=pk, user=request.user)
    if request.method == 'POST':
        character_name = character.name
        character.delete()
        messages.success(request, f'Character "{character_name}" deleted successfully!')
        return redirect('character_list')
    return render(request, 'timeline/character_confirm_delete.html', {'character': character})


# ============== Event/Timeline Views ==============

@login_required
def timeline_view(request):
    """Main timeline view showing all events."""
    events = Event.objects.filter(user=request.user).select_related(
        'book', 'chapter', 'pov_character'
    ).prefetch_related('characters', 'tags').order_by('sequence_order')
    
    # Get filter options
    books = Book.objects.filter(user=request.user)
    characters = Character.objects.filter(user=request.user)
    tags = Tag.objects.filter(user=request.user)
    
    # Apply filters if present
    book_filter = request.GET.get('book')
    character_filter = request.GET.get('character')
    tag_filter = request.GET.get('tag')
    
    if book_filter:
        events = events.filter(book_id=book_filter)
    if character_filter:
        events = events.filter(Q(characters__id=character_filter) | Q(pov_character_id=character_filter)).distinct()
    if tag_filter:
        events = events.filter(tags__id=tag_filter)
    
    context = {
        'events': events,
        'books': books,
        'characters': characters,
        'tags': tags,
        'active_book': book_filter,
        'active_character': character_filter,
        'active_tag': tag_filter,
    }
    return render(request, 'timeline/timeline_view.html', context)


@login_required
def event_detail(request, pk):
    """Detail view for a single event."""
    event = get_object_or_404(Event, pk=pk, user=request.user)
    return render(request, 'timeline/event_detail.html', {'event': event})


@login_required
def event_create(request):
    """Create a new event."""
    if request.method == 'POST':
        form = EventForm(request.POST, user=request.user)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user
            
            # Auto-assign sequence_order if not provided
            if event.sequence_order == 0:
                last_event = Event.objects.filter(user=request.user).order_by('-sequence_order').first()
                event.sequence_order = (last_event.sequence_order + 1) if last_event else 1
            
            event.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, f'Event "{event.title}" created successfully!')
            return redirect('timeline_view')
    else:
        # Auto-suggest next sequence order
        last_event = Event.objects.filter(user=request.user).order_by('-sequence_order').first()
        initial_sequence = (last_event.sequence_order + 1) if last_event else 1
        form = EventForm(user=request.user, initial={'sequence_order': initial_sequence})
    
    return render(request, 'timeline/event_form.html', {'form': form, 'action': 'Create'})


@login_required
def event_edit(request, pk):
    """Edit an existing event."""
    event = get_object_or_404(Event, pk=pk, user=request.user)
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Event "{event.title}" updated successfully!')
            return redirect('event_detail', pk=event.pk)
    else:
        form = EventForm(instance=event, user=request.user)
    
    return render(request, 'timeline/event_form.html', {
        'form': form,
        'action': 'Edit',
        'event': event
    })


@login_required
def event_delete(request, pk):
    """Delete an event."""
    event = get_object_or_404(Event, pk=pk, user=request.user)
    if request.method == 'POST':
        event_title = event.title
        event.delete()
        messages.success(request, f'Event "{event_title}" deleted successfully!')
        return redirect('timeline_view')
    return render(request, 'timeline/event_confirm_delete.html', {'event': event})


@login_required
def event_reorder(request, pk):
    """Manually reorder an event (move up or down)."""
    event = get_object_or_404(Event, pk=pk, user=request.user)
    direction = request.GET.get('direction', 'up')
    
    if direction == 'up' and event.sequence_order > 1:
        event.sequence_order -= 1
        event.save()
    elif direction == 'down':
        event.sequence_order += 1
        event.save()
    
    return redirect('timeline_view')


# ============== Tag Views ==============

@login_required
def tag_list(request):
    """List all tags."""
    tags = Tag.objects.filter(user=request.user).annotate(
        event_count=Count('events')
    )
    return render(request, 'timeline/tag_list.html', {'tags': tags})


@login_required
def tag_create(request):
    """Create a new tag."""
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            tag = form.save(commit=False)
            tag.user = request.user
            tag.save()
            messages.success(request, f'Tag "{tag.name}" created successfully!')
            return redirect('tag_list')
    else:
        form = TagForm()
    return render(request, 'timeline/tag_form.html', {'form': form, 'action': 'Create'})


@login_required
def tag_edit(request, pk):
    """Edit an existing tag."""
    tag = get_object_or_404(Tag, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            messages.success(request, f'Tag "{tag.name}" updated successfully!')
            return redirect('tag_list')
    else:
        form = TagForm(instance=tag)
    return render(request, 'timeline/tag_form.html', {'form': form, 'action': 'Edit', 'tag': tag})


@login_required
def tag_delete(request, pk):
    """Delete a tag."""
    tag = get_object_or_404(Tag, pk=pk, user=request.user)
    if request.method == 'POST':
        tag_name = tag.name
        tag.delete()
        messages.success(request, f'Tag "{tag_name}" deleted successfully!')
        return redirect('tag_list')
    return render(request, 'timeline/tag_confirm_delete.html', {'tag': tag})


# ============== API Views (for AJAX/JavaScript) ==============

@login_required
@require_POST
def api_event_reorder(request):
    """API endpoint for reordering events via drag-and-drop (AJAX)."""
    try:
        data = json.loads(request.body)
        event_id = data.get('event_id')
        new_order = data.get('new_order')
        
        event = Event.objects.get(pk=event_id, user=request.user)
        event.sequence_order = new_order
        event.save()
        
        return JsonResponse({'status': 'success', 'message': 'Event reordered successfully'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def api_ai_consultant(request):
    """
    API endpoint for the Story Consultant.
    Pulls story context and sends it to DeepSeek (primary) or Gemini.
    """
    if not settings.DEEPSEEK_API_KEY and not settings.GEMINI_API_KEY:
        return JsonResponse({
            'status': 'error', 
            'message': 'Consultant features are not configured (Missing API Key).'
        }, status=503)

    try:
        data = json.loads(request.body)
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return JsonResponse({'status': 'error', 'message': 'No query provided'}, status=400)

        # 1. Build Story Context using Smart Resolver
        resolver = ContextResolver(request.user)
        
        # We can also try to find the "active scene" content if provided in the payload, 
        # otherwise just use the query.
        scene_content = data.get('scene_content', '')
        
        relevant_context = resolver.get_context_for_query(user_query, scene_content)
        
        context = "You are a professional Story Consultant. "
        context += "Here is the relevant context from the user's story bible (Characters, Locations, Lore, Relationships, and Deep Analysis):\n"
        context += relevant_context
        
        context += f"\n\nUSER QUESTION: {user_query}\n"
        context += "\nINSTRUCTIONS: Provide creative, helpful, and insightful feedback based ONLY on the provided context. "
        context += "Synthesise the 'Deep Insights' (which contain AI-reasoned character dynamics and scene summaries) with the basic 'Character Profiles' to give a nuanced answer. "
        context += "If the answer is not in the context, say you don't know rather than inventing new characters or facts. "
        context += "Do NOT hallucinate names or backstories. "
        context += "Use UK English spelling and grammar (e.g., 'colour', 'organise', 'centre')."

        # 2. Call AI Provider
        if settings.DEEPSEEK_API_KEY:
            client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a professional Story Consultant."},
                    {"role": "user", "content": context},
                ],
                stream=False
            )
            ai_response = response.choices[0].message.content
        else:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-3-flash-preview')
            response = model.generate_content(context)
            ai_response = response.text

        return JsonResponse({
            'status': 'success', 
            'response': ai_response
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def api_character_deep_dive(request):
    """Generate a deep-dive writing prompt for a character."""
    try:
        data = json.loads(request.body)
        char_id = data.get('character_id')
        character = get_object_or_404(Character, id=char_id, user=request.user)

        prompt = f"""
        You are a professional Creative Writing Coach.
        The user wants to do a "Deep Dive" into their character: {character.name}.
        
        CHARACTER DETAILS:\r\n        Role: {character.get_role_display()}\r\n        Description: {character.description}\r\n        Motivation: {character.motivation}\r\n        Goals: {character.goals}\r\n        Traits: {character.traits}\r\n        \r\n        Please generate ONE thought-provoking, insightful deep-dive question or writing prompt that will help the author understand this character's internal world or backstory better. \r\n        Focus on emotion, conflict, or hidden secrets. \r\n        Keep it to a single paragraph. \r\n        Use UK English spelling and grammar (e.g., 'colour', 'behaviour', 'authorised').\r\n        """

        # Call AI Provider
        if settings.DEEPSEEK_API_KEY:
            client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a professional Creative Writing Coach."},
                    {"role": "user", "content": prompt},
                ],
                stream=False
            )
            ai_response = response.choices[0].message.content
        else:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-3-flash-preview')
            response = model.generate_content(prompt)
            ai_response = response.text

        # Save to database
        character.deep_dive_notes = ai_response
        character.save()

        return JsonResponse({
            'status': 'success', 
            'response': ai_response
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def api_sync_character_data(request):
    """
    Manually sync/fill missing character fields using AI context from books/chapters.
    """
    try:
        data = json.loads(request.body)
        char_id = data.get('character_id')
        character = get_object_or_404(Character, id=char_id, user=request.user)
        
        # Gather context: Check for introduction book content or event descriptions
        context_text = ""
        
        # 1. Look at introduction book first (best source for character foundation)
        if character.introduction_book:
            book = character.introduction_book
            # Get first 3 chapters or first 50k characters
            intro_chapters = book.chapters.all().order_by('chapter_number')[:3]
            for ch in intro_chapters:
                if ch.content:
                    context_text += f"\nChapter {ch.chapter_number} ({ch.title}):\n{ch.content[:20000]}\n"
        
        # 2. Add snippets from events where they appear (for more nuanced character growth)
        events = character.events.all().order_by('sequence_order')[:5]
        for event in events:
            if event.description:
                context_text += f"\nEvent: {event.title}\n{event.description}\n"
        
        if not context_text.strip():
            return JsonResponse({
                'status': 'error', 
                'message': 'No book content or event descriptions found for this character to sync from.'
            }, status=400)
            
        # Truncate context to safe limits (reduced for speed)
        context_text = context_text[:40000]
        
        # Use the targeted analysis function for speed and accuracy
        print(f"DEBUG: Calling AI for {character.name}")
        match = analyze_single_character_with_ai(character.name, context_text)
        print(f"DEBUG: AI match completed for {character.name}")
        
        if not match:
            return JsonResponse({
                'status': 'error', 
                'message': f'AI could not extract data for "{character.name}".'
            }, status=500)
            
        # Update ONLY empty fields
        updated_fields = []
        if not character.description and match.get('description'):
            character.description = match['description']
            updated_fields.append('description')
        if not character.motivation and match.get('motivation'):
            character.motivation = match['motivation']
            updated_fields.append('motivation')
        if not character.goals and match.get('goals'):
            character.goals = match['goals']
            updated_fields.append('goals')
        if not character.traits and match.get('traits'):
            character.traits = match['traits']
            updated_fields.append('traits')
            
        if updated_fields:
            character.save()
            return JsonResponse({
                'status': 'success',
                'updated_fields': updated_fields,
                'data': {
                    'description': character.description,
                    'motivation': character.motivation,
                    'goals': character.goals,
                    'personality_traits': character.traits
                }
            })
        else:
            return JsonResponse({
                'status': 'success',
                'message': 'All fields are already populated. Nothing to sync.',
                'updated_fields': []
            })
            
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ============== World Builder Wiki Views ==============

@login_required
def world_list(request):
    """List all world-building entries, with optional category filter."""
    category = request.GET.get('category', '')
    entries = WorldEntry.objects.filter(user=request.user)
    if category:
        entries = entries.filter(category=category)
    
    categories = WorldEntry.CATEGORY_CHOICES
    return render(request, 'timeline/world_list.html', {
        'entries': entries,
        'categories': categories,
        'active_category': category,
    })


@login_required
def world_create(request):
    """Create a new world-building entry."""
    if request.method == 'POST':
        form = WorldEntryForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()
            messages.success(request, f"Created world entry: {entry.title}")
            return redirect('world_detail', pk=entry.pk)
    else:
        form = WorldEntryForm(user=request.user)
    return render(request, 'timeline/world_form.html', {'form': form, 'is_edit': False})


@login_required
def world_detail(request, pk):
    """View a single world-building entry."""
    entry = get_object_or_404(WorldEntry, pk=pk, user=request.user)
    return render(request, 'timeline/world_detail.html', {'entry': entry})


@login_required
def world_edit(request, pk):
    """Edit an existing world-building entry."""
    entry = get_object_or_404(WorldEntry, pk=pk, user=request.user)
    if request.method == 'POST':
        form = WorldEntryForm(request.POST, request.FILES, instance=entry, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated: {entry.title}")
            return redirect('world_detail', pk=entry.pk)
    else:
        form = WorldEntryForm(instance=entry, user=request.user)
    return render(request, 'timeline/world_form.html', {'form': form, 'is_edit': True, 'entry': entry})


@login_required
def world_delete(request, pk):
    """Delete a world-building entry."""
    entry = get_object_or_404(WorldEntry, pk=pk, user=request.user)
    if request.method == 'POST':
        title = entry.title
        entry.delete()
        messages.success(request, f"Deleted: {title}")
        return redirect('world_list')
    return render(request, 'timeline/world_delete.html', {'entry': entry})


def analyze_single_character_with_ai(character_name, text):
    """Targeted pass to extract details for a specific character from context."""
    print(f"DEBUG: Syncing character {character_name}")
    prompt = f"""
    Analyze the story content below and extract specific details for the character: "{character_name}".
    
    IMPORTANT: Use British English (UK English) for all spelling and grammar.
    
    Provide the following fields based ONLY on the story content:
    - description: A detailed multi-paragraph description covering physical appearance, personality, and background.
    - motivation: What drives this character? Their desires, fears, and internal conflicts.
    - goals: Their specific objectives in the story.
    - traits: Key personality traits and quirks.

    Return ONLY a JSON object:
    {{
      "description": "...",
      "motivation": "...",
      "goals": "...",
      "traits": "..."
    }}

    If a field cannot be determined from the text, return an empty string for that field.

    Story Content:
    {text}
    """
    # Use deepseek-chat for speed; it's excellent at extraction.
    return _call_ai_json(prompt, deepseek_model="deepseek-chat")


@login_required
def horizontal_timeline(request):
    """
    Displays events in a linear, horizontally scrollable timeline.
    Supports 'mode' parameter for Chronological vs Narrative order.
    """
    mode = request.GET.get('mode', 'chronological')
    events = Event.objects.filter(user=request.user)
    
    if mode == 'narrative':
        # Sort by explicit narrative order, fallback to sequence order
        events = events.order_by('narrative_order', 'sequence_order')
    else:
        # Default: Chronological
        # Logic: 
        # 1. Exact dates first? Or mixed with fuzzy?
        # We start by standardizing on new date fields if possible
        # For now, let's trust the 'chronological_order' int field as a primary sort
        # But ideally we want to sort by the actual date if available
        # combining DB sorting with Python sorting might be needed for complex relative dates
         events = events.order_by('chronological_order', 'sequence_order')

    context = {
        'events': events,
        'mode': mode,
    }
    return render(request, 'timeline/horizontal_timeline.html', context)


@login_required
def relationship_map(request):
    """
    Renders the relationship visualization page.
    """
    characters = Character.objects.filter(user=request.user)
    return render(request, 'timeline/relationship_map.html', {'characters': characters})


@login_required
def api_relationship_data(request):
    """
    Returns JSON data for the Vis.js network graph.
    Nodes = Characters
    Edges = Relationships
    """
    characters = Character.objects.filter(user=request.user)
    relationships = CharacterRelationship.objects.filter(user=request.user)
    
    nodes = []
    for char in characters:
        node = {
            'id': char.id,
            'label': char.name,
            'group': char.role, 
            'color': char.color_code or '#97c2fc',
            'description': char.description[:100] + '...' if char.description else '',
            'profile_pic_url': char.profile_pic_url
        }
        
        if char.profile_pic_url:
            node['shape'] = 'circularImage'
            node['image'] = char.profile_pic_url
            node['brokenImage'] = 'https://via.placeholder.com/50' # Fallback
            node['size'] = 30
        else:
             node['shape'] = 'dot'
             
        nodes.append(node)
        
    edges = []
    
    # Color mapping matching the front-end legend
    REL_COLORS = {
        'friend': '#3b82f6',      # Blue
        'ally': '#10b981',        # Green
        'enemy': '#b91c1c',       # Dark Red
        'romantic': '#f43f5e',    # Pink/Rose
        'family': '#8b5cf6',      # Purple
        'professional': '#64748b',# Slate
        'rival': '#f97316',       # Orange
        'mentor': '#eab308',      # Yellow
        'neutral': '#9ca3af',     # Gray
    }
    
    for rel in relationships:
        color = REL_COLORS.get(rel.relationship_type, '#9ca3af')
        
        edges.append({
            'id': rel.id,
            'from': rel.character_a.id,
            'to': rel.character_b.id,
            'label': rel.get_relationship_type_display(),
            'title': rel.description, # tooltip
            'width': rel.strength / 2, # scale 1-10 to 0.5-5 width
            'color': {'color': color, 'highlight': color},
            'type_key': rel.relationship_type,
            'strength': rel.strength,
            'trust_level': rel.trust_level,
            'power_dynamic': rel.power_dynamic,
            'evolution': rel.evolution,
            'status': rel.relationship_status,
            'visibility': rel.visibility,
            'conflict_source': rel.conflict_source,
            'character_a_wants': rel.character_a_wants,
            'character_b_wants': rel.character_b_wants,
            'first_impression': rel.first_impression,
            'shared_secret': rel.shared_secret,
            'vulnerability': rel.vulnerability,
            'major_shared_moments': rel.major_shared_moments,
            'predictability': rel.predictability
        })
        
    return JsonResponse({'nodes': nodes, 'edges': edges})


@login_required
@require_POST
def api_manage_relationship(request):
    """
    AJAX Endpoint to Create, Update, or Delete a relationship.
    """
    try:
        data = json.loads(request.body)
        action = data.get('action')
        rel_id = data.get('id')
        
        if action == 'delete':
            rel = get_object_or_404(CharacterRelationship, pk=rel_id, user=request.user)
            rel.delete()
            return JsonResponse({'status': 'success', 'message': 'Relationship deleted'})
            
        elif action == 'save':
            char_a_id = data.get('character_a')
            char_b_id = data.get('character_b')
            rel_type = data.get('relationship_type')
            desc = data.get('description', '')
            strength = int(data.get('strength', 5))
            trust = int(data.get('trust_level', 5))
            power = data.get('power_dynamic', 'balanced')
            evolution = data.get('evolution', '')
            status = data.get('relationship_status', 'active')
            visibility = data.get('visibility', 'public')
            conflict = data.get('conflict_source', '')
            a_wants = data.get('character_a_wants', '')
            b_wants = data.get('character_b_wants', '')
            
            if not (char_a_id and char_b_id and rel_type):
                 return JsonResponse({'status': 'error', 'message': 'Missing required fields'}, status=400)

            if rel_id:
                # Update existing
                rel = get_object_or_404(CharacterRelationship, pk=rel_id, user=request.user)
                rel.character_a_id = char_a_id
                rel.character_b_id = char_b_id
                rel.relationship_type = rel_type
                rel.description = desc
                rel.strength = strength
                rel.trust_level = trust
                rel.power_dynamic = power
                rel.evolution = evolution
                rel.relationship_status = status
                rel.visibility = visibility
                rel.conflict_source = conflict
                rel.character_a_wants = a_wants
                rel.character_b_wants = b_wants
                rel.first_impression = data.get('first_impression', rel.first_impression)
                rel.shared_secret = data.get('shared_secret', rel.shared_secret)
                rel.vulnerability = data.get('vulnerability', rel.vulnerability)
                rel.major_shared_moments = data.get('major_shared_moments', rel.major_shared_moments)
                rel.predictability = data.get('predictability', rel.predictability)
                rel.save()
            else:
                # Create new (check duplicates first)
                if CharacterRelationship.objects.filter(user=request.user, character_a_id=char_a_id, character_b_id=char_b_id).exists():
                     return JsonResponse({'status': 'error', 'message': 'Relationship already exists!'}, status=400)
                     
                rel = CharacterRelationship.objects.create(
                    user=request.user,
                    character_a_id=char_a_id,
                    character_b_id=char_b_id,
                    relationship_type=rel_type,
                    description=desc,
                    strength=strength,
                    trust_level=trust,
                    power_dynamic=power,
                    evolution=evolution,
                    relationship_status=status,
                    visibility=visibility,
                    conflict_source=conflict,
                    character_a_wants=a_wants,
                    character_b_wants=b_wants,
                    first_impression=data.get('first_impression', ''),
                    shared_secret=data.get('shared_secret', ''),
                    vulnerability=data.get('vulnerability', ''),
                    major_shared_moments=data.get('major_shared_moments', ''),
                    predictability=data.get('predictability', 5)
                )
                
            return JsonResponse({'status': 'success', 'id': rel.id})
            
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def api_suggest_relationship(request):
    """
    Analyzes shared scenes between two characters to suggest relationship details.
    """
    try:
        data = json.loads(request.body)
        char_a_id = data.get('character_a')
        char_b_id = data.get('character_b')
        
        if not (char_a_id and char_b_id):
             return JsonResponse({'status': 'error', 'message': 'Both characters are required.'}, status=400)
             
        char_a = get_object_or_404(Character, pk=char_a_id, user=request.user)
        char_b = get_object_or_404(Character, pk=char_b_id, user=request.user)
        
        # 0. Calculate Metadata Hashes for Invalidation
        char_a_data = f"{char_a.traits}|{char_a.motivation}|{char_a.role}"
        char_b_data = f"{char_b.traits}|{char_b.motivation}|{char_b.role}"
        h_a = hashlib.sha256(char_a_data.encode()).hexdigest()
        h_b = hashlib.sha256(char_b_data.encode()).hexdigest()

        # 1. Find shared events
        shared_events = Event.objects.filter(
            user=request.user, 
            characters=char_a
        ).filter(
            characters=char_b
        ).distinct()
        
        if not shared_events.exists():
             return JsonResponse({
                 'status': 'success', 
                 'suggestion': {
                     'type': 'neutral',
                     'description': 'No shared scenes found in the database yet.',
                     'strength': 1
                 }
             })

        # Order and Split events into 3 batches
        all_events = list(shared_events.order_by('chronological_order', 'sequence_order'))
        total_count = len(all_events)
        
        import math
        chunk_size = math.ceil(total_count / 3)
        batches = [all_events[i:i + chunk_size] for i in range(0, total_count, chunk_size)]
        
        # Calculate Batch Hashes to detect story changes
        batch_hashes = []
        batch_texts = []
        for batch in batches:
            batch_content = ""
            for event in batch:
                content = event.content_json or event.content_html or event.description or ""
                batch_content += f"{event.id}:{str(content)}|"
            batch_hashes.append(hashlib.sha256(batch_content.encode()).hexdigest())
            
            # Form full text for AI pass if needed
            full_text = ""
            for event in batch:
                content = event.content_json or event.content_html or event.description or ""
                full_text += f"\n--- SCENE: {event.title} ---\n{str(content)}\n"
            batch_texts.append(full_text)

        # Check Final Result Cache
        snapshots_hash = "|".join(batch_hashes)
        book = all_events[0].book if all_events[0].book else None
        
        cache_hit = RelationshipAnalysisCache.objects.filter(
            character_a=char_a, 
            character_b=char_b,
            char_a_metadata_hash=h_a,
            char_b_metadata_hash=h_b,
            interaction_snapshots_hash=snapshots_hash
        ).first()

        if cache_hit:
            return JsonResponse({'status': 'success', 'suggestion': cache_hit.full_json, 'cached': True})

        # 2. Process batches for intermediate "Interaction Snapshots" (with caching)
        interaction_summaries = []
        for idx in range(len(batches)):
            # Check intermediate cache
            summary_cache = InteractionSummaryCache.objects.filter(
                character_a=char_a,
                character_b=char_b,
                batch_index=idx,
                content_hash=batch_hashes[idx]
            ).first()

            if summary_cache:
                interaction_summaries.append(summary_cache.summary_text)
                continue

            summary_prompt = f"""
            Analyze this CHUNK OF STORY ({idx+1}/3) between {char_a.name} and {char_b.name}.
            Summarize their interactions, focusing on:
            1. Conflict/Tension shifts.
            2. Secrets or vulnerabilities shared.
            3. Any power dynamic changes (who is dominant).
            4. Significant character growth.
            
            Keep the summary to 300 words. Focus on SUBTEXT and specific data points.
            
            Return JSON ONLY:
            {{
                "summary": "..."
            }}

            STORY CONTENT:
            {batch_texts[idx]}
            """
            result = _call_ai_json(summary_prompt, system_message="Provide deep narrative summaries in JSON format.", deepseek_model="deepseek-reasoner")
            summary_text = result['summary'] if (result and 'summary' in result) else "Summary generation failed."
            interaction_summaries.append(summary_text)

            # Save to intermediate cache
            InteractionSummaryCache.objects.update_or_create(
                character_a=char_a,
                character_b=char_b,
                batch_index=idx,
                defaults={'summary_text': summary_text, 'content_hash': batch_hashes[idx], 'book': book}
            )

        # 3. Final Synthesis Pass (JSON Extraction)
        ai_response = _perform_relationship_analysis(char_a, char_b, book, interaction_summaries, snapshots_hash, h_a, h_b)
        
        return JsonResponse({'status': 'success', 'suggestion': ai_response})
        
        return JsonResponse({'status': 'success', 'suggestion': ai_response})

    except Exception as e:
        print(f"AI Suggest Error: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def export_story_bible(request, pk):
    """
    Export a book as a 'Story Bible' (printable HTML).
    Includes: Overview, Characters, Timeline, World Metadata.
    """
    book = get_object_or_404(Book, pk=pk, user=request.user)
    
    # Context Data
    characters = Character.objects.filter(user=request.user).order_by('role', 'name')
    # Filter characters that appear in this book if possible, but global list is often better for a bible
    
    # Events specific to this book (or all if not assigned?)
    # Let's show events linked to this book + unassigned ones if relevant? 
    # Usually just the book's events.
    events = Event.objects.filter(user=request.user, book=book).order_by('chronological_order', 'sequence_order')
    
    tags = Tag.objects.filter(user=request.user).order_by('category', 'name')
    
    context = {
        'book': book,
        'characters': characters,
        'events': events,
        'tags': tags,
        'now': timezone.now()
    }
    return render(request, 'timeline/story_bible_export.html', context)


@login_required
@require_POST
def api_trigger_deep_scan(request, book_id):
    """
    Triggers a background thread to perform a full book analysis 
    (Omniscience mode).
    """
    book = get_object_or_404(Book, pk=book_id, user=request.user)
    user_id = request.user.id
    
    # Reset or create scan status
    scan_status, created = StoryScanStatus.objects.get_or_create(book=book)
    
    # If it was stuck or failed, let them restart
    if not created and scan_status.status == 'running':
        # Check if it's actually been running too long (e.g. > 5 minutes)
        if (timezone.now() - scan_status.updated_at).total_seconds() < 300:
            return JsonResponse({'status': 'error', 'message': 'A scan is already in progress.'})

    scan_status.status = 'running'
    scan_status.progress_percentage = 0
    scan_status.current_step = 'Starting analysis engine...'
    scan_status.error_message = ""
    scan_status.save()

    # Clear old caches for this book to ensure upgrades take effect
    RelationshipAnalysisCache.objects.filter(book=book).delete()
    InteractionSummaryCache.objects.filter(book=book).delete()

    def run_deep_scan(u_id, b_id, status_id):
        try:
            user = User.objects.get(id=u_id)
            book = Book.objects.get(id=b_id)
            scan_status = StoryScanStatus.objects.get(id=status_id)
            
            # 1. Enrich Characters
            characters = Character.objects.filter(user=user)
            total_chars = characters.count()
            
            for idx, char in enumerate(characters):
                scan_status.current_step = f"Analyzing Profile: {char.name} ({idx+1}/{total_chars})..."
                scan_status.progress_percentage = int(5 + (idx / total_chars) * 15)
                scan_status.save()

                char_scenes = Event.objects.filter(book=book, characters=char).distinct().order_by('chronological_order')
                if char_scenes.exists():
                    scene_text = ""
                    for s in char_scenes[:5]:
                        content = s.content_json or s.content_html or s.description or ""
                        scene_text += f"\n--- SCENE: {s.title} ---\n{str(content)}\n"
                    
                    profile_prompt = f"Analyze Profile for {char.name}. JSON: {{\"traits\": \"...\", \"motivation\": \"...\"}}\n\nSCENES: {scene_text}"
                    res = _call_ai_json(profile_prompt, deepseek_model="deepseek-reasoner")
                    if res:
                        char.traits = res.get('traits', char.traits)
                        char.motivation = res.get('motivation', char.motivation)
                        char.save()
            
            # Step 1.5: Tag Recovery - Scan scenes for character mentions 
            # (Fixes the "Empty Map" issue where AI missed tags during import)
            scan_status.current_step = "Syncing Character Tags..."
            scan_status.progress_percentage = 20
            scan_status.save()
            
            all_chars = list(Character.objects.filter(user=user))
            book_events = Event.objects.filter(book=book)
            
            # Identify common surnames/words to avoid over-tagging (e.g. "Temple" in every name)
            from collections import Counter
            word_counts = Counter()
            for c in all_chars:
                word_counts.update([w.lower() for w in c.name.split() if len(w) > 2])
            common_words = {w for w, count in word_counts.items() if count > 2}
            
            for event in book_events:
                # Scan event-specific text PLUS the whole chapter text for context
                chapter_text = event.chapter.content if event.chapter else ""
                text_to_scan = (event.title or "") + " " + (event.description or "") + " " + chapter_text
                
                for char in all_chars:
                    names_to_check = [char.name]
                    if char.aliases:
                        names_to_check.extend([a.strip() for a in char.aliases.split(',') if a.strip()])
                    
                    name_parts = char.name.split()
                    if len(name_parts) > 1:
                        for part in name_parts:
                            low_part = part.lower()
                            # Skip common titles AND the common family surname
                            if len(part) > 2 and low_part not in ['mrs', 'mr', 'miss', 'dr', 'sir', 'lady'] and low_part not in common_words:
                                if not any(low_part == a.lower().strip() for a in names_to_check):
                                    names_to_check.append(part)
                    
                    # Use a regex with word boundaries for precise matching
                    pattern = r'\b(' + '|'.join(re.escape(name) for name in names_to_check) + r')\b'
                    if re.search(pattern, text_to_scan, re.IGNORECASE):
                        event.characters.add(char)

            # 2. Relationship Pre-Caching
            pairs = list(combinations(characters, 2))
            total_pairs = len(pairs)
            
            for idx, (char_a, char_b) in enumerate(pairs):
                shared = Event.objects.filter(book=book, characters=char_a).filter(characters=char_b).exists()
                if shared:
                    scan_status.current_step = f"Mapping Relationships: {char_a.name} & {char_b.name} ({idx+1}/{total_pairs})..."
                    scan_status.progress_percentage = int(20 + (idx / total_pairs) * 70)
                    scan_status.save()
                    _ensure_relationship_cache(char_a, char_b, book)
            
            # Step 3: Chapter Summaries (New)
            chapters = book.chapters.all()
            total_ch = chapters.count()
            for idx, chapter in enumerate(chapters):
                if not chapter.description:
                    scan_status.current_step = f"Summarizing Chapter {chapter.chapter_number} ({idx+1}/{total_ch})..."
                    scan_status.progress_percentage = int(90 + (idx / total_ch) * 10)
                    scan_status.save()
                    
                    # Core summary logic (simplified)
                    sum_prompt = f"Summarize Chapter {chapter.chapter_number}: {chapter.title}\nContent: {chapter.content[:5000]}"
                    sum_res = _call_ai_json(sum_prompt)
                    if sum_res and 'summary' in sum_res:
                        chapter.description = sum_res['summary']
                        chapter.save()

            scan_status.status = 'completed'
            scan_status.progress_percentage = 100
            scan_status.current_step = "Deep Scan Complete."
            book.last_deep_scan = timezone.now()
            book.save()
            scan_status.save()
            
        except Exception as e:
            s = StoryScanStatus.objects.get(id=status_id)
            s.status = 'failed'
            s.error_message = str(e)
            s.save()

    thread = threading.Thread(target=run_deep_scan, args=(user_id, book.id, scan_status.id))
    thread.daemon = True
    thread.start()

    return JsonResponse({'status': 'success', 'message': 'Deep scan started.'})

@login_required
def api_deep_scan_status(request, book_id):
    """Returns the current progress of the deep scan."""
    book = get_object_or_404(Book, pk=book_id, user=request.user)
    status = book.get_deep_scan_status()
    if not status:
        return JsonResponse({'status': 'none'})
    
    return JsonResponse({
        'status': status.status,
        'progress': status.progress_percentage,
        'step': status.current_step,
        'error': status.error_message
    })

def _ensure_relationship_cache(char_a, char_b, book):
    """
    Internal helper to run the 3-pass R1 analysis and populate caches.
    This is a headless version of api_suggest_relationship.
    """
    try:
        char_a_data = f"{char_a.traits}|{char_a.motivation}|{char_a.role}"
        char_b_data = f"{char_b.traits}|{char_b.motivation}|{char_b.role}"
        h_a = hashlib.sha256(char_a_data.encode()).hexdigest()
        h_b = hashlib.sha256(char_b_data.encode()).hexdigest()

        shared_events = Event.objects.filter(book=book, characters=char_a).filter(characters=char_b).distinct()
        if not shared_events.exists():
            return

        all_events = list(shared_events.order_by('chronological_order', 'sequence_order'))
        total_count = len(all_events)
        
        import math
        chunk_size = math.ceil(total_count / 3)
        batches = [all_events[i:i + chunk_size] for i in range(0, total_count, chunk_size)]
        
        batch_hashes = []
        batch_texts = []
        for batch in batches:
            batch_content = ""
            for event in batch:
                content = event.content_json or event.content_html or event.description or ""
                batch_content += f"{event.id}:{str(content)}|"
            batch_hashes.append(hashlib.sha256(batch_content.encode()).hexdigest())
            
            full_text = ""
            for event in batch:
                content = event.content_json or event.content_html or event.description or ""
                # If the summary is very short, supplement with a snippet from the chapter content 
                # to give the AI actual narrative context for relationship mapping.
                if len(str(content)) < 500 and event.chapter and event.chapter.content:
                    # Take up to 2000 chars of chapter content as context
                    content = f"{content}\n[SCENE CONTEXT]: {event.chapter.content[:2000]}..."
                
                full_text += f"\n--- SCENE: {event.title} ---\n{str(content)}\n"
            batch_texts.append(full_text)

        snapshots_hash = "|".join(batch_hashes)
        
        # Check if already cached
        exists = RelationshipAnalysisCache.objects.filter(
            character_a=char_a, 
            character_b=char_b,
            char_a_metadata_hash=h_a,
            char_b_metadata_hash=h_b,
            interaction_snapshots_hash=snapshots_hash
        ).exists()
        if exists: return

        # 2. Process batches
        interaction_summaries = []
        for idx in range(len(batches)):
            # Check intermediate cache
            summary_cache = InteractionSummaryCache.objects.filter(
                character_a=char_a,
                character_b=char_b,
                batch_index=idx,
                content_hash=batch_hashes[idx]
            ).first()

            if summary_cache:
                interaction_summaries.append(summary_cache.summary_text)
                continue

            summary_prompt = f"""
            Analyze this CHUNK OF STORY ({idx+1}/3) between {char_a.name} and {char_b.name}.
            Summarize their interactions... (truncated for brevity in scan)
            Return JSON ONLY: {{"summary": "..."}}
            STORY CONTENT: {batch_texts[idx]}
            """
            result = _call_ai_json(summary_prompt, system_message="Provide deep narrative summaries in JSON format.", deepseek_model="deepseek-reasoner")
            summary_text = result['summary'] if (result and 'summary' in result) else "Summary generation failed."
            interaction_summaries.append(summary_text)

            InteractionSummaryCache.objects.update_or_create(
                character_a=char_a, character_b=char_b, batch_index=idx,
                defaults={'summary_text': summary_text, 'content_hash': batch_hashes[idx], 'book': book}
            )

        # 3. Final Synthesis
        _perform_relationship_analysis(char_a, char_b, book, interaction_summaries, snapshots_hash, h_a, h_b)
    except Exception as e:
        print(f"Deep Scan error for pair {char_a.name}/{char_b.name}: {e}")

def _perform_relationship_analysis(char_a, char_b, book, interaction_summaries, snapshots_hash, h_a, h_b):
    """
    Standardised synthesis pass. Populates cache AND mirrors data to CharacterRelationship.
    """
    final_prompt = f"""
    Synthesize the full relationship profile between {char_a.name} and {char_b.name} based on three chronological summaries.
    
    Character A: {char_a.name} | Traits: {char_a.traits} | Motivation: {char_a.motivation}
    Character B: {char_b.name} | Traits: {char_b.traits} | Motivation: {char_b.motivation}

    INTERACTION SUMMARIES:
    1: {interaction_summaries[0] if len(interaction_summaries) > 0 else "N/A"}
    2: {interaction_summaries[1] if len(interaction_summaries) > 1 else "N/A"}
    3: {interaction_summaries[2] if len(interaction_summaries) > 2 else "N/A"}
    
    Return Relationship JSON:
    {{
        "type": "...",  (friend, ally, enemy, nemesis, romantic, family, professional, rival, mentor, protege, acquaintance, complicated, neutral)
        "description": "...", (Detailed narrative summary)
        "strength": 5, (1-10)
        "trust_level": 5, (1-10)
        "power_dynamic": "...", (balanced, a_dominant, b_dominant)
        "relationship_status": "...", (active, estranged, deceased, unresolved)
        "visibility": "...", (public, secret, rumored)
        "conflict_source": "...", 
        "character_a_wants": "...", 
        "character_b_wants": "...", 
        "evolution": "...", (Narrative arc)
        "shared_secret": "...", 
        "first_impression": "...", 
        "vulnerability": "...", 
        "major_shared_moments": "...",
        "predictability": 5 (1-10)
    }}
    """
    
    ai_response = _call_ai_json(final_prompt, deepseek_model="deepseek-reasoner")

    if ai_response:
        # Flatten if nested under 'analysis' key
        if 'analysis' in ai_response and isinstance(ai_response['analysis'], dict):
            ai_response = ai_response['analysis']
            
        # 1. Update Cache
        RelationshipAnalysisCache.objects.update_or_create(
            character_a=char_a, character_b=char_b,
            defaults={
                'full_json': ai_response,
                'char_a_metadata_hash': h_a, 'char_b_metadata_hash': h_b,
                'interaction_snapshots_hash': snapshots_hash, 'book': book
            }
        )

        # 2. Mirror/Sync to permanent record
        rel, created = CharacterRelationship.objects.get_or_create(
            user=char_a.user,
            character_a=char_a,
            character_b=char_b,
            defaults={'relationship_type': ai_response.get('type', 'neutral')}
        )
        
        # Smart Sync: Update if AI found significant depth (strength >= existing)
        ai_strength = ai_response.get('strength', 5)
        if ai_strength >= rel.strength or created:
            rel.relationship_type = ai_response.get('type', rel.relationship_type)
            rel.description = ai_response.get('description', rel.description)
            rel.strength = ai_strength
            rel.trust_level = ai_response.get('trust_level', rel.trust_level)
            rel.power_dynamic = ai_response.get('power_dynamic', rel.power_dynamic)
            rel.relationship_status = ai_response.get('relationship_status', rel.relationship_status)
            rel.visibility = ai_response.get('visibility', rel.visibility)
            rel.conflict_source = ai_response.get('conflict_source', rel.conflict_source)
            rel.character_a_wants = ai_response.get('character_a_wants', rel.character_a_wants)
            rel.character_b_wants = ai_response.get('character_b_wants', rel.character_b_wants)
            rel.evolution = ai_response.get('evolution', rel.evolution)
            rel.shared_secret = ai_response.get('shared_secret', rel.shared_secret)
            rel.first_impression = ai_response.get('first_impression', rel.first_impression)
            rel.vulnerability = ai_response.get('vulnerability', rel.vulnerability)
            rel.major_shared_moments = ai_response.get('major_shared_moments', rel.major_shared_moments)
            rel.predictability = ai_response.get('predictability', rel.predictability)
            rel.save()

    return ai_response
