"""Actual increment36 finite return verification, no extraction or Git/network."""
import hashlib,json,os,stat,tarfile
from pathlib import Path,PurePosixPath
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';D=H/'full39entry36';O=H/'full38outcome35'
actual=json.loads((P/'ROOT_ACTUAL_EXPECTED01.json').read_bytes());SOURCE=actual['source'];EXPECTED=(actual['archive_bytes'],actual['archive_sha256']);counts={};refs={};streamed=0
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
for leaf,pin in {'select36.py':'e8cc5bf43b45aa054161369749ddf750af0b9e458f2e86bb9d5006dea4b191ad','capture36.py':'35f441a0fb0d0de19024c68b850521c01030890de24fec971a4ed486ba88f5d3','recover36.py':'69c3e375cbd0806cfe6b91498502faad228f37d103ba2c2dd0089b2dd0a638ec'}.items():ck(digest(D/leaf)[1]==pin,'accepted helper source',leaf)
review_path=P/'SOURCE_REVIEW01.json';ck(sha(read(review_path))=='3e0980427f6384a03bb5d226271eac25db9fcada49491206ad5e3393b61bbfc2','accepted exact helper review')
sb=read(D/'SELECTION36.json');sel=json.loads(sb);cb=read(D/'CAPTURE36.json');cap=json.loads(cb);rec=js(D/'FRESH_GIT_RECOVERY36.json');ops=js(D/'GIT_OPERATIONS36.json');scope=js(D/'TOOL_SCOPE01.json')
ck(sha(sb)==cap['selection']['sha256'] and sha(cb)==rec['capture']['sha256'],'selection capture return hashes')
ck(cap['selection']['path']==str((D/'SELECTION36.json').relative_to(R)) and rec['capture']['path']==str((D/'CAPTURE36.json').relative_to(R)),'exact receipt paths')
ck(rec['source']==rec['actual_remote_head']==rec['actual_fetch_head']==SOURCE,'source remote fetched equality')
ck(cap['archive']['path']==str((D/'pilot39-entry-increment36.tar').relative_to(R)) and rec['returned_archive']['path']==str((D/'fresh-git-recovered-full39entry36.tar').relative_to(R)),'exact archive paths')
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
bare=Path(rec['fresh_bare']);ck(bare==R.parent/'onchain-pilot-recovery/real-pilot-entry39-20261012-36.git' and bare.is_dir() and not bare.is_symlink() and not os.path.lexists(bare/'objects/info/alternates') and rec['no_alternates'] is True,'fresh bare metadata no alternates')
rows=sorted(sel['rows']+sel['directories'],key=lambda r:r['path']);index={r['path']:r for r in rows}
ck(len(rows)==len(index) and len(sel['rows'])==sel['files']==cap['files']==150 and len(sel['directories'])==cap['directories']==actual['directories'],'complete150bodycurrentdirectorydenominator')
ck(sel['symlinks']==0 and all(r['type']=='regular' for r in sel['rows']) and sum(r['bytes'] for r in sel['rows'])==sel['body_bytes']==cap['regular_bytes']==actual['regular_bytes'],'completebodytotals')
def allowed(name):
    p=PurePosixPath(name)
    return not p.is_absolute() and '..' not in p.parts and not {'.git','.venv','node_modules','keys','apis'}&set(p.parts) and p.name not in ('.env','connection.json','hf_token.txt','id_ed25519_storagebox_u676273')
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
pins=scope['selected_pins'];ck(len(pins)==143 and len({p['path'] for p in pins})==143,'exact143metadata')
helpers=('select36.py','capture36.py','recover36.py','TOOL_SCOPE01.json','HELPERS_MANIFEST01.json','LITERAL_PATCH01.diff','LITERAL_INVERSE01.diff')
expected_names={p['path'] for p in pins}|{str((D/n).relative_to(R)) for n in helpers}
ck({r['path'] for r in sel['rows']}==expected_names,'fixed143plus7 complete scope')
for pin in pins:ck((index[pin['path']]['bytes'],index[pin['path']]['sha256'])==(pin['bytes'],pin['sha256']),'all fixed metadata pins returned',pin['path'])
manifest=js(D/'HELPERS_MANIFEST01.json')
for path,pin in manifest.items():ck(index[path]['sha256']==pin,'every manifest helper returned',path)
for row in sel['rows']:
 p=R/row['path'];s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==int(row['mode'],8) and digest(p)==(row['bytes'],row['sha256']),'all current selected original bytes modes',row['path'])

