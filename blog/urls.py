from . import views
from django.urls import path

urlpatterns = [
    path('', views.PostList.as_view(), name='post_list'),
    path('create/', views.PostCreateView.as_view(), name='post_create'),
    path('upload-image/', views.ImageUploadView.as_view(), name='upload_image'),
    path('<slug:slug>/', views.PostDetail.as_view(), name='post_detail'),
]
