import os
import subprocess

from django.conf import settings
import imageio_ffmpeg


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

    # Render's native Python runtime has no system ffmpeg binary (that's
    # only available with a Docker runtime). imageio-ffmpeg ships a static
    # ffmpeg binary as part of the pip package, so this works without any
    # system dependency or Aptfile.
    ffmpeg_binary = imageio_ffmpeg.get_ffmpeg_exe()

    command = [
        ffmpeg_binary,
        '-i', video_path,
        '-vf', f'scale={scale}',
        '-b:v', bitrate,
        '-hls_time', '10',
        '-hls_playlist_type', 'vod',
        '-hls_segment_filename',
        os.path.join(output_dir, 'segment_%03d.ts'),
        output_path,
        '-y',
    ]

    subprocess.run(command, check=True)

    return output_path


def process_video(video_id):
    """Convert a video into 480p, 720p and 1080p HLS streams and save the paths."""

    from videos.models import Video

    video = Video.objects.get(pk=video_id)

    video_path = os.path.join(
        settings.MEDIA_ROOT,
        video.video_file.name,
    )

    base_dir = os.path.join(
        settings.MEDIA_ROOT,
        'videos',
        'hls',
        str(video_id),
    )

    resolutions = [
        ('480p', '800k', 'hls_480p'),
        ('720p', '2500k', 'hls_720p'),
        ('1080p', '5000k', 'hls_1080p'),
    ]

    for resolution, bitrate, field_name in resolutions:
        output_dir = os.path.join(base_dir, resolution)

        output_path = convert_to_hls(
            video_path,
            output_dir,
            resolution,
            bitrate,
        )

        relative_path = os.path.relpath(
            output_path,
            settings.MEDIA_ROOT,
        )

        setattr(video, field_name, relative_path)

    video.save()


def enqueue_video_processing(video_id):
    """Add video processing to the RQ background queue."""

    # Deferred import: django_rq (and the underlying rq library) tries to
    # use multiprocessing.get_context('fork') on import, which does not
    # exist on Windows. Importing it here, only when a video is actually
    # uploaded, means local Windows development never triggers this crash
    # (it's only hit on Render/Linux, where REDIS_URL is set and this
    # function actually runs).
    import django_rq

    queue = django_rq.get_queue('default')
    queue.enqueue(process_video, video_id)