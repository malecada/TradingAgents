"""Actual increment33 finite return verification, no extraction or Git/network."""
import hashlib,json,os,stat,tarfile
from pathlib import Path,PurePosixPath
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';D=H/'full38increment33';O=H/'full36increment32'
SOURCE='d4064aace3d26f33a5708ea4c1665a156644de6f';EXPECTED=(8325120,'0bef9fe8563fe1cde32f8a70662f2510286396ff42f387eefa547e47b27d7e4b');counts={};refs={};streamed=0
def ck(ok,kind,detail=''):
    assert ok,(kind,detail)
    counts[kind]=counts.get(kind,0)+1
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(p):
    p=Path(p);s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<4*1024**2
    b=p.read_bytes();refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':sha(b)};return b
js=lambda p:json.loads(read(p))
def stream(f):
    global streamed
    n=0;h=hashlib.sha256()
    while b:=f.read(65536):
        n+=len(b);streamed+=len(b);assert n<=64*1024**2 and streamed<384*1024**2;h.update(b)
    return n,h.hexdigest()
def digest(p):
    p=Path(p);s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<=64*1024**2
    with p.open('rb') as f:v=stream(f)
    t=p.lstat();assert all(getattr(s,k)==getattr(t,k) for k in ('st_dev','st_ino','st_size','st_mode','st_nlink','st_mtime_ns','st_ctime_ns'));return v
for leaf,pin in {'select33_02.py':'58059f938c185eac57be76b8cc1bd5642c6b8ab67c810446e2966965a42de83d','capture33.py':'bcafc965a1eb0c20fd1062293b36f73458f5cfa057e12c2dfbc685c3c695402f','recover33.py':'87f4c78eb18b4856d54802eb0f191380f4ba94cbf18aece39d0c6184981a15a2'}.items():ck(digest(D/leaf)[1]==pin,'accepted helper source',leaf)
review02=js(F/'pilot38-increment33-tools-review-2026-10-12/SELECTOR02_REVIEW.json');ck(review02['status']=='SOURCE02_ACCEPTED' and review02['selector_sha256']==digest(D/'select33_02.py')[1],'accepted selector02 join')
sb=read(D/'SELECTION33.json');sel=json.loads(sb);cb=read(D/'CAPTURE33.json');cap=json.loads(cb);rec=js(D/'FRESH_GIT_RECOVERY33.json');ops=js(D/'GIT_OPERATIONS33.json');scope=js(D/'TOOL_SCOPE01.json')
ck(sha(sb)==cap['selection']['sha256'] and sha(cb)==rec['capture']['sha256'],'selection capture return hashes')
ck(cap['selection']['path']==str((D/'SELECTION33.json').relative_to(R)) and rec['capture']['path']==str((D/'CAPTURE33.json').relative_to(R)),'exact receipt paths')
ck(rec['source']==rec['actual_remote_head']==rec['actual_fetch_head']==SOURCE,'source remote fetched equality')
ck(cap['archive']['path']==str((D/'pilot38-preparation-increment33.tar').relative_to(R)) and rec['returned_archive']['path']==str((D/'fresh-git-recovered-full38increment33.tar').relative_to(R)),'exact archive paths')
for pin in (cap['archive'],rec['returned_archive']):ck((pin['bytes'],pin['sha256'])==EXPECTED and digest(R/pin['path'])==EXPECTED,'actual capture and return')
names=['local_head','remote_get_url','remote_actual_branch_readback','local_archive_git_tree_join','fresh_bare_init','fresh_remote_add','set_promisor','set_tree_zero_filter','actual_external_commit_only_fetch','fetched_head_readback','actual_external_commit_body','actual_external_selected_blob_fetch','actual_external_archive_blob_return']
ck(ops==rec['operations'] and [x['operation'] for x in ops]==names,'exact13operations')
for op in ops:
    ck(op['exit_code']==0,'operation exits',op['operation'])
    for kind in ('stdout','stderr'):ck(digest(D/(op['operation']+'.'+kind))==(op[kind+'_bytes'],op[kind+'_sha256']),'raw operation hash',op['operation']+'.'+kind)
