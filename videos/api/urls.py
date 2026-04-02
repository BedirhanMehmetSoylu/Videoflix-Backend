from django.urls import path
from .views import VideoListView, VideoDetailView, VideoUploadView

urlpatterns = [
    path('videos/', VideoListView.as_view(), name='video-list'),
    path('videos/<int:pk>/', VideoDetailView.as_view(), name='video-detail'),
    path('videos/upload/', VideoUploadView.as_view(), name='video-upload'),
]