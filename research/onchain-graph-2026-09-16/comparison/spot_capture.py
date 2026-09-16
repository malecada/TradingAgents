"""Frozen anonymous ETHUSDT spot archives. Capture/schema checks only; no prices parsed."""
from __future__ import annotations

import calendar
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
from pathlib import Path
import re
import shutil
import stat
import zipfile

HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location('comparison_spot_storage', HERE.parent / 'pilot/storage.py')
storage = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(storage)

BASE_URL = 'https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1d/'
MONTHS = ('2021-12',) + tuple(f'{year}-{month:02d}' for year in range(2022, 2025) for month in range(1, 13)) + ('2025-01',)
RESPONSE_LIMIT = 1024 ** 2
TOTAL_LIMIT = 16 * 1024 ** 2
DISK_FLOOR = 20 * 1024 ** 3
SPEC = dict(base_url=BASE_URL, max_requests=76, max_response_bytes=RESPONSE_LIMIT,
            max_total_bytes=TOTAL_LIMIT, timeout_seconds=30)


def archive_name(month):
    if month not in MONTHS:
        raise ValueError('month outside frozen spot capture')
    return f'ETHUSDT-1d-{month}.zip'


def registered_url(month, checksum=False):
    return BASE_URL + archive_name(month) + ('.CHECKSUM' if checksum else '')


def validate_month(month, zip_raw, checksum_raw):
    """Validate archive identity, shape and timestamps without interpreting price fields."""
    name = archive_name(month)
    if not isinstance(zip_raw, bytes) or not isinstance(checksum_raw, bytes):
        raise ValueError('archive and checksum must be raw bytes')
    if len(zip_raw) > RESPONSE_LIMIT or len(checksum_raw) > RESPONSE_LIMIT:
        raise ValueError('response bound exceeded')
    match = re.fullmatch(r'([0-9a-fA-F]{64})[ \t]+\*?' + re.escape(name) + r'[\r\n]*', checksum_raw.decode('ascii'))
    if match is None or hashlib.sha256(zip_raw).hexdigest() != match[1].lower():
        raise ValueError('ZIP checksum or named archive mismatch')
    with zipfile.ZipFile(io.BytesIO(zip_raw)) as archive:
        members = archive.infolist()
        if len(members) != 1:
            raise ValueError('archive must contain exactly one member')
        member = members[0]
        expected_csv = name[:-4] + '.csv'
        mode = member.external_attr >> 16
        if (member.filename != expected_csv or member.is_dir() or member.flag_bits & 1
                or stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in (0, stat.S_IFREG))
                or member.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                or not 0 < member.file_size <= RESPONSE_LIMIT):
            raise ValueError('unsafe, encrypted, unexpected or oversized ZIP member')
        with archive.open(member) as source:
            raw = source.read(RESPONSE_LIMIT + 1)
        if len(raw) != member.file_size or len(raw) > RESPONSE_LIMIT:
            raise ValueError('CSV decompression bound or declared size mismatch')
    # Only field count and open/close times are interpreted. Prices, volumes and labels stay opaque.
    year, month_number = map(int, month.split('-'))
    unit = 1_000_000 if year >= 2025 else 1_000
    start = int(datetime(year, month_number, 1, tzinfo=timezone.utc).timestamp()) * unit
    days = calendar.monthrange(year, month_number)[1]
    rows = 0
    for row in csv.reader(io.StringIO(raw.decode('utf-8')), strict=True):
        if len(row) != 12 or not re.fullmatch(r'[0-9]+', row[0]) or not re.fullmatch(r'[0-9]+', row[6]):
            raise ValueError('expected twelve fields and integral open/close timestamps')
        opening, closing = int(row[0]), int(row[6])
        expected_open = start + rows * 86400 * unit
        if opening != expected_open or closing != expected_open + 86400 * unit - 1:
            raise ValueError('UTC day continuity or timestamp-unit mismatch')
        rows += 1
        if rows > days:
            raise ValueError('more rows than calendar month')
    if rows != days:
        raise ValueError('incomplete calendar-month rows')
    return dict(month=month, zip_sha256=hashlib.sha256(zip_raw).hexdigest(),
                checksum_sha256=hashlib.sha256(checksum_raw).hexdigest(),
                csv_member=expected_csv, csv_bytes=len(raw), csv_sha256=hashlib.sha256(raw).hexdigest(),
                rows=rows, fields=12, timestamp_unit='us' if unit == 1_000_000 else 'ms',
                first_open_timestamp=start, last_open_timestamp=start + (days - 1) * 86400 * unit,
                price_fields_parsed=False, qualification='Archive/schema/timestamp admission only; prices and outcomes unopened.')


