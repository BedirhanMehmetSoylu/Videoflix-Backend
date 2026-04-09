from django.db.models.signals import post_save
from django.dispatch import receiver
from videos.models import Video
import os


@receiver(post_save, sender=Video)
def trigger_video_conversion(sender, instance, created, **kwargs):
    if not created:
        return
    if not instance.video_file:
        return
    if os.environ.get('USE_POSTGRES') == 'true':
        import django_rq
        queue = django_rq.get_queue('default')
        queue.enqueue('videos.utils.process_video', instance.id)
    else:
        from videos.utils import process_video
        process_video(instance.id)