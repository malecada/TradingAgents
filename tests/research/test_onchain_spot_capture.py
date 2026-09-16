"""Invented spot archives only. No external HTTP or observed prices."""
import calendar
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('comparison_spot_capture_test', ROOT / 'research/onchain-graph-2026-09-16/comparison/spot_capture.py')
spot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(spot)


def fixture(month, *, member=None, unit_override=None, columns=12, extra=False):
    year, number = map(int, month.split('-'))
    unit = unit_override or (1_000_000 if year >= 2025 else 1000)
    start = int(datetime(year, number, 1, tzinfo=timezone.utc).timestamp()) * unit
    rows = []
    for day in range(calendar.monthrange(year, number)[1]):
        opening = start + day * 86400 * unit
        row = ['opaque-not-a-number'] * 12
        row[0], row[6] = str(opening), str(opening + 86400 * unit - 1)
        rows.append(','.join(row[:columns]))
    sink = io.BytesIO()
    with zipfile.ZipFile(sink, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        info = zipfile.ZipInfo(member or spot.archive_name(month)[:-4] + '.csv', date_time=(2020, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, '\n'.join(rows) + '\n')
        if extra:
            archive.writestr(zipfile.ZipInfo('extra.csv', date_time=(2020, 1, 1, 0, 0, 0)), 'bad')
    raw = sink.getvalue()
    checksum = (hashlib.sha256(raw).hexdigest() + '  ' + spot.archive_name(month) + '\n').encode()
    return raw, checksum


def test_exact_cohort_urls_and_units_without_price_parsing():
    assert len(spot.MONTHS) == 38 and len(set(spot.MONTHS)) == 38
    assert spot.MONTHS[0] == '2021-12' and spot.MONTHS[-1] == '2025-01'
    assert spot.registered_url('2025-01', True) == 'https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1d/ETHUSDT-1d-2025-01.zip.CHECKSUM'
    for month, unit in [('2024-02', 'ms'), ('2025-01', 'us')]:
        result = spot.validate_month(month, *fixture(month))
        assert result['timestamp_unit'] == unit and not result['price_fields_parsed']
    with pytest.raises(ValueError, match='frozen'):
        spot.registered_url('2025-02')
    with pytest.raises(ValueError, match='timestamp-unit'):
        spot.validate_month('2025-01', *fixture('2025-01', unit_override=1000))


@pytest.mark.parametrize('kwargs', [{'member': '../escape.csv'}, {'extra': True}, {'columns': 11}])
def test_zip_member_and_schema_safety(kwargs):
    with pytest.raises(ValueError):
        spot.validate_month('2024-02', *fixture('2024-02', **kwargs))


def test_checksum_and_uncompressed_bound():
    raw, checksum = fixture('2024-02')
    with pytest.raises(ValueError, match='checksum'):
        spot.validate_month('2024-02', raw + b'bad', checksum)
    sink = io.BytesIO()
    with zipfile.ZipFile(sink, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('ETHUSDT-1d-2024-02.csv', b'x' * (spot.RESPONSE_LIMIT + 1))
    raw = sink.getvalue()
    checksum = (hashlib.sha256(raw).hexdigest() + '  ETHUSDT-1d-2024-02.zip').encode()
    with pytest.raises(ValueError, match='oversized'):
        spot.validate_month('2024-02', raw, checksum)


class Response(io.BytesIO):
    def __init__(self, body, status):
        super().__init__(body)
        self.status = status
        self.headers = {'content-length': str(len(body))}


class Opener:
    def __init__(self, status=200):
        self.calls = []
        self.status = status
    def open(self, request, timeout):
        self.calls.append(request.full_url)
        assert timeout == 30
        assert request.full_url in {spot.registered_url(m, c) for m in spot.MONTHS for c in (False, True)}
        assert not request.has_header('Authorization')
        month = request.full_url.split('ETHUSDT-1d-')[1][:7]
        body = fixture(month)[request.full_url.endswith('.CHECKSUM')]
        return Response(body if self.status == 200 else b'unavailable', self.status)


def test_complete_capture_76_requests_immutable_and_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        destination = Path(tmp) / 'capture'
        opener = Opener()
        with patch.object(spot.storage.urllib.request, 'build_opener', return_value=opener), patch.object(spot.shutil, 'disk_usage', return_value=SimpleNamespace(free=30 * 1024 ** 3)):
            result = spot.capture_spot(destination)
        assert result['status'] == 'complete' and result['complete_months'] == 38
        assert len(opener.calls) == result['requests'] == 76
        assert result['raw_bytes'] < spot.TOTAL_LIMIT
        assert len(result['artifacts']) == 38 + 76 * 3 + 1
        for cell in result['cells']:
            assert len(cell['receipts']) == 2 and cell['fields'] == 12
            for key in ('zip_blob', 'checksum_blob'):
                meta = cell[key]
                restored = spot.storage.read_blob(destination / meta['path'], meta)
                assert hashlib.sha256(restored).hexdigest() == meta['raw_sha256']
        with pytest.raises(FileExistsError):
            spot.capture_spot(destination)


def test_denial_and_disk_floor_retain_every_month_without_retry():
    for free, status, calls in [(30 * 1024 ** 3, 403, 1), (spot.DISK_FLOOR, 200, 0), (30 * 1024 ** 3, 404, 38)]:
        with tempfile.TemporaryDirectory() as tmp:
            opener = Opener(status)
            with patch.object(spot.storage.urllib.request, 'build_opener', return_value=opener), patch.object(spot.shutil, 'disk_usage', return_value=SimpleNamespace(free=free)):
                result = spot.capture_spot(Path(tmp) / 'capture')
            assert result['status'] == 'unavailable' and result['complete_months'] == 0
            assert len(result['cells']) == 38 and len(opener.calls) == calls
            assert all(cell['reason'] for cell in result['cells'])


def test_disk_floor_stop_latches_even_if_free_space_returns():
    with tempfile.TemporaryDirectory() as tmp:
        opener = Opener()
        observations = [SimpleNamespace(free=spot.DISK_FLOOR), SimpleNamespace(free=30 * 1024 ** 3)]
        with patch.object(spot.storage.urllib.request, 'build_opener', return_value=opener), patch.object(spot.shutil, 'disk_usage', side_effect=observations) as disk:
            result = spot.capture_spot(Path(tmp) / 'capture')
        assert disk.call_count == 1 and not opener.calls
        assert result['stop_reason'] and all(not cell['acquisition_attempted'] for cell in result['cells'])
        assert all('unattempted after provider stop' in cell['reason'] for cell in result['cells'][1:])
