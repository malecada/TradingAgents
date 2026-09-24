import json
from dataclasses import replace,asdict
from pathlib import Path
import pytest
from tests.research.test_lifecycle import registered,start
from tests.research.onchain_replication.test_dataset import fixture
from tests.research.onchain_replication.test_training import P,CFG
from tradingagents.research.onchain_replication.dataset import build_examples,fit_scaler
from tradingagents.research.onchain_replication.provenance import digest,canonical_bytes
from tradingagents.research.onchain_replication.evaluation import evaluate_cell,reuse_cell,prediction_directory,example_binding
from tradingagents.research.onchain_replication.verification import independent_classification,independent_regression,compare_summary

CONFIG=json.loads((Path(__file__).resolve().parents[3]/'research/onchain-paper-replication-2026-09-24/config/model.json').read_bytes())

@pytest.mark.parametrize('arm,task',[('lstm','direction'),('constant_graph','regression'),('svm','direction'),('svm','regression')])
def test_registered_synthetic_cell_predictions_independently_reconcile(registered,tmp_path,arm,task):
    graphs,prices,fold,config=fixture();examples=build_examples(graphs,prices,fold,config)
    examples=replace(examples,train=examples.train[:40],train_hash=digest(canonical_bytes([asdict(x) for x in examples.train[:40]])),test=examples.test[:4],test_mask_hash=digest(canonical_bytes([x.decision_at for x in examples.test[:4]])))
    scaler=fit_scaler(examples,prices,fold)
    cell={'id':'sum','arm':arm,'task':task,'seed':11,'fold':'2024','variant':'full','lane':'algorithm','asset':'ETH'}
    training={**CFG,'epochs':1};binding={}
    registered=bind_examples(registered,examples,scaler)
    with start(registered) as run:
        provenance={**P,'source_commit':run.admission.source,'input_hash':examples.train_hash,'config_hash':digest(canonical_bytes({'model':CONFIG,'training':training,'cell':{k:cell[k] for k in ('id','lane','asset','arm','task','seed','fold','variant')},'feature_binding':binding,'scaler':asdict(scaler)}))}
        path=prediction_directory(run,'sum')
        rows,summary=evaluate_cell(run,cell,examples,scaler,{},CONFIG,training,provenance,expected_test_mask=examples.test_mask_hash,feature_binding=binding,example_binding_input='examples',output_directory=path)
        independent=independent_classification([r['y_true'] for r in rows],[r['probability_up'] for r in rows]) if task=='direction' else independent_regression([r['y_true'] for r in rows],[r['predicted_price'] for r in rows])
        assert compare_summary(summary,independent)['passed']
        saved,_=reuse_cell(path,cell_id='sum',expected_provenance=provenance,expected_test_mask=examples.test_mask_hash)
        assert saved==rows
        with pytest.raises(ValueError,match='reuse identity'):reuse_cell(path,cell_id='other',expected_provenance=provenance,expected_test_mask=examples.test_mask_hash)


@pytest.mark.parametrize('arm',['lstm','svm'])
def test_prediction_only_recovery_does_not_claim_or_repeat_fit(registered,monkeypatch,arm):
    import copy
    from tests.research.test_lifecycle import commit,api
    from tradingagents.research.onchain_replication.provenance import file_hash
    import tradingagents.research.onchain_replication.evaluation as evaluation
    root,spec,source=registered
    graphs,prices,fold,config=fixture();examples=build_examples(graphs,prices,fold,config)
    examples=replace(examples,train=examples.train[:40],train_hash=digest(canonical_bytes([asdict(x) for x in examples.train[:40]])),test=examples.test[:4],test_mask_hash=digest(canonical_bytes([x.decision_at for x in examples.test[:4]])))
    scaler=fit_scaler(examples,prices,fold);cell={'id':'sum','arm':arm,'task':'direction','seed':11,'fold':'2024','variant':'full','lane':'algorithm','asset':'ETH'}
    training={**CFG,'epochs':1};binding={}
    registered=bind_examples(registered,examples,scaler);root,spec,source=registered
    identity=digest(canonical_bytes({'model':CONFIG,'training':training,'cell':{k:cell[k] for k in ('id','lane','asset','arm','task','seed','fold','variant')},'feature_binding':binding,'scaler':asdict(scaler)}))
    old={**P,'source_commit':source,'input_hash':examples.train_hash,'config_hash':identity}
    with start(registered) as run:
        original=evaluate_cell(run,cell,examples,scaler,{},CONFIG,training,old,expected_test_mask=examples.test_mask_hash,feature_binding=binding,example_binding_input='examples')[0]
        # Model is complete; simulate an interrupted parent before run-level closure.
    complete=list((root/'research_artifacts/onchain_fit_cells').glob('*/example-a/complete.json'))
    assert len(complete)==1
    checkpoint=Path(json.loads(complete[0].read_bytes())['checkpoint'])
    child=copy.deepcopy(spec['experiments']['example-a']);child['parent']='example-a'
    for name,path in [('checkpoint',checkpoint),('completion',complete[0])]:child['inputs'][name]={'path':str(path.relative_to(root)),'sha256':file_hash(path),'dataset':'sample'}
    spec['experiments']['example-b']=child;new_source=commit(root,spec)
    def forbidden(*a,**kw):raise AssertionError('completed model was refitted')
    monkeypatch.setattr(evaluation,'fit_cell',forbidden);monkeypatch.setattr(evaluation,'_reserve',forbidden)
    Run,_,_=api()
    with Run.start(root=root,registration='registration.json',experiment='example-b',source=new_source) as run:
        recovered,_=evaluate_cell(run,cell,examples,scaler,{},CONFIG,training,{**old,'source_commit':new_source},expected_test_mask=examples.test_mask_hash,feature_binding=binding,example_binding_input='examples',completed_fit={'provenance':old,'checkpoint_input':'checkpoint','completion_input':'completion'})
    assert recovered==original
    assert len(list((root/'research_artifacts/onchain_fit_cells').glob('*/*/claim.json')))==1


def bind_examples(registered,examples,scaler):
    from tests.research.test_lifecycle import commit
    from tradingagents.research.onchain_replication.provenance import file_hash
    root,spec,_=registered;path=root/'examples.json';path.write_bytes(canonical_bytes(example_binding(examples,scaler)))
    spec['experiments']['example-a']['inputs']['examples']={'path':'examples.json','sha256':file_hash(path),'dataset':'sample'}
    return root,spec,commit(root,spec)


def test_scientific_cell_cannot_be_relabeled():
    from tradingagents.research.onchain_replication.evaluation import validate_scientific_cell
    cell={'id':'paper_reconstruction/ETH/2024/11/direction/proposed/whole','lane':'paper_reconstruction','asset':'ETH','fold':'2024','seed':11,'task':'direction','arm':'proposed','variant':'whole'}
    validate_scientific_cell(cell)
    with pytest.raises(ValueError,match='contradicts'):validate_scientific_cell({**cell,'asset':'BTC'})
