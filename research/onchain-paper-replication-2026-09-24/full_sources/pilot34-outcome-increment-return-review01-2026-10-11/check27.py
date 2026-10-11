"""Bounded actual outcome27 opaque-byte review. No Git/network/helper execution."""
import ast,datetime,hashlib,json,os,resource,signal,stat,tarfile
from pathlib import Path,PurePosixPath
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(30)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/outcome27';checks=[];refs={};streamed=0
SOURCE='401089cc3e973c134054fb6ef2e762cb4b152e07';EXPECTED=(6318080,'f633732ded76f527087c141475ba5da46d50ef06e2f113faa27791984121d243')
def ck(v,n):checks.append({'check':n,'pass':bool(v)});assert v,n
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 p=Path(p);s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<2*1024**2;b=p.read_bytes();refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':sha(b)};return b
def js(p):return json.loads(read(p))
def stream(f,limit=64*1024**2):
 global streamed
 n=0;h=hashlib.sha256()
 while b:=f.read(65536):n+=len(b);streamed+=len(b);assert n<=limit and streamed<384*1024**2;h.update(b)
 return n,h.hexdigest()
def digest(p,limit=64*1024**2):
 p=Path(p);before=p.lstat();assert stat.S_ISREG(before.st_mode) and before.st_size<=limit
 with p.open('rb') as f:result=stream(f,limit)
 after=p.lstat();assert all(getattr(before,k)==getattr(after,k) for k in ('st_dev','st_ino','st_size','st_mode','st_mtime_ns','st_ctime_ns'));return result
def pincheck(path,pin):ck(digest(path)==(pin['bytes'],pin['sha256']),'exact body '+str(path.relative_to(R)))
Q=F/'pilot34-outcome-increment-tools-review01-2026-10-11/TOOLS_REVIEW01.json';T=F/'pilot34-terminal-outcome-review01-2026-10-11/REVIEW01.json';A=F/'pilot34-preparation-increment-return-review01-2026-10-11/REVIEW01.json';V=F/'matching-compiled-two-attribute-qualification-source-review03-2026-10-11/REVIEW01.json'
for path,expected in [(Q,'a3a3c9df0bb565a1e0f8a142e6defc38130c28e0a5a6002c2c939fcccc6465ab'),(T,'038c243d300464611fcc3d3864ce5cc5b983ab0699f8f7efd0788f0b026ac569'),(A,'0fdeb0c250c50fd677cb787d24192bc961d965541bfcd9013b6a3fcfd4430707'),(V,'dcf05fea48f4ffd4b2a99cdf91fe951b92f77bac399a3cdef70a30e0093cce3d')]:ck(sha(read(path))==expected,'exact accepted anchor '+path.parent.name)
tools=js(Q);terminal=js(T);accepted=js(A);hreview=js(V);hm=js(D/'HELPERS_MANIFEST01.json');pincheck(D/'HELPERS_MANIFEST01.json',tools['references'][str((D/'HELPERS_MANIFEST01.json').relative_to(R))])
for name,pin in hm['files'].items():pincheck(D/name,pin)
selb=read(D/'SELECTION27.json');sel=json.loads(selb);capb=read(D/'CAPTURE27.json');cap=json.loads(capb);rec=js(D/'FRESH_GIT_RECOVERY27.json');ops=js(D/'GIT_OPERATIONS27.json');root=js(D/'ROOT_ACTUAL_OPERATIONS27.json')
ck(sha(selb)==cap['selection']['sha256'] and sha(capb)==rec['capture']['sha256'],'selection/capture/recovery exact body joins')
ck(cap['selection']['path']==str((D/'SELECTION27.json').relative_to(R)) and rec['capture']['path']==str((D/'CAPTURE27.json').relative_to(R)),'exact selection/capture paths')
ck(rec['source']==rec['actual_remote_head']==rec['actual_fetch_head']==SOURCE,'actual commit/remote/fetch source join')
ck(cap['archive']['path']==str((D/'failed-outcome-increment27.tar').relative_to(R)) and rec['returned_archive']['path']==str((D/'fresh-git-recovered-outcome27.tar').relative_to(R)),'exact original/returned archive names')
for pin in (cap['archive'],rec['returned_archive']):ck((pin['bytes'],pin['sha256'])==EXPECTED and digest(R/pin['path'])==EXPECTED,'actual archive length/hash')
names=['local_head','remote_get_url','remote_actual_branch_readback','local_archive_git_tree_join','fresh_bare_init','fresh_remote_add','set_promisor','set_tree_zero_filter','actual_external_commit_only_fetch','fetched_head_readback','actual_external_commit_body','actual_external_selected_blob_fetch','actual_external_archive_blob_return']
ck(ops==rec['operations'] and [o['operation'] for o in ops]==names,'exact thirteen recorded operations')
for op in ops:
 ck(op['exit_code']==0,'actual operation exit '+op['operation'])
 for kind in ('stdout','stderr'):ck(digest(D/(op['operation']+'.'+kind))==(op[kind+'_bytes'],op[kind+'_sha256']),'actual raw operation '+op['operation']+'.'+kind)
