"""Read only gate/receipts and bounded headers; write only this owned directory."""
import hashlib, importlib.util, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]; OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('capacity',OUT/'candidate/index_capacity.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def ref(p):
 p=Path(p);raw=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(r):
 p=ROOT/r['path'];raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256'];return json.loads(raw)
def save(name,v):
 with (OUT/name).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
gate=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-final15-2026-10-07/gate01.json'
g=json.loads(gate.read_bytes()); exp=next(iter(g['experiments'].values()));inputs=exp['inputs']
job=read(inputs['execution_job']);d=job['payload']['representation_jobs']['original32']['descriptor'];old=read(inputs['mcm_policy']);config=d['configs']['dictionary']
report=m.inspect(ROOT,inputs,d['resource_graph_inputs'],old['numeric'],config)
index=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-current-graph-counts05-2026-10-06/INDEX_DRAFT01.json'
prior=json.loads(index.read_bytes());joins=[]
for record in report['graphs']:
 slot=next(v for v in prior['graphs'].values() if v['role']==record['role']);manifest=read(slot['manifest']);c=read(slot['node_count']);e=read(c['evidence'])
 assert slot['manifest']['sha256']==record['manifest']['sha256'] and c['graph_manifest_sha256']==slot['manifest']['sha256'] and c['rows']==record['nodes'] and c['node_features_sha256']==manifest['arrays']['node_features']['sha256']
 joins.append({'role':record['role'],'count_ref':slot['node_count'],'evidence_ref':c['evidence']})
try:m.validate(ROOT,inputs,d['resource_graph_inputs'],old['numeric'],config)
except ValueError as e:failure=str(e)
else:raise AssertionError('old policy unexpectedly passed')
new=json.loads(json.dumps(old));new['numeric']['max_buffer_bytes']=report['max_buffer_required'];new['numeric']['max_numeric_bytes']=report['max_output_required']+report['max_buffer_required']
m.validate(ROOT,inputs,d['resource_graph_inputs'],new['numeric'],config)
report.update({'gate_ref':ref(gate),'count_index_ref':ref(index),'count_joins':joins,'original_mcm_ref':inputs['mcm_policy'],'original_numeric':old['numeric'],'candidate_numeric':new['numeric'],'old_policy_refusal':failure,'edge_chunk':old['numeric']['edge_chunk'],'maximum_neighborhood_nodes':config['maximum_neighborhood_nodes'],'graph_payload_bytes_read':0,'source_refs':[ref(ROOT/'tradingagents/research/onchain_replication/array_neighborhoods.py'),ref(ROOT/'tradingagents/research/onchain_replication/contracts.py')]})
save('CAPACITY01.json',report);save('mcm_policy01.json',new)
print(json.dumps({'old_refusal':failure,'new_numeric':new['numeric'],'graphs':[{k:r[k] for k in ('role','nodes','edges','retained_index_bytes','index_additive_bytes','output_inclusive_buffer_bytes')} for r in report['graphs']]},indent=2))
