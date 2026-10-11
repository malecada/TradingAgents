"""Independent actual returned-byte review; no subprocesses or helper execution."""
import datetime, hashlib, io, json, os, resource, stat, tarfile, signal
from pathlib import Path, PurePosixPath
resource.setrlimit(resource.RLIMIT_AS,(384*1024**2,384*1024**2))
resource.setrlimit(resource.RLIMIT_CPU,(30,30))
resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2]
Q=F/'pilot-full30-preparation-increment-tools-review01-2026-10-11'
A=F/'pilot29-terminal-outcome-review01-2026-10-11/tools16/returned01'
D=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/full30increment18'
signal.alarm(45)
checks=[];refs={};streamed=0
def ck(ok,name):
    assert ok,name
    checks.append(name)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
    p=Path(p);s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<2*1024**2
    b=p.read_bytes();refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':sha(b)};return b
def js(p):return json.loads(read(p))
def stream_digest(stream,limit):
    global streamed
    h=hashlib.sha256();n=0
    while chunk:=stream.read(65536):
        n+=len(chunk);streamed+=len(chunk);assert n<=limit and streamed<384*1024**2;h.update(chunk)
    return n,h.hexdigest()
def digest(p,limit):
    p=Path(p);before=p.lstat();assert stat.S_ISREG(before.st_mode) and before.st_size<=limit
    with p.open('rb') as f:n,h=stream_digest(f,limit)
    after=p.lstat();assert all(getattr(before,k)==getattr(after,k) for k in ('st_dev','st_ino','st_size','st_mode','st_mtime_ns','st_ctime_ns'))
    refs[str(p.relative_to(R))]={'bytes':n,'sha256':h};return n,h
# EXPECTED_RETURN18 is written only after Root reports the actual completed return.
expected_observation=js(P/'EXPECTED_RETURN18.json')
ck(sha(read(R/expected_observation['actual_packet']['path']))==expected_observation['actual_packet']['sha256']=='972142f9a6e3f614a8df571338755175956715c10f33215e79586148712e8663','Root actual operation packet pin')
ck(sha(read(Q/'REVIEW01.json'))=='efb88d2e5d13d0a812a5c0ce8b2cac6ce25be44616e8dfafce3efeda99e313b2','frozen source/caller release18')
ck(sha(read(Q/'MANIFEST01.json'))=='13d35be3c5f2bf172d9c8d9fd9d37351d049bdecd41a23c3ed137ae9b5c50f1d','frozen source review manifest')
for name,row in js(Q/'MANIFEST01.json')['files'].items():ck({'bytes':len(b:=read(Q/name)),'sha256':sha(b)}==row,'frozen review member '+name)
ck(sha(read(A/'REVIEW01.json'))=='1d9e3fc85ac365fc91e1f21214cf2d20107bbe530b22a901af2ad3d12df62a1d','accepted actual16 baseline review')
accepted16=js(A/'REVIEW01.json')
manifest=js(D/'HELPERS_MANIFEST01.json');ck(sha(read(D/'HELPERS_MANIFEST01.json'))=='6b80e2e4b9eafa8cebbd9eb7092bbf4f7812a0af4af8e48e09eac58c4ce662f0','frozen helper18 manifest')
for name,row in manifest['files'].items():ck({'bytes':len(b:=read(D/name)),'sha256':sha(b)}==row,'frozen helper member '+name)
selb=read(D/'SELECTION18.json');sel=json.loads(selb);capb=read(D/'CAPTURE18.json');cap=json.loads(capb);rec=js(D/'FRESH_GIT_RECOVERY18.json')
ck(sha(selb)==cap['selection']['sha256']==expected_observation['selection_sha256'],'selection capture hash join')
ck(sha(capb)==rec['capture']['sha256']==expected_observation['capture_sha256'],'capture recovery hash join')
ck(sha(read(D/'FRESH_GIT_RECOVERY18.json'))==expected_observation['recovery_sha256'],'Root actual recovery receipt pin')
ck(cap['selection']['path']==str((D/'SELECTION18.json').relative_to(R)) and rec['capture']['path']==str((D/'CAPTURE18.json').relative_to(R)),'receipt paths')
ck(rec['source']==rec['actual_remote_head']==rec['actual_fetch_head']==expected_observation['source'],'actual source identities')
expected=(expected_observation['archive_bytes'],expected_observation['archive_sha256'])
ck(cap['archive']['path']==str((D/'full30-preparation-increment18.tar').relative_to(R)) and rec['returned_archive']['path']==str((D/'fresh-git-recovered-full30increment18.tar').relative_to(R)),'exact18 archive paths')
for row in (cap['archive'],rec['returned_archive']):ck((row['bytes'],row['sha256'])==expected and digest(R/row['path'],64*1024**2)==expected,'actual complete archive byte/hash join')
ops=js(D/'GIT_OPERATIONS18.json');ck(ops==rec['operations'] and len(ops)==13,'all actual operation receipts')
expected_ops=['local_head','remote_get_url','remote_actual_branch_readback','local_archive_git_tree_join','fresh_bare_init','fresh_remote_add','set_promisor','set_tree_zero_filter','actual_external_commit_only_fetch','fetched_head_readback','actual_external_commit_body','actual_external_selected_blob_fetch','actual_external_archive_blob_return']
ck([x['operation'] for x in ops]==expected_ops,'exact operation sequence')
for op in ops:
    ck(op['exit_code']==0,'actual successful operation '+op['operation'])
    for suffix in ('stdout','stderr'):
        p=D/(op['operation']+'.'+suffix);ck(digest(p,64*1024**2)==(op[suffix+'_bytes'],op[suffix+'_sha256']),'actual raw operation output '+p.name)
