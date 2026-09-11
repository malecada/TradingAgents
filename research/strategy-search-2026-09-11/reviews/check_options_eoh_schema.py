"""Independent retained-byte/lexical reconstruction; no collector imports/network.

Only literal field identity, dimensions and emptiness are inspected. No numeric
CSV cells or CSV time semantics are interpreted.
"""
import base64
import csv
from datetime import datetime
from email.utils import parsedate_to_datetime
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / 'research_runs/options-eoh-schema-20260911'
REVIEW = Path(__file__).resolve().parent


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def blob(commit, path):
    assert re.fullmatch('[0-9a-f]{40}', commit)
    assert not Path(path).is_absolute() and '..' not in Path(path).parts
    assert not any(part in {'keys', 'apis', '.env', 'hf_token.txt'} for part in Path(path).parts)
    return subprocess.check_output(['git', 'show', f'{commit}:{path}'], cwd=ROOT)


def check():
    claim, terminal = read(RUN / 'claim.json'), read(RUN / 'complete.json')
    assert not (RUN / 'failed.json').exists()
    commit = claim['source']
    assert terminal['source'] == commit == claim['design_source']
    assert terminal['claim_sha256'] == sha((RUN / 'claim.json').read_bytes())
    gate_raw = blob(commit, claim['registration'])
    assert sha(gate_raw) == terminal['registration_sha256'] == claim['registration_sha256']
    gate = json.loads(gate_raw)
    contract = gate['experiments'][claim['experiment_id']]
    assert contract == claim['experiment']
    assert claim['family'] == gate['families'][contract['family']]
    assert contract['parent'] == 'options-metadata-20260911'
    assert contract['stage'] == 'development' and contract['reuse'] == 'exploratory'
    assert contract['selection'] is None
    old_gate = json.loads(blob(commit, 'research/strategy-search-2026-09-11/gates-options-metadata.json'))
    for group in ['families', 'datasets', 'experiments']:
        assert all(gate[group][key] == value for key, value in old_gate[group].items())
    pins = dict(contract['source_files'])
    pins[contract['charter']['path']] = contract['charter']['sha256']
    pins.update({'tradingagents/research/' + name: value for name, value in contract['runtime_hashes'].items()})
    for path, digest in pins.items():
        assert sha(blob(commit, path)) == digest
    spec_info = contract['inputs']['request_spec']
    spec_raw = blob(commit, spec_info['path'])
    assert sha(spec_raw) == spec_info['sha256']
    spec = json.loads(spec_raw)
    output_dir = RUN / 'outputs'
    names = set(contract['outputs'])
    assert names == set(terminal['output_sha256']) == {path.name for path in output_dir.iterdir()}
    assert len(names) == 4
    for name, digest in terminal['output_sha256'].items():
        assert sha((output_dir / name).read_bytes()) == digest
    capture, schema = read(output_dir / 'eoh-capture.json'), read(output_dir / 'eoh-schema.json')
    assert capture['request_spec'] == spec
    ids = [request['id'] for request in spec['requests']]
    assert ids == contract['cells'] and len(set(ids)) == 2
    assert [row['id'] for row in capture['requests']] == ids
    assert terminal['cells'] == schema['cells'] == [{'id': name, 'status': 'complete'} for name in ids]
    assert terminal['cell_count'] == 2 and terminal['unavailable_count'] == 0
    clocks, bodies = [], []
    previous_end = datetime.fromisoformat(claim['started_at'])
    for request, aggregate in zip(spec['requests'], capture['requests']):
        receipt = read(output_dir / (request['id'] + '-receipt.json'))
        assert aggregate == receipt
        assert all(receipt[key] == value for key, value in request.items())
        assert receipt['attempted'] is True and receipt['http_status'] == 200
        assert receipt['body_complete'] is True and receipt['error'] is None
        body = base64.b64decode(receipt['body_base64'], validate=True)
        assert len(body) == receipt['body_bytes'] <= spec['max_response_bytes']
        assert sha(body) == receipt['body_sha256']
        start, end = (datetime.fromisoformat(receipt[key]) for key in ('request_utc', 'retrieval_utc'))
        assert previous_end <= start <= end <= datetime.fromisoformat(terminal['ended_at'])
        assert start.utcoffset().total_seconds() == end.utcoffset().total_seconds() == 0
        clock_delta = (end - start).total_seconds()
        assert abs(clock_delta - receipt['elapsed_seconds']) < .001
        assert 0 <= receipt['elapsed_seconds'] <= spec['timeout_seconds_per_request']
        http_date = parsedate_to_datetime(next(value for key, value in receipt['headers'].items() if key.lower() == 'date'))
        clocks.append({'id': request['id'], 'request_utc': receipt['request_utc'],
                       'retrieval_utc': receipt['retrieval_utc'], 'monotonic_elapsed_seconds': receipt['elapsed_seconds'],
                       'local_vs_monotonic_difference_seconds': clock_delta - receipt['elapsed_seconds'],
                       'http_date_minus_local_retrieval_seconds': (http_date-end).total_seconds()})
        bodies.append(body)
        previous_end = end
    assert sum(map(len, bodies)) == capture['total_body_bytes'] <= spec['max_total_response_bytes']
    checksum_text = bodies[1].decode('utf-8')
    expected_line = sha(bodies[0]) + '  ' + spec['requests'][0]['filename']
    assert checksum_text in (expected_line, expected_line + '\n')
    assert schema['paired_integrity'] == {'status': 'complete', 'sha256': sha(bodies[0])}
    with zipfile.ZipFile(io.BytesIO(bodies[0])) as archive:
        entries = archive.infolist()
        assert len(entries) == 1
        entry = entries[0]
        assert entry.filename == spec['expected_member'] and not entry.is_dir()
        assert not entry.flag_bits & 1
        assert 0 < entry.compress_size and entry.file_size <= spec['max_uncompressed_bytes']
        assert entry.file_size / entry.compress_size <= spec['max_compression_ratio']
        content = archive.read(entry)  # Standard library verifies CRC on full read.
        assert len(content) == entry.file_size
        archive_ratio = entry.file_size / entry.compress_size
    text = content.decode('utf-8')
    old_limit = csv.field_size_limit(spec['max_csv_field_characters'])
    try:
        rows = list(csv.reader(io.StringIO(text, newline=''), strict=True))
    finally:
        csv.field_size_limit(old_limit)
    assert rows
    first, remaining = rows[0], rows[1:]
    widths = sorted(set(map(len, rows)))
    frequencies = {str(width): sum(len(row) == width for row in rows) for width in widths}
    profiles = [{'column_index': column,
                 'empty_string_count': sum(len(row) > column and row[column] == '' for row in remaining),
                 'absent_column_count': sum(len(row) <= column for row in remaining)} for column in range(max(widths))]
    ragged = [index for index, row in enumerate(rows, 1) if len(row) != len(first)]
    expected = {'candidate_header': first, 'column_index_base': 0, 'member': entry.filename,
                'member_sha256': sha(content), 'uncompressed_bytes': len(content),
                'utf8_bom_present': content.startswith(b'\xef\xbb\xbf'),
                'total_records_including_first': len(rows), 'records_after_first': len(remaining),
                'record_width_frequencies': frequencies, 'record_index_base': 1,
                'ragged_record_count': len(ragged), 'ragged_record_indices': ragged,
                'blank_record_count_including_first': sum(len(row) == 0 for row in rows),
                'column_missingness_after_first': profiles}
    result = schema['lexical_schema']
    assert result['status'] == 'complete'
    for key, value in expected.items():
        assert result[key] == value, key
    assert result['header_semantics'].startswith('unverified candidate')
    assert result['field_semantics'].startswith('unavailable; no bid/ask/size/time mapping')
    assert schema['scope'] == 'Literal single-object discovery; no prices, clocks, executable quotes or financial meaning admitted'
    actual_output_bytes = sum((output_dir/name).stat().st_size for name in names)
    assert actual_output_bytes <= spec['max_output_bytes']
    literal_bytes = len((json.dumps(result, sort_keys=True, indent=2, allow_nan=False)+'\n').encode())
    assert literal_bytes <= spec['max_schema_output_bytes']
    resource_report = read(REVIEW / 'options-eoh-resource-execution.json')
    assert resource_report['child_exit_code'] == 0 and resource_report['limit_reason'] is None
    assert resource_report['peak_sampled_tree_rss_bytes'] <= spec['max_memory_mib']*1024**2
    assert resource_report['elapsed_seconds'] <= spec['max_wall_seconds']
    historical_claims = []
    for path in (ROOT/'research_runs').glob('*/claim.json'):
        other = read(path)
        if other['family']['mechanism_id'] == claim['family']['mechanism_id'] and other['started_at'] <= claim['started_at']:
            historical_claims.append(other['experiment_id'])
    used = claim['family']['prior_attempts'] + len(historical_claims)
    return {'status': 'pass', 'scope': 'Independent raw-byte and lexical reconstruction only; no collector imports, network or numeric CSV interpretation',
            'source': commit, 'registration_sha256': sha(gate_raw), 'claim_sha256': terminal['claim_sha256'],
            'output_sha256': terminal['output_sha256'], 'cells': 2, 'unavailable_cells': 0, 'outputs': 4,
            'actual_output_bytes': actual_output_bytes, 'lexical_output_bytes': literal_bytes,
            'raw_body_bytes': list(map(len, bodies)), 'zip_sha256': sha(bodies[0]), 'checksum_body_sha256': sha(bodies[1]),
            'zip_member_compression_ratio': archive_ratio, 'reconstructed_lexical_fields': expected,
            'capture_clocks': clocks, 'resource_report': resource_report,
            'family_claims_through_this_run': sorted(historical_claims), 'known_prior_administrative_bundles': claim['family']['prior_attempts'],
            'used_administrative_units_through_this_run': used, 'remaining_units_then': claim['family']['attempt_budget']-used,
            'untested': ['official field meaning or clock units', 'CSV numeric values, quotes and prices',
                         'historical lifecycle or chain completeness', 'fees/lots/access/fills and financial performance',
                         'independent server-clock attestation', 'remote recoverability']}


if __name__ == '__main__':
    report = check()
    (REVIEW/'options-eoh-review.json').write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print(json.dumps({key: report[key] for key in ['status', 'cells', 'outputs', 'actual_output_bytes', 'remaining_units_then']}))
