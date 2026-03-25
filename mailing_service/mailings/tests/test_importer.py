from unittest.mock import patch

import pytest

from mailings.models import MailingRecord
from mailings.services.importer import import_from_xlsx


@pytest.mark.django_db
class TestImportFromXlsx:
    @patch("mailings.services.importer.send_email")
    def test_import_valid_file(self, mock_send, sample_xlsx):
        """All valid rows should be created and email tasks dispatched."""
        stats = import_from_xlsx(sample_xlsx)
        assert stats.total_rows == 3
        assert stats.created == 3
        assert stats.skipped == 0
        assert stats.errors == 0
        assert MailingRecord.objects.count() == 3
        assert mock_send.delay.call_count == 3

    @patch("mailings.services.importer.send_email")
    def test_duplicate_rows_skipped(self, mock_send, sample_xlsx):
        """Re-importing the same file should skip all rows."""
        import_from_xlsx(sample_xlsx)
        mock_send.delay.reset_mock()

        stats = import_from_xlsx(sample_xlsx)
        assert stats.created == 0
        assert stats.skipped == 3
        assert MailingRecord.objects.count() == 3
        mock_send.delay.assert_not_called()

    @patch("mailings.services.importer.send_email")
    def test_invalid_rows_counted(self, mock_send, xlsx_with_errors):
        """Invalid rows should be counted as errors with details."""
        stats = import_from_xlsx(xlsx_with_errors)
        assert stats.total_rows == 4
        assert stats.created == 2
        assert stats.errors == 2
        assert len(stats.error_details) == 2

    @patch("mailings.services.importer.send_email")
    def test_dry_run_no_records_created(self, mock_send, sample_xlsx):
        """Dry run should count stats but not create records or send emails."""
        stats = import_from_xlsx(sample_xlsx, dry_run=True)
        assert stats.created == 3
        assert MailingRecord.objects.count() == 0
        mock_send.delay.assert_not_called()

    @patch("mailings.services.importer.send_email")
    def test_custom_batch_size(self, mock_send, sample_xlsx):
        """Import should work correctly with batch_size=1."""
        stats = import_from_xlsx(sample_xlsx, batch_size=1)
        assert stats.created == 3
        assert MailingRecord.objects.count() == 3

    @patch("mailings.services.importer.send_email")
    def test_empty_file_no_rows(self, mock_send, empty_xlsx):
        """File with only headers should produce zero stats."""
        stats = import_from_xlsx(empty_xlsx)
        assert stats.total_rows == 0
        assert stats.created == 0
        mock_send.delay.assert_not_called()

    def test_invalid_headers_raises(self, xlsx_bad_headers):
        """File with wrong headers should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid headers"):
            import_from_xlsx(xlsx_bad_headers)