ck(read(D/'local_head.stdout').decode().strip()==read(D/'fetched_head_readback.stdout').decode().strip()==rec['source'],'raw local/fetched source identities')
ck(read(D/'remote_actual_branch_readback.stdout').decode().strip()==rec['source']+'\trefs/heads/research/onchain-paper-replication-2026-09-24','raw remote branch source')
ck(read(D/'remote_get_url.stdout').decode().strip()==rec['actual_external_source']=='git@github.com:malecada/TradingAgents.git','raw remote identity')
ck(read(D/'local_archive_git_tree_join.stdout').decode().strip()==rec['local_commit_tree_join']==f"100644 blob {rec['archive_git_blob_oid']}\t{cap['archive']['path']}",'raw committed regular blob join')
commit=read(D/'actual_external_commit_body.stdout');ck(sha(commit)==rec['commit_body_sha256'] and hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest()==rec['source'],'independent commit object encoding')
returned=R/rec['returned_archive']['path'];blob=hashlib.sha1(b'blob '+str(expected[0]).encode()+b'\0')
with returned.open('rb') as f:
    while part:=f.read(65536):blob.update(part)
ck(blob.hexdigest()==rec['archive_git_blob_oid'],'independent archive blob object encoding')
bare=Path(rec['fresh_bare']);ck(bare==R.parent/'onchain-pilot-recovery/real-pilot-full30-preparation-20261011-18.git' and bare.is_dir() and not bare.is_symlink() and not os.path.lexists(bare/'objects/info/alternates') and rec['no_alternates'] is True,'actual exact bare path and absence of alternates (metadata only)')
rows=sorted(sel['rows']+sel['directories'],key=lambda r:r['path']);index={r['path']:r for r in rows}
ck(len(rows)==len(index)==expected_observation['files']+expected_observation['directories'] and len(sel['rows'])==sel['files']==cap['files']==expected_observation['files'] and len(sel['directories'])==cap['directories']==expected_observation['directories'],'complete member denominator')
regular=sum(r['type']=='regular' for r in rows);symlinks=sum(r['type']=='symlink' for r in rows)
ck(regular+symlinks==sel['files'] and symlinks==sel['symlinks']==expected_observation['symlinks'] and sum(r.get('bytes',0) for r in rows)==sel['body_bytes']==cap['regular_bytes']==expected_observation['body_bytes'],'typed/body denominator')
def public(name):
    path=PurePosixPath(name)
    return not path.is_absolute() and '..' not in path.parts and not ({'.git','.venv','node_modules','keys','apis','research_artifacts','research_runs'}&set(path.parts)) and path.name not in ('.env','hf_token.txt','connection.json','id_ed25519_storagebox_u676273') and '/.onchain-private/' not in name
