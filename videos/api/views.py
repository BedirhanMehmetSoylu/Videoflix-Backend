import os
from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from videos.utils import process_video, enqueue_video_processing
from .serializers import VideoSerializer, VideoUploadSerializer
from videos.models import Video


class VideoListView(APIView):
    """Return a list of all available videos."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return all videos ordered by creation date descending."""
        videos = Video.objects.all()
        serializer = VideoSerializer(videos, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class VideoUploadView(APIView):
    """Handle video upload and trigger HLS conversion."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Save uploaded video and start HLS conversion job."""
        serializer = VideoUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'detail': 'Please check your input.'}, status=status.HTTP_400_BAD_REQUEST)
        video = serializer.save()
        enqueue_video_processing(video.id)
        video.refresh_from_db()
        return Response(VideoUploadSerializer(video, context={'request': request}).data, status=status.HTTP_201_CREATED)


class HLSManifestView(APIView):
    """Serve the HLS manifest file for a specific video and resolution."""
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        """Return the m3u8 playlist file for the given video and resolution."""
        manifest_path = os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(movie_id), resolution, 'index.m3u8')
        if not os.path.exists(manifest_path):
            raise Http404('Manifest not found.')
        return FileResponse(open(manifest_path, 'rb'), content_type='application/vnd.apple.mpegurl')


class HLSSegmentView(APIView):
    """Serve a single HLS video segment file."""
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        """Return a binary .ts segment file for the given video and resolution."""
        segment_path = os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(movie_id), resolution, segment)
        if not os.path.exists(segment_path):
            raise Http404('Segment not found.')
        return FileResponse(open(segment_path, 'rb'), content_type='video/MP2T')