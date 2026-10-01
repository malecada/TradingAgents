"""Read-only terminal/checkpoint/independent-metric verification, no producer or fit."""
import argparse
import io
import json
from pathlib import Path
import torch
from tradingagents.research.onchain_replication.provenance import file_hash,digest
from tradingagents.research.onchain_replication.cache import read_artifact
from tradingagents.research.onchain_replication.verification import independent_classification,independent_regression,compare_summary

def verify(root):
    root=Path(root).resolve();run=root/'research_runs/example-a';base=root/'research_artifacts/onchain-paper-replication-2026-09-24/runs/example-a'
    read=lambda p:json.loads(p.read_bytes())
    final=read(base/'guard/final.json');observer=read(base/'observer.json');terminal=read(run/'complete.json');claim=read(run/'claim.json')
    assert final['phase']=='complete' and final['cleanup_verified'] is True and final['child_exit_code']==0 and final['limit_reason'] is None
    assert all(value==0 for value in final['memory_events'].values())
    assert not Path(final['cgroup']).exists()
    owner=read(base/'owner.json')
    for pid in (owner['monitor_pid'],owner['supervisor_pid']):assert not Path('/proc',str(pid)).exists()
    assert observer['status']=='complete' and observer['all_cells_complete'] and observer['cgroup_empty']
    assert observer['terminal_sha256']==file_hash(run/'complete.json') and observer['owner_sha256']==file_hash(base/'owner.json')
    assert final['owner_identity']==owner and final['command'][-1]==claim['source']
    assert terminal['claim_sha256']==file_hash(run/'claim.json') and terminal['unavailable_count']==0
    for name,sha in terminal['output_sha256'].items():assert file_hash(run/'outputs'/name)==sha
    assert set(terminal['output_sha256'])==set(claim['experiment']['outputs'])
    ledger=read(run/'outputs/ledger.json');population=read(root/'population.json');expected=population['examples']['test']
    assert [r['id'] for r in ledger['cells']]==['sum','count'] and all(r['status']=='complete' for r in ledger['cells'])
    rows=[]
    for row in ledger['cells']:
        path=root/row['cell_record'];assert file_hash(path)==row['cell_record_sha256'];record=read(path)
        predictions=read(path.parent/'predictions.json');assert file_hash(path.parent/'predictions.json')==record['prediction_hash']
        assert len(predictions)==len(expected)==2
        direction=row['id']=='sum';truths=[]
        for prediction,example in zip(predictions,expected,strict=True):
            for field in ('decision_at','label_start','label_end','max_input_available_at'):assert prediction[field]==example[field]
            truth=float(example['up'] if direction else example['target_price']);assert prediction['y_true']==truth;truths.append(truth)
            assert prediction['checkpoint_hash']==record['checkpoint_hash']
        metrics=independent_classification(truths,[p['probability_up'] for p in predictions]) if direction else independent_regression(truths,[p['predicted_price'] for p in predictions])
        assert compare_summary(record['metrics'],metrics)['passed']
        assert record['test_mask_hash']==population['examples']['test_mask_hash']
        completion=read(root/'research_artifacts/onchain_fit_cells'/digest(row['id'].encode())/'example-a/complete.json')
        checkpoint=Path(completion['checkpoint']);assert checkpoint.is_relative_to(root)
        assert file_hash(checkpoint)==completion['sha256']==record['checkpoint_hash']
        artifact=read_artifact(checkpoint,record['provenance']);state=torch.load(io.BytesIO(artifact['state.pt']),map_location='cpu',weights_only=True)
        assert (state['epoch'],state['batch'])==(1,0) and state['optimizer']['state']
        assert record['provenance']['source_commit']==claim['source']
        rows.append({'id':row['id'],'predictions':len(predictions),'checkpoint_sha256':record['checkpoint_hash'],'independent_metrics_match':True})
    return {'schema_version':1,'status':'verified','synthetic_only':True,'financial_fits':0,'cells':rows,
            'terminal_sha256':file_hash(run/'complete.json'),'guard_sha256':file_hash(base/'guard/final.json'),
            'observer_sha256':file_hash(base/'observer.json'),'elapsed_seconds':final['elapsed_seconds'],
            'peak_sampled_memory_current_bytes':final['peak_sampled_memory_current_bytes'],'cleanup_verified':True,
            'limits_qualification':'tiny synthetic integration; no full-scale capacity or retained-data coverage credit'}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
    result=verify(args.root)
    with args.output.open('x') as stream:json.dump(result,stream,sort_keys=True,indent=2);stream.write('\n')
    print(json.dumps(result,sort_keys=True))
