from rest_framework import serializers
from videos.models import Video, Genre


class VideoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Video
        fields = ('id', 'title', 'description', 'genre', 'thumbnail', 'video_file', 'hls_480p', 'hls_720p', 'hls_1080p', 'created_at')
        read_only_fields = ('hls_480p', 'hls_720p', 'hls_1080p', 'created_at')


class GenreSerializer(serializers.ModelSerializer):
    videos = VideoSerializer(many=True, read_only=True)

    class Meta:
        model = Genre
        fields = ('id', 'name', 'videos')