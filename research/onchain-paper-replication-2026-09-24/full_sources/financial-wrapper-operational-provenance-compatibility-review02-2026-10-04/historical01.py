from pathlib import Path
import ast,hashlib,importlib.util,json,stat
H=Path(__file__).resolve().parent;I=H.parent/'financial-wrapper-operational-provenance-compatibility-investigation01-2026-10-04';SRC=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');rows=[]
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def ck(n,v):rows.append({'case':n,'passed':bool(v)});assert v,n
spec=importlib.util.spec_from_file_location('metadata_history_bridge',H/'operational_source_compatibility.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
manifest=json.loads((I/'MANIFEST01.json').read_bytes());ck('original investigator manifest pin',sha((I/'MANIFEST01.json').read_bytes())=='e1dd163b621915924237cf585df0f82ee8e42c19af68d81ca7b925fe32a3a4ff')
reqrow=next(r for r in manifest['members'] if r['path']=='PARENT_INPUT_REQUIREMENTS01.json');raw=(I/reqrow['path']).read_bytes();ck('historical navigation authenticated',sha(raw)==reqrow['sha256']);req=json.loads(raw)
metadata={};dest=H/'parent-metadata';dest.mkdir()
for row in req['rows']:
 p=SRC/row['path'];s=p.lstat();ck('actual historical regular '+row['descriptor_field'],stat.S_ISREG(s.st_mode) and s.st_size==row['bytes']);raw=p.read_bytes();ck('actual historical digest '+row['descriptor_field'],sha(raw)==row['sha256'])
 if row['kind']=='original metadata JSON':metadata[row['descriptor_field']]=json.loads(raw);(dest/(row['descriptor_field']+'.json')).write_bytes(raw)
 # No state decoding, loading, copying or tensor inspection.
claim=metadata['claim_input'];failed=metadata['terminal_input'];oldjob=metadata['parent_job_input'];oldplan=metadata['parent_plan_input'];cp=metadata['checkpoint_input'];fit=metadata['fit_claim_input'];diag=metadata['diagnostic_input'];schedule=metadata['schedule_input'];failedfit=metadata['failed_fit_input'];prov=cp['provenance']
ck('historical identity/source constants authentic',claim['experiment_id']==m.HISTORICAL_ID and claim['source']==claim['design_source']==prov['source_commit']==m.HISTORICAL_SOURCE)
ck('original all193 distinct hashes retained',prov['source_hashes']==sorted(set(m.OLD_MAP.values())))
ck('all194 old paths in genuine original claim',all(claim['experiment']['source_files'].get(p)==v for p,v in m.OLD_MAP.items()))
ck('original failed terminal join',failed['status']=='failed' and failed['claim_sha256']==m.HISTORICAL_CLAIM_SHA256 and failed['experiment_id']==m.HISTORICAL_ID)
ck('historical scientific constants source pinned',claim['inputs'][oldplan['model_input']]['sha256']==m.MODEL and claim['inputs'][oldplan['training_input']]['sha256']==m.TRAINING)
ck('historical model/job/plan/recipe joins',claim['inputs']['execution_job']['sha256']==sha((dest/'parent_job_input.json').read_bytes()) and claim['inputs'][oldjob['payload']['plan_input']]['sha256']==sha((dest/'parent_plan_input.json').read_bytes()) and claim['inputs'][oldplan['recipe_input']]['sha256']==prov['input_hash'])
ck('original fit exact immutable provenance',fit=={'experiment_id':m.HISTORICAL_ID,'provenance':prov,'parent_checkpoint':None})
cppath=SRC/next(r['path'] for r in req['rows'] if r['descriptor_field']=='checkpoint_input')
ck('original absolute failed checkpoint path preserved',failedfit=={'type':'PlannedInterruption','reason':'prospective engineering failed-parent fixture after one real update; no fit completion','last_checkpoint':str(cppath)})
ck('diagnostic exact full old provenance',diag=={'checkpoint':str(cppath),'sha256':m.HISTORICAL_CHECKPOINT_SHA256,'provenance':prov,'epochs_completed':1,'requires_genuine_failed_parent':True})
ck('checkpoint opaque member declaration',cp['members']=={'state.pt':{'size':493424,'sha256':m.HISTORICAL_STATE_SHA256}})
ck('old schedule unchanged100/16/11',schedule['seed']==11 and schedule['n_examples']==16 and schedule['task']=='classification' and schedule['training']['epochs']==100 and schedule['training']['batch_size']==16)
# Authenticate current model/training/recipe/closure literal bodies via original claim.
for role in (oldplan['model_input'],oldplan['training_input'],oldplan['recipe_input'],oldplan['closure_input']):
 info=claim['inputs'][role];raw=(SRC/info['path']).read_bytes();ck('actual registered science '+role,sha(raw)==info['sha256']);(dest/(role+'.json')).write_bytes(raw)
# Explicit exact AST joins. Functions only parsed, never authority-called.
htree=ast.parse((H/'operational_source_compatibility.py').read_bytes());func={n.name:n for n in htree.body if isinstance(n,ast.FunctionDef)}
pt=ast.unparse(func['_parent_predicate']);context=ast.unparse(func['_context'])
for fragment in ("hist['provenance'] == old","manifest['provenance'] == old","new['source_commit'] == ad.source","validate_relation(hist['installed'], target['installed'], old, new)","'old_provenance_rewritten': False"):
 ck('historical/current predicate '+fragment,fragment in pt)
for fragment in ("type(run) is ResearchRun", "type(run.admission) is Admission", "run._active()", "run._check_source()", "ad.design_source == ad.source", "ad.experiment['source_files'].get(path) == pin"):
 ck('current genuine source predicate '+fragment,fragment in context)
# Complete no-lock original methods reachable under existing _reserve lock.
ltree=ast.parse((H/'source-original/tradingagents/research/lifecycle.py').read_bytes());runclass=next(n for n in ltree.body if isinstance(n,ast.ClassDef) and n.name=='ResearchRun');methods={n.name:n for n in runclass.body if isinstance(n,ast.FunctionDef)}
for name in ('_active','_check_source'):ck('original heldlock method has no _lock '+name,not any(isinstance(n,ast.Name) and n.id=='_lock' for n in ast.walk(methods[name])))
for fname in ('admission.py','verify.py'):ck('source whole module no lifecycle _lock '+fname,not any(isinstance(n,ast.Name) and n.id=='_lock' for n in ast.walk(ast.parse((H/'source-original/tradingagents/research'/fname).read_bytes()))))
(H/'HISTORICAL_CHECKS01.json').write_text(json.dumps({'rows':rows,'actual_old_source':m.HISTORICAL_SOURCE,'historical_checkpoint_state_sha256':m.HISTORICAL_STATE_SHA256,'checkpoint_hashed_only':True,'new_source_policy_or_claim_created':False},indent=2)+'\n')
print(json.dumps({'status':'PASS_ACTUAL_METADATA_ONLY','checks':len(rows),'state_deserialized':False}))
