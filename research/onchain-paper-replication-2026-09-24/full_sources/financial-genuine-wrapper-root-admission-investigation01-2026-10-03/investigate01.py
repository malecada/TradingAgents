"""Bounded source/OID inventory; no package import, admission or numerical work."""
import ast, collections, hashlib, json, pathlib, stat, subprocess
ROOT=pathlib.Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
BASE=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
OUT=pathlib.Path(__file__).resolve().parent
PREP=BASE/'financial-genuine-wrapper-preparation02-2026-10-03'
CAP=pathlib.Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source')
MAIN='a9f18fffbc06b9e3996b67fc2a0139ce98900709'
HELD='d443208795f59292c156c5b81b687594efacea4d'
PREFIX='tradingagents/research/onchain_replication/'
H=lambda b:hashlib.sha256(b).hexdigest()
def read(p):
 p=pathlib.Path(p);s=p.lstat()
 assert p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
 assert not any(x.lower() in {'keys','apis','.env','.ssh','hf_token.txt'} for x in p.parts)
 b=p.read_bytes();assert len(b)==s.st_size and p.stat().st_mtime_ns==s.st_mtime_ns
 return b
def js(p):return json.loads(read(p))
def save(n,x):
 with (OUT/n).open('x') as f:json.dump(x,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
def meta(p):
 b=read(p);return {'path':str(p),'sha256':H(b),'bytes':len(b),'mode':stat.S_IMODE(p.stat().st_mode)}
def git(root,*args):
 r=subprocess.run(['git','--no-optional-locks','-C',str(root),*args],capture_output=True,timeout=20,check=True)
 assert len(r.stdout)<512*1024 and not r.stderr
 return r.stdout
def tree(root,oid,paths):
 raw=git(root,'ls-tree','-z',oid,'--',*sorted(paths));rows={}
 for row in raw.split(b'\0'):
  if not row:continue
  header,name=row.split(b'\t');mode,kind,blob=header.decode().split();assert kind=='blob'
  rows[name.decode()]={'mode':mode,'oid':blob}
 return rows,H(raw)
def oid(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
installation=js(PREP/'INSTALLATION01.json')['sources'];closure=js(PREP/'SOURCE_CLOSURE01.json')
assert len(installation)==194 and closure['installed']=={k:v['sha256'] for k,v in installation.items()}
assert H(read(PREP/'financial_wrapper_fixture.py'))=='e13d7170a55165f1c5d2313223cf972dc102d0beac95ba49c493c146ed4a4897'
assert H(read(PREP/'MANIFEST02.json'))=='664ca3075fe1c3eff3b66e8219af44331b2d3ffb082f86977231971a5e5d517b'
assert git(CAP,'rev-parse','HEAD').decode().strip()==HELD
main_observed=git(ROOT,'rev-parse','HEAD').decode().strip()
checks=[]
for directory,mname,pin in [(PREP,'MANIFEST02.json','664ca3075fe1c3eff3b66e8219af44331b2d3ffb082f86977231971a5e5d517b'),(BASE/'financial-genuine-wrapper-review02-2026-10-03','MANIFEST02.json','2148df3dfb53a3851baaba1e4aaa5b3a16955de2acac18d67b2caee3c5e045d0'),(BASE/'financial-genuine-wrapper-review01-2026-10-03','MANIFEST01.json','b3ad1aa408518e275737d17225a3a71165cda0b9b38809f65ff73c9512e6145e')]:
 m=js(directory/mname);assert H(read(directory/mname))==pin
 rows=m.get('members',m.get('files'))
 for row in rows:
  if row.get('kind')=='directory':continue
  b=read(directory/row['path']);assert H(b)==row['sha256'] and len(b)==row['bytes']
  if 'mode' in row:assert stat.S_IMODE((directory/row['path']).stat().st_mode)==row['mode']
 checks.append({'manifest':str(directory/mname),'sha256':pin,'verified_bodies':len(rows)})
mt,mt_hash=tree(ROOT,MAIN,installation);ct,ct_hash=tree(CAP,HELD,installation)
delta=[]
financial={'financial_execution.py','checkpoints.py','training.py','evaluation.py','model_registry.py','run.py'}
for name,v in sorted(installation.items()):
 b=read(ROOT/v['source']);assert H(b)==v['sha256'];node=ast.parse(b) if name.endswith('.py') else None
 role=('new wrapper and genuine admission predicates' if name.endswith('/financial_wrapper_fixture.py') else 'financial candidate02 optional selected-execution seam' if pathlib.Path(name).name in financial else 'conditional job dispatch and native preflight' if name==PREFIX+'job.py' else 'candidate02 replay plus explicit classification/regression task seam' if name==PREFIX+'replay.py' else 'inherited prospective helper; old defaults are not financial launch authority' if name.startswith(('fixture_tools/','proof_tools/')) else 'inherited scientific or authority package closure' if name.startswith('tradingagents/') else 'inherited explicit dynamic source dependency')
 row={'target':name,'origin':v['source'],'candidate_sha256':H(b),'candidate_bytes':len(b),'candidate_mode':stat.S_IMODE((ROOT/v['source']).stat().st_mode),'role':role}
 for label,root,objects in [('main',ROOT,mt),('held_capsule',CAP,ct)]:
  p=root/name
  if name in objects:
   bb=read(p);assert oid(bb)==objects[name]['oid']
   row[label]={**objects[name],'sha256':H(bb),'bytes':len(bb),'relation':'identical' if bb==b else 'different'}
   if bb!=b and node is not None:
    def defs(raw):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
    old,new=defs(bb),defs(b);row[label]['changed_top_level_definitions']=sorted(k for k in old.keys()|new.keys() if old.get(k)!=new.get(k))
  else:assert not p.exists();row[label]={'oid':None,'sha256':None,'relation':'absent'}
 delta.append(row)
pkg={k for k in installation if k.startswith('tradingagents/') and k.endswith('.py')}
cap_pkg={str(p.relative_to(CAP)) for d in ['tradingagents/research','tradingagents/research/onchain_replication'] for p in (CAP/d).glob('*.py')}|{'tradingagents/__init__.py'}
assert len(pkg)==149 and len(cap_pkg)==148
reg=js(CAP/'held-fixture-registration01.json')
case={k:{'source_count':len(v['source_files']),'source_paths_not_in_financial_recipe':sorted(set(v['source_files'])-set(installation))} for k,v in reg['experiments'].items() if k.startswith('original-import-held-')}
inventory={'schema_version':1,'qualification':'read-only authenticated source/OID comparison, not installation or authority','main_reference_commit':MAIN,'main_observed_head':main_observed,'held_immutable_commit':HELD,'main_selected_ls_tree_sha256':mt_hash,'held_selected_ls_tree_sha256':ct_hash,'counts':{'recipe':194,'recipe_package':149,'recipe_nonpackage':45,'main_relations':dict(collections.Counter(r['main']['relation'] for r in delta)),'held_relations':dict(collections.Counter(r['held_capsule']['relation'] for r in delta))},'held_package_extra':sorted(cap_pkg-pkg),'financial_package_additions':sorted(pkg-cap_pkg),'held_cases':case,'rows':delta,'future_installed_source':None,'future_design_source':None,'future_source_count':None}
save('FILE_DELTA01.json',inventory)
phases=[]
templates=js(PREP/'PHASE_TEMPLATES01.json')['templates'];assert len(templates)==18
for n,p in enumerate(templates,1):
 assert p['experiment'] is p['cell_id'] is p['namespace'] is None
 task,backend,phase=p['task'],p['execution'],p['phase'];key=f'{task}/{backend}/{phase}'
 group=f'{task}/{backend}'
 deps=([group+'/interrupt1',group+'/complete100'] if phase=='continue100' else [group+'/continue100'] if phase=='predict' else [])
 row={'slot_index':n,'logical_key_not_identity':key,'phase':phase,'task':task,'backend':backend,'actual_experiment':None,'actual_cell':None,'actual_namespace':None,'actual_source':None,'actual_registration_sha256':None,'actual_claim_sha256':None,'actual_native_evidence':None,'actual_outcome':None,'actual_external_recovery':None,'dependencies':deps,'dependency_selection_qualification':'predict uses continued COMPLETE parent in this concrete proposed coverage DAG; source also permits genuine complete100 parent','expected_lifecycle_status':'FAILED' if phase=='interrupt1' else 'COMPLETE','expected_fit_terminal':'FAILED' if phase=='interrupt1' else 'COMPLETE' if phase in ('complete100','continue100') else None,'optimizer_updates_if_successful':2 if phase=='agreement' else 1 if phase=='interrupt1' else 100 if phase=='complete100' else 99 if phase=='continue100' else 0,'training_fit_cell_calls':int(phase in ('interrupt1','complete100','continue100')),'original_schedule_epochs':100,'paper_fit_credit':0,'cell_constraint':'same cell as authentic interrupt1 parent' if phase=='continue100' else 'same cell as actual COMPLETE parent' if phase=='predict' else 'unique cell relative to other independent fits; uninterrupted reference differs from interrupt1 cell' if phase=='complete100' else 'separate per task/backend cell; reused only by declared continuation and prediction' if phase=='interrupt1' else 'separate agreement engineering cell; checkpoint is never completed-fit authority','checkpoint_requirement':{'agreement':'two actual one-update state roundtrips and replay; no fit completion','interrupt1':'actual failed first epoch, cursor1/batch0, exact schedule/log, PlannedInterruption diagnostic','complete100':'actual 100 epoch/log completion and final checkpoint100/0','continue100':'authentic FAILED interrupt1 plus all checkpoint members and authentic COMPLETE100 reference; actual loader verifies1/0 before fit reservation; exact final model/Adam/RNG/log comparison','predict':'authentic COMPLETE parent plus original fit completion100 and all checkpoint members; zero updates, saved-model replay'}[phase],'prerequisite_inputs':list(js(PREP/'INPUT_TEMPLATE01.json')['inputs'])}
 if phase=='continue100':row['prerequisite_inputs']+=['prior descriptor','parent claim','parent FAILED terminal','parent job','parent selected plan','parent fresh fit claim','parent failed fit','parent interrupted-checkpoint diagnostic','parent schedule','parent checkpoint manifest','every parent checkpoint member','uninterrupted_reference descriptor','reference claim','reference COMPLETE terminal','reference fit complete','reference checkpoint manifest','every reference checkpoint member']
 if phase=='predict':row['prerequisite_inputs']+=['prior descriptor','parent claim','parent COMPLETE terminal','parent fit complete','parent checkpoint manifest','every parent checkpoint member']
 phases.append(row)
keys={r['logical_key_not_identity'] for r in phases};assert len(keys)==18 and all(set(r['dependencies'])<=keys for r in phases)
save('PHASE_DAG01.json',{'schema_version':1,'status':'all18 unreserved/unperformed','rows':phases,'expected_dispositions_if_all_contracts_met':{'claims':18,'COMPLETE':14,'FAILED_planned_interruptions':4,'fit_cell_invocations':12,'completed_100epoch_fits':8,'one_update_agreement_cases':2,'prediction_only_cases':4,'training_optimizer_updates':800,'agreement_optimizer_updates':4,'paper_financial_fits':0},'topological_layers':[[r['logical_key_not_identity'] for r in phases if r['phase']=='agreement'],[r['logical_key_not_identity'] for r in phases if r['phase'] in ('interrupt1','complete100')],[r['logical_key_not_identity'] for r in phases if r['phase']=='continue100'],[r['logical_key_not_identity'] for r in phases if r['phase']=='predict']],'layer_semantics':'dependency order only; ONE numerical launcher sequentially, no parallel job authority; agreement-first is proposed engineering gate, not implicit source prerequisite'})
core=['model.py','gat.py','pooling.py','temporal.py','streamed_gat.py']
science=[]
for name in core:
 row=next(r for r in delta if r['target']==PREFIX+name);assert row['main']['relation']=='identical' and row['held_capsule']['relation']=='identical';science.append(row['target'])
for name,pin in [('model.json',closure['scientific_model']),('training.json',closure['scientific_training'])]:
 b=read(PREP/name);assert H(b)==pin and b==read(ROOT/'research/onchain-paper-replication-2026-09-24/config'/name)
checks.append({'original_scientific_configs_exact':True,'identical_equation_modules':science})
adapt=js(PREP/'adaptations.json');inverse={}
for name,changes in adapt.items():
 txt=read(PREP/name).decode()
 for change in reversed(changes):assert txt.count(change['after'])==change.get('count',1);txt=txt.replace(change['after'],change['before'])
 baseline=PREP/('job.baseline.py' if name=='job.py' else 'candidate02/replay.py');assert txt.encode()==read(baseline)
 inverse[name]={'conditional_hunks':len(changes),'restored_sha256':H(txt.encode()),'restored_origin':str(baseline)}
save('EVIDENCE01.json',{'schema_version':1,'manifest_readbacks':checks,'conditional_full_text_inverse':inverse,'subject_manifest':meta(PREP/'MANIFEST02.json'),'wrapper':meta(PREP/'financial_wrapper_fixture.py'),'inputs':{n:meta(PREP/n) for n in ['JOB_TEMPLATE01.json','REGISTRATION_TEMPLATE01.json','PHASE_TEMPLATES01.json','SOURCE_CLOSURE01.json','RUNTIME_TEMPLATE01.json','CONTINUATION_INPUTS02.json','RECIPE01.json','model.json','training.json']},'authority_interface_sources':{n:meta(ROOT/installation[n]['source']) for n in ['tradingagents/research/admission.py','tradingagents/research/lifecycle.py','tradingagents/research/verify.py',PREFIX+'job.py',PREFIX+'resources.py',PREFIX+'matching_owner.py',PREFIX+'compact_owner.py',PREFIX+'resource_binding.py']},'runtime_native_numerical_claim_execution':False,'future_runtime_pin':None,'future_family_budget_review':None,'future_recovery_pin':None})
print(json.dumps({'main':main_observed,'counts':inventory['counts'],'phases':len(phases),'inverse':inverse},sort_keys=True))
