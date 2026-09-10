"""Read-only public input checks and daily-coverage denominators; no PnL."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tradingagents.predlab.funding_snapshot import load_funding_snapshot


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def market_universe(run, manifest):
    """Compare exact requested identities with captured current market criteria."""
    requested = set(manifest['requested_symbols'])
    assert len(requested) == len(manifest['requested_symbols'])
    result = dict(status='unavailable', reason='successful raw exchangeInfo unavailable',
        requested_count=len(requested),
        captured_requested_count=sum(manifest['instruments'].get(s, {}).get('status') == 'captured'
                                     for s in requested),
        market_eligible_count=None, requested_market_eligible_count=None,
        omitted_market_eligible_symbols=None, requested_outside_market_criteria=None,
        market_eligible_underlying_type_counts=None, all_market_eligible_requested=None)
    observations = [(i, r) for i, r in enumerate(manifest['requests'])
                    if r['endpoint'] == '/fapi/v1/exchangeInfo' and
                    r['status'] == 200 and r.get('error') is None]
    if not observations:
        return result
    assert len(observations) == 1, 'ambiguous successful exchangeInfo observations'
    receipt_index, receipt = observations[0]
    body = json.loads((run / receipt['body_file']).read_bytes())
    assert isinstance(body, dict) and isinstance(body.get('symbols'), list)
    rows = body['symbols']
    assert all(isinstance(row, dict) and isinstance(row.get('symbol'), str) for row in rows)
    assert len({row['symbol'] for row in rows}) == len(rows), 'duplicate exchangeInfo identity'
    eligible = {row['symbol']: row for row in rows
                if row.get('status') == 'TRADING' and row.get('contractType') == 'PERPETUAL'
                and row.get('quoteAsset') == 'USDT' and row.get('marginAsset') == 'USDT'}
    omitted = sorted(set(eligible) - requested)
    result.update(status='observed', reason=None, receipt_index=receipt_index,
        body_file=receipt['body_file'], body_sha256=receipt['body_sha256'],
        market_eligible_count=len(eligible), requested_market_eligible_count=len(requested & set(eligible)),
        omitted_market_eligible_symbols=omitted,
        requested_outside_market_criteria=sorted(requested - set(eligible)),
        market_eligible_underlying_type_counts=dict(sorted(Counter(
            row.get('underlyingType') or '<missing>' for row in eligible.values()).items())),
        all_market_eligible_requested=not omitted)
    return result


def check(run):
    manifest_raw = (run / 'manifest.json').read_bytes()
    manifest = json.loads(manifest_raw)
    receipts = manifest['requests']
    assert [json.loads(line) for line in (run / 'requests.jsonl').read_text().splitlines()] == receipts
    for receipt in receipts:
        body = (run / receipt['body_file']).read_bytes()
        assert len(body) == receipt['body_bytes'] and digest(body) == receipt['body_sha256']
    source = manifest['source']
    committed = subprocess.check_output(['git', 'show', source['git_commit'] + ':tradingagents/predlab/funding_capture.py'], cwd=ROOT)
    assert digest(committed) == source['collector_sha256']
    normalized, event_count, types, offsets = [], 0, Counter(), Counter()
    for symbol, entry in manifest['instruments'].items():
        if entry['status'] != 'captured':
            continue
        path = run / entry['file']
        assert digest(path.read_bytes()) == entry['sha256']
        frame = pd.read_parquet(path)
        event_count += len(frame)
        types.update(frame.rateType)
        offsets.update(int(v % (3600 * 10**9) // 10**6) for v in frame.index.asi8)
        normalized.append({'symbol': symbol, 'rows': len(frame), 'sha256': entry['sha256']})
    result = dict(path=str(run.relative_to(ROOT)), manifest_sha256=digest(manifest_raw),
        source=source, status=manifest['status'], started_utc=manifest['started_utc'], completed_utc=manifest['completed_utc'],
        window=manifest['window'], requested=len(manifest['requested_symbols']),
        statuses=dict(Counter(e['status'] for e in manifest['instruments'].values())),
        unavailable={s:e['reason'] for s,e in manifest['instruments'].items() if e['status'] != 'captured'},
        requests=len(receipts), http_statuses=dict(Counter(str(r['status']) for r in receipts)),
        normalized=normalized, events=event_count, event_types=dict(types), offsets_ms=dict(sorted(offsets.items())),
        market_universe=market_universe(run, manifest))
    if manifest['status'] not in ('captured', 'partial'):
        result['error'] = manifest.get('error')
        return result
    start = pd.Timestamp(manifest['window']['start_ms'], unit='ms', tz='UTC').normalize()
    last_day = pd.Timestamp(manifest['window']['end_ms'], unit='ms', tz='UTC').normalize() - pd.Timedelta(days=1)
    days = pd.date_range(start, last_day, freq='D')
    daily, coverage = load_funding_snapshot(run, manifest['requested_symbols'], days)
    result['coverage'] = dict(method=coverage['method'], qualification=coverage['qualification'],
        alignment_policy_version=coverage['alignment_policy_version'],
        by_day={str(day.date()): {'admitted_inferred': int(daily.loc[day].notna().sum()),
                                'unavailable': int(daily.loc[day].isna().sum())} for day in days},
        latest_unavailable={symbol:coverage['symbols'][symbol] for symbol in daily.columns if pd.isna(daily.loc[last_day, symbol])},
        symbols={symbol:info for symbol,info in coverage['symbols'].items()})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs', nargs='+', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('verification output must be new')
    result = dict(kind='public-funding-data-integrity-and-coverage', checked_utc=pd.Timestamp.now(tz='UTC').isoformat(),
        financial_runs=0, paper_rows_written=0,
        reader_sha256=digest((ROOT/'tradingagents/predlab/funding_snapshot.py').read_bytes()),
        checker_sha256=digest(Path(__file__).read_bytes()), runs=[check(path.resolve()) for path in args.runs])
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'output':str(args.output), 'runs':[{k:r[k] for k in ('path','status','requested','statuses','requests','events')} for r in result['runs']]}))


if __name__ == '__main__':
    main()
