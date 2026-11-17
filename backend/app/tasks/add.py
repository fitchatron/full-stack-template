from app.core.celery import celery_app


@celery_app.task(name="add")
def add(x, y):
    return x + y