for row in rows:ck(public(row['path']),'safe selected public path '+row['path'])
ck(sel['actual_scope_states']==[],'no numerical/runtime/empirical source scopes')
class HashSink:
    def __init__(self):self.size=0;self.h=hashlib.sha256()
    def write(self,b):self.size+=len(b);self.h.update(b);return len(b)
    def tell(self):return self.size
    def flush(self):pass
sink=HashSink();kept={};typed=[]
with tarfile.open(returned,'r:') as original,tarfile.open(fileobj=sink,mode='w',format=tarfile.PAX_FORMAT) as reencoded:
    members=original.getmembers();ck(len(members)==len(rows),'actual archive exact member count')
    for member,row in zip(members,rows,strict=True):
        ck(member.name==row['path'] and member.mode==int(row['mode'],8),'actual ordered name/mode '+member.name)
        ck(member.uid==member.gid==member.mtime==0 and member.uname==member.gname=='','normalized archive owner/time')
        new=tarfile.TarInfo(row['path']);new.mode=int(row['mode'],8);new.uid=new.gid=new.mtime=0
        if row['type']=='directory':
            ck(member.type==tarfile.DIRTYPE and member.size==0,'actual directory');new.type=tarfile.DIRTYPE;reencoded.addfile(new)
        elif row['type']=='symlink':
            ck(member.type==tarfile.SYMTYPE and member.size==0 and member.linkname==row['linkname'],'actual symlink');new.type=tarfile.SYMTYPE;new.linkname=row['linkname'];reencoded.addfile(new)
        else:
            ck(member.type==tarfile.REGTYPE and member.size==row['bytes']<=64*1024**2,'actual regular type and size')
            n,h=stream_digest(original.extractfile(member),64*1024**2);ck((n,h)==(row['bytes'],row['sha256']),'actual regular body '+member.name)
            new.size=n;reencoded.addfile(new,original.extractfile(member))
            if member.name.endswith(('/PREFLIGHT_CHECK02.stdout','/PREFLIGHT_CHECK02.stderr','/ROOT_PREFLIGHT_OPERATION02.json')):
                ck(n<1024**2,'bounded preflight proof body');kept[member.name]=original.extractfile(member).read()
        typed.append({'path':member.name,'type':row['type'],'mode':row['mode'],'bytes':member.size})
ck((sink.size,sink.h.hexdigest())==expected,'independent whole PAX reencoding reproduces returned bytes')
baseline_path=R/sel['baseline_actual_recovery']['path']
ck(baseline_path==D.parent/'outcome16/FRESH_GIT_RECOVERY16.json' and sha(read(baseline_path))==sel['baseline_actual_recovery']['sha256']=='5c5e4f235febe41b37f81d742893032ac49d471439aaeb1a54234d57dc737559','accepted16 receipt anchor')
baseline=js(baseline_path);oldcap=js(R/baseline['capture']['path'])
ck(sha(read(R/baseline['capture']['path']))==baseline['capture']['sha256'],'accepted16 capture reference')
oldselb=read(R/oldcap['selection']['path']);ck(sha(oldselb)==oldcap['selection']['sha256'],'accepted16 selection reference')
oldsel=json.loads(oldselb);oldrows={r['path']:r for r in oldsel['rows']}
ck(baseline['source']==sel['baseline_source']==accepted16['source']=='41b55367bd226c7292c1f4a802c200cc5cd1f841','reused accepted16 source')
ck(baseline['returned_archive']==accepted16['archive'],'accepted16 archive continuity without historical body reread')
reused=sel['exact_unchanged_prior_rows_reused'];ck(len(reused)==len(set(reused))==expected_observation['reused'] and not set(reused)&set(index),'unique disjoint prior16 reuse denominator')
for name in reused:
    ck(public(name),'safe reused public metadata path '+name)
    row=oldrows[name];path=R/name
    ck(row['type']=='regular' and stat.S_IMODE(path.lstat().st_mode)==int(row['mode'],8) and digest(path,64*1024**2)==(row['bytes'],row['sha256']),'actual unchanged accepted16 public row '+name)
