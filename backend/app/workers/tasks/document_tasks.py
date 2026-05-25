from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, name="process_document")
def process_document(self, document_id: str) -> dict:
    """
    Background task: parse uploaded document, chunk text, generate embeddings.
    Implemented in Step 5.
    """
    try:
        # TODO: implement in Step 5
        return {"status": "queued", "document_id": document_id}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
