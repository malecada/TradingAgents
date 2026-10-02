"""Read-only code/compact-evidence capture; writes only its new report directory."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
F='research/onchain-paper-replication-2026-09-24/full_sources/'
P='tradingagents/research/onchain_replication/'
modules=['score_batches','score_tail','mcm_score_stream','compact_stage','archived_stage','compact_mcm',
'compact_mcm_output','compact_mcm_publication','compact_graph_artifacts','compact_terminal','compact_owner',
'archive_owner_policy','archive_owner_operations','archive_owner_seal','archive_pair_writer','archive_pair_reader',
'archive_consume','archive_chunks','archive_transport','compact_native_producer','compact_training','compact_dictionary',
'compact_samples','compact_matcher','compact_policy','job_payload','job','workflow_storage','resources']
(OUT/'observed-source').mkdir()
pins={}
for name in modules:
    path=P+name+'.py'; raw=(ROOT/path).read_bytes()
    (OUT/'observed-source'/f'{name}.py').write_bytes(raw)
    pins[path]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
paths=[F+'compact-workflow-accounting-2026-10-02/lower-bound01.json',F+'score-tail-2026-10-01/accounting01.json',F+'native-resource-admission-2026-10-01/inputs02.json']
for path in paths:
    raw=(ROOT/path).read_bytes();pins[path]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
lower,scores,inputs=[json.loads((ROOT/p).read_bytes()) for p in paths]
graphs={g['week']:g for g in inputs['graphs']}
rows=[]
for old in lower['rows']:
    n=graphs[old['week']]['nodes']*32
    assert old['retained_score_payload_bytes']==88*n
    assert old['two_saved_float32_mcm_payloads_bytes']==8*n
    rows.append({'week':old['week'],'cells':n,'local_score_tail_bytes':80*n,'local_score_batch_bytes':8*n,
        'local_two_float32_matrices_bytes':8*n,'remaining_after_pair_event_offload_bytes':96*n,
        'conditional_after_additional_tail_offload_bytes':16*n,'existing_graph_manifest_array_file_bytes':graphs[old['week']]['saved_array_file_bytes']})
assert sum(r['local_score_tail_bytes'] for r in rows)==46199848960
assert sum(r['remaining_after_pair_event_offload_bytes'] for r in rows)==55439818752
assert sum(r['conditional_after_additional_tail_offload_bytes'] for r in rows)==9239969792
record={'execution_admitted':False,'kind':'read_only_in_progress_source_observation',
'observed_at_utc':datetime.now(timezone.utc).isoformat(),'source_pins':pins,'rows':rows,
'qualification':'Conditional nine-graph32motif logical payload arithmetic; not adopted population, physical upperbound, measured peak or new empirical result.',
'unknowns':['dictionary/checkpoint bytes and lifetime','peak scratch/staging','remote capacity','physical filesystem allocation','full verification throughput','actual prospective graph union'],
'excluded_graph_inputs_note':'Existing graph array bytes shown separately; do not subtract them again from currently measured free space if already resident.',
'lookup_correction':'Initial read request used nonexistent compact_archive_execution.py/archive_policy.py; compact_archive_execution is a descriptor field, and actual selector is archive_owner_policy.py. No code/test failure occurred.'}
(OUT/'observations.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
for path,pin in pins.items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==pin['sha256'],path
print(json.dumps({'status':'PASS','source_files_captured':len(modules),'compact_metadata_files':3,'week_count':len(rows),'remaining_after_pair_events':55439818752,'conditional_after_tail_offload':9239969792,'source_stable_during_capture':True,'empirical_runs':0},sort_keys=True))
print('| Week | Score tails B | Score batches B | Two float32 matrices B | Remaining after pair offload B | Conditional after tail offload B |')
print('|---|---:|---:|---:|---:|---:|')
for r in rows:
    print('| '+r['week']+' | '+' | '.join(f'{r[k]:,}' for k in ['local_score_tail_bytes','local_score_batch_bytes','local_two_float32_matrices_bytes','remaining_after_pair_event_offload_bytes','conditional_after_additional_tail_offload_bytes'])+' |')
