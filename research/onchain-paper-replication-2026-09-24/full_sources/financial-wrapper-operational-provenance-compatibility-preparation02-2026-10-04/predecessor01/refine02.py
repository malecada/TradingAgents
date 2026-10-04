from pathlib import Path
import ast,hashlib,json,difflib
H=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
for n in ('training.py','operational_source_compatibility.py'):(H/('DRAFT01_'+n)).write_bytes((H/n).read_bytes())
p=H/'training.py';s=p.read_text();s=s.replace("    with _lock(run.admission.root):","    compatibility=None\n    with _lock(run.admission.root):",1);s=s.replace("                _require_parent_under_fit_lock(run,old,provenance,checkpoint)","                compatibility=_require_parent_under_fit_lock(run,old,provenance,checkpoint)");s=s.replace("        _immutable(destination/'claim.json',","        if compatibility is not None:\n            _immutable(destination/'operational-source-compatibility.json',compatibility)\n        _immutable(destination/'claim.json',",1);p.write_text(s)
p=H/'operational_source_compatibility.py';s=p.read_text();oldhash=sha((H/'DRAFT01_training.py').read_bytes());s=s.replace(oldhash,sha((H/'training.py').read_bytes()))
s=s.replace("   block=os.read(fd,min(1024**2,FILE+1-len(raw)))","   require(time.monotonic()-budget['begun']<120,'finite operational evidence deadline')\n   block=os.read(fd,min(1024**2,FILE+1-len(raw)))")
s=s.replace("new['source_commit']!=HISTORICAL_SOURCE,","type(new['source_commit'])is str and len(new['source_commit'])==40 and all(c in '0123456789abcdef' for c in new['source_commit']) and new['source_commit']!=HISTORICAL_SOURCE,")
# The same strict policy predicate is independently usable on metadata only.
a=s.index(" require(type(policy)is dict");b=s.index(" require(ad.experiment['family']",a)
segment=s[a:b]
segment=segment.replace(" helper_sha=sha(_read(Path(__file__),budget));delta=", " delta=")
segment=segment.replace("'plan_input','provenance'", "'plan_input','job_input','provenance'")
segment += "\n for name in ('closure_input','claim_input','failed_input','checkpoint_input','plan_input','job_input'):\n  require(type(hist[name])is str and hist[name] and '/' not in hist[name] and '..' not in hist[name],'historical registered role unavailable')\n require(type(target['closure_input'])is str and target['closure_input'],'target closure role unavailable')\n require(type(hist['provenance'])is dict and hist['provenance'].get('source_commit')==HISTORICAL_SOURCE and hist['provenance'].get('source_hashes')==sorted(set(OLD_MAP.values())),'original full provenance unavailable')\n return policy\n"
s=s[:a]+" helper_sha=sha(_read(Path(__file__),budget));validate_contract(policy,helper_sha)\n hist=policy['historical'];target=policy['target'];consumers=policy['consumers']\n"+s[b:]
pos=s.index('\ndef _registered_unlocked')
s=s[:pos]+"\ndef validate_contract(policy,helper_sha):\n \"\"\"Strict metadata only; a matching document is not independent authority.\"\"\"\n"+segment+s[pos:]
s=s.replace("require(ad.experiment['family']==FAMILY,", "require(ad.experiment['family']==FAMILY and ad.spec['program_id']==PROGRAM,")
s=s.replace("closure=json.loads(read(target['closure_input']));require(closure['installed']", "closure=json.loads(read(target['closure_input']));require(type(closure)is dict and set(closure)=={'schema_version','installed','scientific_model','scientific_training','candidate02'} and closure['schema_version']==1 and closure['candidate02']==fixture.CANDIDATE,'full target closure schema')\n require(closure['installed']")
s=s.replace(" oldplan_raw=read(hist['plan_input']);oldplan=json.loads(oldplan_raw)"," oldjob_raw=read(hist['job_input']);oldjob=json.loads(oldjob_raw)\n from . import financial_wrapper_fixture as fixture\n fixture.schema(oldjob)\n require(sha(oldjob_raw)==claim['inputs']['execution_job']['sha256'],'exact original selected job')\n oldplan_raw=read(hist['plan_input']);oldplan=json.loads(oldplan_raw);fixture.validate_plan(oldplan)\n require(sha(oldplan_raw)==claim['inputs'][oldjob['payload']['plan_input']]['sha256'],'exact original job-selected plan')")
s=s.replace(" require(any(r['sha256']==sha(oldplan_raw) for r in claim['inputs'].values()),'old selected plan not a genuine claim input')", " require(claim['experiment']['cells']==[plan['cell_id']],'original admitted fit cell')\n for key,pin in (('model_input',MODEL),('training_input',TRAINING),('recipe_input',old['input_hash'])):\n  require(claim['inputs'][oldplan[key]]['sha256']==pin,'original scientific input hash differs')")
insert=""" # Recheck original failed-fit metadata at the held-lock boundary as well.
 prior=json.loads(read(plan['prior_input']))
 require(prior['parent']==HISTORICAL_ID and prior['provenance']==old and prior['checkpoint_input']==hist['checkpoint_input'],'original parent descriptor join')
 def original(role,path):
  body=read(prior[role]);require(ad.root/ad.inputs[prior[role]]['path']==path and body==_read(path,budget),'original failed-fit evidence origin differs')
  return json.loads(body)
 require(original('fit_claim_input',expected/'claim.json')=={'experiment_id':HISTORICAL_ID,'provenance':old,'parent_checkpoint':None},'original fresh interrupt fit claim')
 require(original('failed_fit_input',expected/'failed.json')=={'type':'PlannedInterruption','reason':'prospective engineering failed-parent fixture after one real update; no fit completion','last_checkpoint':str(cp)},'actual planned failed-fit terminal')
 diagnostic=ad.root/'research_artifacts/financial_wrapper_engineering'/oldplan['namespace']/'interrupted-checkpoint.json'
 require(original('diagnostic_input',diagnostic)=={'checkpoint':str(cp),'sha256':HISTORICAL_CHECKPOINT_SHA256,'provenance':old,'epochs_completed':1,'requires_genuine_failed_parent':True},'original interrupt diagnostic')
 require(original('schedule_input',expected/'schedule.json')=={'training':json.loads(read(plan['training_input'])),'seed':11,'task':plan['task'],'n_examples':16},'original complete schedule')
"""
pos=s.index(" for name,item in manifest['members'].items():");s=s[:pos]+insert+s[pos:]
p.write_text(s);ast.parse(s)
# Final inverse starts from original sources, retains initial inverse separately.
inv=json.loads((H/'SOURCE_INVERSES01.json').read_text())
for n in ('financial_wrapper_fixture.py','training.py'):
 new=(H/n).read_text();base=(H/('original_'+n)).read_text()
 if n=='training.py':
  inv['changes'][n][0]['new']=inv['changes'][n][0]['new'].replace('_require_parent_under_fit_lock(run,old,provenance,checkpoint)','compatibility=_require_parent_under_fit_lock(run,old,provenance,checkpoint)')
  inv['changes'][n]+=[{'old':'    with _lock(run.admission.root):','new':'    compatibility=None\n    with _lock(run.admission.root):'},{'old':"        _immutable(destination/'claim.json',",'new':"        if compatibility is not None:\n            _immutable(destination/'operational-source-compatibility.json',compatibility)\n        _immutable(destination/'claim.json',"}]
 back=new
 for row in reversed(inv['changes'][n]):assert back.count(row['new'])==1;back=back.replace(row['new'],row['old'])
 assert back==base and ast.dump(ast.parse(back))==ast.dump(ast.parse(base))
 inv['sources'][n]['new_sha256']=sha(new.encode())
 (H/(n+'.FINAL.patch')).write_text(''.join(difflib.unified_diff(base.splitlines(True),new.splitlines(True),fromfile='original_'+n,tofile=n)))
(H/'SOURCE_INVERSES02.json').write_text(json.dumps(inv,indent=2,sort_keys=True)+'\n')
print('final copied sources parsed and exact inverses verified')
