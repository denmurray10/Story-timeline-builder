from django.shortcuts import render, get_object_or_404
from django.views import generic, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.files.storage import default_storage
from django.contrib import messages  # ← Add this import
import os
from .models import Post
from .forms import PostForm


class PostList(generic.ListView):
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'

    def get_queryset(self):
        queryset = Post.objects.filter(status=1).order_by('-created_on')
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__iexact=category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Post.objects.filter(status=1).exclude(category='').values_list('category', flat=True).distinct().order_by('category')
        context['current_category'] = self.request.GET.get('category')
        if context['posts'].exists():
            context['featured_post'] = context['posts'].first()
            context['remaining_posts'] = context['posts'][1:]
        return context


class PostDetail(generic.DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'


class PostCreateView(LoginRequiredMixin, UserPassesTestMixin, generic.CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'
    success_url = reverse_lazy('staff_dashboard')

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        # Success message based on publish status
        if self.object.status == 1:
            messages.success(self.request, f'🎉 "{self.object.title}" is now live!')
        else:
            messages.info(self.request, f'✏️ "{self.object.title}" has been saved as a draft.')
        return response


@method_decorator(csrf_exempt, name='dispatch')
class ImageUploadView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, *args, **kwargs):
        if 'upload' not in request.FILES:
            return JsonResponse({'error': {'message': 'No file uploaded.'}}, status=400)

        file = request.FILES['upload']
        file_name = default_storage.save(os.path.join('blog_content', file.name), file)
        file_url = default_storage.url(file_name)

        return JsonResponse({
            'url': file_url
        })
