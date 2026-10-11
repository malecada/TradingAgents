"""Independent declared outcome19 returned-byte review; no subprocess/helper run."""
import datetime,hashlib,io,json,os,resource,signal,stat,tarfile
from pathlib import Path,PurePosixPath
resource.setrlimit(resource.RLIMIT_AS,(384*1024**2,384*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304));signal.alarm(45)
H=Path(__file__).resolve().parent;F=H.parent;R=F.parents[2];D=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/outcome19';checks=[];refs={};streamed=0
SOURCE='8d56ea385a20291b51cf219298a08c5cb585da94';EXPECTED=(3440640,'ba54442284ce3f488c90348943beecb0ca66bf4a43d6828357d2e42bbe2833ad')
def ck(ok,name):
 assert ok,name
 checks.append(name)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 p=Path(p);s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<2*1024**2;b=p.read_bytes();refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':sha(b)};return b
def js(p):return json.loads(read(p))
def stream(f,limit):
 global streamed
 n=0;h=hashlib.sha256()
 while b:=f.read(65536):
  n+=len(b);streamed+=len(b);assert n<=limit and streamed<384*1024**2;h.update(b)
 return n,h.hexdigest()
def digest(p,limit=64*1024**2):
 p=Path(p);before=p.lstat();assert stat.S_ISREG(before.st_mode) and before.st_size<=limit
 with p.open('rb') as f:result=stream(f,limit)
 after=p.lstat();assert all(getattr(before,k)==getattr(after,k) for k in ('st_dev','st_ino','st_size','st_mode','st_mtime_ns','st_ctime_ns'));return result
observation=js(H/'EXPECTED_RETURN19.json');ck(observation['session']==95125 and observation['exit_code']==0 and observation['terminal_chunk']=='f1b9ef','Root actual recovery completion authorized checker')
Q=F/'pilot30-outcome-increment-tools-review01-2026-10-11/TOOLS_REVIEW01.json';T=F/'pilot30-terminal-outcome-review01-2026-10-11/REVIEW01.json';A=F/'pilot-full30-preparation-increment-return-review01-2026-10-11/REVIEW01.json'
ck(sha(read(Q))=='d97233b4302f1925cd55c86460d8fffda5a8aeaa51fa4bb49f5362618d010201','accepted19 tools');tools=js(Q)
ck(sha(read(T))=='7360d77f087f446c7049fb993ac267474a531b053c640c0238ff771c42578e64','accepted actual failed30 terminal');terminal=js(T)
ck(sha(read(A))=='372be424bc66aebbd691f30d03797d6e50cdb7d3476dd214bcb72d2c0976f495','accepted actual18 return');accepted=js(A)
manifest=js(D/'HELPERS_MANIFEST01.json');mp=tools['helper_manifest'];ck(digest(R/mp['path'])==(mp['bytes'],mp['sha256']),'authenticated reviewed helper manifest')
packet=js(D/'ROOT_ACTUAL_OPERATIONS19.json');ck(sha(read(D/'ROOT_ACTUAL_OPERATIONS19.json'))=='65857a3916f381750eb5c5586552969c68f62d24131d9262b718285573a328c7','Root original operation packet post-recovery local evidence')
ck(packet['recovery_operation']=={'exit_code':0,'session_id':95125,'terminal_chunk':'f1b9ef'} and packet['actual_root_exit']==1 and packet['root_terminal_chunk']=='78016d' and packet['commit_operation']['source']==SOURCE,'Root actual recovery and distinct failed pilot terminal')
for key in ('selection','capture','actual_recovery'):
 pin=packet[key];ck(digest(R/pin['path'])==(pin['bytes'],pin['sha256']),'Root packet receipt '+key)
for pin in manifest['candidate_helpers']+[manifest['literal_patch']]:ck(digest(R/pin['path'])==(pin['bytes'],pin['sha256']),'exact reviewed helper '+pin['path'])
selb=read(D/'SELECTION19.json');sel=json.loads(selb);capb=read(D/'CAPTURE19.json');cap=json.loads(capb);rec=js(D/'FRESH_GIT_RECOVERY19.json')
ck(sha(selb)==cap['selection']['sha256'] and sha(capb)==rec['capture']['sha256'],'actual selection/capture/recovery joins')
ck(cap['selection']['path']==str((D/'SELECTION19.json').relative_to(R)) and rec['capture']['path']==str((D/'CAPTURE19.json').relative_to(R)),'exact receipt paths')
ck(rec['source']==rec['actual_remote_head']==rec['actual_fetch_head']==SOURCE,'actual source/remote/fetch commit')
ck(cap['archive']['path']==str((D/'failed-outcome-increment19.tar').relative_to(R)) and rec['returned_archive']['path']==str((D/'fresh-git-recovered-outcome19.tar').relative_to(R)),'exact archive paths')
for pin in (cap['archive'],rec['returned_archive']):ck((pin['bytes'],pin['sha256'])==EXPECTED and digest(R/pin['path'])==EXPECTED,'whole actual archive hash')
ops=js(D/'GIT_OPERATIONS19.json');names=['local_head','remote_get_url','remote_actual_branch_readback','local_archive_git_tree_join','fresh_bare_init','fresh_remote_add','set_promisor','set_tree_zero_filter','actual_external_commit_only_fetch','fetched_head_readback','actual_external_commit_body','actual_external_selected_blob_fetch','actual_external_archive_blob_return']
ck(ops==rec['operations'] and [o['operation'] for o in ops]==names,'exact13 actual operations')
for op in ops:
 ck(op['exit_code']==0,'operation success '+op['operation'])
 for kind in ('stdout','stderr'):ck(digest(D/(op['operation']+'.'+kind))==(op[kind+'_bytes'],op[kind+'_sha256']),'actual raw '+op['operation']+'.'+kind)
