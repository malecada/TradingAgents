import ast,copy,difflib,hashlib,json,os,stat,datetime
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';D=H/'full32increment22';O=H/'full31increment20';P=Path(__file__).resolve().parent
refs={};checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 b=p.read_bytes();assert len(b)<2097152;refs[str(p.relative_to(R))]={'sha256':sha(b),'bytes':len(b)};return b
def js(p):return json.loads(read(p))
def ck(v,n):assert v,n;checks.append(n)
m=js(D/'HELPERS_MANIFEST01.json');ck(sha((D/'HELPERS_MANIFEST01.json').read_bytes())=='ceeb440b54faf013b65033ab683a21db0d3f652de40a0022410096722d29fbe5','frozen manifest')
for name,pin in m['files'].items():ck(sha(read(D/name))==pin['sha256'],'new pin '+name)
prior=js(F/'pilot31-preparation-increment-tools-review01-2026-10-11/TOOLS_REVIEW01.json');ck(prior['decision']=='ACCEPT_SOURCE_ONLY_INCREMENT20_TOOLS','prior accepted source review')
patch=[];literal=[]
for kind in ['select','capture','recover']:
 old=O/(kind+'20.py');new=D/(kind+'22.py');a=read(old).decode();b=read(new).decode()
 ck(sha(a.encode())==m['original_helpers'][str(old.relative_to(R))]['sha256']==prior['references'][str(old.relative_to(R))]['sha256'],'accepted original pin '+kind)
 patch.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=str(old.relative_to(R)),tofile=str(new.relative_to(R))))
 ta=ast.parse(a);tb=ast.parse(b)
 if kind=='select':
  owned=next(n for n in tb.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='owned' for t in n.targets));roster=ast.literal_eval(owned.value)
  ck(len(roster)==10 and len(set(roster))==10,'fixed ten owned public directories')
  for tree in [ta,tb]:
   for n in tree.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='owned' for t in n.targets):n.value=ast.Constant('OWNED')
    if isinstance(n,ast.For) and isinstance(n.iter,ast.Tuple):
     values=ast.literal_eval(n.iter)
     if values[0].startswith('capture'):n.iter=ast.Constant('HELPER_ROSTER')
  ck('scopes=[]' in b and 'scopes=[]' in a,'zero empirical scope unchanged')
 ca=[n for n in ast.walk(ta) if isinstance(n,ast.Constant)];cb=[n for n in ast.walk(tb) if isinstance(n,ast.Constant)];ck(len(ca)==len(cb),'literal count '+kind)
 for x,y in zip(ca,cb):
  if x.value!=y.value:literal.append({'helper':kind,'old':x.value,'new':y.value});y.value=x.value
 ck(ast.dump(ta,include_attributes=False)==ast.dump(tb,include_attributes=False),'exact AST inverse '+kind)
ck(''.join(patch).encode()==read(D/'LITERAL_PATCH01.diff'),'exact literal diff all three helpers')
rvpath=F/'pilot31-outcome-increment-return-review01-2026-10-11/REVIEW01.json';rv=js(rvpath);ck(rv['decision']=='ACCEPT_ACTUAL_OUTCOME21_DECLARED_FAILED31_RETURN','actual21 acceptance reused')
rp=H/'outcome21/FRESH_GIT_RECOVERY21.json';r=js(rp);cp=R/r['capture']['path'];c=js(cp);sp=H/'outcome21/SELECTION21.json';s=js(sp)
for path,pin in [(rp,rv['references'][str(rp.relative_to(R))]),(cp,r['capture']),(sp,c['selection'])]:ck(refs[str(path.relative_to(R))]['sha256']==pin['sha256'],'actual21 authenticated metadata '+path.name)
ck(rv['source']==r['source'],'actual21 source baseline join')
excluded=[c['archive']['path'],r['returned_archive']['path'],str((rp.parent/'actual_external_archive_blob_return.stdout').relative_to(R))]
ck(len(set(excluded))==3 and c['archive']['sha256']==r['returned_archive']['sha256'],'three exact duplicate exclusions metadata')
entries=[];missing=[]
for name in roster:
 root=F/name
 if not root.exists():missing.append(name);continue
 for p in root.rglob('*'):
  st=p.lstat()
  ck(not p.is_symlink() and p.name not in {'.env','connection.json','hf_token.txt'} and not {'keys','apis','.git','.venv','node_modules'}&set(p.parts),'public metadata '+str(p.relative_to(root)))
  if stat.S_ISREG(st.st_mode):ck(st.st_nlink==1 and st.st_size<=64*1024**2,'bounded regular metadata');entries.append(str(p.relative_to(R)))
for name in ['SELECTION22.json','CAPTURE22.json','FRESH_GIT_RECOVERY22.json','GIT_OPERATIONS22.json','pilot-preparation-increment22.tar','fresh-git-recovered-preparation22.tar']:ck(not os.path.lexists(D/name),'fresh22 output '+name)
ck(not os.path.lexists(R.parent/'onchain-pilot-recovery/real-pilot-full32-preparation-20261011-22.git'),'fresh22 bare path')
out={'decision':'ACCEPT_SOURCE_ONLY_INCREMENT22_TOOLS','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'helper_manifest':{'path':str((D/'HELPERS_MANIFEST01.json').relative_to(R)),'sha256':sha((D/'HELPERS_MANIFEST01.json').read_bytes())},'checks':checks,'literal_changes':literal,'references':refs,'owned_roots':roster,'metadata_entries':len(entries),'missing_owned_roots_at_review':missing,'explicit_scopes':[],'prior_archive_exclusions':excluded,'baseline_source':r['source'],'limitations':['Helpers were not executed; no Git/network/private or empirical input reads.','Prior actual21 archive recovery is reused by accepted metadata; archive bodies were not reread.','Source-only release; Root must finalize entries before selection. Original selector checks actual Git delta and fresh body metadata at execution.','No actual22 capture/recovery/admission or empirical launch authority.']}
(P/'TOOLS_REVIEW01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({'decision':out['decision'],'checks':len(checks),'missing':missing,'metadata_entries':len(entries)}))