ck(read(D/'local_head.stdout').decode().strip()==read(D/'fetched_head_readback.stdout').decode().strip()==SOURCE,'actual raw source and fetch')
ck(read(D/'remote_actual_branch_readback.stdout').decode().strip()==SOURCE+'\trefs/heads/research/onchain-paper-replication-2026-09-24','actual raw remote branch')
ck(read(D/'remote_get_url.stdout').decode().strip()==rec['actual_external_source']=='git@github.com:malecada/TradingAgents.git','actual remote URL')
ck(read(D/'local_archive_git_tree_join.stdout').decode().strip()==rec['local_commit_tree_join']==f"100644 blob {rec['archive_git_blob_oid']}\t{cap['archive']['path']}",'actual local tree join')
commit=read(D/'actual_external_commit_body.stdout');ck(sha(commit)==rec['commit_body_sha256'] and hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest()==SOURCE,'commit object reencoding')
returned=R/rec['returned_archive']['path'];blob=hashlib.sha1(b'blob '+str(EXPECTED[0]).encode()+b'\0')
with returned.open('rb') as f:
    while b:=f.read(65536):blob.update(b)
ck(blob.hexdigest()==rec['archive_git_blob_oid'],'returned blob object reencoding')
bare=Path(rec['fresh_bare']);ck(bare==R.parent/'onchain-pilot-recovery/real-pilot-preparation38-20261012-33.git' and bare.is_dir() and not bare.is_symlink() and not os.path.lexists(bare/'objects/info/alternates') and rec['no_alternates'] is True,'fresh bare metadata no alternates')
rows=sorted(sel['rows']+sel['directories'],key=lambda r:r['path']);index={r['path']:r for r in rows}
ck(len(rows)==len(index) and len(sel['rows'])==sel['files']==cap['files']==430 and len(sel['directories'])==cap['directories']==62,'complete430body62directorydenominator')
ck(sel['symlinks']==0 and all(r['type']=='regular' for r in sel['rows']) and sum(r['bytes'] for r in sel['rows'])==sel['body_bytes']==cap['regular_bytes']==7508597,'completebodytotals')
ck(set(sel['mandatory_public_roots'])==set(scope['mandatory_public_roots']) and len(scope['mandatory_public_roots'])==19 and sel['prior_generated_files']==scope['prior32_exact_postcapture_names'],'exact public scope')
private=scope['opaque38']['path'];ck(private in index,'sole opaque envelope selected')
def allowed(name):
    p=PurePosixPath(name)
    return not p.is_absolute() and '..' not in p.parts and not {'.git','.venv','node_modules','keys','apis'}&set(p.parts) and p.name not in ('.env','connection.json','hf_token.txt','id_ed25519_storagebox_u676273') and (not name.startswith(('research_artifacts/','research_runs/')) or name==private or any(PurePosixPath(name).is_relative_to(PurePosixPath(root)) for root in scope['closed36_owned_roots']))
for row in rows:
    if row['type']!='directory':ck(allowed(row['path']),'exact public or single envelope path',row['path'])
    else:ck(not PurePosixPath(row['path']).is_absolute() and '..' not in PurePosixPath(row['path']).parts,'canonical directory path',row['path'])
class Sink:
    def __init__(self):self.n=0;self.h=hashlib.sha256()
    def write(self,b):self.n+=len(b);self.h.update(b);return len(b)
    def tell(self):return self.n
    def flush(self):pass
sink=Sink()
with tarfile.open(returned,'r:') as archive,tarfile.open(fileobj=sink,mode='w',format=tarfile.PAX_FORMAT) as target:
    members=archive.getmembers();ck(len(members)==len(rows),'complete tar member count')
    for member,row in zip(members,rows,strict=True):
        ck(member.name==row['path'] and member.mode==int(row['mode'],8) and member.uid==member.gid==member.mtime==0 and member.uname==member.gname=='','every typed name mode order',member.name)
        m=tarfile.TarInfo(row['path']);m.mode=int(row['mode'],8);m.uid=m.gid=m.mtime=0
        if row['type']=='directory':ck(member.type==tarfile.DIRTYPE and member.size==0,'directory type extent');m.type=tarfile.DIRTYPE;target.addfile(m)
        else:
            ck(member.type==tarfile.REGTYPE and member.size==row['bytes']<=64*1024**2,'regular type extent');ck(stream(archive.extractfile(member))==(row['bytes'],row['sha256']),'every returned body hash',member.name);m.size=member.size;target.addfile(m,archive.extractfile(member))
