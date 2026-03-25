from __future__ import annotations

import dataclasses
from pathlib import Path

import structlog
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from openpyxl import load_workbook

from mailings.models import MailingRecord
from mailings.services.email import send_email

logger = structlog.get_logger(__name__)

EXPECTED_HEADERS = ["external_id", "user_id", "email", "subject", "message"]


@dataclasses.dataclass
class ImportStats:
    total_rows: int = 0
    created: int = 0
    skipped: int = 0
    errors: int = 0
    error_details: list[str] = dataclasses.field(default_factory=list)


def _clean_cell(value: object) -> str:
    """Normalize cell value: convert numeric types, strip whitespace."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _validate_row(data: dict[str, str], row_num: int) -> str | None:
    for field in EXPECTED_HEADERS:
        if not data.get(field):
            return f"Row {row_num}: missing required field '{field}'"

    try:
        validate_email(data["email"])
    except ValidationError:
        return f"Row {row_num}: invalid email '{data['email']}'"

    return None


def _process_batch(
    batch: list[dict[str, str]],
    stats: ImportStats,
    dry_run: bool,
) -> None:
    incoming_ids = [row["external_id"] for row in batch]
    existing_ids = set(
        MailingRecord.objects.filter(
            external_id__in=incoming_ids,
        ).values_list("external_id", flat=True)
    )

    new_records = []
    for row in batch:
        if row["external_id"] in existing_ids:
            stats.skipped += 1
            continue
        new_records.append(
            MailingRecord(
                external_id=row["external_id"],
                user_id=row["user_id"],
                email=row["email"],
                subject=row["subject"],
                message=row["message"],
            )
        )

    if dry_run:
        stats.created += len(new_records)
        return

    if not new_records:
        return

    MailingRecord.objects.bulk_create(new_records, ignore_conflicts=True)
    stats.created += len(new_records)

    created_pks = list(
        MailingRecord.objects.filter(
            external_id__in=[r.external_id for r in new_records],
            status=MailingRecord.Status.PENDING,
        ).values_list("pk", flat=True)
    )

    for pk in created_pks:
        send_email.delay(pk)

    logger.info("Batch processed", created=len(new_records), tasks_queued=len(created_pks))


def import_from_xlsx(
    file_path: Path,
    batch_size: int = 500,
    dry_run: bool = False,
) -> ImportStats:
    stats = ImportStats()

    wb = load_workbook(file_path, read_only=True)
    ws = wb.active

    rows = ws.iter_rows(values_only=True)
    raw_headers = next(rows, None)

    if raw_headers is None:
        wb.close()
        raise ValueError("File is empty or has no header row")

    headers = [_clean_cell(h).lower() for h in raw_headers]

    if headers != EXPECTED_HEADERS:
        wb.close()
        raise ValueError(f"Invalid headers: expected {EXPECTED_HEADERS}, got {headers}")

    batch: list[dict[str, str]] = []

    for row_num, row in enumerate(rows, start=2):
        stats.total_rows += 1

        data = {header: _clean_cell(value) for header, value in zip(headers, row)}

        error = _validate_row(data, row_num)
        if error:
            stats.errors += 1
            stats.error_details.append(error)
            continue

        batch.append(data)

        if len(batch) >= batch_size:
            _process_batch(batch, stats, dry_run)
            batch = []

    if batch:
        _process_batch(batch, stats, dry_run)

    wb.close()
    return stats