exclusions={oldcap['archive']['path'],baseline['returned_archive']['path'],str((baseline_path.parent/'actual_external_archive_blob_return.stdout').relative_to(R))}
ck(set(sel['exact_already_recovered_duplicate_exclusions'])==exclusions and len(exclusions)==3 and not exclusions&set(index),'three exact prior archive duplicate exclusions')
ck(not set(oldsel['original_alias_members'])&set(index) and not any(name==sub or name.startswith(sub+'/') for name in index for sub in oldsel['excluded_synthetic_git_subtrees']),'prior16 alias and synthetic Git fixtures not recopied')
required=manifest['owned']+expected_observation['additional_required_directories']
for directory in required:
    prefix=str((F/directory).relative_to(R))+'/'
    ck(any(name.startswith(prefix) for name in index),'required frozen preparation represented '+directory)
for name,row in manifest['files'].items():
    selected=index[str((D/name).relative_to(R))]
    ck(selected['type']=='regular' and selected['bytes']==row['bytes'] and selected['sha256']==row['sha256'],'returned frozen helper body '+name)
for pin in expected_observation['required_member_pins']:
    selected=index[pin['path']]
    ck(selected['type']=='regular' and selected['bytes']==pin['bytes'] and selected['sha256']==pin['sha256'],'actual final prerequisite member pin '+pin['path'])
entry=str((F/'real-data-pilot-full30-entry-preparation01-2026-10-11').relative_to(R))
preflight_raw=kept[entry+'/PREFLIGHT_CHECK02.stdout'];preflight=json.loads(preflight_raw);preflight_op=json.loads(kept[entry+'/ROOT_PREFLIGHT_OPERATION02.json'])
ck(preflight_op['actual_exit_code']==0 and preflight_op['stdout']=={'bytes':len(preflight_raw),'sha256':sha(preflight_raw)} and preflight_op['stderr']=={'bytes':len(kept[entry+'/PREFLIGHT_CHECK02.stderr']),'sha256':sha(kept[entry+'/PREFLIGHT_CHECK02.stderr'])},'returned actual preflight operation/raw output join')
ck(preflight_op['command']==['.venv/bin/python','-B',entry+'/preflight30_05.py'],'returned actual latest preflight05 command')
ck(preflight['source']=='7f11ecb850ee53fdf84e3ab9e2a8d6e089f023b0' and preflight['source_pins']==496 and preflight['compact_input_pins']==67 and preflight['effective_attempt_budget']==101,'returned preflight actual source/denominators (earlier source than preservation commit)')
ck(preflight['registration_sha256']==index[entry+'/gate03.json']['sha256'] and preflight['release_sha256']==index[entry+'/RELEASE_REVIEW03.json']['sha256'],'returned latest genuine preflight/gate/release identity join')
with (P/'TYPED_MEMBERS18.json').open('x') as f:json.dump(typed,f,indent=2,sort_keys=True);f.write('\n')
out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'decision':'ACCEPT_ACTUAL_INCREMENT18_DECLARED_PUBLIC_PREPARATION_RETURN','source':rec['source'],'archive':rec['returned_archive'],'archive_git_blob_oid':rec['archive_git_blob_oid'],'members':len(rows),'regular':regular,'symlinks':symlinks,'directories':len(sel['directories']),'regular_bytes':sel['body_bytes'],'reused_prior16_rows':len(reused),'whole_pax_reencoding_exact':True,'no_alternates_metadata_verified':True,'checks':checks,'references':refs,'streamed_bytes_accounted':streamed,'source_review_unchanged':True,'scope_limitations':['Only declared public increment18 with authenticated actual16 reference reuse; no entire worktree/private/runtime/scientific-store completeness.','No prior16 raw/alias bodies reread; prior exact accepted review reused.','Actual retained13 Git-operation outputs authenticated; no new Git/network operation or subsequent remote freshness claim.','No POSIX reconstruction/deletion authority or original hardlink recreation.','No financial/native/scientific/authority execution or full30 launch/admission release.']}
with (P/'REVIEW01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('checks','references','scope_limitations')},sort_keys=True));print('checks',len(checks))