class DiskFloorStop(ValueError):
    """A provider-local permanent stop for this finite acquisition."""


def _get(capture, month, checksum=False):
    # Reserve the maximum retained response plus its sentinel so the floor survives acquisition.
    free = shutil.disk_usage(capture.directory).free
    if free < DISK_FLOOR + RESPONSE_LIMIT + 1:
        raise DiskFloorStop('disk free-space floor would be crossed; remaining spot acquisition stopped')
    body, receipt = capture.get(registered_url(month, checksum))
    if body is None or receipt.get('error') or receipt.get('status') != 200:
        raise ValueError('archive response unavailable: ' + str(receipt.get('error', receipt.get('status'))))
    return body, receipt


def capture_spot(directory):
    """Capture the exact 38-month cohort once, returning a durable immutable manifest."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    capture = storage.BinaryCapture(SPEC, directory)
    manifest = dict(status='unavailable', source='Binance public spot monthly archive',
                    market='spot', symbol='ETHUSDT', interval='1d', months=list(MONTHS),
                    requested_months=len(MONTHS), limits=dict(SPEC, disk_free_floor=DISK_FLOOR),
                    started_at=storage.now(), cells=[], price_fields_parsed=False)
    storage.atomic_json(directory / 'capture-intent.json', manifest)
    stop_reason = None
    for month in MONTHS:
        cell = dict(month=month, status='unavailable', reason=None,
                    zip_url=registered_url(month), checksum_url=registered_url(month, True), receipts=[])
        before = len(capture.records)
        requests_before = capture.count
        try:
            if stop_reason is not None:
                raise ValueError('unattempted after provider stop: ' + stop_reason)
            zip_raw, zip_receipt = _get(capture, month)
            checksum_raw, checksum_receipt = _get(capture, month, True)
            cell.update(validate_month(month, zip_raw, checksum_raw), status='complete',
                        zip_blob=zip_receipt['blob'], checksum_blob=checksum_receipt['blob'])
        except Exception as exc:
            if isinstance(exc, DiskFloorStop) or capture.denied:
                stop_reason = str(exc)
            cell.update(reason=f'{type(exc).__name__}: {exc}', error_type=type(exc).__name__)
        finally:
            # Include failed and partially acquired attempts, even when validation did not run.
            cell['network_requests'] = capture.count - requests_before
            cell['acquisition_attempted'] = cell['network_requests'] > 0
            cell['receipts'] = [dict(path=f'request-{r["request_number"]:04d}.json',
                                     request_number=r['request_number'], status=r['status'],
                                     error=r.get('error'), bytes=r['bytes'], sha256=r['sha256'], blob=r['blob'])
                                for r in capture.records[before:]]
            storage.atomic_json(directory / f'month-{month}.json', cell)
            manifest['cells'].append(cell)
    manifest.update(status='complete' if all(c['status'] == 'complete' for c in manifest['cells']) else 'unavailable',
                    complete_months=sum(c['status'] == 'complete' for c in manifest['cells']),
                    requests=capture.count, raw_bytes=capture.total, denied=capture.denied, stop_reason=stop_reason,
                    completed_at=storage.now())
    artifacts = []
    for path in sorted(directory.iterdir()):
        if path.is_file():
            raw = path.read_bytes()
            artifacts.append(dict(path=path.name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    manifest['artifacts'] = artifacts
    storage.atomic_json(directory / 'manifest.json', manifest)
    return manifest
