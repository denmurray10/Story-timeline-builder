"""
Models for the Story Timeline Builder application.
These models represent the core entities: Books, Chapters, Characters, Events, Tags, and Relationships.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Book(models.Model):
    """
    Represents a book in your series.
    Each book contains multiple chapters and is owned by a user.
    """
    image = models.ImageField(upload_to='book_covers/', null=True, blank=True, help_text="Upload a cover image for this book.")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='books')
    title = models.CharField(max_length=200)
    series_order = models.PositiveIntegerField(
        help_text="Position in the series (1-20 for your 20-book series)"
    )
    description = models.TextField(blank=True)
    word_count_target = models.PositiveIntegerField(
        default=160000,
        help_text="Target word count for this book"
    )
    current_word_count = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=100,
        choices=[
            ('importing', 'Import in Progress'),
            ('planning', 'Planning'),
            ('drafting', 'Drafting'),
            ('editing', 'Editing'),
            ('complete', 'Complete'),
            ('published', 'Published'),
        ],
        default='planning'
    )
    import_progress = models.PositiveIntegerField(default=0)
    import_status_message = models.CharField(max_length=255, blank=True, default='')
    last_import_update = models.DateTimeField(auto_now=True)
    started_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['series_order']
        unique_together = ['user', 'series_order']

    def __str__(self):
        return f"Book {self.series_order}: {self.title}"

    def update_word_count(self):
        """Aggregate word count from all events in this book."""
        from django.db.models import Sum
        total = self.events.aggregate(Sum('word_count'))['word_count__sum'] or 0
        self.current_word_count = total
        self.save(update_fields=['current_word_count'])
        return total

    @property
    def progress_percentage(self):
        """Calculate writing progress as a percentage."""
        if self.word_count_target == 0:
            return 0
        return min(100, (self.current_word_count / self.word_count_target) * 100)


class Chapter(models.Model):
    """
    Represents a chapter within a book.
    Chapters contain multiple events/scenes.
    """
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chapters')
    chapter_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    word_count = models.PositiveIntegerField(default=0)
    is_complete = models.BooleanField(default=False)
    chapter_file = models.FileField(
        upload_to='chapters/',
        null=True,
        blank=True,
        help_text="Upload your chapter manuscript (.docx or .txt) to automatically calculate word count."
    )
    content = models.TextField(blank=True, help_text="Paste your chapter content here.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['book', 'chapter_number']
        unique_together = ['book', 'chapter_number']

    def __str__(self):
        return f"{self.book.title} - Chapter {self.chapter_number}: {self.title}"


class Character(models.Model):
    """
    Represents a character in your story.
    Characters can appear in multiple events across different books.
    """
    ROLE_CHOICES = [
        ('protagonist', 'Protagonist'),
        ('antagonist', 'Antagonist'),
        ('supporting', 'Supporting'),
        ('minor', 'Minor'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='characters')
    name = models.CharField(max_length=100)
    nickname = models.CharField(max_length=100, blank=True)
    aliases = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated alternate names (e.g. 'Mum, Mrs. Smith, Sarah')"
    )
    role = models.CharField(max_length=100, choices=ROLE_CHOICES, default='supporting')
    description = models.TextField(
        blank=True,
        help_text="Physical description, personality, background"
    )
    motivation = models.TextField(
        blank=True,
        help_text="What drives this character?"
    )
    goals = models.TextField(
        blank=True,
        help_text="Long-term and short-term objectives"
    )
    traits = models.TextField(
        blank=True,
        help_text="Key personality traits and quirks"
    )
    color_code = models.CharField(
        max_length=7,
        default='#3498db',
        help_text="Hex color code for timeline visualization (e.g., #3498db)"
    )
    introduction_book = models.ForeignKey(
        Book,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='introduced_characters',
        help_text="Which book does this character first appear in?"
    )
    introduction_chapter = models.ForeignKey(
        Chapter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='introduced_characters'
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this character still active in the current narrative?"
    )
    profile_image = models.ImageField(
        upload_to='character_profiles/',
        null=True,
        blank=True,
        help_text="Upload a custom profile picture"
    )
    avatar_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="ID of the selected cartoon avatar"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deep_dive_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Last generated AI deep dive for this character"
    )

    @property
    def profile_pic_url(self):
        """Returns the URL of the profile picture or a fallback avatar."""
        if self.profile_image:
            return self.profile_image.url
        
        if self.avatar_id:
            # Check if it's one of our predefined SVGs
            from django.templatetags.static import static
            return static(f'img/avatars/{self.avatar_id}.svg')
            
        # Default fallback logic
        return None

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"


class Tag(models.Model):
    """
    Flexible tagging system for organizing events by themes, locations, subplots, etc.
    """
    TAG_CATEGORIES = [
        ('theme', 'Theme'),
        ('location', 'Location'),
        ('subplot', 'Subplot'),
        ('motif', 'Motif'),
        ('tone', 'Tone'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=50)
    category = models.CharField(max_length=100, choices=TAG_CATEGORIES, default='other')
    color = models.CharField(
        max_length=7,
        default='#95a5a6',
        help_text="Hex color code for visual identification"
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']
        unique_together = ['user', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class Event(models.Model):
    """
    Core model representing a scene, plot point, or story beat.
    Events are the building blocks of your timeline.
    """
    EMOTIONAL_TONE_CHOICES = [
        ('tension', 'High Tension'),
        ('action', 'Action'),
        ('emotional', 'Emotional'),
        ('reflective', 'Reflective'),
        ('humorous', 'Humorous'),
        ('dark', 'Dark'),
        ('neutral', 'Neutral'),
    ]

    STORY_BEAT_CHOICES = [
        ('exposition', 'Exposition'),
        ('inciting', 'Inciting Incident'),
        ('rising', 'Rising Action'),
        ('climax', 'Climax'),
        ('falling', 'Falling Action'),
        ('resolution', 'Resolution'),
        ('setup', 'Setup/Plant'),
        ('payoff', 'Payoff'),
    ]

    DATE_TYPE_CHOICES = [
        ('exact', 'Exact Date'),
        ('fuzzy', 'Fuzzy/Uncertain'),
        ('ongoing', 'Ongoing/Event Span'),
        ('relative', 'Relative Date'),
        ('none', 'No Date Yet'),
    ]

    SCENE_TYPE_CHOICES = [
        ('scene', 'Scene'),
        ('exposition', 'Exposition/Infodump'),
        ('flashback', 'Flashback'),
        ('flashforward', 'Flashforward'),
        ('interlude', 'Interlude'),
        ('teaser', 'Cold Open/Teaser'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    description = models.TextField(
        blank=True,
        help_text="Brief summary of the scene (optional)"
    )
    content_json = models.JSONField(
        null=True,
        blank=True,
        help_text="Rich text content in JSON format"
    )
    content_html = models.TextField(
        null=True,
        blank=True,
        help_text="Rich text content in HTML format"
    )
    
    # Book and chapter assignment
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='events',
        null=True,
        blank=True
    )
    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name='events',
        null=True,
        blank=True
    )
    
    # Timeline positioning
    sequence_order = models.PositiveIntegerField(
        default=0,
        help_text="Order of this event in the narrative sequence"
    )
    chronological_order = models.PositiveIntegerField(
        default=0,
        help_text="Order of this event in actual story chronology (for flashbacks/non-linear narratives)"
    )
    narrative_order = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Explicit order for narrative view (reading order)"
    )

    # Smart Date Fields
    date_type = models.CharField(
        max_length=10, 
        choices=DATE_TYPE_CHOICES, 
        default='exact'
    )
    
    # For exact dates (replaces old usage of story_date potentially)
    date = models.DateTimeField(null=True, blank=True)
    
    # For fuzzy dates (range)
    earliest_date = models.DateTimeField(null=True, blank=True)
    latest_date = models.DateTimeField(null=True, blank=True)
    
    # For ongoing events
    end_date = models.DateTimeField(null=True, blank=True)
    
    # For relative dates
    relative_description = models.CharField(
        max_length=100, 
        blank=True,
        help_text="e.g., 'Three days later', 'One week after'"
    )
    relative_to_event = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='dependent_events'
    )
    relative_days = models.IntegerField(null=True, blank=True)
    
    # Constraints
    is_locked = models.BooleanField(
        default=False, 
        help_text="Prevent accidental automatic rescheduling"
    )
    
    # Story world timestamp (optional - for tracking in-world dates/times as string)
    story_date = models.CharField(
        max_length=100,
        blank=True,
        help_text="Date/time within your story world (e.g., 'June 2024' or 'Day 3')"
    )
    
    # Event characteristics
    location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Where does this event take place?"
    )
    pov_character = models.ForeignKey(
        Character,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pov_events',
        help_text="Which character's POV is this scene from?"
    )
    characters = models.ManyToManyField(
        Character,
        related_name='events',
        blank=True,
        help_text="All characters involved in this event"
    )
    emotional_tone = models.CharField(
        max_length=100,
        choices=EMOTIONAL_TONE_CHOICES,
        default='neutral'
    )
    story_beat = models.CharField(
        max_length=100,
        choices=STORY_BEAT_CHOICES,
        blank=True
    )
    scene_type = models.CharField(
        max_length=15,
        choices=SCENE_TYPE_CHOICES,
        default='scene'
    )
    tension_level = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Tension/intensity level (1-10)"
    )
    
    # Tags for flexible organization
    tags = models.ManyToManyField(Tag, related_name='events', blank=True)
    
    # Notes and metadata
    notes = models.TextField(
        blank=True,
        help_text="Private notes, reminders, or research notes for this event"
    )
    word_count = models.PositiveIntegerField(
        default=0,
        help_text="Approximate word count for this scene"
    )
    is_written = models.BooleanField(
        default=False,
        help_text="Have you actually written this scene yet?"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sequence_order']

    def __str__(self):
        try:
            chapter_info = f"{self.chapter.chapter_number}" if self.chapter else "Unassigned"
        except (Chapter.DoesNotExist, AttributeError):
            chapter_info = "Deleted"
        return f"[Ch.{chapter_info}] {self.title}"

    def save(self, *args, **kwargs):
        # If chronological_order isn't set, default it to sequence_order
        if self.chronological_order == 0 and self.sequence_order > 0:
            self.chronological_order = self.sequence_order
        super().save(*args, **kwargs)
        
        # Update book's total word count
        if self.book:
            self.book.update_word_count()

    def get_absolute_date(self):
        """
        Resolves the actual date for sorting/timeline positioning.
        Handles nested recursive checks.
        """
        # 1. Exact Date
        if self.date_type == 'exact':
            return self.date
        
        # 2. Fuzzy Date (midpoint)
        elif self.date_type == 'fuzzy':
            if self.earliest_date and self.latest_date:
                # Calculate midpoint
                delta = self.latest_date - self.earliest_date
                return self.earliest_date + (delta / 2)
            return self.earliest_date or self.latest_date
            
        # 3. Ongoing (Start date)
        elif self.date_type == 'ongoing':
            return self.date
            
        # 4. Relative Date (Resolved)
        elif self.date_type == 'relative' and self.relative_to_event:
            # Simple recursion protection: only go 1 level deep for now OR check ID
            if self.relative_to_event.id == self.id:
                return None # Prevent self-reference
                
            base_date = self.relative_to_event.get_absolute_date()
            if base_date and self.relative_days is not None:
                from datetime import timedelta
                return base_date + timedelta(days=self.relative_days)
                
        return None

    def get_display_date(self):
        """Returns human-readable date string"""
        if self.date_type == 'exact' and self.date:
            return self.date.strftime("%Y-%m-%d")
        elif self.date_type == 'fuzzy':
            start = self.earliest_date.strftime('%Y') if self.earliest_date else '?'
            end = self.latest_date.strftime('%Y') if self.latest_date else '?'
            return f"{start} - {end}"
        elif self.date_type == 'ongoing':
            start = self.date.strftime('%Y') if self.date else '?'
            end = self.end_date.strftime('%Y') if self.end_date else 'Present'
            return f"{start} - {end}"
        elif self.date_type == 'relative':
            return self.relative_description or f"{self.relative_days} days after {self.relative_to_event.title}"
        return "TBD"


class CharacterRelationship(models.Model):
    """
    Tracks relationships between characters and how they evolve over time.
    """
    RELATIONSHIP_TYPES = [
        ('ally', 'Ally/Friend'),
        ('enemy', 'Enemy/Rival'),
        ('romantic', 'Romantic'),
        ('family', 'Family'),
        ('mentor', 'Mentor/Student'),
        ('business', 'Business/Professional'),
        ('neutral', 'Neutral/Acquaintance'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='relationships')
    character_a = models.ForeignKey(
        Character,
        on_delete=models.CASCADE,
        related_name='relationships_as_a'
    )
    character_b = models.ForeignKey(
        Character,
        on_delete=models.CASCADE,
        related_name='relationships_as_b'
    )
    relationship_type = models.CharField(max_length=100, choices=RELATIONSHIP_TYPES)
    description = models.TextField(
        blank=True,
        help_text="Describe the nature of this relationship"
    )
    strength = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Strength/intensity of relationship (1-10)"
    )
    trust_level = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Trust level (1-10)"
    )
    POWER_DYNAMICS = [
        ('balanced', 'Balanced (=)'),
        ('a_dominant', 'Character A Dominant (>)'),
        ('b_dominant', 'Character B Dominant (<)'),
    ]
    power_dynamic = models.CharField(
        max_length=20, 
        choices=POWER_DYNAMICS, 
        default='balanced'
    )

    RELATIONSHIP_STATUSES = [
        ('active', 'Active'),
        ('estranged', 'Estranged'),
        ('deceased', 'Deceased'),
        ('unresolved', 'Unresolved'),
    ]
    relationship_status = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_STATUSES,
        default='active'
    )

    VISIBILITY_LEVELS = [
        ('public', 'Public Knowledge'),
        ('secret', 'Secret'),
        ('rumored', 'Rumored/Suspected'),
    ]
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_LEVELS,
        default='public'
    )

    conflict_source = models.TextField(
        blank=True,
        help_text="Source of conflict/tension"
    )
    character_a_wants = models.TextField(
        blank=True,
        help_text="What Character A wants from B"
    )
    character_b_wants = models.TextField(
        blank=True,
        help_text="What Character B wants from A"
    )

    evolution = models.TextField(
        blank=True,
        help_text="Notes on how this relationship changes over time"
    )
    starts_at_event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='relationships_starting',
        help_text="When does this relationship begin or become significant?"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['character_a', 'character_b']

    def __str__(self):
        return f"{self.character_a.name} → {self.character_b.name} ({self.get_relationship_type_display()})"


class AIFocusTask(models.Model):
    """
    Generated tasks by AI to keep the user focused on the story.
    Regenerated daily.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='focus_tasks')
    task_text = models.CharField(max_length=500)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.user.username} - {self.task_text[:50]}"


class ActivityLog(models.Model):
    """
    Tracks recent activity (creations, edits, deletions) across all models.
    """
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)  # e.g., 'Book', 'Character'
    object_name = models.CharField(max_length=200) # e.g., 'Chapter 1'
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action.capitalize()} {self.model_name}: {self.object_name}"


class WorldEntry(models.Model):
    """
    A world-building wiki entry for locations, lore, factions, rules, items, etc.
    """
    CATEGORY_CHOICES = [
        ('location', 'Location'),
        ('lore', 'Lore'),
        ('faction', 'Faction'),
        ('rule', 'Rule/Magic System'),
        ('item', 'Item/Artifact'),
        ('culture', 'Culture/Society'),
        ('creature', 'Creature/Species'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='world_entries')
    book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True, blank=True, related_name='world_entries')
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='location')
    content = models.TextField(help_text="Detailed description of this world element.")
    image = models.ImageField(upload_to='world_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'title']
        verbose_name_plural = "World Entries"

    def __str__(self):
        return f"{self.get_category_display()}: {self.title}"
