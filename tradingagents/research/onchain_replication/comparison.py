"""Finite execution allocation and literal table reporting without survivor means."""
import math
import copy
from .cells import enumerate_cells,initial_cells,reconcile_cells
from .cache import cache_key


def execution_batches(table_rows,training_config):
    cells=enumerate_cells(table_rows,training_config)
    first=initial_cells(cells);used={c['id'] for c in first}
    batches=[{'id':'initial-ETH-2024','asset':'ETH','fold':'2024','cells':[c['id'] for c in first]}]
    for asset in ('BTC','ETH'):
        for fold in sorted({c['fold'] for c in cells if c['asset']==asset}):
            group=[c['id'] for c in cells if c['asset']==asset and c['fold']==fold and c['id'] not in used]
            if group:batches.append({'id':asset+'-'+fold,'asset':asset,'fold':fold,'cells':group})
    assigned=[cell for batch in batches for cell in batch['cells']]
    if len(assigned)!=len(set(assigned)) or set(assigned)!={c['id'] for c in cells}:raise ValueError('execution allocation differs from complete cell denominator')
    return {'schema_version':1,'batches':batches,'unique_fits':len(cells),
        'paper_fits':sum(bool(c['tables']) for c in cells),'diagnostic_fits':sum(not c['tables'] for c in cells),
        'cell_hash':cache_key(cells),'qualification':'allocation only; no source/resource/fit admission'}


def table_results(table_rows,training_config,dispositions):
    """All printed rows, all years and all seeds, with exact shared-fit reuse.

    The input is a full fit-cell ledger. Incomplete rows retain each disposition
    and have no headline average. Complete rows use equal annual means per seed,
    then the mean and range over every registered seed. Metrics must already be
    independently reconciled from immutable per-date predictions.
    """
    expected=enumerate_cells(table_rows,training_config)
    ledger=reconcile_cells(expected,dispositions)
    by_id={x['id']:x for x in dispositions};output=[]
    for row_index,row in enumerate(table_rows):
        expanded=[row['cell_pattern'].format(fold=fold,seed=seed) for seed in row['seeds'] for fold in row['folds']]
        if len(expanded)!=len(set(expanded)):raise ValueError('duplicate printed-row member')
        cells=[by_id[h] for h in expanded];counts={status:sum(c['status']==status for c in cells) for status in ('complete','failed','unavailable','pending')}
        record={'row_index':row_index,'table':row['table'],'asset':row['asset'],'task':row['task'],
            'arm':row['arm'],'variant':row['variant'],'cell_ids':expanded,'expected_cells':len(expanded),
            'statuses':counts,'complete':counts['complete']==len(expanded),'seed_annual_means':None,
            'all_seed_mean':None,'all_seed_range':None,'metrics_verified':False}
        if record['complete']:
            keys=None;per_seed={}
            for seed in row['seeds']:
                annual=[]
                for fold in row['folds']:
                    cell=by_id[row['cell_pattern'].format(fold=fold,seed=seed)]
                    values=cell.get('metrics')
                    if not isinstance(values,dict) or not values:raise ValueError('complete cell lacks metrics')
                    if keys is None:keys=set(values)
                    if set(values)!=keys:raise ValueError('printed-row metric membership differs')
                    if any(type(v) not in (int,float) or not math.isfinite(v) for v in values.values()):raise ValueError('invalid metric scalar')
                    annual.append(values)
                per_seed[str(seed)]={k:math.fsum(a[k] for a in annual)/len(annual) for k in sorted(keys)}
            record.update(seed_annual_means=per_seed,
                all_seed_mean={k:math.fsum(v[k] for v in per_seed.values())/len(per_seed) for k in sorted(keys)},
                all_seed_range={k:[min(v[k] for v in per_seed.values()),max(v[k] for v in per_seed.values())] for k in sorted(keys)})
        else:record['reason']='Every registered year and seed is required; available cells are not substituted for the full row.'
        output.append(record)
    return {'schema_version':1,'rows':output,'printed_rows':len(output),'fit_ledger':ledger,
        'cell_dispositions':copy.deepcopy(list(dispositions)),
        'numerical_agreement':None,'qualification':'arithmetic/coverage only; independent prediction/metric evidence and published-paper comparison remain separate'}
