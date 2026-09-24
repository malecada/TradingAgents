import json
from pathlib import Path
import pytest
from tradingagents.research.onchain_replication.cells import enumerate_cells,initial_cells,reconcile_cells


def test_full_paper_and_diagnostic_denominators_are_finite_and_reused():
    root=Path(__file__).resolve().parents[3]/'research/onchain-paper-replication-2026-09-24'
    cells=enumerate_cells(json.loads((root/'table-map.json').read_bytes()),json.loads((root/'config/training.json').read_bytes()))
    assert len(cells)==1420 and sum(bool(c['tables']) for c in cells)==1400
    assert len(initial_cells(cells))==45
    assert any(len(c['tables'])>1 for c in cells)
    assert reconcile_cells(cells,cells)['statuses']['pending']==1420
    with pytest.raises(ValueError):reconcile_cells(cells,cells[:-1])


def test_every_scientific_identity_has_unique_reversible_lifecycle_name():
    import json
    from pathlib import Path
    from tradingagents.research.onchain_replication.cells import lifecycle_cell_id,scientific_cell_id
    root=Path(__file__).resolve().parents[3]/'research/onchain-paper-replication-2026-09-24'
    rows=json.loads((root/'table-map.json').read_bytes())
    if isinstance(rows,dict):rows=rows['rows']
    cells=enumerate_cells(rows,json.loads((root/'config/training.json').read_bytes()))
    mapped=[lifecycle_cell_id(c['id']) for c in cells]
    assert len(set(mapped))==1420
    assert [scientific_cell_id(x) for x in mapped]==[c['id'] for c in cells]
