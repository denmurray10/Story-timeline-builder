"""
Views for the Timeline app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
import docx2txt
import io
import os
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.views.decorators.http import require_POST
from django.utils import timezone
import json
import re
import google.generativeai as genai
from openai import OpenAI
from django.conf import settings

from .models import Book, Chapter, Character, Event, Tag, CharacterRelationship, AIFocusTask, ActivityLog
from .forms import (
    UserRegisterForm, BookForm, ChapterForm, CharacterForm, 
    EventForm, TagForm, UserAccountForm, CharacterRelationshipForm
)
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


@login_required
def dashboard(request):
    """Main dashboard showing overview of all projects."""
    books = Book.objects.filter(user=request.user).annotate(
        chapter_count=Count('chapters'),
        event_count=Count('events')
    )
    
    characters = Character.objects.filter(user=request.user, is_active=True)
    total_events = Event.objects.filter(user=request.user).count()
    events_written = Event.objects.filter(user=request.user, is_written=True).count()
    
    # Recent activity logs (last 5)
    recent_activity = ActivityLog.objects.filter(user=request.user).order_by('-timestamp')[:5]
    
    # AI Focus Tasks
    today = timezone.localdate()
    focus_tasks = AIFocusTask.objects.filter(user=request.user, created_at__date=today)
    
    if not focus_tasks.exists():
        # Generate new tasks if none exist for today
        generate_daily_focus_tasks(request.user)
        focus_tasks = AIFocusTask.objects.filter(user=request.user, created_at__date=today)
    else:
        # Auto-sense if tasks have been completed
        auto_sense_focus_tasks(request.user, focus_tasks)
    
    context = {
        'books': books,
        'character_count': characters.count(),
        'total_events': total_events,
        'events_written': events_written,
        'recent_activity': recent_activity,
        'focus_tasks': focus_tasks,
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
        event_count=Count('events')
    )
    return render(request, 'timeline/book_list.html', {'books': books})


@login_required
def book_detail(request, pk):
    """Detail view for a single book."""
    book = get_object_or_404(Book, pk=pk, user=request.user)
    chapters = book.chapters.all().annotate(event_count=Count('events'))
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
    """Import a book from a file and analyze with AI."""
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
            status='drafting'
        )
        
        # 2. Extract Text
        content = extract_text_from_file(book_file)
        
        if not content:
            messages.error(request, "Could not extract text from file.")
            return redirect('book_list')

        # 3. Call AI to analyze (limit for context window)
        analysis_text = content[:20000] # Take first 20k chars
        
        messages.info(request, "AI is analyzing your book. This may take a moment...")
        ai_data = analyze_book_content_with_ai(analysis_text)
        
        if ai_data:
            # 4. Create Characters
            char_map = {}
            new_chars = 0
            for char_info in ai_data.get('characters', []):
                name = char_info.get('name')
                if name:
                    char = Character.objects.create(
                        user=request.user,
                        name=name,
                        role=char_info.get('role', 'supporting'),
                        description=char_info.get('description', ''),
                        goals=char_info.get('goals', ''),
                        traits=char_info.get('traits', '')
                    )
                    char_map[name.lower()] = char
                    new_chars += 1
            
            # 5. Create Chapters
            new_chapters = 0
            for chap_info in ai_data.get('chapters', []):
                Chapter.objects.create(
                    book=book,
                    chapter_number=chap_info.get('number', new_chapters + 1),
                    title=chap_info.get('title', f"Chapter {new_chapters + 1}"),
                    description=chap_info.get('summary', '')
                )
                new_chapters += 1
            
            # 6. Create Events
            new_events = 0
            for event_info in ai_data.get('events', []):
                pov_name = event_info.get('pov_character', '').lower()
                pov_char = char_map.get(pov_name)
                
                # Deduce chapter link if possible
                chap_num = event_info.get('chapter_number')
                chapter = None
                if chap_num:
                    chapter = Chapter.objects.filter(book=book, chapter_number=chap_num).first()

                event = Event.objects.create(
                    user=request.user,
                    book=book,
                    chapter=chapter,
                    title=event_info.get('title', f"Event {new_events + 1}"),
                    description=event_info.get('summary', ''),
                    pov_character=pov_char,
                    emotional_tone=event_info.get('tone', 'neutral'),
                    story_beat=event_info.get('beat', ''),
                    tension_level=event_info.get('tension', 5),
                    sequence_order=new_events + 1
                )
                
                # Link involved characters
                for c_name in event_info.get('involved_characters', []):
                    c_obj = char_map.get(c_name.lower())
                    if c_obj:
                        event.characters.add(c_obj)
                
                new_events += 1

            messages.success(request, f"Successfully imported '{title}'! Created {new_chars} characters, {new_chapters} chapters, and {new_events} events.")
            return redirect('book_detail', pk=book.pk)
        else:
            messages.warning(request, "Book created, but AI analysis failed to extract details.")
            return redirect('book_detail', pk=book.pk)

    return render(request, 'timeline/book_import.html')


@login_required
def book_delete(request, pk):
    """Delete a book."""
    book = get_object_or_404(Book, pk=pk, user=request.user)
    if request.method == 'POST':
        book_title = book.title
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
    return render(request, 'timeline/relationship_map.html')


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
        color = '#94a3b8' # Default
        if rel.relationship_type == 'romantic': color = '#f43f5e'
        elif rel.relationship_type == 'enemy': color = '#b91c1c'
        elif rel.relationship_type == 'ally': color = '#059669'
        
        edges.append({
            'from': rel.character_a.id,
            'to': rel.character_b.id,
            'label': rel.get_relationship_type_display(),
            'title': rel.description,
            'width': width,
            'color': color,
        'arrows': 'to' # Or none if mutual
        })
        
    data = {
        'nodes': nodes,
        'edges': edges
    }
    return JsonResponse(data)


# ============== Helper Functions ==============

def get_file_word_count(file):
    """Calculate word count from an uploaded file (.docx or .txt)."""
    text = extract_text_from_file(file)
    if text:
        return len(text.split())
    return 0

def extract_text_from_file(file):
    """Extract string content from .docx or .txt files."""
    filename = file.name.lower()
    text = ""
    try:
        if filename.endswith('.docx'):
            text = docx2txt.process(file)
        elif filename.endswith('.txt'):
            file.seek(0)
            text = file.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error processing file: {e}")
    return text

def analyze_book_content_with_ai(text):
    """Calls AI to extract characters, chapters, and events as JSON."""
    if not settings.DEEPSEEK_API_KEY and not settings.GEMINI_API_KEY:
        return None

    prompt = f"""
    Analyze the following book content and identify:
    1. Characters (name, role, description, goals, traits)
    2. Chapters (number, title, summary)
    3. Key Scenes/Events (title, summary, pov_character, tone, beat, tension level 1-10, involved characters)

    Return the result ONLY as a JSON object with this structure:
    {{
      "characters": [{{ "name": "...", "role": "protagonist/antagonist/supporting", "description": "...", "goals": "...", "traits": "..." }}],
      "chapters": [{{ "number": 1, "title": "...", "summary": "..." }}],
      "events": [{{ "title": "...", "summary": "...", "pov_character": "...", "tone": "tension/action/reflective/emotional/humorous/dark/neutral", "beat": "exposition/inciting/rising/climax/falling/resolution/setup/payoff", "tension": 7, "involved_characters": ["Name1", "Name2"], "order": 1 }}]
    }}

    Content:
    {text}
    """

    try:
        if settings.DEEPSEEK_API_KEY:
            client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a professional literary analyst. Always respond with valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                stream=False
            )
            content = response.choices[0].message.content
        else:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-3-flash-preview')
            response = model.generate_content(prompt)
            content = response.text

        # Clean JSON response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        return json.loads(content)
    except Exception as e:
        print(f"AI Analysis Error: {e}")
        return None


# ============== Chapter Views ==============

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
    return render(request, 'timeline/chapter_detail.html', {
        'chapter': chapter,
        'events': events
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
    API endpoint for the AI Story Consultant.
    Pulls story context and sends it to DeepSeek (primary) or Gemini.
    """
    if not settings.DEEPSEEK_API_KEY and not settings.GEMINI_API_KEY:
        return JsonResponse({
            'status': 'error', 
            'message': 'AI features are not configured (Missing API Key).'
        }, status=503)

    try:
        data = json.loads(request.body)
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return JsonResponse({'status': 'error', 'message': 'No query provided'}, status=400)

        # 1. Build Story Context
        books = Book.objects.filter(user=request.user)
        characters = Character.objects.filter(user=request.user)
        recent_events = Event.objects.filter(user=request.user).order_by('-updated_at')[:10]
        
        context = "You are a professional Story Consultant. Here is the context of the user's story:\n\n"
        
        context += "BOOKS:\n"
        for b in books:
            context += f"- {b.title} (Status: {b.get_status_display()}, Progress: {b.progress_percentage}%)\n"
            
        context += "\nCHARACTERS:\n"
        for c in characters:
            context += f"- {c.name} ({c.get_role_display()}): {c.description[:200]}...\n"
            
        context += "\nRECENT EVENTS:\n"
        for e in recent_events:
            context += f"- {e.title}: {e.description[:100]}...\n"

        context += f"\nUSER QUESTION: {user_query}\n"
        context += "\nPlease provide creative, helpful, and insightful feedback based on this context. Keep it concise."

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
