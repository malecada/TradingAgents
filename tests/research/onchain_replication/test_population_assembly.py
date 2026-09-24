"""Population assembly uses synthetic graph metadata, never financial fitting."""
from dataclasses import asdict, replace
import json

import pytest

from tests.research.test_lifecycle import registered
from tests.research.onchain_replication.test_dataset import fixture
from tradingagents.research.onchain_replication.dataset import build_examples, fit_scaler
from tradingagents.research.onchain_replication.graph_store import save_graph
from tradingagents.research.onchain_replication.provenance import canonical_bytes, digest
from tradingagents.research.onchain_replication.job_payload import population_record, population_from_record
from tradingagents.research.onchain_replication.population_assembly import (
    required_weeks, assemble_population, publish_population,
)


def setup(tmp_path, *, graphs=None, prices=None):
    base, original_prices, fold, config=fixture()
    graphs=base if graphs is None else graphs
    prices=original_prices if prices is None else prices
    expected=required_weeks(fold,config['lookback_days'])
    refs={}
    for i,g in enumerate(graphs):
        path=save_graph(tmp_path/str(i),g)
        raw=path.read_bytes()
        from tradingagents.research.onchain_replication.calendar import stamp
        refs[stamp(g.start_utc)]={'status':'complete','raw_manifest':raw,'sha256':digest(raw)}
    refs={week:refs.get(week,{'status':'unavailable','reason':'synthetic missing week','evidence_hashes':['f'*64]}) for week in expected}
    admission={'asset':'ETH','graph_config_hash':'a'*64,'price_source_hash':prices.source_hash,
               'price_panel_hash':digest(canonical_bytes(asdict(prices))),
               'calendar_hash':digest(canonical_bytes(config)),'fold_hash':fold.member_hash,
               'graph_manifest_hashes':sorted(v['sha256'] for v in refs.values() if v['status']=='complete'),
               'source_hashes':['a'*64],
               'unavailable_week_hashes':{w:digest(canonical_bytes(r)) for w,r in refs.items() if r['status']=='unavailable'}}
    return graphs,prices,fold,config,expected,refs,admission


def assemble(parts):
    _,prices,fold,config,weeks,refs,admission=parts
    return assemble_population(refs,prices,fold,config,weeks,admission)


def test_metadata_assembly_matches_full_graph_population_and_roundtrips(tmp_path,monkeypatch):
    parts=setup(tmp_path);graphs,prices,fold,config,*_=parts
    expected=build_examples(graphs,prices,fold,config)
    scaler=fit_scaler(expected,prices,fold)
    import tradingagents.research.onchain_replication.graph_store as store
    monkeypatch.setattr(store,'load_graph',lambda *a,**k:pytest.fail('population assembly loaded graph arrays'))
    result=assemble(parts)
    assert canonical_bytes(result['population'])==canonical_bytes(population_record(expected,scaler))
    actual=population_from_record(json.loads(canonical_bytes(result['population'])))
    assert actual==(expected,scaler)
    assert result['decision_count']==1096
    assert len(expected.train)+len(expected.test)+len(expected.exclusions)==1096
    assert any(row.decision_at.startswith('2024-02-29') for row in expected.test)
    assert any(x['reason']=='purged_training_label' for x in expected.exclusions)
    assert result['provenance']['array_bytes_reverified'] is False


@pytest.mark.parametrize('fault',['hash','asset','config','source','price','denominator','duplicate_manifest'])
def test_changed_or_unbound_metadata_refused(tmp_path,fault):
    parts=list(setup(tmp_path));refs=parts[5];admission=parts[6]
    week=next(w for w,r in refs.items() if r['status']=='complete')
    ref=refs[week]
    if fault=='hash':ref['sha256']='0'*64
    elif fault in ('asset','config','source'):
        m=json.loads(ref['raw_manifest'])
        key={'asset':'asset','config':'graph_config_hash','source':'source_hashes'}[fault]
        m['metadata'][key]={'asset':'BTC','config':'0'*64,'source':['0'*64]}[fault]
        admission['graph_manifest_hashes'].remove(ref['sha256'])
        ref['raw_manifest']=canonical_bytes(m);ref['sha256']=digest(ref['raw_manifest'])
        admission['graph_manifest_hashes'].append(ref['sha256'])
        admission['graph_manifest_hashes'].sort()
    elif fault=='price':admission['price_panel_hash']='0'*64
    elif fault=='denominator':refs.pop(week)
    elif fault=='duplicate_manifest':admission['graph_manifest_hashes'].append(ref['sha256'])
    with pytest.raises(ValueError):assemble(parts)


