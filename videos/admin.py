from django.contrib import admin
from .models import Video, Genre


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'genre', 'created_at')
    list_filter = ('genre',)
    search_fields = ('title', 'description')
    readonly_fields = ('hls_480p', 'hls_720p', 'hls_1080p', 'created_at')