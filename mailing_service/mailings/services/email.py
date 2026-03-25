import time
from random import randint

import structlog
from celery import shared_task

from mailings.models import MailingRecord

logger = structlog.get_logger(__name__)


@shared_task(bind=True, max_retries=3, retry_backoff=True)
def send_email(self, mailing_record_id: int) -> None:
    """Simulate email sending with random delay and update record status."""
    try:
        record = MailingRecord.objects.get(pk=mailing_record_id)
    except MailingRecord.DoesNotExist:
        logger.error("MailingRecord not found", id=mailing_record_id)
        return

    try:
        time.sleep(randint(5, 20))
        logger.info(
            "Send EMAIL",
            to=record.email,
            subject=record.subject,
            external_id=record.external_id,
            user_id=record.user_id,
        )
        record.status = MailingRecord.Status.SENT
        record.save(update_fields=["status", "updated_at"])
    except Exception as exc:
        logger.error(
            "Failed to send email",
            to=record.email,
            external_id=record.external_id,
            error=str(exc),
            retry=self.request.retries,
        )
        if self.request.retries >= self.max_retries:
            record.status = MailingRecord.Status.FAILED
            record.error_message = str(exc)
            record.save(update_fields=["status", "error_message", "updated_at"])
            raise
        raise self.retry(exc=exc)