def test_missing_and_late_weeks_stay_explicit_without_fallback(tmp_path):
    graphs,prices,fold,config=fixture()
    missing='2024-01-01'
    graphs=[replace(g,available_at='2024-01-30T00:00:00Z') if g.start_utc.startswith('2024-01-08') else g
            for g in graphs if not g.start_utc.startswith(missing)]
    result=assemble(setup(tmp_path,graphs=graphs))
    exclusions=result['population']['examples']['exclusions']
    assert {'missing_expected_graph','late_expected_graph'} <= {x['reason'] for x in exclusions}
    assert result['weeks']['2024-01-01T00:00:00Z']['status']=='unavailable'


def test_future_prices_do_not_change_training_membership_or_scaler(tmp_path):
    first=setup(tmp_path/'first');p=first[1]
    changed=replace(p,closes=tuple(v*10 if d>='2024-01-01' else v for d,v in zip(p.dates,p.closes)))
    a,b=assemble(first),assemble(setup(tmp_path/'second',prices=changed))
    assert a['population']['examples']['train_hash']==b['population']['examples']['train_hash']
    assert a['population']['scaler']==b['population']['scaler']
    assert a['binding']['test_examples_hash']!=b['binding']['test_examples_hash']


def test_population_publication_is_exclusive_and_recoverable(tmp_path):
    result=assemble(setup(tmp_path/'graphs'))
    directory=tmp_path/'population'
    receipt=publish_population(directory,result)
    assert receipt['status']=='complete'
    assert digest((directory/'population.json').read_bytes())==receipt['files']['population.json']
    with pytest.raises(FileExistsError):publish_population(directory,result)


def test_same_claim_population_producer_executes_synthetic_price_cells(registered,tmp_path,monkeypatch):
    from tests.research.onchain_replication.test_run import setup as batch_setup,register_plan
    from tests.research.test_lifecycle import start
    from tradingagents.research.onchain_replication.job_payload import execute_fit_payload
    from tradingagents.research.onchain_replication.run import preflight_batch
    registered,_,batch=batch_setup(registered)
    root,spec,_=registered
    parts=setup(tmp_path/'source')
    expected=assemble(parts)
    _,prices,fold,config,weeks,refs,admission=parts
    inputs=[];graph_inputs={}
    for i,(week,ref) in enumerate(refs.items()):
        name='week_'+str(i)
        inputs.append((name,json.loads(ref['raw_manifest']) if ref['status']=='complete' else ref))
        graph_inputs[week]={'input':name,'status':ref['status']}
    # The admitted bytes here are canonical JSON, exactly as register_plan writes.
    admission={**admission,'graph_manifest_hashes':sorted(digest(canonical_bytes(value))
                for name,value in inputs if value.get('graph_hash'))}
    producer={'schema_version':1,'graphs':graph_inputs,'price_input':'prices',
              'fold':asdict(fold),'calendar_input':'calendar','expected_weeks':weeks,
              'admission_input':'source_admission',
              'outputs':{'population':'population.json','binding':'population-binding.json','assembly':'population-assembly.json'}}
    outputs=list(producer['outputs'].values())
    spec['experiments']['example-a']['outputs']+=outputs
    batch['populations']['whole']={**batch['populations']['whole'],
        'output':'population-binding.json','binding':expected['binding'],
        'train_examples':len(expected['population']['examples']['train']),
        'test_examples':len(expected['population']['examples']['test'])}
    batch['populations']['whole'].pop('input')
    payload={'population_inputs':{'whole':{'producer_input':'population_plan'}},
             'batch_plan_input':'batch_plan','representation_jobs':{}}
    registered=register_plan((root,spec,None),batch,[*inputs,('prices',asdict(prices)),('calendar',config),
        ('source_admission',admission),('population_plan',producer),('execution_job',{'kind':'fit','payload':payload})])
    import tradingagents.research.onchain_replication.run as execution
    original_execute=execution.execute_batch
    def check_only(run,populations,representations,**kwargs):
        preflight_batch(run,populations,representations,**kwargs)
        assert set(outputs)<=set(run._published_outputs)
        assert canonical_bytes(population_record(*populations['whole']))==canonical_bytes(expected['population'])
        return original_execute(run,populations,representations,**kwargs)
    monkeypatch.setattr(execution,'execute_batch',check_only)
    with start(registered) as run:
        rows,_=execute_fit_payload(run,payload)
        assert [r['status'] for r in rows]==['complete','complete','unavailable']
        with pytest.raises((FileExistsError,ValueError)):
            execute_fit_payload(run,payload)


def test_fold_fields_cannot_change_behind_old_member_hash(tmp_path):
    parts=list(setup(tmp_path))
    parts[2]=replace(parts[2],train_end='2023-07-01T00:00:00Z')
    with pytest.raises(ValueError,match='fold'):
        assemble(parts)


def test_unavailable_week_evidence_is_bound_before_mask_assembly(tmp_path):
    parts=list(setup(tmp_path));refs=parts[5]
    week=next(w for w,r in refs.items() if r['status']=='unavailable')
    refs[week]['evidence_hashes']=['0'*64]
    with pytest.raises(ValueError,match='evidence'):
        assemble(parts)