parent_paths=set()
for name in expected_names:
 parent=(R/name).parent
 while parent!=R:parent_paths.add(str(parent.relative_to(R)));parent=parent.parent
ck({r['path'] for r in sel['directories']}==parent_paths,'exact parent directories')
for row in sel['directories']:
 p=R/row['path'];ck(p.is_dir() and not p.is_symlink() and p.resolve()==p and stat.S_IMODE(p.stat().st_mode)==int(row['mode'],8),'actual directory mode',row['path'])
for key in ('baseline','accepted_review'):
 pin=scope[key];ck(digest(R/pin['path'])==(pin['bytes'],pin['sha256']),'actual35 baseline reference',key)
ck(sel['baseline_actual_recovery']==scope['baseline'] and sel['baseline_accepted_review']==scope['accepted_review'],'selection exact prior35 joins')
base=js(R/scope['baseline']['path']);oldreview=js(R/scope['accepted_review']['path'])
ck(oldreview['decision']=='accepted' and oldreview['evidence'][scope['baseline']['path']]==scope['baseline']['sha256'],'accepted actual35 receipt joined')
ck(base['source']==sel['baseline_source'],'actual35 source join')
ck(sel['exact_unchanged_prior35_rows_reused']==scope['reused_pins'] and len(scope['reused_pins'])==23,'exact23 reuse')
for pin in scope['reused_pins']:ck(pin['path'] not in expected_names and digest(R/pin['path'])==(pin['bytes'],pin['sha256']) and stat.S_IMODE((R/pin['path']).stat().st_mode)==int(pin['mode'],8),'unchanged reused body',pin['path'])
ck(all(index[scope['opaque39']['path']][k]==scope['opaque39'][k] for k in ('bytes','sha256','mode')),'exact opaque39 body hash only')
ck((bare/'FETCH_HEAD').read_text().split()[0]==SOURCE and 'bare = true' in (bare/'config').read_text(),'direct bare FETCH_HEAD/config')
entry=F/'real-data-pilot-full39-entry-preparation01-2026-10-12'
with tarfile.open(returned,'r:') as archive:
 gate=json.loads(archive.extractfile(str((entry/'gate01.json').relative_to(R))).read());binding=json.loads(archive.extractfile(str((entry/'BINDING_DRAFT01.json').relative_to(R))).read())
 experiment=gate['experiments']['eth-paper-real-data-end-to-end-resource-20261012-39']
 ck(len(gate['experiments'])==16 and len(experiment['source_files'])==1142 and len(experiment['inputs'])==73,'returned actual39 Gate scope')
 ck(binding['status']=='DRAFT_NOT_RELEASED','returned binding remains draft')
ck(not any(p.startswith(str(P.relative_to(R))+'/') for p in expected_names),'current review excluded postcapture')
out={'schema_version':1,'decision':'accepted','scope':'Actual declared full39 draft entry increment36 only; inherited actual35 scope reused. Not final entry release or memory fit.','source':SOURCE,'archive':rec['returned_archive'],'archive_git_blob_oid':rec['archive_git_blob_oid'],'regular_files':150,'directories':len(sel['directories']),'regular_bytes':sel['body_bytes'],'symlinks':0,'operation_count':13,'fixed_metadata_files':143,'helper_files':7,'whole_PAX_reencoding_exact':True,'baseline35_return_review_sha256':scope['accepted_review']['sha256'],'reused_prior_rows':23,'gate_definitions':16,'gate_source_pins':1142,'input_roles':73,'opaque_decoded':False,'final_binding_release_recovered':False,'category_checks':counts,'evidence':{p:v['sha256'] for p,v in refs.items()},'evidence_metadata':refs,'streamed_bytes':streamed,'limitations':['No preservation helper/Git/network execution, extraction, numerical run or new claim. Original13 raw operations and direct bare metadata authenticated.','FinalBinding/release, current review and later receipts remain postcapture metadata outside archive.','No unrelated stores, installed runtime reconstruction, POSIX reconstruction, deletion authority, financial fit or whole memory fit accepted.','Opaque body hashed only; referenced credentials and connection targets never read.']}
with (P/'RETURN_REVIEW01.json').open('x') as h:json.dump(out,h,indent=2,sort_keys=True);h.write('\n')
print(json.dumps({'decision':'accepted','checks':sum(counts.values()),'return_review_sha256':sha((P/'RETURN_REVIEW01.json').read_bytes())}))
