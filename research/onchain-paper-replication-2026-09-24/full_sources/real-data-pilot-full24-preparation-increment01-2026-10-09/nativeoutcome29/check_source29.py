"""Finite author source check only; --freeze after mandatory public roots exist."""
import ast,difflib,hashlib,json,os,resource,signal,sys
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(15)
H=Path(__file__).resolve().parent;O=H.parent/'postnative28';F=H.parent.parent;R=F.parents[2];checks=[];refs={}
def read(p):
 b=p.read_bytes();assert len(b)<2*1024**2;refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};return b.decode()
def ck(v,n):checks.append({'name':n,'pass':bool(v)});assert v,n
def write(n,v):
 with (H/n).open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
roster=json.loads(read(H/'PROSPECTIVE_ROSTER01.json'));oldm=json.loads(read(O/'HELPERS_MANIFEST01.json'));ck(refs[str((O/'HELPERS_MANIFEST01.json').relative_to(R))]['sha256']=='7fcce3d8362bc16288e5706e9613c16bfa32df0fbf6fb41e44b04b8351b47725','exact accepted28 helper manifest')
patch=[];inverse=[];texts={}
for name in ('select','capture','recover'):
 old=read(O/(name+'28.py'));new=read(H/(name+'29.py'));texts[name]=new;ast.parse(new)
 ck(refs[str((O/(name+'28.py')).relative_to(R))]==oldm['files'][name+'28.py'],'original28 source '+name)
 patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=name+'28.py',tofile=name+'29.py'));inverse.extend(difflib.unified_diff(new.splitlines(True),old.splitlines(True),fromfile=name+'29.py',tofile=name+'28.py'))
 if name!='select':
  restored=new
  for a,b in roster['capture_literal_map' if name=='capture' else 'recovery_literal_map'].items():restored=restored.replace(b,a)
  ck(restored==old and ast.dump(ast.parse(restored))==ast.dump(ast.parse(old)),'exact literal and AST inverse '+name)
  ck(new.count('hashlib.sha256')==old.count('hashlib.sha256') and 'sha296' not in new,'unaltered digest primitive '+name)
