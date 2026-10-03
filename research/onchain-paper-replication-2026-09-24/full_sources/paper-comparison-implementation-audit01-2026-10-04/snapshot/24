import json
from pathlib import Path
import pytest
from tradingagents.research.onchain_replication.cells import enumerate_cells
from tradingagents.research.onchain_replication.comparison import execution_batches,table_results

ROOT=Path(__file__).resolve().parents[3]/'research/onchain-paper-replication-2026-09-24'


def inputs():return json.loads((ROOT/'table-map.json').read_bytes()),json.loads((ROOT/'config/training.json').read_bytes())


def test_full_matrix_allocates_initial_once_and_every_later_asset_year():
    rows,config=inputs();plan=execution_batches(rows,config)
    assert len(plan['batches'])==15 and plan['unique_fits']==1420 and plan['paper_fits']==1400 and plan['diagnostic_fits']==20
    assert len(plan['batches'][0]['cells'])==45
    assert len(next(x for x in plan['batches'] if x['id']=='ETH-2024')['cells'])==100
    assert {x['id'] for x in plan['batches'][1:]}=={a+'-'+str(y) for a in ('BTC','ETH') for y in range(2018,2025)}


def test_printed_rows_reuse_identical_cells_and_do_not_average_survivors():
    rows,config=inputs();cells=[dict(c) for c in enumerate_cells(rows,config)]
    for c in cells:c.update(status='complete',metrics={'accuracy':c['seed']/100.,'N':int(c['fold'])})
    report=table_results(rows,config,cells)
    assert report['printed_rows']==44 and sum(r['expected_cells'] for r in report['rows'])==1540
    first=report['rows'][0]
    assert first['all_seed_mean']['accuracy']==pytest.approx(.386)
    assert first['all_seed_range']['accuracy']==[.11,.71]
    assert first['all_seed_mean']['N']==2021
    control=next(r for r in report['rows'] if r['table']==4 and r['asset']=='BTC' and r['variant']=='whole')
    assert control['cell_ids']==first['cell_ids']
    changed=next(c for c in cells if c['id']==first['cell_ids'][0]);changed.update(status='failed',reason='synthetic failure')
    incomplete=table_results(rows,config,cells)
    retained=next(c for c in incomplete['cell_dispositions'] if c['id']==changed['id'])
    assert retained['status']=='failed' and retained['reason']=='synthetic failure'
    for r in incomplete['rows']:
        if changed['id'] in r['cell_ids']:
            assert not r['complete'] and r['all_seed_mean'] is None and r['statuses']['failed']==1
    with pytest.raises(ValueError,match='denominator'):table_results(rows,config,cells[:-1])