ck(read(D/'local_head.stdout').decode().strip()==read(D/'fetched_head_readback.stdout').decode().strip()==SOURCE,'actual raw local/fetch source')
ck(read(D/'remote_actual_branch_readback.stdout').decode().strip()==SOURCE+'\trefs/heads/research/onchain-paper-replication-2026-09-24','actual raw remote branch')
ck(read(D/'remote_get_url.stdout').decode().strip()==rec['actual_external_source']=='git@github.com:malecada/TradingAgents.git','actual external source')
ck(read(D/'local_archive_git_tree_join.stdout').decode().strip()==rec['local_commit_tree_join']==f"100644 blob {rec['archive_git_blob_oid']}\t{cap['archive']['path']}",'committed regular archive tree join')
commit=read(D/'actual_external_commit_body.stdout');ck(sha(commit)==rec['commit_body_sha256'] and hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest()==SOURCE,'independent commit object reencoding')
returned=R/rec['returned_archive']['path'];blob=hashlib.sha1(b'blob '+str(EXPECTED[0]).encode()+b'\0')
with returned.open('rb') as f:
 while b:=f.read(65536):blob.update(b)
ck(blob.hexdigest()==rec['archive_git_blob_oid'],'independent returned blob object reencoding')
bare=Path(rec['fresh_bare']);ck(bare==R.parent/'onchain-pilot-recovery/real-pilot-failed34-outcome-20261011-27.git' and bare.is_dir() and not bare.is_symlink() and not os.path.lexists(bare/'objects/info/alternates') and rec['no_alternates'] is True,'exact bare/no-alternates metadata only')
rows=sorted(sel['rows']+sel['directories'],key=lambda r:r['path']);index={r['path']:r for r in rows}
ck(len(index)==len(rows)==597 and len(sel['rows'])==sel['files']==cap['files']==516 and len(sel['directories'])==cap['directories']==81 and sel['symlinks']==0,'516 regular plus81 directory denominator')
ck(all(r['type']=='regular' for r in sel['rows']) and sum(r['bytes'] for r in sel['rows'])==sel['body_bytes']==cap['regular_bytes']==5302719,'complete regular byte denominator')
N='eth-paper-real-data-end-to-end-resource-20261011-34';rep='eab8d86b62c9274c2888e73538431496527fc376eb1f0f73ebd3c6f9ce1da778'
scopes=['research_runs/'+N,'research_artifacts/onchain-paper-replication-2026-09-24/runs/'+N,'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent/'+N,'research_artifacts/onchain_representations/'+rep+'/'+N,'research_artifacts/archive-dispatch-ethpilot-20261011-34','research_artifacts/onchain_compact_mcm/'+rep+'/'+N]
ck([s['path'] for s in sel['actual_scope_states']]==scopes and all(s['exists'] and s['empty_directories_included'] for s in sel['actual_scope_states']),'six exact original failed34 scope states')
def public(name):
 p=PurePosixPath(name)
 return not p.is_absolute() and '..' not in p.parts and not {'.git','.venv','node_modules','keys','apis','real_pilot_runtime'}&set(p.parts) and p.name not in ('.env','connection.json','hf_token.txt') and (not name.startswith(('research_runs/','research_artifacts/')) or any(name==s or name.startswith(s+'/') for s in scopes))
for r in rows:ck(public(r['path']) or (r['type']=='directory' and any(s.startswith(r['path']+'/') for s in scopes)),'public scoped name '+r['path'])
class Sink:
 def __init__(self):self.n=0;self.h=hashlib.sha256()
 def write(self,b):self.n+=len(b);self.h.update(b);return len(b)
 def tell(self):return self.n
 def flush(self):pass
