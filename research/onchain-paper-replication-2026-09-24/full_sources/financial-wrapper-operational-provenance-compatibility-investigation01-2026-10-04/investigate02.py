"""Read-only source/metadata/opaque digest investigation; no project imports."""
import ast,copy,hashlib,json,os,stat,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');N=B/'financial-wrapper-complete100-next-phase-investigation01-2026-10-04';checks=[];rows=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def ck(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def read(p):
 s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_size<=4194304 and p.resolve()==p,'bounded canonical '+str(p));raw=p.read_bytes();t=p.lstat();ck((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns,t.st_ctime_ns),'stable '+str(p));return raw
def put(n,v):(H/n).write_text(json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+'\n')
ck(sys.version_info[:3]==(3,13,13),'pinned runtime')
# Authenticate frozen next-phase investigation, without executing its stale pre-failure assertions.
mraw=read(N/'MANIFEST01.json');manifest=json.loads(mraw)
for r in manifest['members']:
 p=N/r['path'];s=p.lstat();ck(stat.S_IMODE(s.st_mode)==r['mode'],'next-phase mode')
 if r.get('kind')=='directory':ck(stat.S_ISDIR(s.st_mode),'next-phase directory')
 else:ck(sha(read(p))==r['sha256'],'next-phase hash')
(H/'NEXT_PHASE_MANIFEST01.json').write_bytes(mraw);(H/'NEXT_PHASE_REPORT_ORIGINAL01.md').write_bytes(read(N/'REPORT01.md'))
for name in ('PARENT_INPUT_REQUIREMENTS01.json','ORIGINAL_PHASE_TEMPLATES01.json','ORIGINAL_CHARTER02.json','NEXT_PHASE_REQUIREMENTS02.json'):(H/name).write_bytes(read(N/name))
closure_raw=read(S/'fixture_inputs/financial_wrapper_claimedrun01/source_closure.json');closure=json.loads(closure_raw);source=closure['installed'];ck(len(source)==194,'194 installed paths');(H/'SOURCE_CLOSURE_ORIGINAL01.json').write_bytes(closure_raw)
source_rows=[]
for rel,pin in sorted(source.items()):
 ck(not Path(rel).is_absolute() and '..' not in Path(rel).parts and not set(Path(rel).parts)&{'keys','apis','.env','hf_token.txt'},'safe literal source path')
 raw=read(S/rel);ck(sha(raw)==pin,'installed source hash '+rel);p=H/'source-original'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);os.chmod(p,stat.S_IMODE((S/rel).stat().st_mode));source_rows.append({'path':rel,'sha256':pin,'bytes':len(raw),'mode':stat.S_IMODE((S/rel).stat().st_mode)})
# Authenticate parent bytes, preserving historical paths/provenance and hashing state only.
parent_req=json.loads((H/'PARENT_INPUT_REQUIREMENTS01.json').read_text());metadata={};opaque=[]
for row in parent_req['rows']:
 raw=read(S/row['path']);ck(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'actual parent evidence '+row['descriptor_field'])
 if row['descriptor_field'].startswith('checkpoint_member:'):opaque.append(row)
 else:
  name=row['descriptor_field']+'.json';(H/'parent-metadata').mkdir(exist_ok=True);(H/'parent-metadata'/name).write_bytes(raw);metadata[row['descriptor_field']]=json.loads(raw)
