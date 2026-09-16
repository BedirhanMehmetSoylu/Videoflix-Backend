"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import socket
import threading

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Prime Python's DNS/encoding machinery (encodings.idna) in this single
# main thread BEFORE the background worker thread starts below.
#
# Without this, the first ever socket.getaddrinfo() call (e.g. when the
# admin panel enqueues a video processing job and connects to Redis for
# the first time) triggers a one-time, non-thread-safe module import deep
# inside Python's standard library. If the background RQ worker thread
# happens to trigger the same first-time import at the same moment, both
# threads can deadlock on Python's per-module import lock - this
# reproduced 100% of the time on the first video upload after a restart.
# Doing this import once, here, single-threaded, means it's already
# cached in sys.modules before any other thread can race for it.
try:
    socket.getaddrinfo('localhost', 80)
except Exception:
    pass

application = get_wsgi_application()


def _start_inprocess_rq_worker():
    """
    Starts an RQ worker in a background thread inside the same web process.

    This is a cost-saving workaround for hosting on Render's free/starter
    tier, which does not offer a free separate background worker service.

    The worker is intentionally configured without the RQ scheduler because
    this project only uses immediate jobs via queue.enqueue(). This keeps
    Redis/Upstash command usage as low as possible.

    SimpleWorker is used because the normal RQ Worker creates a separate
    work-horse process and uses OS signals for job timeouts. OS signal
    handlers cannot be installed from a background thread.
    """

    if os.environ.get('RUN_INPROCESS_WORKER') != 'true':
        return

    import django
    django.setup()

    from redis import Redis
    from rq import Queue, SimpleWorker
    from rq.timeouts import TimerDeathPenalty

    class ThreadSafeSimpleWorker(SimpleWorker):
        """
        RQ SimpleWorker configured for execution inside a background thread.

        - Does not fork a separate work-horse process.
        - Does not install OS signal handlers.
        - Uses TimerDeathPenalty instead of Unix SIGALRM.
        """

        death_penalty_class = TimerDeathPenalty

        def _install_signal_handlers(self):
            """
            Disable RQ's OS signal handlers because this worker runs
            inside a Gunicorn background thread.
            """
            pass

    def run_worker():
        redis_url = os.environ.get('REDIS_URL')

        if not redis_url:
            return

        conn = Redis.from_url(redis_url)
        queue = Queue('default', connection=conn)

        worker = ThreadSafeSimpleWorker(
            [queue],
            connection=conn,
        )

        # IMPORTANT:
        # This project only uses immediate queue.enqueue() jobs.
        # The scheduler is intentionally disabled to minimize
        # unnecessary Redis/Upstash commands.
        worker.work(with_scheduler=False)

    thread = threading.Thread(
        target=run_worker,
        daemon=True,
        name='rq-worker',
    )

    thread.start()


_start_inprocess_rq_worker()