sink=Sink();typed=[]
with tarfile.open(returned,'r:') as archive,tarfile.open(fileobj=sink,mode='w',format=tarfile.PAX_FORMAT) as target:
 members=archive.getmembers();ck(len(members)==597,'complete returned member roster')
 for m,r in zip(members,rows,strict=True):
  ck(m.name==r['path'] and m.mode==int(r['mode'],8) and m.uid==m.gid==m.mtime==0 and m.uname==m.gname=='','returned name/mode/normalized metadata '+m.name)
  n=tarfile.TarInfo(r['path']);n.mode=int(r['mode'],8);n.uid=n.gid=n.mtime=0
  if r['type']=='directory':ck(m.type==tarfile.DIRTYPE and m.size==0,'typed directory '+m.name);n.type=tarfile.DIRTYPE;target.addfile(n)
  else:
   ck(m.type==tarfile.REGTYPE and m.size==r['bytes']<=64*1024**2,'typed regular extent '+m.name);ck(stream(archive.extractfile(m))==(r['bytes'],r['sha256']),'opaque returned body '+m.name);n.size=m.size;target.addfile(n,archive.extractfile(m))
  typed.append({'path':m.name,'type':r['type'],'mode':r['mode'],'bytes':m.size,'sha256':r.get('sha256')})
ck((sink.n,sink.h.hexdigest())==EXPECTED,'entire canonical PAX reencoding exact')
base=js(R/sel['baseline_actual_recovery']['path']);ck(sha(read(R/sel['baseline_actual_recovery']['path']))==sel['baseline_actual_recovery']['sha256']=='2a947a7df2406ee678c44ffe960288c837ee3abc60d64e095c9c342cbe156484','accepted26 recovery anchor')
ck(base['source']==sel['baseline_source']==accepted['source']=='67335f5e1987f28219e75e8cb679ff339739d853' and base['returned_archive']==accepted['archive'],'prior26 accepted return continuity; no archive replay')
bcapb=read(R/base['capture']['path']);ck(sha(bcapb)==base['capture']['sha256'],'prior26 capture join');bcap=json.loads(bcapb);bselb=read(R/bcap['selection']['path']);ck(sha(bselb)==bcap['selection']['sha256'],'prior26 selection join');bsel=json.loads(bselb);oldrows={r['path']:r for r in bsel['rows']};reused=sel['exact_unchanged_prior_rows_reused'];ck(len(reused)==len(set(reused))==67 and not set(reused)&set(index),'67 disjoint explicitly reused prior rows')
for name in reused:
 r=oldrows[name];ck(public(name) and r['type']=='regular' and digest(R/name)==(r['bytes'],r['sha256']) and stat.S_IMODE((R/name).lstat().st_mode)==int(r['mode'],8),'unchanged prior26 row '+name)
exclusions={bcap['archive']['path'],base['returned_archive']['path'],str((R/sel['baseline_actual_recovery']['path']).parent.relative_to(R))+'/actual_external_archive_blob_return.stdout'};ck(set(sel['exact_already_recovered_duplicate_exclusions'])==exclusions and not exclusions&set(index),'three exact prior26 duplicate archives excluded')
available=dict(index);available.update({n:oldrows[n] for n in reused})
def returned_pin(path,pin):
 name=str(path.relative_to(R));ck(name in available and available[name]['type']=='regular' and (available[name]['bytes'],available[name]['sha256'])==(pin['bytes'],pin['sha256']),'returned or explicitly reused required '+name)
for path in (T,V,Q):returned_pin(path,refs[str(path.relative_to(R))])
for name,pin in terminal['references'].items():
 if any(name==s or name.startswith(s+'/') for s in scopes) or name.startswith(str((F/'real-data-pilot-full34-entry-preparation01-2026-10-11').relative_to(R))+'/'):returned_pin(R/name,pin)
outputs=[r for r in sel['rows'] if r['path'].startswith('research_runs/'+N+'/outputs/')];ck(len(outputs)==8 and {Path(r['path']).name for r in outputs}=={'archive-receipt.json','archive-terminal.json','cell-ledger.json','pilot-summary.json','resource-binding.json','resource-journal.json','resource-population-binding.json','resource-population.json'},'all eight original worker output bodies')
command=js(F/'pilot34-native-owner-qualification02-2026-10-11/COMMAND02.json')
for pin in [command['script'],command['candidate_manifest'],*command['role_references'].values()]:returned_pin(Path(pin['path']),pin)
opts=dict(zip(command['argv'][3::2],command['argv'][4::2]))
for role in ('owner','kernel','policy'):
 path=Path(opts['--'+role]);body=read(path);returned_pin(path,{'bytes':len(body),'sha256':opts['--'+role+'-sha256']})