ck((sink.n,sink.h.hexdigest())==EXPECTED,'exact full canonical PAX reencoding')
# Exact accepted32 lineage; do not traverse old stores or extract their tar.
baseb=read(O/'FRESH_GIT_RECOVERY32.json');base=json.loads(baseb)
ck(sha(baseb)==sel['baseline_actual_recovery']['sha256']=='8db63835ace586bc84bb93f7ab4a87debab2e2c89ddd34cda61d353b314b3b50','actual32lineage')
accepted=read(R/sel['baseline_accepted_review']['path']);ck(sha(accepted)==sel['baseline_accepted_review']['sha256']=='230a939c4ed35ed09d0fc3dda5ad9328f7920c4686769d6f3e6a852a557ec1f8','accepted32review')
ck(base['source']==sel['baseline_source']=='4c9029af4e35d508c02254f91081d56bea15b28c','baseline source')
bcapb=read(O/'CAPTURE32.json');ck(sha(bcapb)==base['capture']['sha256'],'baseline capture');bcap=json.loads(bcapb)
bsb=read(O/'SELECTION32.json');ck(sha(bsb)==bcap['selection']['sha256'],'baseline selection');bs=json.loads(bsb);oldrows={r['path']:r for r in bs['rows']};reused=sel['exact_unchanged_prior_rows_reused']
ck(len(reused)==len(set(reused)) and not set(reused)&set(index) and set(reused)<=set(oldrows),'disjoint immutable prior32 reuse')
for name in reused:
 row=oldrows[name];ck(allowed(name) and row['type']=='regular' and digest(R/name)==(row['bytes'],row['sha256']) and stat.S_IMODE((R/name).lstat().st_mode)==int(row['mode'],8),'each immutable reused row',name)
ck(sel['prior_inherited_reuse_preserved_by_receipt']==bs['exact_unchanged_prior_rows_reused'] and sel['earlier_inherited_reuse_preserved_by_receipt']==bs['prior_inherited_reuse_preserved_by_receipt'],'inherited receipt lineage')
excluded={str((O/n).relative_to(R)) for n in ('pilot36-preparation-increment32.tar','fresh-git-recovered-full36increment32.tar','actual_external_archive_blob_return.stdout')}
ck(set(sel['exact_already_recovered_duplicate_exclusions'])==excluded and not excluded&set(index),'exact duplicate exclusions')
for name in excluded:ck(digest(R/name)==(base['returned_archive']['bytes'],base['returned_archive']['sha256']),'previous32 archive aliases')
for row in sel['rows']:
 p=R/row['path'];s=p.lstat();ck(stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==int(row['mode'],8) and s.st_nlink==1 and digest(p)==(row['bytes'],row['sha256']),'each selected local body mode',row['path'])
for row in sel['directories']:
 p=R/row['path'];ck(p.is_dir() and not p.is_symlink() and p.resolve()==p and stat.S_IMODE(p.stat().st_mode)==int(row['mode'],8),'each local directory mode',row['path'])
# Finite census of declared roots only. No historical supporting roots followed.
census=[];postcapture={}
postcapture_names={str((F/'real-data-pilot-full38-entry-preparation01-2026-10-12'/leaf).relative_to(R)) for leaf in ('ROOT_METADATA_ADMISSION_OPERATION01.json','metadata_admission01.stdout','metadata_admission01.stderr')}
for root in [F/n for n in scope['mandatory_public_roots']]+[R/n for n in scope['closed36_owned_roots']]:
 found={}
 for parent,dirs,files in os.walk(root,followlinks=False):
  p=Path(parent);found[str(p.relative_to(R))]=('directory',stat.S_IMODE(p.lstat().st_mode))
  for child in dirs+files:
   p=Path(parent)/child;s=p.lstat()
   if stat.S_ISREG(s.st_mode):found[str(p.relative_to(R))]=('regular',stat.S_IMODE(s.st_mode))
   elif stat.S_ISLNK(s.st_mode):found[str(p.relative_to(R))]=('symlink',stat.S_IMODE(s.st_mode))
   else:assert stat.S_ISDIR(s.st_mode)
 expected={n:(row['type'],int(row['mode'],8)) for n,row in index.items() if (R/n).is_relative_to(root)}
 expected.update({n:(oldrows[n]['type'],int(oldrows[n]['mode'],8)) for n in reused if (R/n).is_relative_to(root)})
 additions=set(found)-set(expected)
 ck(additions<=postcapture_names and all(found.get(k)==v for k,v in expected.items()),'exact finite root census plus named postcapture metadata',str(root.relative_to(R)))
 for name in additions:read(R/name);postcapture[name]=refs[name]
 census.append({'root':str(root.relative_to(R)),'captured_or_reused_entries':len(expected),'later_uncaptured_entries':len(additions)})
ck(set(postcapture)==postcapture_names,'exact three postcapture metadata exclusions')
for path,pin in scope['main_source_pins'].items():ck(path in index and index[path]['sha256']==pin,'all eight current source pins returned',path)
extra=js(D/'TOOL_SCOPE02.json')['exact_additional_committed_metadata_pins'];ck(extra==sel['exact_additional_committed_metadata_pins']==review02['exact_extra_pins'],'exact selector02 metadata delta')
for path,pin in extra.items():ck(path in index and index[path]['sha256']==pin,'all56 exact added bodies returned',path)
for leaf in scope['prior32_exact_postcapture_names']:
 name=str((O/leaf).relative_to(R));ck(name in index or name in reused or name in excluded,'every prior32 operation accounted',leaf)
