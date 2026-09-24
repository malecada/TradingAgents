import json
from dataclasses import replace,asdict
from pathlib import Path
import pytest
from tests.research.test_lifecycle import registered,start
from tests.research.onchain_replication.test_dataset import fixture
from tests.research.onchain_replication.test_training import P,CFG
from tradingagents.research.onchain_replication.dataset import build_examples,fit_scaler
from tradingagents.research.onchain_replication.provenance import digest,canonical_bytes
from tradingagents.research.onchain_replication.evaluation import evaluate_cell,reuse_cell,prediction_directory
from tradingagents.research.onchain_replication.verification import independent_classification,independent_regression,compare_summary

CONFIG=json.loads((Path(__file__).resolve().parents[3]/'research/onchain-paper-replication-2026-09-24/config/model.json').read_bytes())

@pytest.mark.parametrize('arm,task',[('lstm','direction'),('constant_graph','regression'),('svm','direction'),('svm','regression')])
def test_registered_synthetic_cell_predictions_independently_reconcile(registered,tmp_path,arm,task):
    graphs,prices,fold,config=fixture();examples=build_examples(graphs,prices,fold,config)
    examples=replace(examples,train=examples.train[:40],train_hash=digest(canonical_bytes([asdict(x) for x in examples.train[:40]])),test=examples.test[:4],test_mask_hash=digest(canonical_bytes([x.decision_at for x in examples.test[:4]])))
    scaler=fit_scaler(examples,prices,fold)
    cell={'id':'sum','arm':arm,'task':task,'seed':11,'fold':'2024','variant':'full','lane':'algorithm','asset':'ETH'}
    training={**CFG,'epochs':1};binding={}
    with start(registered) as run:
        provenance={**P,'source_commit':run.admission.source,'input_hash':examples.train_hash,'config_hash':digest(canonical_bytes({'model':CONFIG,'training':training,'cell':{k:cell[k] for k in ('id','arm','task','seed','fold','variant')},'feature_binding':binding,'scaler':asdict(scaler)}))}
        path=prediction_directory(run,'sum')
        rows,summary=evaluate_cell(run,cell,examples,scaler,{},CONFIG,training,provenance,expected_test_mask=examples.test_mask_hash,feature_binding=binding,output_directory=path)
        independent=independent_classification([r['y_true'] for r in rows],[r['probability_up'] for r in rows]) if task=='direction' else independent_regression([r['y_true'] for r in rows],[r['predicted_price'] for r in rows])
        assert compare_summary(summary,independent)['passed']
        saved,_=reuse_cell(path,cell_id='sum',expected_provenance=provenance,expected_test_mask=examples.test_mask_hash)
        assert saved==rows
        with pytest.raises(ValueError,match='reuse identity'):reuse_cell(path,cell_id='other',expected_provenance=provenance,expected_test_mask=examples.test_mask_hash)
