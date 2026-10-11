"""Plan validation uses invented metadata; no graph bodies or launcher."""
import copy
import pytest
from tradingagents.research.onchain_replication import real_pilot_import_caller as caller
from tradingagents.research.onchain_replication.phase_timing import FORMAT


def plan():
    hashes=[f'{n:064x}' for n in range(1,8)];gib=1024**3
    limits={'max_allocated_bytes':gib,'max_logical_bytes':gib,'max_entries':32768,'max_depth':32,'max_scan_seconds':5}
    resources={'memory_max_bytes':gib,'memory_high_bytes':gib,'reserve_bytes':3*gib,
        'start_reserve_bytes':4*gib,'disk_floor_bytes':10*gib,'disk_paths':['/invented'],
        'wall_seconds':1800,'storage_budget':{'root':'/invented','limits':limits},
        'native_unit_limits':{'file_size_bytes':4*1024**2}}
    return {'schema_version':2,'kind':caller.KIND,'asset':'ETH','seed':11,'batch_size':16,
        'lookback_days':28,'cell_id':'invented','graph_inputs':{h:'graph'+str(i) for i,h in enumerate(hashes)},
        'indices':list(range(16)),'decisions':[f'2000-01-{n:02d}' for n in range(1,17)],
        'graph_sequences':[hashes*4 for _ in range(16)],'population_plan_input':'population',
        'model_input':'model','training_input':'training','model_execution':None,'max_checkpoint_bytes':1024,
        'outputs':{name:name+'.json' for name in ('summary','ledger','binding','journal')},'resource_policy':resources}


def test_profile_is_opt_in_and_requires_its_distinct_output():
    p=plan();assert caller.validate_plan(p) is p
    p['phase_timing_policy']=FORMAT
    with pytest.raises(ValueError,match='output'):caller.validate_plan(p)
    p['outputs']['timing']='timing.json';assert caller.validate_plan(p) is p
    p['outputs']['timing']=p['outputs']['summary']
    with pytest.raises(ValueError,match='output'):caller.validate_plan(p)


@pytest.mark.parametrize('bad',[None,True,'unknown',{'format':FORMAT}])
def test_unknown_profile_contract_refuses(bad):
    p=plan();p['phase_timing_policy']=bad;p['outputs']['timing']='timing.json'
    with pytest.raises(ValueError,match='phase timing'):caller.validate_plan(p)


def test_output_cannot_be_added_without_profile_selection():
    p=plan();p['outputs']['timing']='timing.json'
    with pytest.raises(ValueError,match='output'):caller.validate_plan(p)
