from django.db.models.signals import post_save
from django.dispatch import receiver
from videos.models import Video
from videos.utils import enqueue_video_processing


@receiver(post_save, sender=Video)
def trigger_video_conversion(sender, instance, created, **kwargs):
    """Trigger HLS video conversion when a new video is uploaded."""
    if not created or not instance.video_file:
        return
    enqueue_video_processing(instance.id)