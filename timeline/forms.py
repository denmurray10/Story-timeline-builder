"""
Forms for the Timeline app.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Book, Chapter, Character, Event, Tag, CharacterRelationship, WorldEntry


class UserRegisterForm(UserCreationForm):
    """User registration form."""
    first_name = forms.CharField(max_length=30, required=False, label="First name")
    last_name = forms.CharField(max_length=30, required=False, label="Last name")
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "password1", "password2"]

    def save(self, commit=True):
        """Save the user with first/last name and email set."""
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        user.email = self.cleaned_data.get("email", "")
        if commit:
            user.save()
        return user


class BookForm(forms.ModelForm):
    """Form for creating/editing books."""

    class Meta:
        model = Book
        fields = [
            "title",
            "series_order",
            "description",
            "word_count_target",
            "current_word_count",
            "status",
            "started_date",
            "completed_date",
            "image",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "series_order": forms.NumberInput(attrs={"class": "form-control"}),
            "word_count_target": forms.NumberInput(attrs={"class": "form-control"}),
            "current_word_count": forms.NumberInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "started_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "completed_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }


class ChapterForm(forms.ModelForm):
    """Form for creating/editing chapters."""

    class Meta:
        model = Chapter
        fields = ["chapter_number", "title", "description", "chapter_file", "content", "word_count", "is_complete"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "chapter_number": forms.NumberInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "chapter_file": forms.FileInput(attrs={"class": "form-control"}),
            "content": forms.Textarea(attrs={"rows": 10, "class": "form-control", "placeholder": "Paste your chapter content here..."}),
            "word_count": forms.NumberInput(attrs={"class": "form-control"}),
            "is_complete": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class CharacterForm(forms.ModelForm):
    """Form for creating/editing characters."""

    class Meta:
        model = Character
        fields = [
            "name",
            "nickname",
            "aliases",
            "role",
            "description",
            "motivation",
            "goals",
            "traits",
            "color_code",
            "introduction_book",
            "introduction_chapter",
            "is_active",
            "profile_image",
            "avatar_id",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "nickname": forms.TextInput(attrs={"class": "form-control"}),
            "aliases": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Mum, Mrs. Smith, Sarah"}),
            "role": forms.Select(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "motivation": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "goals": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "traits": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "color_code": forms.TextInput(attrs={"class": "form-control", "type": "color"}),
            "introduction_book": forms.Select(attrs={"class": "form-control"}),
            "introduction_chapter": forms.Select(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "profile_image": forms.FileInput(attrs={"class": "form-control"}),
            "avatar_id": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["introduction_book"].queryset = Book.objects.filter(user=user)
            self.fields["introduction_chapter"].queryset = Chapter.objects.filter(book__user=user)


class EventForm(forms.ModelForm):
    """Form for creating/editing events."""

    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "content_json",
            "content_html",
            "book",
            "chapter",
            "sequence_order",
            "chronological_order",
            "story_date",
            "location",
            "pov_character",
            "characters",
            "emotional_tone",
            "story_beat",
            "tension_level",
            "tags",
            "notes",
            "word_count",
            "is_written",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "content_json": forms.HiddenInput(),
            "content_html": forms.HiddenInput(),
            "word_count": forms.HiddenInput(),
            "book": forms.Select(attrs={"class": "form-control"}),
            "chapter": forms.Select(attrs={"class": "form-control"}),
            "sequence_order": forms.NumberInput(attrs={"class": "form-control"}),
            "chronological_order": forms.NumberInput(attrs={"class": "form-control"}),
            "story_date": forms.TextInput(attrs={"class": "form-control"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "pov_character": forms.Select(attrs={"class": "form-control"}),
            "characters": forms.CheckboxSelectMultiple(),
            "emotional_tone": forms.Select(attrs={"class": "form-control"}),
            "story_beat": forms.Select(attrs={"class": "form-control"}),
            "tension_level": forms.NumberInput(attrs={"class": "form-control", "min": "1", "max": "10"}),
            "tags": forms.CheckboxSelectMultiple(),
            "notes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "is_written": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        # Ensure optional fields don't block submission
        self.fields["content_json"].required = False
        self.fields["content_html"].required = False
        self.fields["word_count"].required = False
        self.fields["notes"].required = False
        self.fields["tags"].required = False
        self.fields["chronological_order"].required = False
        self.fields["description"].required = False
        
        if user:
            self.fields["book"].queryset = Book.objects.filter(user=user)
            self.fields["chapter"].queryset = Chapter.objects.filter(book__user=user)
            self.fields["pov_character"].queryset = Character.objects.filter(user=user)
            self.fields["characters"].queryset = Character.objects.filter(user=user)
            self.fields["tags"].queryset = Tag.objects.filter(user=user)


class TagForm(forms.ModelForm):
    """Form for creating/editing tags."""

    class Meta:
        model = Tag
        fields = ["name", "category", "color", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-control"}),
            "color": forms.TextInput(attrs={"class": "form-control", "type": "color"}),
            "description": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }


class UserAccountForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']


class CharacterRelationshipForm(forms.ModelForm):
    """Form for creating/editing character relationships."""

    class Meta:
        model = CharacterRelationship
        fields = [
            "character_a",
            "character_b",
            "relationship_type",
            "description",
            "strength",
            "starts_at_event",
        ]
        widgets = {
            "character_a": forms.Select(attrs={"class": "form-control"}),
            "character_b": forms.Select(attrs={"class": "form-control"}),
            "relationship_type": forms.Select(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "strength": forms.NumberInput(attrs={"class": "form-control", "min": "1", "max": "10"}),
            "starts_at_event": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["character_a"].queryset = Character.objects.filter(user=user)
            self.fields["character_b"].queryset = Character.objects.filter(user=user)
            self.fields["starts_at_event"].queryset = Event.objects.filter(user=user)


class WorldEntryForm(forms.ModelForm):
    """Form for creating/editing world-building wiki entries."""

    class Meta:
        model = WorldEntry
        fields = ["title", "category", "book", "content", "image"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-control"}),
            "book": forms.Select(attrs={"class": "form-control"}),
            "content": forms.Textarea(attrs={"rows": 8, "class": "form-control"}),
            "image": forms.FileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["book"].required = False
        if user:
            self.fields["book"].queryset = Book.objects.filter(user=user)
