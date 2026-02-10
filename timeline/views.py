"""
Views for the Timeline app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.views.decorators.http import require_POST
import json

from .models import Book, Chapter, Character, Event, Tag, CharacterRelationship
from .forms import (
    UserRegisterForm, BookForm, ChapterForm, CharacterForm, UserAccountForm
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
    
    # Recent events
    recent_events = Event.objects.filter(user=request.user).order_by('-updated_at')[:5]
    
    context = {
        'books': books,
        'character_count': characters.count(),
        'total_events': total_events,
        'events_written': events_written,
        'recent_events': recent_events,
    }
    return render(request, 'timeline/dashboard.html', context)


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
        form = BookForm(request.POST)
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
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, f'Book "{book.title}" updated successfully!')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm(instance=book)
    return render(request, 'timeline/book_form.html', {'form': form, 'action': 'Edit', 'book': book})


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


# ============== Chapter Views ==============

@login_required
def chapter_create(request, book_pk):
    """Create a new chapter in a book."""
    book = get_object_or_404(Book, pk=book_pk, user=request.user)
    if request.method == 'POST':
        form = ChapterForm(request.POST)
        if form.is_valid():
            chapter = form.save(commit=False)
            chapter.book = book
            chapter.save()
            messages.success(request, f'Chapter "{chapter.title}" created successfully!')
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
def chapter_edit(request, pk):
    """Edit an existing chapter."""
    chapter = get_object_or_404(Chapter, pk=pk, book__user=request.user)
    if request.method == 'POST':
        form = ChapterForm(request.POST, instance=chapter)
        if form.is_valid():
            form.save()
            messages.success(request, f'Chapter "{chapter.title}" updated successfully!')
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
        form = CharacterForm(request.POST, user=request.user)
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
        form = CharacterForm(request.POST, instance=character, user=request.user)
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
