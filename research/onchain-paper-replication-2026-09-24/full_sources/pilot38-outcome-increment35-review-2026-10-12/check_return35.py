"""Actual increment35 finite return verification, no extraction or Git/network."""
import hashlib,json,os,stat,tarfile
from pathlib import Path,PurePosixPath
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';D=H/'full38outcome35';O=H/'full38increment34'
SOURCE='f0daad8bd480f4e28838424d0124480bff032af7';EXPECTED=(4730880,'2c5392aa8a63c5949f5de06a695318c9ba1347d7461425f3d51a602ed4247c3d');counts={};refs={};streamed=0
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
for leaf,pin in {'select35.py':'bf6d360914f6015e5310284616ae3af70d3b6d229624b0f7284ab4415eaffee6','capture35.py':'2e27046da8ca2e7389bd86cd91023570e44c1ad728f9d279332f6e872b097282','recover35.py':'e89e27a505147d8bb7bd31b9e700c804f68ebfb143315b1bf559ba4f377d0fa8'}.items():ck(digest(D/leaf)[1]==pin,'accepted helper source',leaf)
review_path=P/'SOURCE_REVIEW01.json';ck(sha(read(review_path))=='d0238bd828384044149d53d6edefad82b086238697c49684d3dffee7a424e691','accepted exact helper review')
sb=read(D/'SELECTION35.json');sel=json.loads(sb);cb=read(D/'CAPTURE35.json');cap=json.loads(cb);rec=js(D/'FRESH_GIT_RECOVERY35.json');ops=js(D/'GIT_OPERATIONS35.json');scope=js(D/'TOOL_SCOPE01.json')
ck(sha(sb)==cap['selection']['sha256'] and sha(cb)==rec['capture']['sha256'],'selection capture return hashes')
ck(cap['selection']['path']==str((D/'SELECTION35.json').relative_to(R)) and rec['capture']['path']==str((D/'CAPTURE35.json').relative_to(R)),'exact receipt paths')
ck(rec['source']==rec['actual_remote_head']==rec['actual_fetch_head']==SOURCE,'source remote fetched equality')
ck(cap['archive']['path']==str((D/'pilot38-outcome-increment35.tar').relative_to(R)) and rec['returned_archive']['path']==str((D/'fresh-git-recovered-full38outcome35.tar').relative_to(R)),'exact archive paths')
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
bare=Path(rec['fresh_bare']);ck(bare==R.parent/'onchain-pilot-recovery/real-pilot-outcome38-20261012-35.git' and bare.is_dir() and not bare.is_symlink() and not os.path.lexists(bare/'objects/info/alternates') and rec['no_alternates'] is True,'fresh bare metadata no alternates')
rows=sorted(sel['rows']+sel['directories'],key=lambda r:r['path']);index={r['path']:r for r in rows}
ck(len(rows)==len(index) and len(sel['rows'])==sel['files']==cap['files']==257 and len(sel['directories'])==cap['directories']==46,'complete257body46directorydenominator')
ck(sel['symlinks']==0 and all(r['type']=='regular' for r in sel['rows']) and sum(r['bytes'] for r in sel['rows'])==sel['body_bytes']==cap['regular_bytes']==4238841,'completebodytotals')
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
pins=scope['selected_pins'];ck(len(pins)==250 and len({p['path'] for p in pins})==250,'exact250metadata')
helpers=('select35.py','capture35.py','recover35.py','TOOL_SCOPE01.json','HELPERS_MANIFEST01.json','LITERAL_PATCH01.diff','LITERAL_INVERSE01.diff')
expected_names={p['path'] for p in pins}|{str((D/n).relative_to(R)) for n in helpers}
ck({r['path'] for r in sel['rows']}==expected_names,'fixed250plus7 complete scope')
for pin in pins:ck((index[pin['path']]['bytes'],index[pin['path']]['sha256'])==(pin['bytes'],pin['sha256']),'all fixed metadata pins returned',pin['path'])
manifest=js(D/'HELPERS_MANIFEST01.json')
for path,pin in manifest.items():ck(index[path]['sha256']==pin,'every manifest helper returned',path)
for row in sel['rows']:
 p=R/row['path'];s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==int(row['mode'],8) and digest(p)==(row['bytes'],row['sha256']),'all current selected original bytes modes',row['path'])
parent_paths=set()
for name in expected_names:
 parent=(R/name).parent
 while parent!=R:parent_paths.add(str(parent.relative_to(R)));parent=parent.parent
parent_paths.update(x['path'] for x in scope['closed_directory_roster'])
ck({r['path'] for r in sel['directories']}==parent_paths,'exact46parent and closed directories')
for row in sel['directories']:
 p=R/row['path'];ck(p.is_dir() and not p.is_symlink() and p.resolve()==p and stat.S_IMODE(p.stat().st_mode)==int(row['mode'],8),'actual directory mode',row['path'])

# Exact inherited34 receipts and accepted review, without replaying older archives.
for pin in scope['baseline']:
 ck(digest(R/pin['path'])==(pin['bytes'],pin['sha256']),'actual34 baseline pins',pin['path'])
