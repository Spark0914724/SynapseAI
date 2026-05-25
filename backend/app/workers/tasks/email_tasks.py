from app.workers.celery_app import celery_app


@celery_app.task(name="send_email")
def send_email(to: str, subject: str, html_body: str) -> dict:
    """
    Background task: send transactional email.
    Implemented in Step 2.
    """
    # TODO: implement in Step 2
    return {"status": "queued", "to": to}
