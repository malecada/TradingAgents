"""Actual increment32 finite return verification, no extraction or Git/network."""
import hashlib,json,os,stat,tarfile
from pathlib import Path,PurePosixPath
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';D=H/'full36increment32';O=H/'full35outcome31'
SOURCE='4c9029af4e35d508c02254f91081d56bea15b28c';EXPECTED=(4444160,'86203753e9863e23349db31f37ee8f983ba871bf35b65caf8fe36cb034598fca');counts={};refs={};streamed=0
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
tools=F/'pilot36-increment32-tools-review-2026-10-11/REPORT.md';ck(sha(read(tools))=='a0f1d8dd26c00a9188952af7ae89de6ed3d78def832c00b4e938fc34a715cbe4','accepted exact tools review')
hm=js(D/'HELPERS_MANIFEST01.json')
for path,pin in hm.items():ck(digest(R/path)[1]==pin,'exact reviewed helper',path)
for leaf,pin in {'select32.py':'97e8803c7c2577bc3dbf9da42c00692ba333b4f3ee5027fb380eecf0a122742a','capture32.py':'ef7bb5eb728e517e5d5c90f97f628872c274e640e39673a84e4fcb5a6b3be440','recover32.py':'44d4c80bc385fe2490000843ddf417ba8c0b80e14aab041ee70abce9f4f1326a'}.items():ck(digest(D/leaf)[1]==pin,'accepted helper source',leaf)
sb=read(D/'SELECTION32.json');sel=json.loads(sb);cb=read(D/'CAPTURE32.json');cap=json.loads(cb);rec=js(D/'FRESH_GIT_RECOVERY32.json');ops=js(D/'GIT_OPERATIONS32.json');scope=js(D/'TOOL_SCOPE01.json')
ck(sha(sb)==cap['selection']['sha256'] and sha(cb)==rec['capture']['sha256'],'selection capture return hashes')
ck(cap['selection']['path']==str((D/'SELECTION32.json').relative_to(R)) and rec['capture']['path']==str((D/'CAPTURE32.json').relative_to(R)),'exact receipt paths')
ck(rec['source']==rec['actual_remote_head']==rec['actual_fetch_head']==SOURCE,'source remote fetched equality')
ck(cap['archive']['path']==str((D/'pilot36-preparation-increment32.tar').relative_to(R)) and rec['returned_archive']['path']==str((D/'fresh-git-recovered-full36increment32.tar').relative_to(R)),'exact archive paths')
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
bare=Path(rec['fresh_bare']);ck(bare==R.parent/'onchain-pilot-recovery/real-pilot-preparation36-20261011-32.git' and bare.is_dir() and not bare.is_symlink() and not os.path.lexists(bare/'objects/info/alternates') and rec['no_alternates'] is True,'fresh bare metadata no alternates')
rows=sorted(sel['rows']+sel['directories'],key=lambda r:r['path']);index={r['path']:r for r in rows}
ck(len(rows)==len(index) and len(sel['rows'])==sel['files']==cap['files']==289 and len(sel['directories'])==cap['directories']==51,'complete289body51directorydenominator')
ck(sel['symlinks']==0 and all(r['type']=='regular' for r in sel['rows']) and sum(r['bytes'] for r in sel['rows'])==sel['body_bytes']==cap['regular_bytes']==3894966,'completebodytotals')
ck(set(sel['mandatory_public_roots'])==set(scope['public_roots']) and len(scope['public_roots'])==14 and sel['prior_generated_files']==scope['prior_generated_names'],'exact public scope')
private=scope['private_scope'][0];ck(len(scope['private_scope'])==1 and private in index,'sole opaque envelope selected')
def allowed(name):
    p=PurePosixPath(name)
    return not p.is_absolute() and '..' not in p.parts and not {'.git','.venv','node_modules','keys','apis'}&set(p.parts) and p.name not in ('.env','connection.json','hf_token.txt','id_ed25519_storagebox_u676273') and (not name.startswith(('research_artifacts/','research_runs/')) or name==private)
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
accepted=F/'pilot35-efficiency-increment31-return-review-2026-10-11/REPORT01.md';ck(sha(read(accepted))==sel['baseline_accepted_review']['sha256']=='9c41681cf63bb49df02873061f11bf245dab4ad6e440cb7532e9bc887d296100','accepted31baseline')
base=js(O/'FRESH_GIT_RECOVERY31.json');ck(sha(read(O/'FRESH_GIT_RECOVERY31.json'))==sel['baseline_actual_recovery']['sha256']=='527f22e70b79a040928a56dea2d7dbccb127ef1d9cc615fe042a67780a889083','actual31lineage')
ck(base['source']==sel['baseline_source']=='cf4138dd4b902c1ec63bae7cf0116ad49da74be8','baseline source join')
bcapb=read(O/'CAPTURE31.json');ck(sha(bcapb)==base['capture']['sha256'],'baseline capture hash');bcap=json.loads(bcapb);bsb=read(O/'SELECTION31.json');ck(sha(bsb)==bcap['selection']['sha256'],'baseline selection hash');bs=json.loads(bsb);oldrows={r['path']:r for r in bs['rows']};reused=sel['exact_unchanged_prior_rows_reused']
ck(len(reused)==len(set(reused)) and not set(reused)&set(index) and set(reused)<=set(oldrows),'explicit disjoint reused rows')
for name in reused:
    row=oldrows[name];ck(allowed(name) and row['type']=='regular' and digest(R/name)==(row['bytes'],row['sha256']) and stat.S_IMODE((R/name).lstat().st_mode)==int(row['mode'],8),'actual current reused row',name)
