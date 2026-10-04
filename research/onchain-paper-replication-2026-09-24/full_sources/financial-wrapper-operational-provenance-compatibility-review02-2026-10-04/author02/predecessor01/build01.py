import ast,hashlib,json,difflib
from pathlib import Path
H=Path(__file__).resolve().parent;SRC=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');P='tradingagents/research/onchain_replication/'
sha=lambda b:hashlib.sha256(b).hexdigest()
def put(n,v):(H/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
old={n:(SRC/P/n).read_text() for n in ('financial_wrapper_fixture.py','training.py')}
changes={n:[] for n in old}
def change(n,a,b):
 assert output[n].count(a)==1;output[n]=output[n].replace(a,b);changes[n].append({'old':a,'new':b})
output=dict(old)
change('financial_wrapper_fixture.py'," return p,json.loads(raw_model),json.loads(raw_training),source,sha(raw_recipe)"," if 'operational_source_compatibility' in ad.inputs:\n  from .operational_source_compatibility import validate_current\n  validate_current(run,p,source)\n return p,json.loads(raw_model),json.loads(raw_training),source,sha(raw_recipe)")
a=" require({k:v for k,v in value['provenance'].items() if k!='source_commit'}=={k:v for k,v in prov.items() if k!='source_commit'},'prior scientific provenance differs')"
b=" if 'operational_source_compatibility' in run.admission.inputs and p['phase']=='continue100':\n  from .operational_source_compatibility import require_parent_compatibility\n  require_parent_compatibility(run,value['provenance'],prov,run.admission.root/run.admission.inputs[value['checkpoint_input']]['path'])\n else:\n "+a
change('financial_wrapper_fixture.py',a,b)
a=" require({k:v for k,v in ref['provenance'].items() if k not in ('source_commit','cell_id')}=={k:v for k,v in prov.items() if k not in ('source_commit','cell_id')},'reference scientific provenance differs')"
b=a+"\n if 'operational_source_compatibility' in run.admission.inputs:\n  from .operational_source_compatibility import require_reference_policy\n  require_reference_policy(run,claim)"
change('financial_wrapper_fixture.py',a,b)
a="            if {k:v for k,v in old.items() if k!='source_commit'}!={k:v for k,v in provenance.items() if k!='source_commit'}:raise ValueError('continuation scientific provenance mismatch')"
b="            if 'operational_source_compatibility' in run.admission.inputs:\n                from .operational_source_compatibility import _require_parent_under_fit_lock\n                _require_parent_under_fit_lock(run,old,provenance,checkpoint)\n            else:\n    "+a
change('training.py',a,b)
for n in old:
 ast.parse(output[n]);(H/('original_'+n)).write_text(old[n]);(H/n).write_text(output[n]);back=output[n]
 for r in reversed(changes[n]):assert back.count(r['new'])==1;back=back.replace(r['new'],r['old'])
 assert back==old[n]
 (H/(n+'.patch')).write_text(''.join(difflib.unified_diff(old[n].splitlines(True),output[n].splitlines(True),fromfile='original_'+n,tofile=n)))
put('SOURCE_INVERSES01.json',{'changes':changes,'sources':{n:{'old_sha256':sha(old[n].encode()),'new_sha256':sha(output[n].encode())} for n in old},'full_literal_inverse':True})
# Every scientific fit/model/prediction function is untouched. Only control-plane
# function statements explicitly substituted above differ.
for n,allowed in [('training.py',{'_reserve'}),('financial_wrapper_fixture.py',{'authorize','_parent','_reference_state'})]:
 a=ast.parse(old[n]);b=ast.parse(output[n]);a.body=[x for x in a.body if getattr(x,'name',None) not in allowed];b.body=[x for x in b.body if getattr(x,'name',None) not in allowed];assert ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
closure=json.loads((SRC/'fixture_inputs/financial_wrapper_claimedrun01/source_closure.json').read_text());mapping=closure['installed'];assert len(mapping)==194 and len(set(mapping.values()))==193
watch=H.parent/'financial-wrapper-storage-watch-concurrent-publication-correction03-2026-10-04/workflow_storage.py';watch_raw=watch.read_bytes();assert sha(watch_raw)=='91e21c525a156cc8c25877ac35f0308896a1a0d1e6279d5aecf91d7e02567780';(H/'workflow_storage.py').write_bytes(watch_raw)
claimpath=SRC/'research_runs/financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01/claim.json';claim=json.loads(claimpath.read_text());assert claim['source']=='0a2e7639b42b9423b90743feadcda4078aa21816'
constants={'ROLE':'operational_source_compatibility','PREFIX':P,'HISTORICAL_SOURCE':claim['source'],'HISTORICAL_ID':claim['experiment_id'],'HISTORICAL_CLAIM_SHA256':sha(claimpath.read_bytes()),'HISTORICAL_FAILED_SHA256':'4b2d7b0d162e80fe2074997baed35f2d6e6c86e5f660872fc2b8e97bb9622558','HISTORICAL_CHECKPOINT_SHA256':'b2f7d33b2f2280f5d9b0a9731ea320c64d18768bda772926421ddb0af2e12c70','HISTORICAL_STATE_SHA256':'223ced42edec29ec0afd4ea5265b2e0a557a98787e57be47e841e8491511a281','HISTORICAL_PROTOCOL_SHA256':claim['experiment']['charter']['sha256'],'MODEL':closure['scientific_model'],'TRAINING':closure['scientific_training'],'OLD_MAP':mapping,'CONTROL_TARGETS':{P+n:sha(output[n].encode()) for n in output}|{P+'workflow_storage.py':sha(watch_raw)},'PROGRAM':claim['program_id'],'FAMILY':claim['experiment']['family']}
put('CONSTANTS01.json',constants)
print(json.dumps({'status':'COPIED_CONTROL_PLANE_SOURCES_PREPARED','old_paths':len(mapping),'old_distinct_hashes':len(set(mapping.values())),'unchanged_original_paths':191,'candidate_added_helper_paths':1,'no_live_installation':True},indent=2))
