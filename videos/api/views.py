from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from videos.utils import process_video
from .serializers import VideoSerializer, GenreSerializer
from videos.models import Video, Genre


class VideoListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        genres = Genre.objects.prefetch_related('videos').all()
        serializer = GenreSerializer(genres, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class VideoDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            video = Video.objects.get(pk=pk)
        except Video.DoesNotExist:
            return Response({'detail': 'Video not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = VideoSerializer(video, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class VideoUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VideoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'detail': 'Please check your input.'}, status=status.HTTP_400_BAD_REQUEST)
        video = serializer.save()
        process_video(video.id)
        video.refresh_from_db()  # ← NEU: Pfade neu laden
        return Response(VideoSerializer(video, context={'request': request}).data, status=status.HTTP_201_CREATED)