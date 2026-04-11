from django.apps import AppConfig


class VideosConfig(AppConfig):
    """App configuration for the videos application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'videos'

    def ready(self):
        """Register signal handlers when the app is ready."""
        import videos.signals