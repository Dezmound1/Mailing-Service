import pytest
from django.db import IntegrityError

from mailings.models import MailingRecord
from mailings.tests.factories import MailingRecordFactory


@pytest.mark.django_db
class TestMailingRecord:
    def test_create_with_defaults(self):
        """New record should have PENDING status and empty error_message."""

        record = MailingRecordFactory()
        assert record.pk is not None
        assert record.status == MailingRecord.Status.PENDING
        assert record.error_message == ""
        assert record.created_at is not None
        assert record.updated_at is not None

    def test_external_id_unique(self):
        """Duplicate external_id should raise IntegrityError."""

        MailingRecordFactory(external_id="dup-1")
        with pytest.raises(IntegrityError):
            MailingRecordFactory(external_id="dup-1")
