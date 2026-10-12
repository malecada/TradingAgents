"""Actual increment34 finite return verification, no extraction or Git/network."""
import hashlib,json,os,stat,tarfile
from pathlib import Path,PurePosixPath
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';D=H/'full38increment34';O=H/'full38increment33'
SOURCE='0d4b1a9b294a4b0a484fbd2a1d7e27f8257738ec';EXPECTED=(2426880,'08bb1a7d3134926a292b64870467d7dcd8cb1c43c19cbbf892c346ea373ec65f');counts={};refs={};streamed=0
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
for leaf,pin in {'select34.py':'e45cec5f96dfd6cf667661341141be95a057572544948603e7e6c05d0e66ae66','capture34.py':'c88cadaf99f5219f3637723ae0e6370efd6b34f7c226cf755483f0caf8906c5c','recover34.py':'31b4d6e1afa13774fd386f176517743ed09028afbb470fd3a58c6b0d9c5f1bd3'}.items():ck(digest(D/leaf)[1]==pin,'accepted helper source',leaf)
review_path=F/'pilot38-increment34-tools-review-2026-10-12/SOURCE_REVIEW01.json';ck(sha(read(review_path))=='b447003b3c9662019e16d0a5f9e8a8b0cd42483058cd1f4a51888fac87779d33','accepted exact helper review')
sb=read(D/'SELECTION34.json');sel=json.loads(sb);cb=read(D/'CAPTURE34.json');cap=json.loads(cb);rec=js(D/'FRESH_GIT_RECOVERY34.json');ops=js(D/'GIT_OPERATIONS34.json');scope=js(D/'TOOL_SCOPE01.json')
ck(sha(sb)==cap['selection']['sha256'] and sha(cb)==rec['capture']['sha256'],'selection capture return hashes')
ck(cap['selection']['path']==str((D/'SELECTION34.json').relative_to(R)) and rec['capture']['path']==str((D/'CAPTURE34.json').relative_to(R)),'exact receipt paths')
ck(rec['source']==rec['actual_remote_head']==rec['actual_fetch_head']==SOURCE,'source remote fetched equality')
ck(cap['archive']['path']==str((D/'pilot38-preparation-increment34.tar').relative_to(R)) and rec['returned_archive']['path']==str((D/'fresh-git-recovered-full38increment34.tar').relative_to(R)),'exact archive paths')
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
bare=Path(rec['fresh_bare']);ck(bare==R.parent/'onchain-pilot-recovery/real-pilot-preparation38-20261012-34.git' and bare.is_dir() and not bare.is_symlink() and not os.path.lexists(bare/'objects/info/alternates') and rec['no_alternates'] is True,'fresh bare metadata no alternates')
rows=sorted(sel['rows']+sel['directories'],key=lambda r:r['path']);index={r['path']:r for r in rows}
ck(len(rows)==len(index) and len(sel['rows'])==sel['files']==cap['files']==74 and len(sel['directories'])==cap['directories']==9,'complete74body9directorydenominator')
ck(sel['symlinks']==0 and all(r['type']=='regular' for r in sel['rows']) and sum(r['bytes'] for r in sel['rows'])==sel['body_bytes']==cap['regular_bytes']==2282256,'completebodytotals')
def allowed(name):
    p=PurePosixPath(name)
    return not p.is_absolute() and '..' not in p.parts and not {'.git','.venv','node_modules','keys','apis'}&set(p.parts) and p.name not in ('.env','connection.json','hf_token.txt','id_ed25519_storagebox_u676273') and name.startswith('research/onchain-paper-replication-2026-09-24/full_sources/')
for row in rows:
    if row['type']!='directory':ck(allowed(row['path']),'exact public metadata only',row['path'])
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
# Fixed scope, no directory discovery or historical store recheck.
pins=scope['selected_pins'];ck(len(pins)==67 and len({p['path'] for p in pins})==67,'exact67metadata')
helpers=('select34.py','capture34.py','recover34.py','TOOL_SCOPE01.json','HELPERS_MANIFEST01.json','LITERAL_PATCH01.diff','LITERAL_INVERSE01.diff')
expected_names={p['path'] for p in pins}|{str((D/n).relative_to(R)) for n in helpers}
ck({r['path'] for r in sel['rows']}==expected_names,'fixed67plus7 complete scope')
for pin in pins:ck((index[pin['path']]['bytes'],index[pin['path']]['sha256'])==(pin['bytes'],pin['sha256']),'all fixed metadata pins returned',pin['path'])
manifest=js(D/'HELPERS_MANIFEST01.json')
for path,pin in manifest.items():ck(index[path]['sha256']==pin,'every manifest helper returned',path)
for row in sel['rows']:
 p=R/row['path'];s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==int(row['mode'],8) and digest(p)==(row['bytes'],row['sha256']),'all current selected original bytes modes',row['path'])
parent_paths=set()
for name in expected_names:
 parent=(R/name).parent
 while parent!=R:parent_paths.add(str(parent.relative_to(R)));parent=parent.parent
ck({r['path'] for r in sel['directories']}==parent_paths,'exact9parent directories only')
for row in sel['directories']:
 p=R/row['path'];ck(p.is_dir() and not p.is_symlink() and p.resolve()==p and stat.S_IMODE(p.stat().st_mode)==int(row['mode'],8),'actual directory mode',row['path'])
