"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import threading

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()


def _start_inprocess_rq_worker():
    """
    Starts an RQ worker in a background thread inside the same web process.

    This is a cost-saving workaround for hosting on Render's free/starter
    tier, which does not offer a free separate "background worker" service.
    Running the worker in-process is fine for portfolio-scale demo traffic,
    but in a real production setup this should be a dedicated worker process.

    Only runs when RUN_INPROCESS_WORKER=true is set (so it never runs during
    local development, migrations, or other management commands).
    """
    if os.environ.get('RUN_INPROCESS_WORKER') != 'true':
        return

    import django
    django.setup()

    from redis import Redis
    from rq import Worker, Queue
    from django.conf import settings

    class NoSignalWorker(Worker):
        """
        RQ's default Worker tries to install OS signal handlers, which only
        works on the main thread. Since this worker runs on a background
        thread, we override that step to no-op.
        """
        def _install_signal_handlers(self):
            pass

    def run_worker():
        redis_url = os.environ.get('REDIS_URL')
        if not redis_url:
            return
        conn = Redis.from_url(redis_url)
        queue = Queue('default', connection=conn)
        worker = NoSignalWorker([queue], connection=conn)
        worker.work(with_scheduler=True)

    thread = threading.Thread(target=run_worker, daemon=True)
    thread.start()


_start_inprocess_rq_worker()
