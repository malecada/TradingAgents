"""Synthetic exact-sentinel normalization and offline forensic reconstruction checks."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


forensic = load('graph_forensic_tested', ROOT / 'research/onchain-graph-2026-09-16/forensic/reconstruct.py')
fixtures = load('graph_forensic_fixtures', ROOT / 'tests/research/test_onchain_graph_prototype.py')


@pytest.mark.parametrize('recipient, changed', [('None', True), (None, False), ('none', False), ('None ', False), ('NULL', False), ('', False)])
def test_only_exact_sentinel_is_normalized_without_mutating_input(recipient, changed):
    row = list(fixtures.rows()[0]); row[6] = recipient
    result, actual = forensic.normalize_recipient(row)
    assert actual is changed and row[6] == recipient
    assert result[6] == (None if changed else recipient)


def test_saved_range_reconstruction_remains_offline_and_preserves_exclusion(monkeypatch):
    rows = [list(r) for r in fixtures.rows()]; rows[4][6] = 'None'
    monkeypatch.setattr(fixtures, 'rows', lambda: rows)
    plan, raw, footer, blocks = fixtures.parquet_fixture()
    def read(number):
        item = plan['ranges'][number - 1]; body = raw[item['start']:item['end'] + 1]
        return json.dumps({'status': 206, 'url': plan['base_url'] + plan['object']['key'],
            'request_number': number, 'request_headers': {'Range': f'bytes={item["start"]}-{item["end"]}', 'If-Match': '"fixture"'},
            'response_headers': {'content-range': f'bytes {item["start"]}-{item["end"]}/{len(raw)}', 'etag': '"fixture"'},
            'body_base64': base64.b64encode(body).decode(), 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}).encode()
    with patch.object(forensic.original.transport.urllib.request.OpenerDirector, 'open', side_effect=AssertionError('network prohibited')) as network:
        result = forensic.reconstruct(plan, footer, blocks, read)
    network.assert_not_called()
    assert result['normalization']['affected_rows'] == 1
    assert result['integrity']['checks_pass_after_declared_normalization']
    assert result['integrity']['categories']['null_recipient'] == 1
    assert result['diagnostic_graph']['events'] == 3
    assert not result['source_admitted_feature_panel'] and not result['original_lifecycle_result_changed']


def test_other_bad_strings_still_fail_integrity():
    state = fixtures.state()
    for row in fixtures.rows():
        row = list(row)
        if row[6] is None: row[6] = 'None '
        fixed, changed = forensic.normalize_recipient(row)
        state.add(fixed)
    result = state.finish()
    assert not result['admitted'] and result['errors']['invalid_recipient'] == 1