ck(sel['prior_inherited_reuse_preserved_by_receipt']==bs['exact_unchanged_prior_rows_reused'] and sel['earlier_inherited_reuse_preserved_by_receipt']==bs['prior_inherited_reuse_preserved_by_receipt'],'exact inherited lineage')
excluded={str((O/n).relative_to(R)) for n in ('failed35-outcome-increment31.tar','fresh-git-recovered-full35outcome31.tar','actual_external_archive_blob_return.stdout')};ck(set(sel['exact_already_recovered_duplicate_exclusions'])==excluded and not excluded&set(index),'exact3exclusions')
for name in excluded:ck(digest(R/name)==(base['returned_archive']['bytes'],base['returned_archive']['sha256']),'actual excluded archive alias')
for row in sel['rows']:
    p=R/row['path'];s=p.lstat();ck(stat.S_IMODE(s.st_mode)==int(row['mode'],8) and s.st_nlink==1 and digest(p)==(row['bytes'],row['sha256']),'every frozen local body and mode',row['path'])
for row in sel['directories']:
    p=R/row['path'];ck(p.is_dir() and not p.is_symlink() and p.resolve()==p and stat.S_IMODE(p.stat().st_mode)==int(row['mode'],8),'every local directory mode',row['path'])
census=[];postcapture={}
postcapture_names={str((F/'real-data-pilot-full36-entry-preparation01-2026-10-11'/leaf).relative_to(R)) for leaf in ('ADMISSION01.json','ROOT_ADMISSION_OPERATIONS01.json')}
for scope_name in scope['public_roots']:
    root=F/scope_name;found={}
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
    ck(additions<=postcapture_names and all(found.get(k)==v for k,v in expected.items()),'complete frozen public scope plus exact later metadata',scope_name)
    for name in sorted(additions):
        read(R/name);postcapture[name]=refs[name]
    census.append(dict(root=scope_name,captured_or_reused_entries=len(expected),later_uncaptured_entries=len(additions)))
for path,pin in scope['changed_source_pins'].items():ck(path in index and index[path]['sha256']==pin,'all19sourcepinsreturned',path)
for leaf in scope['prior_generated_names']:
    name=str((O/leaf).relative_to(R));ck(name in index or name in reused or name in excluded,'all previous operation files accounted',leaf)
ck(set(postcapture)==postcapture_names,'exact later admission metadata exclusions')
ck(js(F/'real-data-pilot-full36-entry-preparation01-2026-10-11/ADMISSION01.json')==json.loads(js(F/'real-data-pilot-full36-entry-preparation01-2026-10-11/ROOT_ADMISSION_OPERATIONS01.json')['output']),'later admission raw result join')
out=dict(postcapture_unrecovered_evidence=postcapture,schema_version=1,decision='accepted',reviewer='Independent increment32 return and release reviewer',scope='Actual declared increment32 and authenticated31 lineage only. No whole runtime/POSIX/deletion/scientific authority or future availability promise.',source=SOURCE,archive=rec['returned_archive'],archive_git_blob_oid=rec['archive_git_blob_oid'],regular_files=289,directories=51,regular_bytes=3894966,symlinks=0,operation_count=13,reused_prior31_rows=len(reused),sole_opaque_body=private,scope_census=census,whole_PAX_reencoding_exact=True,category_checks=counts,evidence=refs,streamed_bytes=streamed,limitations=['No helper/Git/network execution or extraction; original raw operation evidence authenticated.','Opaque dispatch authenticated only as bytes; no decoding or referenced connection/credential target read.','Postcapture32 receipts and this return/release review remain later generated evidence, not falsely represented inside the captured32 tar.'])
with (P/'RETURN_REVIEW01.json').open('x') as h:json.dump(out,h,indent=2,sort_keys=True);h.write('\n')
print(json.dumps(dict(decision='accepted',checks=sum(counts.values()),sha256=sha((P/'RETURN_REVIEW01.json').read_bytes()))))
