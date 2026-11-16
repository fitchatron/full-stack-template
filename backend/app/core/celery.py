from celery import Celery

from app.core.config import settings

celery_app = Celery(
    __name__,
    backend=settings.CELERY_RESULT_BACKEND,
    broker=settings.CELERY_BROKER_URL,
    include=["app.tasks"],
)

# Optional configuration, see the application user guide.
celery_app.conf.update(
    result_expires=3600,
)

if __name__ == "__main__":
    celery_app.start()