ck(read(D/'local_head.stdout').decode().strip()==read(D/'fetched_head_readback.stdout').decode().strip()==SOURCE,'raw local/fetch identities')
ck(read(D/'remote_actual_branch_readback.stdout').decode().strip()==SOURCE+'\trefs/heads/research/onchain-paper-replication-2026-09-24','raw remote branch identity')
ck(read(D/'remote_get_url.stdout').decode().strip()==rec['actual_external_source']=='git@github.com:malecada/TradingAgents.git','raw external source identity')
ck(read(D/'local_archive_git_tree_join.stdout').decode().strip()==rec['local_commit_tree_join']==f"100644 blob {rec['archive_git_blob_oid']}\t{cap['archive']['path']}",'actual committed regular archive join')
commit=read(D/'actual_external_commit_body.stdout');ck(sha(commit)==rec['commit_body_sha256'] and hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest()==SOURCE,'independent commit object encoding')
returned=R/rec['returned_archive']['path'];blob=hashlib.sha1(b'blob '+str(EXPECTED[0]).encode()+b'\0')
with returned.open('rb') as f:
 while b:=f.read(65536):blob.update(b)
ck(blob.hexdigest()==rec['archive_git_blob_oid'],'independent blob object encoding')
bare=Path(rec['fresh_bare']);ck(bare==R.parent/'onchain-pilot-recovery/real-pilot-full30-outcome-20261011-19.git' and bare.is_dir() and not bare.is_symlink() and not os.path.lexists(bare/'objects/info/alternates') and rec['no_alternates'] is True,'actual exact bare/no alternates metadata')
rows=sorted(sel['rows']+sel['directories'],key=lambda x:x['path']);index={r['path']:r for r in rows};ck(len(index)==len(rows)==176 and len(sel['rows'])==sel['files']==cap['files']==144 and len(sel['directories'])==32 and sel['symlinks']==0,'144 regular plus32 directory denominator')
ck(all(r['type']=='regular' for r in sel['rows']) and sum(r['bytes'] for r in sel['rows'])==sel['body_bytes']==cap['regular_bytes']==3158982,'exact regular body denominator')
scopes=[x['path'] for x in sel['actual_scope_states']];ck(len(scopes)==5 and all(x['exists'] and x['empty_directories_included'] for x in sel['actual_scope_states']),'five actual declared scope states')
ck(scopes==tools['explicit_scopes'],'reviewed exact runtime/claim scope roster')
def public(name):
 p=PurePosixPath(name)
 return not p.is_absolute() and '..' not in p.parts and not {'.git','.venv','node_modules','keys','apis','real_pilot_runtime'}&set(p.parts) and p.name not in ('.env','connection.json','hf_token.txt') and (not name.startswith(('research_runs/','research_artifacts/')) or any(name==s or name.startswith(s+'/') for s in scopes))
for row in rows:ck(public(row['path']),'declared safe path '+row['path'])
class Sink:
 def __init__(self):self.n=0;self.h=hashlib.sha256()
 def write(self,b):self.n+=len(b);self.h.update(b);return len(b)
 def tell(self):return self.n
 def flush(self):pass
sink=Sink();typed=[]
with tarfile.open(returned,'r:') as source,tarfile.open(fileobj=sink,mode='w',format=tarfile.PAX_FORMAT) as target:
 members=source.getmembers();ck(len(members)==176,'complete returned member roster')
 for m,r in zip(members,rows,strict=True):
  ck(m.name==r['path'] and m.mode==int(r['mode'],8),'typed exact name/mode '+m.name);ck(m.uid==m.gid==m.mtime==0 and m.uname==m.gname=='','normalized owner/time')
  n=tarfile.TarInfo(r['path']);n.mode=int(r['mode'],8);n.uid=n.gid=n.mtime=0
  if r['type']=='directory':ck(m.type==tarfile.DIRTYPE and m.size==0,'actual directory');n.type=tarfile.DIRTYPE;target.addfile(n)
  else:
   ck(m.type==tarfile.REGTYPE and m.size==r['bytes']<=64*1024**2,'actual regular extent');ck(stream(source.extractfile(m),64*1024**2)==(r['bytes'],r['sha256']),'returned body '+m.name);n.size=m.size;target.addfile(n,source.extractfile(m))
  typed.append({'path':m.name,'type':r['type'],'mode':r['mode'],'bytes':m.size})
