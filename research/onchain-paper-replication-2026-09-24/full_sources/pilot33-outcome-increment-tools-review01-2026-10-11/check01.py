"""Changed-seam source and current public metadata review; no helper execution."""
import ast,copy,difflib,hashlib,json,os,resource,signal,stat,subprocess
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(268435456,268435456));resource.setrlimit(resource.RLIMIT_CPU,(20,20));resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304));signal.alarm(40)
H=Path(__file__).resolve().parent;F=H.parent;R=F.parents[2];D=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/outcome25';O=D.parent/'outcome23';B=D.parent/'full33increment24';checks=[];refs={}
def ck(x,n):
 assert x,n
 checks.append(n)
def read(p):
 b=p.read_bytes();assert len(b)<4194304;refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};return b
def sha(p):return hashlib.sha256(read(p)).hexdigest()
def js(p):return json.loads(read(p))
m=js(D/'HELPERS_MANIFEST01.json');ck(sha(D/'HELPERS_MANIFEST01.json')=='4a0cff7fdfaf45c418e451540e44ea9283f6034f4a080a76ea67c2ac0d5f255b','exact frozen different-author helpers')
for name,p in m['files'].items():ck(sha(D/name)==p['sha256'] and (D/name).stat().st_size==p['bytes'],'candidate body '+name)
for name,p in m['original_helpers'].items():ck(sha(R/name)==p['sha256'],'accepted23 predecessor '+name)
rec=js(B/'FRESH_GIT_RECOVERY24.json');ck(sha(B/'FRESH_GIT_RECOVERY24.json')==m['baseline_recovery']['sha256'] and rec['source']==m['baseline_source']=='ac4b921dcb70ff2069a58cb5d2994b20595b6d51','actual24 baseline')
prior=F/'pilot33-preparation-increment-return-review01-2026-10-11/REVIEW01.json';ck(sha(prior)=='67e906456b98f9eeebc810640962b27de3fad9d78bd5d499ed52aa60c98f6bdc','accepted actual24 return reused');priorv=js(prior)
cap=js(R/rec['capture']['path']);ck(sha(R/rec['capture']['path'])==rec['capture']['sha256'] and sha(B/'SELECTION24.json')==cap['selection']['sha256'],'baseline capture/selection24 joins')
aliases=[cap['archive']['path'],rec['returned_archive']['path'],str((B/'actual_external_archive_blob_return.stdout').relative_to(R))]
for name in aliases:
 p=R/name;h=hashlib.sha256();size=0
 with p.open('rb') as stream:
  while chunk:=stream.read(65536):h.update(chunk);size+=len(chunk);assert size<=64*1024**2
 ck(size==rec['returned_archive']['bytes'] and h.hexdigest()==rec['returned_archive']['sha256'],'exact prior duplicate hash '+name)
forward='';inverse='';changes={};owned=[]
def assignment(t,name):return next(x for x in t.body if isinstance(x,ast.Assign) and any(isinstance(n,ast.Name) and n.id==name for n in x.targets))
for stem in ('select','capture','recover'):
 p=O/(stem+'23.py');q=D/(stem+'25.py');old=read(p).decode();new=read(q).decode();forward+=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(p.relative_to(R)),tofile=str(q.relative_to(R))));inverse+=''.join(difflib.unified_diff(new.splitlines(True),old.splitlines(True),fromfile=str(q.relative_to(R)),tofile=str(p.relative_to(R))));a=ast.parse(old);b=ast.parse(new)
 if stem=='select':
  owned=ast.literal_eval(assignment(b,'owned').value);ck(len(owned)==5 and len(set(owned))==5,'finite five public roots')
  scopes=eval(compile(ast.Expression(assignment(b,'scopes').value),'<exact public scopes>','eval'),{'ROOT':R,'N':ast.literal_eval(assignment(b,'N').value)});ck([str(p.relative_to(R)) for p in scopes]==m['explicit_scopes'] and len(scopes)==5,'five exact failed33 scopes')
  b.body[b.body.index(assignment(b,'owned'))]=copy.deepcopy(assignment(a,'owned'))
  # The only tuple-structure change adds three explicit owned proof files.
  af=next(x for x in a.body if isinstance(x,ast.For) and isinstance(x.iter,ast.Tuple));bf=next(x for x in b.body if isinstance(x,ast.For) and isinstance(x.iter,ast.Tuple));vals=ast.literal_eval(bf.iter);ck(vals[-3:]==('LITERAL_INVERSE01.diff','AUTHOR_CHECK01.json','REPORT.md'),'exact three extra helper proof entries');bf.iter.elts=bf.iter.elts[:-3]
 ac=[n for n in ast.walk(a) if isinstance(n,ast.Constant)];bc=[n for n in ast.walk(b) if isinstance(n,ast.Constant)];ck(len(ac)==len(bc),'same shape '+stem);delta=[]
 for x,y in zip(ac,bc,strict=True):
  if x.value!=y.value:ck(type(x.value) is type(y.value) is str,'string-only identity delta '+stem);delta.append([x.value,y.value]);y.value=x.value
 ck(ast.dump(a)==ast.dump(b),'exact AST inverse '+stem);changes[stem]=delta
