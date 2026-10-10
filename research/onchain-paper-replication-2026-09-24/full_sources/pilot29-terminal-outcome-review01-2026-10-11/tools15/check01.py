import resource
resource.setrlimit(resource.RLIMIT_AS,(384*1024**2,384*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
from pathlib import Path
import ast,json,hashlib,os,stat,datetime
P=Path(__file__).resolve().parent;F=P.parent.parent;R=F.parents[2];D=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/outcome15';checks=[];refs={};total=0

def ck(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def read(p):
 global total
 p=Path(p);p=p if p.is_absolute() else R/p;b=p.read_bytes();total+=len(b);ck(len(b)<=4*1024**2 and total<=24*1024**2,'bounded metadata '+p.name);refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};return b
def sha(b):return hashlib.sha256(b).hexdigest()
def js(p):return json.loads(read(p))
mb=read(D/'HELPERS_MANIFEST01.json');ck(sha(mb)=='d25ceae72c82c6b62e6a785542b8000f5cf90da50b234cb5f3de5d42e7e6d702','external frozen helper manifest');m=json.loads(mb);ib=read(D/'LITERAL_INVERSE01.json');ck(sha(ib)=='eb36efb6010ab25b35feb70affd0e90ffacc6af52b03cb20593f109dd4d0588a','external inverse anchor');inverse=json.loads(ib)
scripts={}
for name in ('select15.py','capture15.py','recover15.py'):
 b=read(D/name);ck(sha(b)==m['files'][name]['sha256'] and len(b)==m['files'][name]['bytes'],'frozen helper '+name);scripts[name]=b.decode();ast.parse(b)
 restored=b.decode()
 for i,c in reversed(list(enumerate(inverse['changes'][name]))):
  ck(c['after'] in restored,'inverse present '+name+'/'+str(i));restored=restored.replace(c['after'],c['before'])
 old=D.parent/'outcome13'/name.replace('15','13');oldb=read(old);ck(restored.encode()==oldb,'exact complete predecessor inverse '+name)
 ck(sha(oldb)==m['references'][str(old.relative_to(R))]['sha256'],'accepted baseline source '+name)
review13=js(F/'pilot-full28-outcome-increment-tools-review01-2026-10-09/TOOLS_REVIEW01.json');ck(review13['decision']=='accepted' and refs[str((F/'pilot-full28-outcome-increment-tools-review01-2026-10-09/TOOLS_REVIEW01.json').relative_to(R))]['sha256']=='995491a3d3e13dd427bb8006dc92adc531b33902639ba89f0d70daf90b18dbb9','accepted original13 source-review anchor')
ret14path=F/'pilot-full29-preparation-increment-tools-review01-2026-10-09/returned14/RECOVERY_REVIEW01.json';ck(sha(read(ret14path))=='ebe9b2adda620cf707c9cec5414721431a4991916da78cbcaf4361c364bcb771','actual14 independent recovery acceptance anchor')
priorpath=D.parent/'full29increment14/FRESH_GIT_RECOVERY14.json';pb=read(priorpath);ck(sha(pb)=='4b78e2df7d12a414920f18e121712d7d6a0b26150204c69fb94b19de68fbff25','actual14 recovery body');prior=json.loads(pb)
ck(prior['source']==prior['actual_remote_head']==prior['actual_fetch_head']==m['baseline_source']=='f58540f5e55ca701bab4b20969a5b77ad43e5260' and prior['no_alternates'] is True,'actual14 fresh source identity')
cb=read(prior['capture']['path']);ck(sha(cb)==prior['capture']['sha256'],'prior capture recovery join');cap=json.loads(cb);sb=read(D.parent/'full29increment14/SELECTION14.json');ck(sha(sb)==cap['selection']['sha256'],'prior selection capture join');selection=json.loads(sb)
ck(len({r['path'] for r in selection['rows']})==len(selection['rows']),'unique previous regular reuse namespace')
exclusions=[cap['archive']['path'],prior['returned_archive']['path'],str((priorpath.parent/'actual_external_archive_blob_return.stdout').relative_to(R))]
for relative in exclusions:
 p=R/relative;h=hashlib.sha256();count=0
 with p.open('rb') as stream:
  while chunk:=stream.read(65536):
   count+=len(chunk);total+=len(chunk);ck(total<=24*1024**2,'bounded prior duplicate bytes');h.update(chunk)
 ck(count==prior['returned_archive']['bytes'] and h.hexdigest()==prior['returned_archive']['sha256']==cap['archive']['sha256'],'actual unchanged excluded duplicate '+p.name);refs[relative]={'bytes':count,'sha256':h.hexdigest()}
# Only extract immutable AST literals, never execute selection/capture/recovery.
tree=ast.parse(scripts['select15.py']);owned=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='owned' for t in n.targets))
ck(owned==m['owned_directories'] and len(owned)==len(set(owned))==34,'exact explicit34 public roster')
ck(all((F/x).is_dir() and not (F/x).is_symlink() for x in owned),'all public roster directories present')
for name in ('matching-compiled-normalization-connected01-2026-10-10','matching-compiled-normalization-connected03-2026-10-10','matching-compiled-normalization-connected-review01-2026-10-10','matching-compiled-normalization-connected-review03-2026-10-10','pilot29-first-group-review01-2026-10-10','pilot29-third-group-recovery-review01-2026-10-10',P.parent.name):ck(name in owned,'failed/withheld/reviewer evidence roster '+name)
ID='eth-paper-real-data-end-to-end-resource-20261009-29';workflow=m['public_workflow_identity'];owner=m['public_offload_namespace']
scopes=[R/'research_runs'/ID,R/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/ID,R/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent'/ID,R/'research_artifacts/onchain_representations'/workflow/ID,R/'research_artifacts/onchain_compact_mcm'/workflow/ID,R/'research_artifacts/onchain_batched_offload'/owner,R/'research_artifacts/archive-dispatch-ethpilot-20261009-29']
ck(all(p.is_dir() and not p.is_symlink() for p in scopes),'actual seven scopes exist')
ck(all(str(p.relative_to(R)).split('/'+ID)[0] in scripts['select15.py'] for p in scopes),'source contains all seven actual public scopes')
for old in ('4d8349713a3f764fe931f0dda2330c5b7de5560f291241fdd8043a75ca4f4401','223798d84810b5f0f49aa89b17b35db96c6ddbcc7c86948472e81ec49573e5d6','eth-paper-real-data-end-to-end-resource-20261009-28'):ck(old not in scripts['select15.py'],'no stale28 identity '+old[:12])
metadata=[];bad=[]
for root in [F/x for x in owned]+scopes:
 for p in root.rglob('*'):
  st=p.lstat()
  if stat.S_ISDIR(st.st_mode):continue
  ck(len(metadata)<20000,'finite metadata roster entries')
  rel=str(p.relative_to(R));metadata.append({'path':rel,'bytes':st.st_size,'type':'symlink' if stat.S_ISLNK(st.st_mode) else 'regular' if stat.S_ISREG(st.st_mode) else 'other'})
  if p.name in ('.env','hf_token.txt','connection.json','id_ed25519_storagebox_u676273') or {'.git','.venv','node_modules','keys','apis'}&set(p.parts):bad.append(rel)
  if stat.S_ISREG(st.st_mode):ck(st.st_nlink==1 and st.st_size<=64*1024**2,'finite singly linked actual member '+p.name)
  else:ck(stat.S_ISLNK(st.st_mode),'only preserved original types '+p.name)
ck(not bad,'no forbidden credential/runtime paths in actual explicit public scopes')
for batch in range(48,52):
 for suffix in ('.pending.json','.records.bin','.complete.json'):
  path=scopes[3]/'compact/mcm-0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba/matching'/f'{batch:08d}{suffix}';ck(path.is_file(),'local terminal tail included '+path.name)
for name in ('select15.py','capture15.py','recover15.py','HELPERS_MANIFEST01.json','LITERAL_INVERSE01.json'):ck(repr(name) in scripts['select15.py'],'helper own artifact included '+name)
ck(P.is_relative_to(F/P.parent.name),'new nested tools review within selected terminal review')
for name in ('SELECTION15.json','CAPTURE15.json','failed-outcome-increment15.tar','FRESH_GIT_RECOVERY15.json','GIT_OPERATIONS15.json','fresh-git-recovered-outcome15.tar'):ck(not (D/name).exists(),'fresh output absent '+name)
ck(not (R.parent/'onchain-pilot-recovery/real-pilot-full29-outcome-20261011-15.git').exists(),'fresh recovery bare namespace absent')
ck("with (HERE/'SELECTION15.json').open('x')" in scripts['select15.py'] and "tarfile.open(p,'x'" in scripts['capture15.py'],'exclusive selector/capture outputs')
ck("S=D/'SELECTION15.json'" in scripts['capture15.py'] and "D/'CAPTURE15.json'" in scripts['recover15.py'],'sequential caller uses actual15 products')
ck("remotehead==source" in scripts['recover15.py'] and "head==source" in scripts['recover15.py'] and "sha(returned)==a['sha256']" in scripts['recover15.py'],'fresh external exact commit/blob joins retained')
result={'disposition':'ACCEPT_OUTCOME15_SOURCE_CALLER_ONLY_UNEXECUTED','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'metadata_roster_entries':len(metadata),'metadata_roster_regular_bytes':sum(x['bytes'] for x in metadata if x['type']=='regular'),'read_bytes':total,'read_cap_bytes':24*1024**2,'references':refs,'owned_directories':owned,'seven_scopes':[str(x.relative_to(R)) for x in scopes],'three_exclusions':exclusions,'source_inverse':'exact outcome13 full bytes recovered for all three helpers','caller':['.venv/bin/python -B '+str((D/'select15.py').relative_to(R)),'.venv/bin/python -B '+str((D/'capture15.py').relative_to(R)),'Root commits and pushes exact selected outputs, SELECTION15, CAPTURE15 and archive; require actual remote HEAD equals that committed source','.venv/bin/python -B '+str((D/'recover15.py').relative_to(R))],'future':['Complete all tools15 review artifacts before selector enumerates directory; preserve stable selected paths between selection and capture','Actual returned archive roster/body/type/mode verification and remaining four batch recovered journal checks still required','Bounded source review is not evidence that selection, capture, push or fresh recovery has occurred'],'limitations':['Metadata roster inspection is not executing selector, hashing all eventual selected payloads or proving future directory stability','64MiB is per regular member, not an aggregate process-memory cap; inherited capture/recovery reads full aggregate archives in memory','No private dispatch body or credentials read; dispatch names/types inspected only','Accepted unchanged mechanics reused; no universal symlink/POSIX restoration/completeness claim','Capture/selection are single exclusive attempts; any partial output/failure must remain and cannot be silently rerun in same names'],'fixture_failures':[]}
(P/'REVIEW01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'disposition':result['disposition'],'checks':len(checks),'read_bytes':total,'roster_entries':len(metadata),'regular_bytes':result['metadata_roster_regular_bytes'],'sha256':sha((P/'REVIEW01.json').read_bytes())}))
