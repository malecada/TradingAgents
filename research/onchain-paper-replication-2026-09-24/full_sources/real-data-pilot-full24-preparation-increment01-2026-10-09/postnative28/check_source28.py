"""Prospective stdlib source checks; --freeze only after mandatory roots exist."""
import ast,difflib,hashlib,json,os,resource,signal,sys
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(15)
H=Path(__file__).resolve().parent;O=H.parent/'outcome27';F=H.parent.parent;R=F.parents[2];checks=[];refs={}
def read(p):
 b=p.read_bytes();assert len(b)<2*1024**2;refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};return b.decode()
def ck(v,n):checks.append({'name':n,'pass':bool(v)});assert v,n
def write(name,value):
 with (H/name).open('x') as stream:json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n')
roster=json.loads(read(H/'PROSPECTIVE_ROSTER01.json'));oldmanifest=json.loads(read(O/'HELPERS_MANIFEST01.json'));frozen={}
for name in ('select','capture','recover'):
 old=read(O/(name+'27.py'));ck(refs[str((O/(name+'27.py')).relative_to(R))]==oldmanifest['files'][name+'27.py'],'accepted27 source '+name)
 new=read(H/(name+'28.py'));ast.parse(new);frozen[name]=new
 if name!='select':
  literals=roster['capture_literal_map' if name=='capture' else 'recovery_literal_map'];restored=new
  for before,after in literals.items():restored=restored.replace(after,before)
  ck(restored==old,'exact literal inverse '+name);ck(ast.dump(ast.parse(restored))==ast.dump(ast.parse(old)),'exact AST inverse '+name);ck('sha276' not in new and new.count('hashlib.sha256')==old.count('hashlib.sha256'),'sha256 primitive retained '+name)
selector=frozen['select'];tree=ast.parse(selector)
def literal(name):return ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)))
ck(literal('owned')==roster['owned_public_roots'] and len(set(literal('owned')))==14,'exact14 finite public roots')
ck(literal('scopes')==[] and 'scope.rglob' not in selector,'no original six scientific/runtime scope traversal')
ck(literal('helper_names')==tuple(roster['helper_names']) and literal('prior_generated_names')==roster['prior_generated_files'],'finite own and generated27 filename rosters')
ck('for path in root.rglob' in selector and "assert root.is_dir() and not root.is_symlink()" in selector and 'elif path.is_dir():scope_directories.add(path)' in selector,'mandatory non-symlink roots and empty directories retained')
ck("sha(ROOT/prior_receipt['capture']['path'])==prior_receipt['capture']['sha256']" in selector and "prior_selection['exact_unchanged_prior_rows_reused']" in selector,'prior27 capture/selection and inherited67 receipt continuity')
prior=json.loads(read(O/'FRESH_GIT_RECOVERY27.json'));ck(refs[str((O/'FRESH_GIT_RECOVERY27.json').relative_to(R))]['sha256']==roster['baseline_recovery_sha256'] and prior['source']==roster['baseline_source']=='401089cc3e973c134054fb6ef2e762cb4b152e07','actual27 baseline anchored')
cap=json.loads(read(R/prior['capture']['path']));ck(refs[prior['capture']['path']]['sha256']==prior['capture']['sha256'],'actual27 capture body join');selection=json.loads(read(O/'SELECTION27.json'));ck(refs[str((O/'SELECTION27.json').relative_to(R))]['sha256']==cap['selection']['sha256'] and len(selection['exact_unchanged_prior_rows_reused'])==67,'actual27 selection and67 inherited rows')
review=read(F/'pilot34-outcome-increment-return-review01-2026-10-11/REVIEW01.json');ck(hashlib.sha256(review.encode()).hexdigest()=='15f94fd288e1bf89feb911e578829303e9b223be70524047a70053b894381af8','accepted27 external return anchor reused')
ck("assert excluded=={str((prior.parent/name).relative_to(ROOT))" in selector and "path.stat().st_size==prior_receipt['returned_archive']['bytes']" in selector,'exact three archive aliases require length/hash before exclusion')
ck("assert set(main_source_names)<=names" in selector and "Git delta outside declared postnative28 scope" in selector and "accepted serializer receipt changed" in selector,'Git delta constrained and five accepted current Main changes required')
ck("native03 identity already attempted" in selector and "(HERE/'SELECTION28.json').open('x')" in selector and 'generated postnative28 products are outside selection' in selector,'fresh prospective03 and one-use selection/product refusal')
ck(all(t in selector for t in ['before.st_nlink == 1','before.st_size <= 64*1024**2','path.parent.resolve(strict=True) == path.parent',"'.git', '.venv', 'node_modules', 'keys', 'apis'","'connection.json'",'os.readlink(path)','st_mtime_ns','st_ctime_ns']),'unchanged typed/body64MiB/secret/metadata guards')
# Pure declared-name controls only; no selector import, subprocess, filesystem census or capture.
roots=[F/n for n in roster['owned_public_roots']];allowed=set(roster['fixed_public_names']+roster['main_source_names'])|{str((O/n).relative_to(R)) for n in roster['prior_generated_files']}|{str((H/n).relative_to(R)) for n in roster['helper_names']}
def permitted(name):return name in allowed or any((R/name).is_relative_to(root) for root in roots)
ck(all(permitted(n) for n in roster['main_source_names']+roster['fixed_public_names']),'five Main and two coordination names supported')
ck(not any(permitted(n) for n in ['research_runs/eth-paper-real-data-end-to-end-resource-20261011-34/failed.json','research_artifacts/archive-dispatch-ethpilot-20261011-34/result.json','research/unrelated.txt',str((H/'SELECTION28.json').relative_to(R))]),'out-of-scope raw/private-style/unrelated/generated names refused')
patch=[];inverse=[]
for name,new in frozen.items():
 old=(O/(name+'27.py')).read_text();patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=name+'27.py',tofile=name+'28.py'));inverse.extend(difflib.unified_diff(new.splitlines(True),old.splitlines(True),fromfile=name+'28.py',tofile=name+'27.py'))
