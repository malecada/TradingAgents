"""Read-only actual source/metadata handoff. Writes only this new owned directory.
Never import scientific project code, admit/start, decode checkpoints or mutate Git.
"""
import ast,copy,hashlib,json,os,re,stat,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
C=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
SOURCE='0a2e7639b42b9423b90743feadcda4078aa21816'
GATE='fixture_inputs/financial_wrapper_claimedrun01/gates.json'
REF='financial-wrapper-classification-eager-complete100-20261003-01'
INT='financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01'
PKG='tradingagents/research/onchain_replication/'
sha=lambda b:hashlib.sha256(b).hexdigest()
def encoded(v):return (json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
def put(n,v):(H/n).write_bytes(encoded(v))
checks=[]
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def read(p):
 s=p.lstat();ok(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304 and p.resolve()==p,'bounded canonical metadata/source '+str(p));raw=p.read_bytes();ok((s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==tuple(getattr(p.lstat(),k) for k in ('st_dev','st_ino','st_mode','st_size','st_mtime_ns','st_ctime_ns')),'stable metadata/source '+str(p));return raw
head=subprocess.run(['git','-C',str(C),'rev-parse','HEAD'],check=True,capture_output=True,timeout=10).stdout.decode().strip();ok(head==SOURCE,'actual current source HEAD')
graw=read(C/GATE);ok(sha(graw)=='3a20293832fa7ecc5e2821fb27dc940d1a997ab7f2ad373bc28f73e893e8781a','actual current gate');gate=json.loads(graw);ref=gate['experiments'][REF];active=gate['experiments'][INT]
charterraw=read(C/ref['charter']['path']);ok(sha(charterraw)==ref['charter']['sha256']=='041ab6260eeb81805202ba31c4ba1710b3109bbd0b24131e83a5c4f05984cbb1','original corrected18 phase charter');charter=json.loads(charterraw);(H/'ORIGINAL_CHARTER02.json').write_bytes(charterraw)
ok(len(charter['phases'])==18 and charter['denominator']['training_optimizer_updates']==800 and charter['denominator']['agreement_optimizer_updates']==4,'all18 original phases and804 planned updates')
# Actual current all339 Git records: hash original regular bodies; no array decode.
tree=subprocess.run(['git','-C',str(C),'ls-tree','-rz','--full-tree',SOURCE],check=True,capture_output=True,timeout=10).stdout
source_rows=[];current={}
for item in tree.split(b'\0'):
 if not item:continue
 meta,rawpath=item.split(b'\t',1);mode,kind,oid=meta.decode().split();name=rawpath.decode();ok(kind=='blob' and mode in ('100644','100755') and not Path(name).is_absolute() and '..' not in Path(name).parts,'actual source ordinary Git member')
 body=read(C/name);ok(hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==oid,'actual current Git/body '+name);ok(bool((C/name).stat().st_mode&0o111)==(mode=='100755'),'actual Git executable class '+name)
 source_rows.append({'path':name,'git_mode':mode,'oid':oid,'bytes':len(body),'sha256':sha(body),'actual_mode':stat.S_IMODE((C/name).stat().st_mode)})
 if name!=GATE:current[name]=sha(body)
ok(len(source_rows)==339 and len(current)==338 and current==active['source_files'],'complete actual339/338 current source')
# Eight reference role bodies: only job + closure descriptor relocation necessary.
proposal=copy.deepcopy(ref)
for role in ('execution_job','source_closure'):proposal['inputs'][role]=copy.deepcopy(active['inputs'][role])
proposal['source_files']=current;proposal['cumulative_budget_extension']=copy.deepcopy(active['cumulative_budget_extension'])
roles=[];(H/'draft-inputs').mkdir();old_inputs={};new_inputs={}
for role,descriptor in proposal['inputs'].items():
 raw=read(C/descriptor['path']);ok(sha(raw)==descriptor['sha256'],'draft actual role hash '+role);(H/'draft-inputs'/f'{role}.json').write_bytes(raw);new_inputs[role]=json.loads(raw)
 old_descriptor=ref['inputs'][role];oldraw=read(C/old_descriptor['path']);ok(sha(oldraw)==old_descriptor['sha256'],'historical reference role hash '+role);old_inputs[role]=json.loads(oldraw)
 roles.append({'role':role,'old':old_descriptor,'proposed':descriptor,'source_body_changed':oldraw!=raw,'bytes':len(raw)})
ok(set(new_inputs)=={'environment','execution_job','model','runtime_mapping','source_closure','synthetic_recipe','training','wrapper_plan'},'exact8 roles')
changed=[r['role'] for r in roles if r['source_body_changed']];ok(changed==['execution_job','source_closure'],'exactly2 required corrected role bodies')
plan=new_inputs['wrapper_plan'];ok(plan['phase']=='complete100' and plan['execution']=='eager' and plan['task']=='classification' and plan['experiment']==REF and plan['namespace']==REF and plan['prior_input'] is None and plan['reference_input'] is None,'original unused independent100 reference plan')
ok(proposal['parent'] is None and proposal['cells']==[plan['cell_id']],'independent reference no failed-parent continuation shortcut')
closure=new_inputs['source_closure']['installed'];ok(len(closure)==194 and sum(p.startswith('tradingagents/research/onchain_replication/') for p in closure)==149,'actual194 implementation149package closure')
for p,h in closure.items():ok(current[p]==h,'unchanged implementation current pin '+p)
oldclosure=old_inputs['source_closure']['installed'];diff=[p for p in oldclosure if oldclosure[p]!=closure.get(p)];ok(diff==[PKG+'financial_wrapper_fixture.py'] and closure[diff[0]]=='f4ea651b4677c83f8e16c316d17f704d44d9ec86ff78a4bf7c4b895e92e1a16e','old reference closure one correction193unchanged')
job=new_inputs['execution_job'];oldjob=copy.deepcopy(old_inputs['execution_job']);oldjob['resources']['disk_paths']=[str(C)];oldjob['resources']['storage_budget']['root']=str(C);ok(oldjob==job,'exact job two-root correction only')
# Literal source/API snapshots, AST only; pure original validators are isolated.
source_names=[PKG+n for n in ('financial_wrapper_fixture.py','job.py','training.py','checkpoints.py','environment.py','model.py','model_registry.py','financial_execution.py','streamed_gat.py','resources.py')]+['tradingagents/research/'+n for n in ('budget_extensions.py','admission.py','lifecycle.py','verify.py')]
(H/'source').mkdir();snapshots=[]
for p in source_names:
 raw=read(C/p);ok(sha(raw)==current[p],'actual source closure body '+p);(H/'source'/p.replace('/','__')).write_bytes(raw);t=ast.parse(raw);snapshots.append({'path':p,'sha256':sha(raw),'bytes':len(raw),'definitions':[{'name':n.name,'line':n.lineno,'ast_sha256':sha(ast.dump(n,include_attributes=False).encode())} for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))]})
