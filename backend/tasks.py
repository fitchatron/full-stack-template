from celery import Celery

from app.core.config import settings

app = Celery("tasks", broker=settings.CELERY_BROKER_URL)


@app.task
def add(x, y):
    return x + y