ck(read(H/'LITERAL_PATCH01.diff')==''.join(patch) and read(H/'LITERAL_INVERSE01.diff')==''.join(inverse),'full three-helper exact diff')
select=texts['select'];tree=ast.parse(select)
def value(name):return ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)))
ck(value('owned')==roster['owned_public_roots'] and len(set(value('owned')))==6,'six exact public roots')
ck(value('main_source_names')==[] and value('scopes')==[] and 'scope.rglob' not in select and 'installation=json.loads' not in select and 'prospective native03 identity already attempted' not in select,'no Main adoption or empirical scope and no obsolete pre-attempt guard')
ck(value('prior_generated_names')==roster['prior_generated_files'] and len(value('prior_generated_names'))==33 and value('helper_names')==tuple(roster['helper_names']),'finite prior28 receipts13 raw pairs and commit stdout stderr plus own helper roster')
ck(value('fixed_public_names')==roster['fixed_public_names'],'exact STATE coordination names')
ck("required final public scope absent" in select and "root.is_dir() and not root.is_symlink()" in select and "elif path.is_dir():scope_directories.add(path)" in select,'mandatory roots fail closed and empty directories retained')
old=read(O/'select28.py');ck(select[select.index('reused=[]'):select.index('selection = {')]==old[old.index('reused=[]'):old.index('selection = {')],'unchanged exact row reuse typed body mode secret64MiB metadata guards')
ck("'earlier_inherited_reuse_preserved_by_receipt':prior_selection['prior_inherited_reuse_preserved_by_receipt']" in select and "'prior_inherited_reuse_preserved_by_receipt':prior_selection['exact_unchanged_prior_rows_reused']" in select,'preserve both inherited receipt generations')
prior=json.loads(read(O/'FRESH_GIT_RECOVERY28.json'));ck(refs[str((O/'FRESH_GIT_RECOVERY28.json').relative_to(R))]['sha256']==roster['baseline_recovery_sha256'] and prior['source']==roster['baseline_source']=='7d7adf135f319530770c328cb19a7ec438364994','actual28 baseline source receipt pin')
cap=json.loads(read(O/'CAPTURE28.json'));ck(refs[str((O/'CAPTURE28.json').relative_to(R))]['sha256']==prior['capture']['sha256'],'actual28 capture join')
sel=json.loads(read(O/'SELECTION28.json'));ck(refs[str((O/'SELECTION28.json').relative_to(R))]['sha256']==cap['selection']['sha256'] and len(sel['exact_unchanged_prior_rows_reused'])==8 and len(sel['prior_inherited_reuse_preserved_by_receipt'])==67,'actual28 reused8 and inherited67 receipt scope')
accepted=json.loads(read(F/'pilot34-postnative-increment-return-review01-2026-10-11/REVIEW01.json'));ck(refs[str((F/'pilot34-postnative-increment-return-review01-2026-10-11/REVIEW01.json').relative_to(R))]['sha256']==roster['accepted_return_sha256'] and accepted['source']==prior['source'] and accepted['archive']==prior['returned_archive'],'accepted actual28 continuity without archive replay')
ck("('post-native-increment28.tar','fresh-git-recovered-postnative28.tar','actual_external_archive_blob_return.stdout')" in select and "path.stat().st_size==prior_receipt['returned_archive']['bytes'] and sha(path)==prior_receipt['returned_archive']['sha256']" in select,'exact three duplicate aliases extent hash authentication')
ck("Git delta outside declared nativeoutcome29 scope" in select and "HERE/'SELECTION29.json'" in select and "'selection29 already spent'" in select and "(HERE/'SELECTION29.json').open('x')" in select,'bounded Git delta and exclusive selection identity')
roots=[F/n for n in roster['owned_public_roots']];allowed=set(roster['fixed_public_names'])|{str((O/n).relative_to(R)) for n in roster['prior_generated_files']}|{str((H/n).relative_to(R)) for n in roster['helper_names']}
def permits(n):return n in allowed or any((R/n).is_relative_to(p) for p in roots)
ck(all(permits(n) for n in roster['fixed_public_names']) and permits(str((F/roster['owned_public_roots'][3]/'compiled_edge_owner.py').relative_to(R))),'finite public bundle and fixed supported names')
ck(not any(permits(n) for n in ['tradingagents/research/onchain_replication/compiled_edge_owner.py','research_runs/eth-paper-real-data-end-to-end-resource-20261011-34/failed.json','research_artifacts/archive-dispatch-ethpilot-20261011-34/result.json',str((H/'SELECTION29.json').relative_to(R))]),'Main scientific and generated products refused by declared name domain')
missing=[n for n in roster['owned_public_roots'] if not (F/n).is_dir() or (F/n).is_symlink()]
out={'status':'SOURCE_CHECKS_PASS_ROOTS_PRESENT' if not missing else 'SOURCE_CHECKS_PASS_ROOTS_PENDING','checks':checks,'references':refs,'missing_mandatory_roots':missing,'helpers_executed':False,'limits':['Author source checks only; different-author helper review required.','Directory presence is not review acceptance; Root must wait for frozen bundle/outcome/integration/tools reviews before one selection.','No Git/native/network/selection/capture/recovery or old scientific scope execution.','Current declared sources only; no Main adoption or full runtime/private/POSIX reconstruction/deletion claim.']}
if '--freeze' in sys.argv:
 ck(not missing,'mandatory roots exist before author freeze');write('AUTHOR_CHECK01.json',out)
 files={n:{'bytes':(H/n).stat().st_size,'sha256':hashlib.sha256((H/n).read_bytes()).hexdigest()} for n in roster['helper_names'] if n!='HELPERS_MANIFEST01.json'}
 write('HELPERS_MANIFEST01.json',{'status':'FROZEN_SOURCE_ONLY_INDEPENDENT_REVIEW_PENDING','files':files,'baseline_source':roster['baseline_source'],'original_helpers':{n+'28.py':oldm['files'][n+'28.py'] for n in ('select','capture','recover')},'helpers_executed':False})
else:write('PREPARATION_CHECK01.json',out)
print(json.dumps({'status':out['status'],'checks':len(checks),'missing':missing,'helpers_executed':False}))
