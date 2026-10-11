"""Finite stdlib source checks only; future mandatory roots checked by selection."""
import ast,difflib,hashlib,json,os,resource,signal,sys
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(15)
H=Path(__file__).resolve().parent;O=H.parent/'nativeoutcome29';F=H.parent.parent;R=F.parents[2];checks=[];refs={}
def read(p):
 b=p.read_bytes();assert len(b)<2*1024**2;refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};return b.decode()
def ck(v,n):checks.append({'name':n,'pass':bool(v)});assert v,n
def write(n,v):
 with (H/n).open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
roster=json.loads(read(H/'PROSPECTIVE_ROSTER01.json'));oldm=json.loads(read(O/'HELPERS_MANIFEST01.json'))
ck(refs[str((O/'HELPERS_MANIFEST01.json').relative_to(R))]['sha256']=='0e3aa221c7c75045c90b740cd3e25919ca5e2f523f18dd1322d2c232b4d10e1e','original29 manifest')
patch=[];inverse=[];texts={}
for name in ('select','capture','recover'):
 old=read(O/(name+'29.py'));new=read(H/(name+'30.py'));texts[name]=new;ast.parse(new)
 ck(refs[str((O/(name+'29.py')).relative_to(R))]==oldm['files'][name+'29.py'],'original29 pinned '+name)
 patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=name+'29.py',tofile=name+'30.py'));inverse.extend(difflib.unified_diff(new.splitlines(True),old.splitlines(True),fromfile=name+'30.py',tofile=name+'29.py'))
 if name!='select':
  restored=new
  for a,b in roster['capture_literal_map' if name=='capture' else 'recovery_literal_map'].items():restored=restored.replace(b,a)
  ck(restored==old and ast.dump(ast.parse(restored))==ast.dump(ast.parse(old)),'literal AST inverse '+name)
 ck(new.count('hashlib.sha256')==old.count('hashlib.sha256'),'digest primitive '+name)
ck(read(H/'LITERAL_PATCH01.diff')==''.join(patch) and read(H/'LITERAL_INVERSE01.diff')==''.join(inverse),'complete exact forward inverse')
select=texts['select'];tree=ast.parse(select)
def value(name):return ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)))
for name,key in [('owned','owned_public_roots'),('main_source_names','main_source_names'),('main_source_pins','main_source_pins'),('prior_generated_names','prior_generated_files'),('fixed_public_names','fixed_public_names')]:ck(value(name)==roster[key],'declared '+name)
ck(value('helper_names')==tuple(roster['helper_names']) and len(value('prior_generated_names'))==34,'finite own files and original29 receipts including unavailable staging')
ck(value('scopes')==[] and 'scope.rglob' not in select,'no empirical traversal')
old=read(O/'select29.py');ck(select[select.index('reused=[]'):select.index('selection = {')]==old[old.index('reused=[]'):old.index('selection = {')],'unchanged typed metadata modes secret64MiB row reuse guards')
ck('required final public scope absent' in select and 'root.is_dir() and not root.is_symlink()' in select and 'elif path.is_dir():scope_directories.add(path)' in select,'required roots fail closed empty directories retained')
ck("'earlier_inherited_reuse_preserved_by_receipt':prior_selection['prior_inherited_reuse_preserved_by_receipt']" in select,'inherited receipt continuity')
prior=json.loads(read(O/'FRESH_GIT_RECOVERY29.json'));ck(refs[str((O/'FRESH_GIT_RECOVERY29.json').relative_to(R))]['sha256']==roster['baseline_recovery_sha256'] and prior['source']==roster['baseline_source'],'actual29 source receipt')
cap=json.loads(read(O/'CAPTURE29.json'));ck(refs[str((O/'CAPTURE29.json').relative_to(R))]['sha256']==prior['capture']['sha256'],'capture join')
sel=json.loads(read(O/'SELECTION29.json'));ck(refs[str((O/'SELECTION29.json').relative_to(R))]['sha256']==cap['selection']['sha256'],'selection join')
reviewpath=F/'pilot34-native03-increment-return-review01-2026-10-11/REVIEW01.json';accepted=json.loads(read(reviewpath));ck(refs[str(reviewpath.relative_to(R))]['sha256']==roster['accepted_return_sha256'] and accepted['source']==prior['source'] and accepted['archive']==prior['returned_archive'],'accepted actual return continuity')
ck("('native-outcome-increment29.tar','fresh-git-recovered-nativeoutcome29.tar','actual_external_archive_blob_return.stdout')" in select and "path.stat().st_size==prior_receipt['returned_archive']['bytes'] and sha(path)==prior_receipt['returned_archive']['sha256']" in select,'only three proven duplicate aliases')
ck("(HERE/'SELECTION30.json').open('x')" in select and 'selection30 already spent' in select and 'Git delta outside declared full35increment30 scope' in select,'fresh exclusive bounded selection')
for relative,expected in roster['main_source_pins'].items():read(R/relative);ck(refs[relative]['sha256']==expected,'installed body '+relative)
ck(len(roster['main_source_pins'])==10 and 'names.add(relative)' in select and 'sha(ROOT/relative)==expected' in select,'ten Main paths pinned and selected')
roots=[F/n for n in roster['owned_public_roots']];allowed=set(roster['fixed_public_names']+roster['main_source_names'])|{str((O/n).relative_to(R)) for n in roster['prior_generated_files']}|{str((H/n).relative_to(R)) for n in roster['helper_names']}
def permits(n):return n in allowed or any((R/n).is_relative_to(p) for p in roots)
ck(all(permits(n) for n in roster['main_source_names']),'Main exact allowlist')
ck(not any(permits(n) for n in ['research_runs/eth-paper-real-data-end-to-end-resource-20261011-35/failed.json','research_artifacts/archive-dispatch-ethpilot-20261011-35/result.json',str((H/'SELECTION30.json').relative_to(R)),'tradingagents/research/onchain_replication/unknown.py']),'unlisted scientific and generated products refused')
missing=[n for n in roster['owned_public_roots'] if not (F/n).is_dir() or (F/n).is_symlink()]
out={'status':'SOURCE_CHECKS_PASS_PROSPECTIVE','checks':checks,'references':refs,'missing_mandatory_roots':missing,'helpers_executed':False,'limits':['Source checks only; independent review and Root final roster freeze required.','Missing future review roots permitted at author freeze, refused by actual selector.','Directory presence does not establish accepted reviews or final release.','No selection/capture/recovery/Git/network/scientific execution; no recovery/deletion/whole-runtime claim.']}
if '--freeze' in sys.argv:
 write('AUTHOR_CHECK01.json',out)
 files={n:{'bytes':(H/n).stat().st_size,'sha256':hashlib.sha256((H/n).read_bytes()).hexdigest()} for n in roster['helper_names'] if n!='HELPERS_MANIFEST01.json'}
 write('HELPERS_MANIFEST01.json',{'status':'FROZEN_SOURCE_ONLY_INDEPENDENT_REVIEW_PENDING','files':files,'baseline_source':roster['baseline_source'],'original_helpers':{n+'29.py':oldm['files'][n+'29.py'] for n in ('select','capture','recover')},'pending_mandatory_roots':missing,'helpers_executed':False})
else:write('PREPARATION_CHECK01.json',out)
print(json.dumps({'status':out['status'],'checks':len(checks),'missing':missing,'helpers_executed':False}))
