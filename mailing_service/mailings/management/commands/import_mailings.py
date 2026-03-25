from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from mailings.services.importer import import_from_xlsx


class Command(BaseCommand):
    """Management command to import mailing records from XLSX."""

    help = "Import mailing records from an XLSX file and dispatch email tasks"

    def add_arguments(self, parser):
        """Define positional and optional command arguments."""
        parser.add_argument("file_path", type=str, help="Path to the XLSX file")
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Number of records per batch (default: 500)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and validate without creating records or sending emails",
        )

    def handle(self, *args, **options):
        """Validate input file and run the import process."""
        file_path = Path(options["file_path"])

        if not file_path.exists():
            raise CommandError(f"File not found: {file_path}")

        if file_path.suffix.lower() != ".xlsx":
            raise CommandError(f"Expected .xlsx file, got '{file_path.suffix}'")

        dry_run = options["dry_run"]
        batch_size = options["batch_size"]

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] No records will be created\n"))

        try:
            stats = import_from_xlsx(
                file_path=file_path,
                batch_size=batch_size,
                dry_run=dry_run,
            )
        except ValueError as exc:
            raise CommandError(str(exc))

        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write(f"\n{prefix}Import complete:")
        self.stdout.write(f"  Total rows:  {stats.total_rows}")
        self.stdout.write(f"  Created:     {stats.created}")
        self.stdout.write(f"  Skipped:     {stats.skipped}")
        self.stdout.write(f"  Errors:      {stats.errors}")

        if stats.error_details:
            limit = min(10, len(stats.error_details))
            self.stdout.write(f"\nFirst {limit} errors:")
            for detail in stats.error_details[:limit]:
                self.stdout.write(self.style.ERROR(f"  {detail}"))