ftext=(C/(PKG+'financial_wrapper_fixture.py')).read_text();ft=ast.parse(ftext);wanted={'require','validate_plan','schema'};ns={'PHASES':('agreement','interrupt1','complete100','continue100','predict'),'FILE':4194304,'GIB':1024**3}
exec(compile(ast.Module(body=[n for n in ft.body if isinstance(n,ast.FunctionDef) and n.name in wanted],type_ignores=[]),'actual_wrapper_metadata_validators','exec'),ns)
ns['schema'](job);ok(ns['validate_plan'](plan)==plan,'actual source pure plan/job schema accepted')
for key,value in [('prior_input','fake-prior'),('reference_input','fake-reference'),('cell_id','../bad')]:
 v=copy.deepcopy(plan);v[key]=value
 try:ns['validate_plan'](v)
 except ValueError:checks.append('actual plan mutation refusal '+key)
 else:raise AssertionError('plan mutation accepted')
for field,value in [('wall_seconds',1801),('memory_max_bytes',4*1024**3),('disk_floor_bytes',1)]:
 v=copy.deepcopy(job);v['resources'][field]=value
 try:ns['schema'](v)
 except ValueError:checks.append('actual resource mutation refusal '+field)
 else:raise AssertionError('resource mutation accepted')
# Actual two permanently closed claims; no verify/admit/Run API invocation.
claims=[];claim_rows=[];(H/'claims').mkdir()
for p in sorted((C/'research_runs').glob('*/claim.json')):
 raw=read(p);c=json.loads(raw);terminal=read(p.parent/'failed.json');t=json.loads(terminal)
 ok(t['status']=='failed' and t['claim_sha256']==sha(raw) and t['experiment_id']==c['experiment_id'] and not (p.parent/'complete.json').exists(),'actual immutable FAILED claim '+p.parent.name)
 ok(c['program_id']==gate['program_id'] and c['experiment']['family']=='synthetic-financial-wrapper','same program cumulative claim')
 (H/'claims'/(p.parent.name+'.claim.json')).write_bytes(raw);(H/'claims'/(p.parent.name+'.failed.json')).write_bytes(terminal)
 claims.append(c);claim_rows.append({'identity':c['experiment_id'],'claim_sha256':sha(raw),'failed_sha256':sha(terminal),'source':c['source'],'design_source':c['design_source'],'effective_attempt_budget':c['effective_attempt_budget'],'reason':t['reason']})
