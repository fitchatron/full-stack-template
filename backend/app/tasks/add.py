from app.core.celery import celery_app


@celery_app.task(name="add_task")
def add_task(x: int, y: int):
    return x + y