opaque=scope['opaque38'];ck((index[private]['bytes'],index[private]['sha256'])==(opaque['bytes'],opaque['sha256']),'opaque exact raw bytes only')
# Join every actual36 review reference in the four owned roots to actual returned rows.
outcome_name=str((F/'pilot36-outcome-review-2026-10-12/OUTCOME_REVIEW01.json').relative_to(R));ck(index[outcome_name]['sha256']=='d1fae63a7248b3f3fb1fbabe1c2fe4f9ec63dd9c57bb57b58a718b164606fb19','accepted closed36 review returned unchanged')
outcome=js(R/outcome_name);joins=[]
for path,v in outcome['evidence'].items():
 if any((R/path).is_relative_to(R/root) for root in scope['closed36_owned_roots']):
  ck(path in index and (index[path]['bytes'],index[path]['sha256'])==(v['bytes'],v['sha256']),'original36 returned review evidence join',path);joins.append(path)
ck(len(joins)>10,'substantive original36 evidence join')
# Returned outcome review byte equality preserves nulls and all scientific disposition exactly.
with tarfile.open(returned,'r:') as archive:
 returned_outcome=archive.extractfile(outcome_name).read();ck(returned_outcome==read(R/outcome_name),'original36 review all nulls and dispositions byte unchanged')
 for leaf in ('ROOT_IO_CLOSED01.json','ROOT_ADMISSION_OPERATIONS01.json'):
  name=str((F/'real-data-pilot-full36-entry-preparation01-2026-10-11'/leaf).relative_to(R));ck(name in index or name in reused,'original Root closure and admission preserved',name)
# Only metadata inspect bare; never trigger lazy fetching or execute a recovery tool.
ck((bare/'FETCH_HEAD').read_text().split()[0]==SOURCE,'direct bare FETCH_HEAD source')
ck('bare = true' in (bare/'config').read_text() and (bare/'objects').is_dir(),'direct bare configuration')
# Current38 gate/input/caller joined as preserved bodies, not a new gate decision.
for root in ('real-data-pilot-full38-entry-preparation01-2026-10-12','real-data-pilot-full38-binding-preparation01-2026-10-12','real-data-pilot-full38-cumulative-preparation01-2026-10-12'):
 ck(any((R/path).is_relative_to(F/root) for path in index),'current38 preparation included',root)
future=['FINAL_BINDING01.json','RELEASE_REVIEW01.json','ADMISSION01.json','ROOT_ADMISSION_OPERATIONS01.json']
# Root will create final binding/release; current run36 admission rows are intentionally distinct.
future38=[path for path in index if '/full38' in path and PurePosixPath(path).name in future]
out={'schema_version':1,'decision':'accepted','reviewer':'Independent increment33 returned-scope reviewer','scope':'Actual declared increment33 returned byte/name/type/mode scope and authenticated32 lineage only. No pilot qualification, entry release, installed runtime, whole-store/POSIX or deletion authority.','source':SOURCE,'archive':rec['returned_archive'],'archive_git_blob_oid':rec['archive_git_blob_oid'],'regular_files':430,'directories':62,'regular_bytes':7508597,'symlinks':0,'operation_count':13,'reused_prior32_rows':len(reused),'sole_opaque_body':private,'scope_census':census,'postcapture_excluded':postcapture,'original36_reference_joins':joins,'original36_review_sha256':index[outcome_name]['sha256'],'original36_nulls_and_dispositions_preserved':True,'whole_PAX_reencoding_exact':True,'category_checks':counts,'evidence':refs,'streamed_bytes':streamed,'limitations':['No helper/network execution or archive extraction. Raw actual13 Git operation evidence authenticated.','Direct bare FETCH_HEAD/config/no-alternates metadata checked; no new remote operation or ongoing availability claim.','Opaque dispatch processed only as raw bytes, never decoded or referenced targets read.','Final38 binding/release, postcapture admission and this independent review are later evidence outside the returned archive.']}
with (P/'RETURN_REVIEW01.json').open('x') as h:json.dump(out,h,indent=2,sort_keys=True);h.write('\n')
print(json.dumps({'decision':'accepted','checks':sum(counts.values()),'return_review_sha256':sha((P/'RETURN_REVIEW01.json').read_bytes()),'reused_prior32_rows':len(reused)}))