ck((sink.n,sink.h.hexdigest())==EXPECTED,'complete independent PAX reencoding exact')
base=js(R/sel['baseline_actual_recovery']['path']);ck(sha(read(R/sel['baseline_actual_recovery']['path']))==sel['baseline_actual_recovery']['sha256']=='634ecd4283cc5798a17b950796be92b1ea48e643de3f52f7d9187d50dd2ca3f5','actual18 receipt anchor')
ck(base['source']==sel['baseline_source']==accepted['source']=='5105cd89c4a38c2ba236c5c810ea6ce2f9652435' and base['returned_archive']==accepted['archive'],'accepted18 continuity without replay')
bcapb=read(R/base['capture']['path']);ck(sha(bcapb)==base['capture']['sha256'],'prior18 capture join');bcap=json.loads(bcapb);bselb=read(R/bcap['selection']['path']);ck(sha(bselb)==bcap['selection']['sha256'],'prior18 selection join');bsel=json.loads(bselb);oldrows={r['path']:r for r in bsel['rows']};reused=sel['exact_unchanged_prior_rows_reused'];ck(len(reused)==len(set(reused))==69 and not set(reused)&set(index),'69 disjoint prior row reuse')
for name in reused:
 row=oldrows[name];ck(public(name) and row['type']=='regular' and stat.S_IMODE((R/name).lstat().st_mode)==int(row['mode'],8) and digest(R/name)==(row['bytes'],row['sha256']),'unchanged prior18 public row '+name)
exclusions={bcap['archive']['path'],base['returned_archive']['path'],str((R/sel['baseline_actual_recovery']['path']).parent.relative_to(R))+'/actual_external_archive_blob_return.stdout'};ck(set(sel['exact_already_recovered_duplicate_exclusions'])==exclusions and not exclusions&set(index),'three exact prior archive exclusions')
for name,pin in terminal['inventory'].items():
 if name in index:
  row=index[name];ck(row['type']=='regular' and (row['bytes'],row['sha256'])==(pin['bytes'],pin['sha256']),'returned original terminal evidence '+name)
outputs=[r for r in rows if r['path'].startswith('research_runs/eth-paper-real-data-end-to-end-resource-20261011-30/outputs/') and r['type']=='regular'];ck(len(outputs)==terminal['original_output_count']==8 and {Path(r['path']).name for r in outputs}=={'archive-receipt.json','archive-terminal.json','cell-ledger.json','pilot-summary.json','resource-binding.json','resource-journal.json','resource-population-binding.json','resource-population.json'},'all eight original worker output bodies')
for scope in scopes:ck(any(n.startswith(scope+'/') for n in index),'returned typed scope '+scope)
for suffix in ('SOURCE_FREEZE01.json','ROOT_IO_CLOSED01.json','ROOT_TERMINAL_OPERATION01.json','FINAL_STORAGE01.json'):
 ck(any(n.endswith('/'+suffix) for n in index),'returned Root closure '+suffix)
for pin in manifest['candidate_helpers']+[manifest['literal_patch']]:ck(index[pin['path']]['sha256']==pin['sha256'],'returned actual helper '+pin['path'])
(H/'TYPED_MEMBERS19.json').write_text(json.dumps(typed,sort_keys=True,indent=2)+'\n')
out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'decision':'ACCEPT_ACTUAL_OUTCOME19_DECLARED_FAILED30_RETURN','source':SOURCE,'archive':rec['returned_archive'],'archive_git_blob_oid':rec['archive_git_blob_oid'],'regular':144,'directories':32,'regular_bytes':3158982,'reused_prior18_rows':69,'whole_pax_reencoding_exact':True,'no_alternates_metadata_verified':True,'original_worker_outputs':8,'checks':checks,'references':refs,'streamed_bytes_accounted':streamed,'limitations':['Declared144 bodies and32 typed names/modes only; no whole historical/scientific/runtime/private store completeness.','Actual retained13 Git-operation outputs verified; no new network/Git operation or future remote availability proof.','No POSIX reconstruction, hardlink reconstruction, deletion authority, numerical/financial completion or launch admission.','Prior18 accepted byte-return reused by exact receipt/review, not historical archive replay.']}
(H/'REVIEW01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('checks','references','limitations')},sort_keys=True));print('checks',len(checks))
