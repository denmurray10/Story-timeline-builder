from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'slug', 'category', 'content', 'image', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control rounded-pill px-4',
                'placeholder': 'Enter post title...'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control rounded-pill px-4',
                'placeholder': 'url-friendly-slug'
            }),
            'category': forms.TextInput(attrs={
                'class': 'form-control rounded-pill px-4',
                'placeholder': 'e.g. News, Update, Tips'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control rounded-4 px-4 py-3',
                'placeholder': 'Write your story here...',
                'rows': 10
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control rounded-pill',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select rounded-pill px-4',
            }),
        }
