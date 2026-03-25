from unittest.mock import patch

import pytest

from mailings.models import MailingRecord
from mailings.services.email import send_email
from mailings.tests.factories import MailingRecordFactory


@pytest.mark.django_db
class TestSendEmailTask:
    """Test the send_email task."""
    
    @patch("mailings.services.email.time.sleep")
    def test_success_updates_status(self, mock_sleep):
        """Successful send should set status to SENT."""
        record = MailingRecordFactory()
        send_email.apply(args=[record.pk])
        record.refresh_from_db()
        assert record.status == MailingRecord.Status.SENT
        mock_sleep.assert_called_once()

    @patch("mailings.services.email.time.sleep", side_effect=Exception("send failed"))
    def test_failure_after_retries(self, mock_sleep):
        """After exhausting retries, status should be FAILED with error message."""
        record = MailingRecordFactory()
        with pytest.raises(Exception, match="send failed"):
            send_email.apply(args=[record.pk], retries=send_email.max_retries)
        record.refresh_from_db()
        assert record.status == MailingRecord.Status.FAILED
        assert record.error_message == "send failed"

    @patch("mailings.services.email.time.sleep")
    def test_missing_record_returns_early(self, mock_sleep):
        """Non-existent record should not trigger sleep or raise."""
        send_email.apply(args=[99999])
        mock_sleep.assert_not_called()
