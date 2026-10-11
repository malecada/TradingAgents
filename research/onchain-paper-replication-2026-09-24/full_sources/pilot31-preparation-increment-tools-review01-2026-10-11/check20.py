"""Source-only incremental tool review; never imports/executes reviewed helpers."""
import ast,copy,difflib,hashlib,json,os,resource,signal,stat
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(20,20));resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304));signal.alarm(30)
H=Path(__file__).resolve().parent;F=H.parent;R=F.parents[2];D=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/full31increment20';O=D.parent/'outcome19';checks=[];refs={}
def ck(v,n):
 assert v,n
 checks.append(n)
def body(p):
 b=p.read_bytes();assert len(b)<4194304;refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};return b
def sha(p):return hashlib.sha256(body(p)).hexdigest()
def js(p):return json.loads(body(p))
m=js(D/'HELPERS_MANIFEST01.json');ck(sha(D/'HELPERS_MANIFEST01.json')=='6fb4c084bfda1e101a1d3e2ee26854d923c18cd0525c1f5b1eb258318e8e0aea','exact Root helper manifest')
for name,pin in m['files'].items():ck(sha(D/name)==pin['sha256'] and (D/name).stat().st_size==pin['bytes'],'manifest '+name)
prior_review=F/'pilot30-outcome-increment-return-review01-2026-10-11/REVIEW01.json';v=js(prior_review);ck(sha(prior_review)=='8bbc8e5a19f0351eca184f94f7a3d38e38f360b895ec77529bdace99784e24c9','accepted actual19 review')
rec=js(O/'FRESH_GIT_RECOVERY19.json');ck(sha(O/'FRESH_GIT_RECOVERY19.json')=='0bedba9caa95ea54c4a5b5fedcd3792ba6fc9a3bab0358312f024b49d16d129e' and rec['source']==v['source']=='8d56ea385a20291b51cf219298a08c5cb585da94','actual19 baseline source/receipt')
cap=js(R/rec['capture']['path']);ck(sha(R/rec['capture']['path'])==rec['capture']['sha256'],'baseline capture join');sel=js(O/'SELECTION19.json');ck(sha(O/'SELECTION19.json')==cap['selection']['sha256'],'correct19 selection body join')
exclusions=[cap['archive']['path'],rec['returned_archive']['path'],str((O/'actual_external_archive_blob_return.stdout').relative_to(R))]
ck(len(set(exclusions))==3 and rec['returned_archive']==v['archive'],'three distinct accepted19 archive references; no archive replay')
patch='';literal_changes={};owned=[]
def assign(tree,name):return next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
for stem in ('select','capture','recover'):
 old=body(O/(stem+'19.py')).decode();new=body(D/(stem+'20.py')).decode();patch+=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str((O/(stem+'19.py')).relative_to(R)),tofile=str((D/(stem+'20.py')).relative_to(R))))
 a=ast.parse(old);b=ast.parse(new);compile(b,str(D/(stem+'20.py')),'exec');ck(True,stem+' syntax only')
 if stem=='select':
  owned=ast.literal_eval(assign(b,'owned').value);ck(len(owned)==len(set(owned))==11 and all('/' not in x and '31' in x for x in owned),'finite11 fresh31 public roster')
  ck(ast.literal_eval(assign(b,'scopes').value)==[],'no empirical scopes')
  b.body[b.body.index(assign(b,'owned'))]=copy.deepcopy(assign(a,'owned'));b.body[b.body.index(assign(b,'scopes'))]=copy.deepcopy(assign(a,'scopes'));a.body.remove(assign(a,'N'))
 ac=[x for x in ast.walk(a) if isinstance(x,ast.Constant)];bc=[x for x in ast.walk(b) if isinstance(x,ast.Constant)];ck(len(ac)==len(bc),stem+' same constant count')
 changes=[]
 for x,y in zip(ac,bc,strict=True):
  if x.value!=y.value:
   ck(type(x.value) is type(y.value) is str,stem+' only string literal change');changes.append({'old':x.value,'new':y.value});y.value=x.value
 ck(ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False),stem+' exact inverse outside declared identities/roster/scopes')
 literal_changes[stem]=changes
ck(patch==body(D/'LITERAL_PATCH01.diff').decode(),'entire literal patch independently regenerated exactly')
# Metadata-only preflight of explicit roster; current Git diff paths remain Root selector responsibility.
metadata=[]
for name in owned:
 root=F/name;ck(root.is_dir() and not root.is_symlink(),'owned public directory '+name)
 for p in sorted(root.rglob('*')):
  s=p.lstat();rel=str(p.relative_to(R));ck(not {'.git','.venv','node_modules','keys','apis'}&set(p.parts) and p.name not in ('.env','connection.json','hf_token.txt','id_ed25519_storagebox_u676273'),'public metadata '+rel)
  if stat.S_ISREG(s.st_mode):ck(s.st_nlink==1 and s.st_size<=64*1024**2,'single link bounded body metadata '+rel)
  else:ck(stat.S_ISDIR(s.st_mode) or stat.S_ISLNK(s.st_mode),'supported type '+rel)
  metadata.append({'path':rel,'mode':format(stat.S_IMODE(s.st_mode),'04o'),'bytes':s.st_size,'nlink':s.st_nlink})
for name in ('SELECTION20.json','CAPTURE20.json','FRESH_GIT_RECOVERY20.json','GIT_OPERATIONS20.json','pilot-preparation-increment20.tar','fresh-git-recovered-preparation20.tar'):ck(not os.path.lexists(D/name),'fresh output '+name)
ck(not os.path.lexists(R.parent/'onchain-pilot-recovery/real-pilot-full31-preparation-20261011-20.git'),'fresh20 bare path absent')
out={'decision':'ACCEPT_SOURCE_ONLY_INCREMENT20_TOOLS','helper_manifest':{'path':str((D/'HELPERS_MANIFEST01.json').relative_to(R)),**refs[str((D/'HELPERS_MANIFEST01.json').relative_to(R))]},'baseline_source':rec['source'],'owned_roots':owned,'explicit_scopes':[],'prior_archive_exclusions':exclusions,'literal_changes':literal_changes,'checks':checks,'references':refs,'metadata_entries':len(metadata),'limitations':['No selection/capture/recovery/helper execution or Git/network operation.','Metadata roster preflight only; actual Git-diff-derived paths and current files are checked by original selector at Root execution.','Prior19 actual return reused by exact review/receipt; no historical matrix/archive replay.','No actual external increment20 recovery, broadstore/runtime/POSIX/deletion or empirical admission claim.']}
(H/'TOOLS_REVIEW01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');(H/'ROSTER_METADATA01.json').write_text(json.dumps(metadata,indent=2,sort_keys=True)+'\n');print(json.dumps({'decision':out['decision'],'checks':len(checks),'metadata_entries':len(metadata),'review_sha256':hashlib.sha256((H/'TOOLS_REVIEW01.json').read_bytes()).hexdigest()}))
