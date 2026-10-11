import ast,copy,difflib,hashlib,json,os,stat,datetime
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';D=H/'full33increment24';O=H/'full32increment22';P=Path(__file__).resolve().parent
refs={};checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 b=p.read_bytes();assert len(b)<2097152;refs[str(p.relative_to(R))]={'sha256':sha(b),'bytes':len(b)};return b
def js(p):return json.loads(read(p))
def ck(v,n):assert v,n;checks.append(n)
m=js(D/'HELPERS_MANIFEST01.json');ck(sha((D/'HELPERS_MANIFEST01.json').read_bytes())=='26f3c810c6d2be37468ca861d1ec5866faf0aa03104bf91106d2eb6cb7650f40','frozen manifest')
for name,pin in m['files'].items():ck(sha(read(D/name))==pin['sha256'],'new pin '+name)
prior=js(F/'pilot32-preparation-increment-tools-review01-2026-10-11/TOOLS_REVIEW01.json');ck(prior['decision']=='ACCEPT_SOURCE_ONLY_INCREMENT22_TOOLS','prior accepted source review')
patch=[];literal=[]
for kind in ['select','capture','recover']:
 old=O/(kind+'22.py');new=D/(kind+'24.py');a=read(old).decode();b=read(new).decode()
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
rvpath=F/'pilot32-outcome-increment-return-review01-2026-10-11/REVIEW01.json';rv=js(rvpath);ck(rv['decision']=='ACCEPT_ACTUAL_OUTCOME23_DECLARED_FAILED32_RETURN','actual21 acceptance reused')
rp=H/'outcome23/FRESH_GIT_RECOVERY23.json';r=js(rp);cp=R/r['capture']['path'];c=js(cp);sp=H/'outcome23/SELECTION23.json';s=js(sp)
for path,pin in [(rp,rv['references'][str(rp.relative_to(R))]),(cp,r['capture']),(sp,c['selection'])]:ck(refs[str(path.relative_to(R))]['sha256']==pin['sha256'],'actual21 authenticated metadata '+path.name)
ck(rv['source']==r['source'],'actual21 source baseline join')
excluded=[c['archive']['path'],r['returned_archive']['path'],str((rp.parent/'actual_external_archive_blob_return.stdout').relative_to(R))]
ck(len(set(excluded))==3 and c['archive']['sha256']==r['returned_archive']['sha256'],'three exact duplicate exclusions metadata')
# Exact duplicate-body equality only, no archive extraction or member replay.
for name in excluded:
 p=R/name;before=p.lstat();h=hashlib.sha256();n=0
 with p.open('rb') as f:
  while b:=f.read(65536):n+=len(b);h.update(b);assert n<=4*1024**2
 after=p.lstat();ck(before==after and n==r['returned_archive']['bytes'] and h.hexdigest()==r['returned_archive']['sha256'],'actual duplicate alias hash '+name)
entries=[];missing=[]
for name in roster:
 root=F/name
 if not root.exists():missing.append(name);continue
 for p in root.rglob('*'):
  st=p.lstat()
  ck(not p.is_symlink() and p.name not in {'.env','connection.json','hf_token.txt'} and not {'keys','apis','.git','.venv','node_modules'}&set(p.parts),'public metadata '+str(p.relative_to(root)))
  if stat.S_ISREG(st.st_mode):ck(st.st_nlink==1 and st.st_size<=64*1024**2,'bounded regular metadata');entries.append(str(p.relative_to(R)))
for name in ['SELECTION24.json','CAPTURE24.json','FRESH_GIT_RECOVERY24.json','GIT_OPERATIONS24.json','pilot-preparation-increment24.tar','fresh-git-recovered-preparation24.tar']:ck(not os.path.lexists(D/name),'fresh22 output '+name)
ck(not os.path.lexists(R.parent/'onchain-pilot-recovery/real-pilot-full33-preparation-20261011-24.git'),'fresh22 bare path')
out={'decision':'ACCEPT_SOURCE_ONLY_INCREMENT24_TOOLS','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'helper_manifest':{'path':str((D/'HELPERS_MANIFEST01.json').relative_to(R)),'sha256':sha((D/'HELPERS_MANIFEST01.json').read_bytes())},'checks':checks,'literal_changes':literal,'references':refs,'owned_roots':roster,'metadata_entries':len(entries),'missing_owned_roots_at_review':missing,'explicit_scopes':[],'prior_archive_exclusions':excluded,'baseline_source':r['source'],'limitations':['Helpers were not executed; no Git/network/private or empirical input reads.','Prior actual23 acceptance reused; three exact duplicate aliases streamed and hashed only, no member replay.','Source-only release; Root must finalize entries before selection. Original selector checks actual Git delta and fresh body metadata at execution.','No actual24 capture/recovery/admission or empirical launch authority. Inherited missing-directory skipping requires Root full roster confirmation after final release before select.']}
(P/'TOOLS_REVIEW01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({'decision':out['decision'],'checks':len(checks),'missing':missing,'metadata_entries':len(entries)}))
