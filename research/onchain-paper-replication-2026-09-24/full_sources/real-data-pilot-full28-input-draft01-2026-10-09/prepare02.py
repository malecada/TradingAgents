"""Metadata-only draft from admitted27; no binder, admission or private reads."""
import copy,difflib,hashlib,json
from pathlib import Path
ROOT=Path.cwd().resolve();HERE=Path(__file__).resolve().parent;F=HERE.parent
OLD='eth-paper-real-data-end-to-end-resource-20261009-27';NEW=OLD[:-2]+'28'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
raw=lambda v:(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
def read(ref):
 p=ROOT/ref['path'];assert sha(p)==ref['sha256'];return json.loads(p.read_bytes())
def save(name,v):
 p=HERE/name
 with p.open('xb') as f:f.write(raw(v))
 return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
def move(v):
 if type(v)is dict:return {k:move(x) for k,x in v.items()}
 if type(v)is list:return [move(x) for x in v]
 if type(v)is str:return v.replace(OLD,NEW).replace('ethpilot-20261009-27','ethpilot-20261009-28').replace('real-eth-seven-graph-joint-update-resource27','real-eth-seven-graph-joint-update-resource28')
 return v
bp=F/'real-data-pilot-full27-entry01-2026-10-09/BINDING01.json';binding=json.loads(bp.read_bytes());gate=read(binding['gate']);entry=gate['experiments'][OLD]
assert not (ROOT/'research_runs'/NEW).exists()
refs=copy.deepcopy(entry['inputs']);assert len(refs)==64
for role,ref in binding['input_refs'].items():assert {k:refs[role][k] for k in ('path','sha256')}==ref
prepared=read(binding['preparation']);roles=set(prepared['builder03_result']['inputs'])|{'archive_policy'};assert len(roles)==12
original={role:read(refs[role]) for role in roles}
# Never persist or follow the historical connection; retain only its absence in draft/diff.
original['archive_transport']['connection']=None
docs=move(copy.deepcopy(original));docs['archive_policy']['transport_identity']=None
files=docs['pair_policy']['numerical_source']['files'];assert len(files)==193
current={n:sha(ROOT/n) for n in files};changed={n:{'prior':files[n],'current':current[n]} for n in files if files[n]!=current[n]}
assert set(changed)=={'tradingagents/research/onchain_replication/batched_driver.py','tradingagents/research/onchain_replication/batched_numeric_reuse.py'}
assert current['tradingagents/research/onchain_replication/batched_driver.py']=='047a0762cc0eee53e0ad440339238baeb527158c3a2f33293164e0b91b7a395b'
assert current['tradingagents/research/onchain_replication/batched_numeric_reuse.py']=='a9df46197c1284f7f6287cc5b04ded33cb9aae58eb9eca14d91f8bd6b8253440'
assert all(entry['source_files'][n]==files[n] for n in files)
docs['pair_policy']['numerical_source']={'commit':None,'files':current}
selected=docs['execution_job']['payload']['representation_jobs']['original32'];producer=docs['producer_plan']['producers']['original32']
for role,key in [('pair_policy','pair_execution'),('compact_policy','compact_execution'),('archive_policy','compact_archive_execution')]:
 for v in (selected,producer):v['descriptor'][key]['policy_sha256']=hashlib.sha256(raw(docs[role])).hexdigest()
assert selected['descriptor']==producer['descriptor'];assert selected['descriptor']['configs']==original['execution_job']['payload']['representation_jobs']['original32']['descriptor']['configs']
assert len(selected['descriptor']['required_graphs'])==7
assert selected['descriptor']['configs']['dictionary']['size']==32 and selected['descriptor']['configs']['dictionary']['sample_count']==512
assert docs['mcm_policy']==original['mcm_policy'] and docs['execution_job']['resources']==move(original['execution_job']['resources'])
(HERE/'public01').mkdir();out={};patch=[]
for role in sorted(docs):
 out[role]=save('public01/'+role+'.json',docs[role]);refs[role]={**out[role],'dataset':entry['inputs'][role]['dataset']}
 patch.extend(difflib.unified_diff(json.dumps(original[role],indent=2,sort_keys=True).splitlines(True),json.dumps(docs[role],indent=2,sort_keys=True).splitlines(True),fromfile='admitted27-redacted/'+role,tofile='draft28/'+role))
scratch=move(read(entry['inputs']['matching_ordered_edge_scratch']));refs['matching_ordered_edge_scratch']={**save('MATCHING_SCRATCH_RESERVATION01.json',scratch),'dataset':'eth'}
public=move(read(binding['public_manifest']));public.update(status='DRAFT_NOT_RELEASED',source_anchor=None,source_pins={n:sha(ROOT/n) for n in public['source_pins']},public_inputs=out,builder_sha256=sha(Path(__file__)))
public['qualification']='Draft28 only. Immutable168-byte grouped tokens and sampled callback timing counters; original science/order/caps unchanged. Historical polling and deferred later-graph refusal remain. No genuine connection, source anchor, admission, currentness, capacity or recovery evidence supplied.'
save('PUBLIC_MANIFEST01.json',public);save('PUBLIC_INPUT_REFS01.json',refs)
save('SOURCE_MANIFEST01.json',{'status':'DRAFT_NOT_RELEASED','source_anchor':None,'numerical_sources':current,'changes':changed,'admitted27_source_pins':entry['source_files'],'current_source_pins':{n:sha(ROOT/n) for n in entry['source_files']}})
save('PREPARATION01.json',{'status':'DRAFT_NOT_REGISTERED_NOT_ADMITTED','identity':NEW,'baseline_binding':{'path':str(bp.relative_to(ROOT)),'sha256':sha(bp)},'baseline_gate':binding['gate'],'builder03_result':{'inputs':docs},'unresolved':{'numerical_source_commit':None,'archive_transport_connection':None,'archive_policy_transport_identity':None},'remaining_root_work':['Commit and authenticate exact193 numerical-source bodies; replace null commit and cascade pair/job/producer refs.','Bind genuine transport for fresh namespace; replace connection and transport_identity, cascade archive/job/producer refs using accepted binder.','Register cumulative99 and exact source/reviews; final gate/entry/currentness/capacity/recovery and release remain Root-owned.']})
(HERE/'public-diff.patch').write_text(''.join(patch))
save('CHECK01.json',{'decision':'PASS_DRAFT_ONLY','input_roles':len(refs),'public_documents':len(docs),'numerical_roster':len(files),'changed_sources':changed,'full_graphs':7,'original_model_ref':refs['model'],'original_training_ref':refs['training'],'matching_dictionary_config_identical':True,'native_resources_identical_except_fixed_identity':True,'mcm_policy_identical':True,'private_connection_copied':False,'source_anchor':None})
print('PASS:64 roles,12 public templates,193 source pins; anchor/connection unresolved')