basebytes=read(O/'FRESH_GIT_RECOVERY33.json');base=json.loads(basebytes)
ck(sha(basebytes)==scope['baseline']['sha256']==sel['baseline_actual_recovery']['sha256']=='d122ab404607b2eb114157f87aef41619688b87db04a221af12b68a9cf4a599d','actual33baseline')
ck(base['source']==sel['baseline_source']=='d4064aace3d26f33a5708ea4c1665a156644de6f','parent source join')
oldreview=read(R/scope['accepted_return_review']['path']);ck(sha(oldreview)==sel['baseline_accepted_review']['sha256']=='ea801acb7276c98409a60b7018a38d7e6fc1e3bd16253bc4e4a501c56608d923','accepted33declaredscope baseline')
bcapb=read(O/'CAPTURE33.json');ck(sha(bcapb)==base['capture']['sha256'],'parent capture join');bcap=json.loads(bcapb)
bsb=read(O/'SELECTION33.json');ck(sha(bsb)==bcap['selection']['sha256'],'parent selection join');bs=json.loads(bsb);oldrows={r['path']:r for r in bs['rows']}
# Only explicit omitted metadata is rejoined; original36/opaque remains accepted33 evidence.
for name in scope['unchanged33_rows_omitted']:
 row=oldrows[name];p=R/name;ck(name not in expected_names and digest(p)==(row['bytes'],row['sha256']) and stat.S_IMODE(p.stat().st_mode)==int(row['mode'],8),'unchanged omitted33 metadata',name)
ck(not any(PurePosixPath(p).name in scope['excluded_duplicate_names'] for p in expected_names),'no archive duplicate recopy')
entry=F/'real-data-pilot-full38-entry-preparation01-2026-10-12'
gate=str((entry/'gate01.json').relative_to(R));generator=str((entry/'prepare_entry01.py').relative_to(R));cell=str((F/'pilot38-entry-registration-review-2026-10-12/CELL_CORRECTION_REVIEW01.json').relative_to(R))
ck(index[gate]['sha256']=='cd22da5d2d036b54e9f7d17af64d9d51e331e5e7b503d3123acc7c46e9de1489' and oldrows[gate]['sha256']!=index[gate]['sha256'],'corrected gate actually returned separate from old33')
ck(index[generator]['sha256']=='947b0ca2f511ff6ad1531343b126ac7437f833b9ad13a514708ba784a216865f','corrected generator returned')
ck(index[cell]['sha256']=='aeade665a2b41f0dbaf006100ae00fbaa636f4443676a24e86d7663796243a92','accepted cell correction returned')
with tarfile.open(returned,'r:') as archive:
 admission=json.loads(archive.extractfile(str((entry/'JOB_METADATA_ADMISSION02.json').relative_to(R))).read())
 result=json.loads(archive.extractfile(str((entry/'JOB_METADATA_ADMISSION02.stdout').relative_to(R))).read())
 for side,pin in admission['raw'].items():
  body=archive.extractfile(pin['path']).read();ck((len(body),sha(body))==(pin['bytes'],pin['sha256']),'returned admission02 raw joins',side)
ck(admission['source']=='4cb2d366ca3d210156c1f99d2d7b953355648eb1' and admission['exit_code']==0 and admission['claim'] is False and admission['native_launched'] is False,'returned bounded metadata check provenance')
ck(result=={'ready':True,'effective_attempt_budget':110,'source_pins':1036,'input_roles':73,'registered_cells':['real-eth-first-graph-entry-preparation-resource38'],'claim':False,'native_launched':False},'returned metadata-only ready110103673correctcell')
ck((bare/'FETCH_HEAD').read_text().split()[0]==SOURCE and 'bare = true' in (bare/'config').read_text(),'direct bare FETCH_HEAD and config')
ck(not any(PurePosixPath(p).name in {'STATE.md','COORDINATION.md','FINAL_BINDING01.json','RELEASE_REVIEW01.json','ROOT_ACTUAL_OPERATIONS34.json','ROOT_CAPTURE_OPERATIONS34.json'} for p in expected_names),'later navigation binding release and own postcapture excluded')
out={'schema_version':1,'decision':'accepted','reviewer':'Independent increment34 returned-scope reviewer','scope':'Actual fixed corrected38-registration increment34 byte/name/type/mode scope plus authenticated33 lineage only. No entry release, pilot qualification, installed-runtime completeness, POSIX reconstruction or deletion authority.','source':SOURCE,'archive':rec['returned_archive'],'archive_git_blob_oid':rec['archive_git_blob_oid'],'regular_files':74,'directories':9,'regular_bytes':2282256,'symlinks':0,'operation_count':13,'fixed_metadata_files':67,'helper_files':7,'whole_PAX_reencoding_exact':True,'baseline33_return_review_sha256':'ea801acb7276c98409a60b7018a38d7e6fc1e3bd16253bc4e4a501c56608d923','old33_gate_sha256':oldrows[gate]['sha256'],'corrected_gate_sha256':index[gate]['sha256'],'corrected_generator_sha256':index[generator]['sha256'],'cell_correction_review_sha256':index[cell]['sha256'],'actual_returned_admission02':result,'unchanged33_omitted_metadata':len(scope['unchanged33_rows_omitted']),'category_checks':counts,'evidence':refs,'streamed_bytes':streamed,'limitations':['No helper/Git/network execution, extraction, numerical or empirical launch. Original13 operation evidence and direct bare metadata authenticated.','Original36 outcome and old gate remain covered by accepted33; no original36/runtime/envelope recopy or reinterpretation.','Final binding/release and navigation/postcapture receipts remain outside this fixed archive; current release eligibility is not established.']}
with (P/'RETURN_REVIEW01.json').open('x') as h:json.dump(out,h,indent=2,sort_keys=True);h.write('\n')
print(json.dumps({'decision':'accepted','checks':sum(counts.values()),'return_review_sha256':sha((P/'RETURN_REVIEW01.json').read_bytes())}))
