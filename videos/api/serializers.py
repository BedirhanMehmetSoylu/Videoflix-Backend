from rest_framework import serializers
from videos.models import Video, Genre


class VideoSerializer(serializers.ModelSerializer):
    """Serializer for displaying video metadata in the video list."""

    thumbnail_url = serializers.SerializerMethodField()
    category = serializers.CharField(source='genre.name', read_only=True)

    class Meta:
        model = Video
        fields = ('id', 'created_at', 'title', 'description', 'thumbnail_url', 'category')

    def get_thumbnail_url(self, obj):
        """Return the absolute URL of the video thumbnail if available."""
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None


class VideoUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading a new video with all related fields."""

    class Meta:
        model = Video
        fields = ('id', 'title', 'description', 'genre', 'video_file', 'thumbnail', 'hls_480p', 'hls_720p', 'hls_1080p', 'created_at')
        read_only_fields = ('hls_480p', 'hls_720p', 'hls_1080p', 'created_at')