for name,pin in hm['files'].items():returned_pin(D/name,pin)
# Census exact original six trees using names/types only; no scientific decoding.
census=[]
for scope in scopes:
 found={};empty=[]
 for basepath,dirs,files in os.walk(R/scope,followlinks=False):
  p=Path(basepath);s=p.lstat();assert stat.S_ISDIR(s.st_mode);name=str(p.relative_to(R));found[name]=('directory',stat.S_IMODE(s.st_mode))
  if not dirs and not files:empty.append(name)
  for child in dirs+files:
   cp=p/child;st=cp.lstat();assert not stat.S_ISLNK(st.st_mode)
   if stat.S_ISREG(st.st_mode):found[str(cp.relative_to(R))]=('regular',stat.S_IMODE(st.st_mode))
   else:assert stat.S_ISDIR(st.st_mode)
 selected={n:(r['type'],int(r['mode'],8)) for n,r in index.items() if n==scope or n.startswith(scope+'/')}
 ck(found==selected,'exact typed original scope census '+scope);ck(all(n in index for n in empty),'all original empty directories retained '+scope)
 census.append({'scope':scope,'regular':sum(t=='regular' for t,m in found.values()),'directories':sum(t=='directory' for t,m in found.values()),'empty_directories':empty})
for name in tools['owned_public_directories']:ck(str((F/name).relative_to(R)) in index,'mandatory owned root directory preserved '+name)
for r in sel['rows']:ck(digest(R/r['path'])==(r['bytes'],r['sha256']) and stat.S_IMODE((R/r['path']).lstat().st_mode)==int(r['mode'],8),'original current opaque selected body '+r['path'])
for key,chunk in [('selection','1d685d'),('capture','3caaf1'),('push_terminal','e7c4ce'),('recovery_terminal','9f46ac')]:ck(root[key]['exit_code']==0 and root[key]['chunk_id']==chunk,'Root retained tool terminal '+key)
ck(root['commit']['source']==SOURCE and root['commit']['exit_code']==0 and root['push_initial']['session_id']==31419 and root['recovery_initial']['session_id']==85285,'actual Root commit/push/recover session joins')
ck(json.loads(root['capture']['output'])==cap and json.loads(root['recovery_terminal']['output'])=={'status':'ACTUAL_SELECTED_EXTERNAL_RETURN','source':SOURCE,'bytes':EXPECTED[0],'sha256':EXPECTED[1]},'actual Root raw JSON outputs match capture and recovered archive')
out={'decision':'ACCEPT_ACTUAL_OUTCOME27_DECLARED_FAILED34_RETURN','source':SOURCE,'archive':rec['returned_archive'],'archive_git_blob_oid':rec['archive_git_blob_oid'],'regular':516,'directories':81,'regular_bytes':5302719,'reused_prior26_rows':67,'original_worker_outputs':8,'six_scope_census':census,'whole_pax_reencoding_exact':True,'no_alternates_metadata_verified':True,'checks':checks,'references':refs,'streamed_bytes_accounted':streamed,'limitations':['Exact declared public increment and six original failed34 scopes only; no whole installed runtime/private/scientific store or arbitrary POSIX reconstruction claim.','Native/scientific payloads hashed as opaque bytes, never imported/decoded/executed.','Actual recorded13 operation outputs authenticated; no new Git/network operation or future availability promise.','Prior26 accepted return reused by exact review/receipt/rows, not historical replay.','Root commit tool stdout was not fully retained; receipt explicitly says not reconstructed. Independent raw commit-object/tree/blob/remote/fetch joins establish recorded return.','Post-capture ROOT_ACTUAL_OPERATIONS27 and this independent review are outside returned archive and need later preservation.','No deletion, admission, empirical success or unconditional native-launch authority.']}
for name,value in [('TYPED_MEMBERS27.json',typed),('REVIEW01.json',out)]:
 with (P/name).open('x') as f:json.dump(value,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('checks','references','limitations','six_scope_census')},sort_keys=True));print('checks',len(checks))