ck(sel['baseline_actual_recovery']==scope['baseline'][0] and sel['baseline_accepted_review']==scope['baseline'][1],'selection baseline exact references')
base=js(R/scope['baseline'][0]['path']);ck(base['source']==sel['baseline_source'] and base['capture']['sha256']==scope['baseline'][2]['sha256'],'baseline source and capture')
ck(js(R/scope['baseline'][2]['path'])['selection']['sha256']==scope['baseline'][3]['sha256'],'baseline selection hash')
ck(scope['baseline'][1]['sha256']=='4808fc224d8edaa4f31a5c3df61d544031d01feef9e6b6f59ba1515dfa0a8104','genuine accepted34 review')
ck(sel['exact_prior33_34_rows_reused']==scope['exact_prior33_34_rows_reused'],'unchanged declared reuse')
# Source review already authenticated40 omitted rows. Recheck current exact pins only.
for pin in scope['exact_prior33_34_rows_reused']:
 ck(pin['path'] not in expected_names and digest(R/pin['path'])==(pin['bytes'],pin['sha256']) and stat.S_IMODE((R/pin['path']).stat().st_mode)==int(pin['mode'],8),'40 unchanged reused rows')
for x in scope['closed_directory_roster']:
 p=R/x['path'];ck(sorted(z.name for z in p.iterdir())==x['children'] and index[x['path']]['mode']==x['mode'],'closed original child roster',x['path'])
for pin in scope['opaque36_exact']:
 ck(all(index[pin['path']][k]==pin[k] for k in ('bytes','sha256','mode')),'exact opaque36 member only')
ck(len(scope['opaque36_exact'])==3 and len([p for p in expected_names if p.startswith('research_artifacts/archive-dispatch-ethpilot-20261011-36/')])==3,'exact three missing36 controls')
N='eth-paper-real-data-end-to-end-resource-20261012-38'
original='research_runs/'+N+'/failed.json'
outcome_path=str((F/'pilot38-preparation-outcome-review-2026-10-12/OUTCOME_REVIEW01.json').relative_to(R))
with tarfile.open(returned,'r:') as archive:
 failed=json.loads(archive.extractfile(original).read());outcome=json.loads(archive.extractfile(outcome_path).read())
 ck(failed['status']=='failed' and outcome['original_outer_status']=='failed' and outcome['original_outer_attempt_spent'] is True and outcome['component_qualification']['accepted'] is True,'returned genuine failed/component distinction')
 ck(outcome['original_reason']==failed['reason']=='EntryPreparationComplete: registered first-graph entry prepared; no MCM stage or financial fit completed','exact original preparation stop')
 for name,h in failed['output_sha256'].items():ck(index['research_runs/'+N+'/outputs/'+name]['sha256']==h,'all9 returned original output joins')
ck(index[outcome_path]['sha256']=='70010944ab8cfa0494f80d7034d3b88247411789d66b2864c2146267e324103b','accepted original38 outcome returned')
ck((bare/'FETCH_HEAD').read_text().split()[0]==SOURCE and 'bare = true' in (bare/'config').read_text(),'direct bare FETCH_HEAD/config')
ck(not any(p.startswith(str(P.relative_to(R))+'/') for p in expected_names),'current review excluded postcapture')
# Hash references use exact path->SHA values required by downstream binding checks.
for p in [D/'FRESH_GIT_RECOVERY35.json',D/'CAPTURE35.json',D/'SELECTION35.json',R/outcome_path,R/original]:read(p)
out={'schema_version':1,'decision':'accepted','reviewer':'Independent increment35 returned-scope reviewer /root/pilot_efficiency_integration_review','scope':'Actual declared original38 closed FAILED outcome/context and finite post34 preparation increment35, plus exact three missing36 controls and authenticated34 reuse. Component preparation qualification remains distinct from outer FAILED/spent.','source':SOURCE,'archive':rec['returned_archive'],'archive_git_blob_oid':rec['archive_git_blob_oid'],'regular_files':257,'directories':46,'regular_bytes':4238841,'symlinks':0,'operation_count':13,'fixed_metadata_files':250,'helper_files':7,'whole_PAX_reencoding_exact':True,'baseline34_return_review_sha256':scope['baseline'][1]['sha256'],'original38_outcome_sha256':index[outcome_path]['sha256'],'original38_outer_status':'failed','original38_component_preparation_qualification':True,'exact_missing36_opaque_files':3,'reused_prior_rows':40,'category_checks':counts,'evidence':{p:v['sha256'] for p,v in refs.items()},'evidence_metadata':refs,'streamed_bytes':streamed,'limitations':['No helper/Git/network execution, extraction, numerical/empirical rerun or new claim. Original13 raw operations and direct bare metadata authenticated.','Postcapture actual binder39, new entry candidate, this review and later operation receipts are outside this archive.','No unrelated stores, complete installed runtime, POSIX reconstruction, deletion, financial fit, whole39 capacity or empirical release accepted.','Opaque controls hashed as raw bodies only, never decoded and no referenced connection/credential target read.']}
with (P/'RETURN_REVIEW01.json').open('x') as h:json.dump(out,h,indent=2,sort_keys=True);h.write('\n')
print(json.dumps({'decision':'accepted','checks':sum(counts.values()),'return_review_sha256':sha((P/'RETURN_REVIEW01.json').read_bytes())}))
