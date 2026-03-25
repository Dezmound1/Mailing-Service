from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from mailings.models import MailingRecord


@pytest.mark.django_db
class TestImportMailingsCommand:
    """Test the import_mailings command."""

    @patch("mailings.services.importer.send_email")
    def test_import_prints_stats(self, mock_send, sample_xlsx):
        """Command should print import statistics to stdout."""
        out = StringIO()
        call_command("import_mailings", str(sample_xlsx), stdout=out)
        output = out.getvalue()
        assert "Import complete" in output
        assert "Total rows:" in output
        assert "Created:" in output

    @patch("mailings.services.importer.send_email")
    def test_dry_run_no_records(self, mock_send, sample_xlsx):
        """Dry run should print DRY RUN prefix and not create records."""
        out = StringIO()
        call_command("import_mailings", str(sample_xlsx), "--dry-run", stdout=out)
        output = out.getvalue()
        assert "DRY RUN" in output
        assert MailingRecord.objects.count() == 0

    def test_missing_file_raises_error(self):
        """Non-existent file should raise CommandError."""
        with pytest.raises(CommandError, match="File not found"):
            call_command("import_mailings", "/nonexistent/file.xlsx")

    def test_wrong_extension_raises_error(self, tmp_path):
        """Non-XLSX file should raise CommandError."""
        csv_file = tmp_path / "data.csv"
        csv_file.touch()
        with pytest.raises(CommandError, match="Expected .xlsx"):
            call_command("import_mailings", str(csv_file))
