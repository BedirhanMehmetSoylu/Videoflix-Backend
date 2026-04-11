import subprocess
import os
from django.conf import settings


def convert_to_hls(video_path, output_dir, resolution, bitrate):
    """Convert a video file to HLS format at the given resolution and bitrate."""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'index.m3u8')
    resolution_map = {
        '480p': '854:480',
        '720p': '1280:720',
        '1080p': '1920:1080',
    }
    scale = resolution_map[resolution]
    command = [
        'ffmpeg', '-i', video_path,
        '-vf', f'scale={scale}',
        '-b:v', bitrate,
        '-hls_time', '10',
        '-hls_playlist_type', 'vod',
        '-hls_segment_filename', os.path.join(output_dir, 'segment_%03d.ts'),
        output_path,
        '-y'
    ]
    subprocess.run(command, check=True)
    return output_path


def process_video(video_id):
    """Convert a video into 480p, 720p and 1080p HLS streams and save the paths."""
    from videos.models import Video
    video = Video.objects.get(pk=video_id)
    video_path = os.path.join(settings.MEDIA_ROOT, video.video_file.name)
    base_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(video_id))
    resolutions = [
        ('480p', '800k', 'hls_480p'),
        ('720p', '2500k', 'hls_720p'),
        ('1080p', '5000k', 'hls_1080p'),
    ]
    for resolution, bitrate, field_name in resolutions:
        output_dir = os.path.join(base_dir, resolution)
        output_path = convert_to_hls(video_path, output_dir, resolution, bitrate)
        relative_path = os.path.relpath(output_path, settings.MEDIA_ROOT)
        setattr(video, field_name, relative_path)
    video.save()


def enqueue_video_processing(video_id):
    """Enqueue video processing as a background job or run it synchronously."""
    if os.environ.get('USE_POSTGRES') == 'true':
        import django_rq
        queue = django_rq.get_queue('default')
        queue.enqueue(process_video, video_id)
    else:
        process_video(video_id)