claim=metadata['claim_input'];cp=metadata['checkpoint_input'];oldprov=cp['provenance'];parent=claim['experiment_id'];ck(claim['source']==claim['design_source']==oldprov['source_commit']=='0a2e7639b42b9423b90743feadcda4078aa21816','actual historical source0a2')
ck(claim['inputs']['source_closure']['sha256']==sha(closure_raw),'historical/current closure identity');ck(oldprov['source_hashes']==sorted(set(source.values())),'checkpoint equals all installed source hashes');ck(len(oldprov['source_hashes'])==193,'193 distinct hashes from194 paths');ck(metadata['fit_claim_input']['provenance']==oldprov==metadata['diagnostic_input']['provenance'],'all old provenance equal');ck(metadata['terminal_input']['claim_sha256']==sha((H/'parent-metadata/claim_input.json').read_bytes()),'failed terminal exact parent claim')
current=subprocess.run(['git','-C',str(S),'rev-parse','HEAD'],capture_output=True,text=True,check=True,timeout=10).stdout.strip();ck(current=='9dc5c79f738920b52947b4e63fed0397f1b5b207','current9dc5 distinct historical0a2')
# Exact source predicates, executed only as pure metadata AST expressions.
prefix='tradingagents/research/onchain_replication/'
fw=ast.parse(read(S/(prefix+'financial_wrapper_fixture.py')));training=ast.parse(read(S/(prefix+'training.py')));cache=ast.parse(read(S/(prefix+'cache.py')))
def node(tree,name):return next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)
def require_pred(func,message):
 return next(n.args[0] for n in ast.walk(func) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value==message)
parent_pred=require_pred(node(fw,'_parent'),'prior scientific provenance differs');reference_pred=require_pred(node(fw,'_reference_state'),'reference scientific provenance differs')
reserve_pred=next(n.test for n in ast.walk(node(training,'_reserve')) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and any(isinstance(x,ast.Constant) and x.value=='continuation scientific provenance mismatch' for x in ast.walk(n)))
def runexpr(expr,env):return eval(compile(ast.Expression(expr),'<actual-source-metadata-predicate>','eval'),{'__builtins__':{}},env)
new=copy.deepcopy(oldprov);new['source_commit']='1'*40
ck(runexpr(parent_pred,{'value':{'provenance':oldprov},'prov':new}),'same full hashes allows only commit change');ck(not runexpr(reserve_pred,{'old':oldprov,'provenance':new}),'reserve same full hashes allows only commit change')
watch=prefix+'workflow_storage.py';watch2=B/'financial-wrapper-storage-watch-concurrent-publication-correction02-2026-10-04/workflow_storage.py';newmap=dict(source);newmap[watch]=sha(read(watch2));new['source_hashes']=sorted(set(newmap.values()))
ck(not runexpr(parent_pred,{'value':{'provenance':oldprov},'prov':new}),'watcher-only change rejected by wrapper');ck(runexpr(reserve_pred,{'old':oldprov,'provenance':new}),'watcher-only change rejected by reserve')
ref=copy.deepcopy(new);ref['cell_id']='opaque-separate-reference';ck(runexpr(reference_pred,{'ref':{'provenance':ref},'prov':new}),'same future map reference/current compare unchanged')
ck(not runexpr(reference_pred,{'ref':{'provenance':oldprov},'prov':new}),'old map reference/current compare refuses')
rows.append({'case':'actual-source-comparison-barriers','wrapper_parent_refuses_changed_watch':True,'training_reserve_refuses_changed_watch':True,'same_future_map_reference_accepted':True,'old_map_reference_refused':True})
# A source-map-delta evidence checker only; it is deliberately not a run/migration authorization API.
def exact_map_delta(old,new,declared):
 if type(old)is not dict or type(new)is not dict or set(old)!=set(new):raise ValueError('source path census differs')
 actual={k:(old[k],new[k]) for k in old if old[k]!=new[k]}
 if actual!=declared:raise ValueError('complete path-addressed delta differs')
 return len(old)-len(actual)
ck(exact_map_delta(source,newmap,{watch:(source[watch],newmap[watch])})==193,'watcher-only source-delta witness193 unchanged')
for name,mutate in [('undeclared-model-change',lambda v:v.__setitem__(prefix+'model.py','a'*64)),('dropped-path',lambda v:v.pop(watch)),('extra-path',lambda v:v.__setitem__(prefix+'opaque-extra.py','b'*64)),('same-set-path-swap',lambda v:(v.__setitem__(prefix+'model.py',source[prefix+'training.py']),v.__setitem__(prefix+'training.py',source[prefix+'model.py']))),('old-hash-laundering',lambda v:v.__setitem__(watch,source[watch]))]:
 v=dict(newmap);mutate(v)
 try:exact_map_delta(source,v,{watch:(source[watch],newmap[watch])})
 except ValueError:rows.append({'case':name,'refused':True})
 else:raise AssertionError('forged source delta admitted')