ck(forward==read(D/'LITERAL_PATCH01.diff').decode() and inverse==read(D/'LITERAL_INVERSE01.diff').decode(),'entire independent forward/inverse patch regeneration')
tp=F/'pilot33-terminal-outcome-review01-2026-10-11/REVIEW01.json';ck(sha(tp)=='5047103b1a6cad4f95767dc504fd5d751f70b791169527d6480608f2d40e5279','exact accepted failed33 terminal');terminal=js(tp)
ck(all(any(name.startswith(str(p.relative_to(R))+'/') for name in terminal['inventory']) for p in scopes),'scope roster joins all five actual terminal trees')
# Read only Git names, not helper invocation; retain current names for final selection freeze.
ops=[];names=set()
for args in (['git','diff','--name-only',rec['source'],'HEAD'],['git','diff','--name-only','HEAD']):
 proc=subprocess.run(args,cwd=R,capture_output=True,timeout=10);ck(proc.returncode==0 and proc.stderr==b'','readonly current Git name diff');names.update(proc.stdout.decode().splitlines());ops.append({'argv':args,'exit_code':0,'stdout_sha256':hashlib.sha256(proc.stdout).hexdigest()})
missing=[]
for name in owned:
 p=F/name
 if not p.exists():missing.append(name);continue
 names.update(str(x.relative_to(R)) for x in p.rglob('*') if x.is_file())
for p in scopes:names.update(str(x.relative_to(R)) for x in p.rglob('*') if x.is_file() or x.is_symlink())
names.update(str((D/name).relative_to(R)) for name in list(m['files'])+['HELPERS_MANIFEST01.json'])
for name in sorted(names-set(aliases)):
 p=R/name;ck(not {'.git','.venv','node_modules','keys','apis','real_pilot_runtime'}&set(p.parts) and p.name not in ('.env','hf_token.txt','connection.json','id_ed25519_storagebox_u676273'),'public selected-candidate metadata '+name);s=p.lstat();ck((stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=64*1024**2) or stat.S_ISLNK(s.st_mode),'supported bounded member metadata '+name)
e=F/'real-data-pilot-full33-entry-preparation01-2026-10-11'
for name in ('ROOT_TERMINAL_OPERATION01.json','ROOT_IO_CLOSED01.json','FINAL_STORAGE01.json','SOURCE_FREEZE01.json','STATE_PRIOR_TERMINAL01.md'):ck(str((e/name).relative_to(R)) in names,'late E33 evidence in selection scope '+name)
ck(any(n.endswith('/STATE.md') for n in names) and any('coordination' in n.lower() for n in names),'current STATE and coordination included by diff')
for name in ('SELECTION25.json','CAPTURE25.json','FRESH_GIT_RECOVERY25.json','failed-outcome-increment25.tar','fresh-git-recovered-outcome25.tar'):ck(not os.path.lexists(D/name),'fresh25 output '+name)
ck(not os.path.lexists(R.parent/'onchain-pilot-recovery/real-pilot-full33-outcome-20261011-25.git'),'fresh25 bare absent')
out={'decision':'ACCEPT_SOURCE_ONLY_OUTCOME25_TOOLS_CONDITIONAL_FINAL_ROSTER_FREEZE','helper_manifest':{'path':str((D/'HELPERS_MANIFEST01.json').relative_to(R)),**refs[str((D/'HELPERS_MANIFEST01.json').relative_to(R))]},'baseline_source':rec['source'],'owned_roots':owned,'explicit_scopes':m['explicit_scopes'],'prior_archive_exclusions':aliases,'missing_owned_roots_at_review':missing,'checks':checks,'references':refs,'literal_changes':changes,'readonly_git_names_operations':ops,'conditions':['Root must finish and freeze optional cadence source review directory before selection, or obtain explicit revised reviewed roster; inherited rglob silently skips absent directories.','Root must freeze late E33/STATE/coordination and review files, run selector once, then capture; actual commit/push must precede recovery.','Any failed/partial operation retained; no blind replay. Actual returned bytes require independent review.'],'limitations':['No helper/network/private/scientific/numerical/claim execution.','Finite public metadata review only; no complete historical/runtime/POSIX/deletion or preservation claim.']}
(H/'CANDIDATE_NAMES01.json').write_text(json.dumps(sorted(names-set(aliases)),indent=2)+'\n');(H/'TOOLS_REVIEW01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'decision':out['decision'],'checks':len(checks),'missing_roots':missing,'sha256':hashlib.sha256((H/'TOOLS_REVIEW01.json').read_bytes()).hexdigest()}))