ok(len(claims)==2 and max(c['effective_attempt_budget'] for c in claims)==19,'actual2spent/highest19')
ok(any(r['claim_sha256']=='d390980c956aab64d5521698cbb6123ccf01ece94a95277b97755f019adf692b' for r in claim_rows),'actual accepted interruption claim')
# Original existing budget API with genuine claim snapshots and genuine authored
# adopted extension/review bytes. No fake review or admission object.
budget_ns={'hashlib':hashlib,'json':json,'re':re};bt=ast.parse((C/'tradingagents/research/budget_extensions.py').read_text());exec(compile(ast.Module(body=[n for n in bt.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'actual_budget_metadata_only','exec'),budget_ns)
def bound(d):
 raw=read(C/d['path']);ok(sha(raw)==d['sha256'],'actual adopted budget metadata pin');return raw
family=gate['families']['synthetic-financial-wrapper']
try:budget_ns['effective_budget'](C,gate['program_id'],REF,ref,family,claims,bound)
except ValueError as e:ok(str(e)=='adopted budget extension must be carried forward','original reference stale budget refusal')
else:raise AssertionError('stale budget admitted')
ceiling=budget_ns['effective_budget'](C,gate['program_id'],REF,proposal,family,claims,bound);ok(ceiling==19 and 19-len(claims)==17,'genuine exact carryforward ceiling19 remaining17')
# Genuine path conventions from actual job source, not invented caller namespace.
jt=ast.parse((C/(PKG+'job.py')).read_text());literal={}
for n in jt.body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('PREFIX','MODULE'):literal[n.targets[0].id]=ast.literal_eval(n.value)
cell=plan['cell_id'];paths={'claim':C/'research_runs'/REF,'job':C/literal['PREFIX']/'runs'/REF,'wrapper':C/'research_artifacts/financial_wrapper_engineering'/REF,'fit_cell':C/'research_artifacts/onchain_fit_cells'/sha(cell.encode())}
for role,p in paths.items():ok(not os.path.lexists(p),'actual next reference fresh '+role)
# Complete18-slot DAG. Logical slot1 maps to actual corrected planned FAILED,
# not the original permanently reserved no-claim outer or unexpected failure.
phases=[]
for p in charter['phases']:
 row=copy.deepcopy(p);row['observed_proposed_claim_exists']=os.path.lexists(C/'research_runs'/p['proposed_identity']);row['actual_fulfillment']=None
 if p['slot_index']==1:row['actual_fulfillment']={'identity':INT,'status':'FAILED_PLANNED_INTERRUPT_OPAQUE_ACCEPTED','claim_sha256':'d390980c956aab64d5521698cbb6123ccf01ece94a95277b97755f019adf692b','checkpoint_state_sha256':'223ced42edec29ec0afd4ea5265b2e0a557a98787e57be47e841e8491511a281','external_recovery':None,'tensor_cursor_validation':False}
 if p['logical_key_not_identity']=='classification/eager/continue100':row['required_actual_parent_identity']=INT;row['required_actual_reference_identity']=REF
 phases.append(row)
ok(sum(r['actual_fulfillment'] is not None for r in phases)==1 and len(phases)-1==17,'full18 slots one planned interruption fulfilled17pending')
# Complete gate draft is NONLIVE. Same physical-root minimal topology only; new
# source=currentdesign commit and fresh external Parent/release remain null.
newgate=copy.deepcopy(gate);newgate['experiments'][REF]=proposal
ok(all(newgate['experiments'][k]==gate['experiments'][k] for k in gate['experiments'] if k!=REF),'all11 other original gate definitions preserved')
put('GATE.DRAFT.json',newgate);put('EXPERIMENT.DRAFT.json',proposal);put('PHASES18.json',phases);put('SOURCE339_READBACK.json',{'source':SOURCE,'git_records':source_rows,'source_pins':current});put('SOURCE_API_JOINS.json',snapshots)
put('INPUT_DELTA.json',{'roles':roles,'unchanged_plan_sha256':sha((H/'draft-inputs/wrapper_plan.json').read_bytes()),'source_closure_delta':[{'path':p,'old':oldclosure[p],'new':closure[p]} for p in diff],'job_delta':['resources.disk_paths[0]','resources.storage_budget.root'],'reference_gate_fields_changed':[k for k in proposal if proposal.get(k)!=ref.get(k)],'old_reference_source_count':289,'current_proposed_source_count':338,'added_source_entries':sorted(set(current)-set(ref['source_files'])),'changed_source_entries':diff,'new_source_files_added':0,'implementation_body_changes':0})
put('CURRENT_CUMULATIVE.json',{'program':gate['program_id'],'family':family,'actual_claims':claim_rows,'effective_ceiling_carried_forward':ceiling,'spent':2,'remaining':17,'new_budget_amendment':False,'base18_prior0_unchanged':True,'first_unused_reference':REF,'actual_reference_claim':None,'paper_fit_credit':0,'old_outer_reserved_no_claim':'financial-wrapper-classification-eager-interrupt1-20261003-01','original_correction_failure_spent':True})
put('CALLER.DRAFT.json',{'status':'DRAFT_NOT_RELEASED','experiment':REF,'cell_id':cell,'phase':'complete100','task':'classification','execution':'eager','root':str(C),'topology':'conditional gate-only current/design successor at SAME absolute root; not executed','registration':GATE,'source':None,'design_source':None,'gate_sha256_if_exact_draft_adopted':sha((H/'GATE.DRAFT.json').read_bytes()),'argv_template':[str(C/'.venv/bin/python'),'-B','-m',literal['MODULE'],'--mode','supervisor','--root',str(C),'--registration',GATE,'--experiment',REF,'--source',None],'interpreter_qualification':'actual reviewed runtime/caller must bind real pinned interpreter; .venv path here is not asserted installed in capsule','derived_namespaces':{k:str(p) for k,p in paths.items()},'new_external_parent_root':None,'new_parent_source':None,'new_request_sha256':None,'independent_source_input_runtime_proof':None,'budget_review':'carry unchanged actual3268 review via source-pinned extension/reference','failed_outcome_actual_external_and_flat_recovery':None,'new_source_and_full_caller_external_and_flat_recovery':None,'native_readiness':None,'numerical_release':None,'scientific_Owner_Binding':'synthetic wrapper does not construct compact scientific Owner/Binding; genuine ResearchRun and native monitor Owner still required','forbidden_reuse':['old5d5 Parent/request529c fixed to spent interrupt identity','spent claimedrun or recordfix identities','old reference289pins/e13wrapper/old absolute resource roots','old source0a2 with changed gate bytes','new root silently relocating absolute checkpoint/diagnostic references']})
put('CHECKS01.json',{'checks':len(checks),'names':checks,'actual_admission_executed':False,'genuine_handles_constructed':False,'checkpoint_decoded':False,'numeric_imports':False,'scope':'actual bounded source/raw metadata and pure extracted schema/budget checks'})
print(json.dumps({'checks':len(checks),'reference':REF,'old_sources':289,'current_sources':338,'claims':len(claims),'ceiling':ceiling,'remaining':17,'draft_gate_sha256':sha((H/'GATE.DRAFT.json').read_bytes())}))