# Source-set alone cannot preserve the source path denominator.
groups={}
for path,pin in source.items():groups.setdefault(pin,[]).append(path)
duplicates=[v for v in groups.values() if len(v)>1];ck(sum(len(x)-1 for x in duplicates)==1,'exact duplicate-source denominator')
# Preserve function line/AST/source identities for all required interfaces.
api_names={'financial_wrapper_fixture.py':{'validate_plan','admitted','authorize','provenance','_parent','_interrupt_parent','_interrupt_case','_one_epoch_state','_reference_state','execute'},'training.py':{'_reserve','fit_cell'},'checkpoints.py':{'_provenance','save_checkpoint','load_checkpoint'},'cache.py':{'read_artifact'},'financial_execution.py':{'identity','for_run','check_model','check_state_model','validate_state'},'evaluation.py':{'recover_completed_model'},'job.py':{'required_sources','_admitted','_command'}}
apis=[]
for filename,needed in api_names.items():
 rel=prefix+filename;raw=read(S/rel);tree=ast.parse(raw)
 apis.append({'path':rel,'sha256':sha(raw),'definitions':[{'name':n.name,'line':n.lineno,'end_line':n.end_lineno,'ast_sha256':sha(ast.dump(n,include_attributes=False).encode())} for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in needed]})
for filename in ('admission.py','lifecycle.py'):
 rel='tradingagents/research/'+filename;raw=read(S/rel);tree=ast.parse(raw);apis.append({'path':rel,'sha256':sha(raw),'definitions':[{'name':n.name,'line':n.lineno,'end_line':n.end_lineno,'ast_sha256':sha(ast.dump(n,include_attributes=False).encode())} for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name in {'admit','start','_check_inputs','_check_source','read_input'}]})
put('SOURCE_MAP01.json',{'installed':source,'rows':source_rows,'paths':194,'distinct_hashes':193,'duplicate_hash_paths':duplicates,'actual_current_commit':current,'historical_checkpoint_commit':oldprov['source_commit']})
put('SOURCE_API_MAP01.json',apis);put('SOURCE_PREDICATES01.json',{'wrapper_parent':ast.unparse(parent_pred),'training_reserve_refusal':ast.unparse(reserve_pred),'reference':ast.unparse(reference_pred),'old_source_map_sha256':sha(json.dumps(source,sort_keys=True,separators=(',',':')).encode()),'illustrative_watcher_only_map_sha256':sha(json.dumps(newmap,sort_keys=True,separators=(',',':')).encode()),'illustrative_watch_candidate':{'sha256':newmap[watch],'status':'WITHHELD_SOURCE02_USED_ONLY_FOR_METADATA_INEQUALITY_PROOF'}})
put('RAW_CONTROLS01.json',{'checks':len(checks),'checks_descriptions':checks,'rows':rows,'opaque_checkpoint_members_hashed_not_decoded':opaque,'no_new_provenance_or_receipts_written':True})
put('FACTS01.json',{'historical_parent':parent,'historical_parent_source':claim['source'],'current_source':current,'source_map_paths':194,'checkpoint_distinct_source_hashes':193,'same_current_and_parent_closure':True,'historical_checkpoint_manifest_sha256':sha((H/'parent-metadata/checkpoint_input.json').read_bytes()),'one_watcher_change_keeps_193_other_bodies_equal_but_cannot_pass_current_interfaces':True,'required_equality_call_sites':[{'file':prefix+'financial_wrapper_fixture.py','line':277},{'file':prefix+'training.py','line':42}],'no_checkpoint_loader_change_required':True,'next_phase_investigation_sha256':sha(mraw),'frozen_next_phase_historical_ref_status_superseded':'originalcomplete100 is now permanently FAILED; no accepted replacement reference exists','runtime_imports_or_claims':False})
print(json.dumps({'status':'SOURCE_ONLY_COMPATIBILITY_INVESTIGATION','checks':len(checks),'source_bodies_retained':len(source_rows),'opaque_checkpoint_decoded':False,'comparison_barriers':2}))
