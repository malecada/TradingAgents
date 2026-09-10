"""Timestamp-only inventory under the September 10 data-recovery charter."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
import pyarrow.parquet as pq

from scripts.audit_reeval_common import sha256

KEY = 'audit_data_recovery_2026_09_10'
START = pd.Timestamp('2020-06-01', tz='UTC')
END = pd.Timestamp('2025-04-01', tz='UTC')
MAJORS = {'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'DOGEUSDT', 'XRPUSDT', 'TRXUSDT'}


def ranges(index, freq):
    if not len(index):
        return []
    step = pd.Timedelta(freq)
    groups = (index.to_series().diff() != step).cumsum()
    return [{'start': str(g.iloc[0]), 'end_exclusive': str(g.iloc[-1]+step), 'periods': len(g)}
            for _, g in index.to_series().groupby(groups)]


def inspect_clock(path, freq):
    schema = pq.ParquetFile(path).schema_arrow
    meta = json.loads(schema.metadata.get(b'pandas', b'{}'))
    indexes = [x for x in meta.get('index_columns', []) if isinstance(x, str)]
    field = 'ts' if 'ts' in schema.names else (indexes[0] if indexes else None)
    if field is None:
        raise ValueError(f'no explicit timestamp: {path}')
    # Only the timestamp column is materialized, and never beyond development.
    table = pq.read_table(path, columns=[field], filters=[(field, '>=', START), (field, '<', END)])
    clock = pd.DatetimeIndex(table.column(field).to_pandas())
    if clock.tz is None:
        raise ValueError(f'naive clock: {path}')
    clock = clock.tz_convert('UTC')
    row = {'path': str(path), 'sha256': sha256(path), 'n_rows': len(clock),
           'unique': clock.is_unique, 'monotone': clock.is_monotonic_increasing,
           'aligned': bool((clock == clock.floor(freq)).all()),
           'first': str(clock.min()) if len(clock) else None,
           'last': str(clock.max()) if len(clock) else None}
    if len(clock):
        expected = pd.date_range(clock.min(), clock.max(), freq=freq)
        gaps = expected.difference(clock)
        row.update(internal_missing_periods=len(gaps), internal_ranges=ranges(gaps, freq),
                   leading_unobserved_periods=int((clock.min()-START)/pd.Timedelta(freq)),
                   trailing_unobserved_periods=int((END-clock.max())/pd.Timedelta(freq))-1)
    return row


def main():
    from tradingagents.predlab import registry
    gate = registry.get_experiment(KEY)
    if gate['strategy_evaluation_permitted'] or gate['price_inventory_window'] != [START.isoformat().replace('+00:00','Z'), END.isoformat().replace('+00:00','Z')]:
        raise ValueError('inventory contract differs')
    source = Path(gate['source_roots'][0])/'xsect'
    names_file = source/'liq_fade_symbols.txt'
    manifest_file = source/'klines_manifest.json'
    hourly = sorted(set(names_file.read_text().split()) | MAJORS)
    daily = sorted(json.loads(manifest_file.read_text()))
    out = ROOT/gate['output_root']/'clock-inventory.json'
    if out.exists():
        raise FileExistsError(out)
    result = {'experiment': KEY, 'created_utc': datetime.now(timezone.utc).isoformat(),
              'transform_commit': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
              'gate_sha256': sha256(registry.gates_path()), 'window': [str(START),str(END)],
              'materialized_fields': ['timestamp'], 'strategy_metrics_computed': False,
              'scope_files': {str(p): sha256(p) for p in (names_file,manifest_file)},
              'tail_interpretation': 'Unobserved leading/trailing periods are not classified as missing trades; listings and terminations require lifecycle evidence.'}
    for name, symbols, folder, freq in [('hourly',hourly,'klines_1h','1h'), ('daily',daily,'klines','1D')]:
        rows = [dict(symbol=s, **inspect_clock(source/folder/f'{s}.parquet',freq)) for s in symbols]
        result[name] = {'n_files':len(rows), 'n_with_development_rows':sum(r['n_rows']>0 for r in rows),
                        'n_files_with_internal_gaps':sum(r.get('internal_missing_periods',0)>0 for r in rows),
                        'total_internal_missing_periods':sum(r.get('internal_missing_periods',0) for r in rows), 'files':rows}
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('x') as f:
        json.dump(result,f,indent=2,allow_nan=False)
        f.write('\n')
    print(json.dumps({k:{a:b for a,b in result[k].items() if a!='files'} for k in ('hourly','daily')}))


if __name__ == '__main__':
    main()
