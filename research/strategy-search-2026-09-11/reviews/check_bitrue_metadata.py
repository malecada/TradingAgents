"""Independent saved-source verification; no collector imports or network."""
from pathlib import Path
import base64
from collections import Counter
from datetime import datetime
import hashlib
import json
import math
import subprocess

ROOT = Path(__file__).resolve().parents[3]
PROGRAM = ROOT / 'research/strategy-search-2026-09-11'
RUN = ROOT / 'research_runs/bitrue-metadata-20260911'
SOURCE = '328b23f88357656a23ce5ba2874cf514f6fce547'

def pairs(items):
    result = {}
    for key, value in items:
        assert key not in result, 'duplicate JSON key'
        result[key] = value
    return result

def strict(raw):
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                       parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    def check(x):
        if isinstance(x, float): assert math.isfinite(x)
        elif isinstance(x, dict):
            for y in x.values(): check(y)
        elif isinstance(x, list):
            for y in x: check(y)
    check(value)
    return value

def read(path): return strict(path.read_bytes())
def sha(raw): return hashlib.sha256(raw).hexdigest()
def same(a, b): assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
def clock(s):
    value = datetime.fromisoformat(s)
    assert value.utcoffset().total_seconds() == 0
    return value

def main():
    gate_path = PROGRAM / 'gates-bitrue-metadata.json'
    gate = read(gate_path)
    assert sha(gate_path.read_bytes()) == 'c8325be306f6a4faa4af5df94f8764d741c9550a81409ae01117195b51dba51c'
    exp = gate['experiments']['bitrue-metadata-20260911']
    claim, complete = read(RUN/'claim.json'), read(RUN/'complete.json')
    assert claim['design_source'] == complete['source'] == SOURCE
    same(claim['experiment'], exp)
    assert complete['claim_sha256'] == sha((RUN/'claim.json').read_bytes())
    assert complete['registration_sha256'] == sha(gate_path.read_bytes())
    pinned = dict(exp['source_files'])
    for entry in [exp['charter'], *exp['inputs'].values()]: pinned[entry['path']] = entry['sha256']
    for name, digest in exp['runtime_hashes'].items(): pinned['tradingagents/research/'+name] = digest
    pinned[str(gate_path.relative_to(ROOT))] = sha(gate_path.read_bytes())
    for name, digest in pinned.items():
        assert sha((ROOT/name).read_bytes()) == digest
        committed = subprocess.check_output(['git', 'show', SOURCE+':'+name], cwd=ROOT)
        assert sha(committed) == digest
    outputs = RUN/'outputs'
    assert set(complete['output_sha256']) == set(exp['outputs']) == {p.name for p in outputs.iterdir()}
    for name, digest in complete['output_sha256'].items(): assert sha((outputs/name).read_bytes()) == digest
    spec = read(ROOT/exp['inputs']['request_spec']['path'])
    capture, admission = read(outputs/'metadata-capture.json'), read(outputs/'metadata-admission.json')
    same(capture['request_spec'], spec)
    assert len(capture['requests']) == len(admission['cells']) == 2
    rows = None
    previous = None
    total = 0
    for request, receipt, cell in zip(spec['requests'], capture['requests'], admission['cells']):
        same(read(outputs/(request['id']+'-receipt.json')), receipt)
        for key, value in request.items(): assert receipt[key] == value
        assert receipt['attempted'] is True and receipt['body_complete'] is True
        assert type(receipt['http_status']) is int and receipt['http_status'] == 200 and receipt['error'] is None
        raw = base64.b64decode(receipt['body_base64'], validate=True)
        assert type(receipt['body_bytes']) is int and len(raw) == receipt['body_bytes'] <= spec['max_response_bytes']
        assert sha(raw) == receipt['body_sha256']
        start, end = clock(receipt['request_utc']), clock(receipt['retrieval_utc'])
        assert start <= end and (previous is None or previous <= start)
        assert 0 <= receipt['elapsed_seconds'] <= spec['timeout_seconds']
        previous = end
        total += len(raw)
        value = strict(raw)
        assert cell['id'] == request['id'] and cell['status'] == 'complete'
        if request['kind'] == 'server-time':
            assert isinstance(value, dict) and 'code' not in value
            same(cell['raw_fields'], value)
            assert cell['clock_semantics']['status'] == 'unavailable'
            continue
        rows = value
        assert isinstance(rows, list) and all(isinstance(r, dict) for r in rows)
        names = [r.get('symbol') for r in rows]
        assert all(isinstance(n, str) and n for n in names) and len(set(names)) == len(names)
        same(cell['contract_rows'], rows)
        assert cell['observed_rows'] == len(rows) == len(cell['row_metadata'])
        for index, (row, normalized) in enumerate(zip(rows, cell['row_metadata'])):
            problems = []
            for field in ('symbol','type','multiplierCoin'):
                if not isinstance(row.get(field),str) or not row[field]: problems.append(field+' missing or invalid')
            for field in ('side','status'):
                if type(row.get(field)) is not int or row[field] not in (0,1): problems.append(field+' undocumented or invalid')
            for field in ('multiplier','minOrderVolume','minOrderMoney'):
                v = row.get(field)
                valid = type(v) in (int,float) and math.isfinite(v) and (v >= 0 if field == 'minOrderMoney' else v > 0)
                if not valid: problems.append(field+' missing or invalid')
            asset = {'E-BTC-USDT':'BTC','E-ETH-USDT':'ETH'}.get(row['symbol'])
            matched = not problems and asset is not None and row['multiplierCoin']==asset and row['type']=='E' and row['side']==1 and row['status']==1
            same(normalized, {'row_index':index,'metadata_status':'unavailable' if problems else 'complete',
                 'problems':problems,'conditional_target_asset':asset if matched else None,
                 'target_mapping':'conditional literal naming/unit match' if matched else 'ambiguous or outside fixed target mapping',
                 'account_eligibility':'unavailable'})
    assert total == capture['total_body_bytes']
    assert clock(complete['ended_at']) >= previous
    same(complete['cells'], [{'id':r['id'],'status':'complete'} for r in spec['requests']])
    assert complete['cell_count']==2 and complete['unavailable_count']==0
    output_bytes = sum(p.stat().st_size for p in outputs.iterdir())
    assert output_bytes <= spec['max_output_bytes'] and (outputs/'metadata-admission.json').stat().st_size <= spec['max_admission_bytes']
    guard = read(PROGRAM/'reviews/bitrue-resource-execution.json')
    assert guard['child_exit_code']==0 and guard['limit_reason'] is None
    assert guard['elapsed_seconds'] <=120 and guard['peak_sampled_tree_rss_bytes'] <=512*1024**2
    result = {'review':'PASS source admission only','source':SOURCE,'requests':2,'complete':2,'unavailable':0,
        'raw_bytes':total,'output_bytes':output_bytes,'rows':len(rows),
        'row_metadata_statuses':dict(Counter(r['metadata_status'] for r in admission['cells'][0]['row_metadata'])),
        'conditional_target_rows':[r for r in rows if r['symbol'] in ('E-BTC-USDT','E-ETH-USDT')],
        'first_request_utc':capture['requests'][0]['request_utc'],'last_retrieval_utc':capture['requests'][-1]['retrieval_utc'],
        'time_semantics':'unavailable; no field-unit inference','resource':guard,
        'limitation':'No funding cashflows, applicable fees, margin, eligibility, synchronized Binance comparison or profitability established.'}
    (PROGRAM/'reviews/bitrue-metadata-review.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('conditional_target_rows','resource')}))

if __name__ == '__main__': main()