# These new helper diffs remain prospective until final freeze.
if '--freeze' not in sys.argv:
 (H/'LITERAL_PATCH01.diff').write_text(''.join(patch));(H/'LITERAL_INVERSE01.diff').write_text(''.join(inverse))
else:
 ck(read(H/'LITERAL_PATCH01.diff')==''.join(patch) and read(H/'LITERAL_INVERSE01.diff')==''.join(inverse),'full frozen three-helper literal deltas')
missing=[n for n in roster['owned_public_roots'] if not (F/n).is_dir() or (F/n).is_symlink()]
out={'status':'SOURCE_CHECKS_PASS_MANDATORY_ROOTS_PENDING' if missing else 'SOURCE_CHECKS_PASS_REQUIRED_ROOTS_PRESENT','checks':checks,'references':refs,'missing_mandatory_roots':missing,'helpers_executed':False,'selection_capture_recovery_git_network_executed':False,'opaque_archive_or_scientific_bodies_read':False,'limitations':['Exact finite public roots only; absent final sources/reviews still block actual selection.','Source checks reuse prior accepted27 capture/recovery mechanics and actual receipts; no archive/recovery replay.','Root must freeze all writers before one selection/capture and commit/push before fresh recovery.','Independent source/entry and actual-return review remain required.']}
if '--freeze' in sys.argv:
 ck(not missing,'all mandatory public roots exist before source freeze')
 write('AUTHOR_CHECK01.json',out)
 files={n:{'bytes':(H/n).stat().st_size,'sha256':hashlib.sha256((H/n).read_bytes()).hexdigest()} for n in roster['helper_names'] if n!='HELPERS_MANIFEST01.json'}
 write('HELPERS_MANIFEST01.json',{'status':'FROZEN_SOURCE_ONLY_INDEPENDENT_REVIEW_PENDING','baseline_source':roster['baseline_source'],'files':files,'original_helpers':{str((O/(n+'27.py')).relative_to(R)):oldmanifest['files'][n+'27.py'] for n in ('select','capture','recover')},'helpers_executed':False})
else:write('PREPARATION_CHECK01.json',out)
print(json.dumps({'status':out['status'],'checks':len(checks),'missing_mandatory_roots':missing,'helpers_executed':False},sort_keys=True))
