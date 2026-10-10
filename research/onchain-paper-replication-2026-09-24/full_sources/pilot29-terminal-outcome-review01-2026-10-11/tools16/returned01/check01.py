"""Independent actual returned-byte review; no subprocesses or helper execution."""
import datetime, hashlib, io, json, os, resource, stat, struct, tarfile
from pathlib import Path, PurePosixPath
resource.setrlimit(resource.RLIMIT_AS,(384*1024**2,384*1024**2))
resource.setrlimit(resource.RLIMIT_CPU,(30,30))
resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
P=Path(__file__).resolve().parent;Q=P.parent;T=Q.parent;F=T.parent;R=F.parents[2]
D=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/outcome16'
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
        n+=len(chunk);streamed+=len(chunk);assert n<=limit and streamed<192*1024**2;h.update(chunk)
    return n,h.hexdigest()
def digest(p,limit):
    p=Path(p);before=p.lstat();assert stat.S_ISREG(before.st_mode) and before.st_size<=limit
    with p.open('rb') as f:n,h=stream_digest(f,limit)
    after=p.lstat();assert all(getattr(before,k)==getattr(after,k) for k in ('st_dev','st_ino','st_size','st_mode','st_mtime_ns','st_ctime_ns'))
    refs[str(p.relative_to(R))]={'bytes':n,'sha256':h};return n,h
ck(sha(read(Q/'REVIEW01.json'))=='518b2120d4ab26b20efabd755f09fa4713f486f3968fd53903cfb9a0314a4604','frozen caller release')
ck(sha(read(Q/'MANIFEST01.json'))=='5e3de3914ad30a06ee4b1aa4ab677f355df265955395771e8c96a0b9110abee2','frozen source review manifest')
for name,row in js(Q/'MANIFEST01.json')['files'].items():ck({'bytes':len(b:=read(Q/name)),'sha256':sha(b)}==row,'frozen review member '+name)
manifest=js(D/'HELPERS_MANIFEST01.json');ck(sha(read(D/'HELPERS_MANIFEST01.json'))=='1e33236c7420c4346f4b026c257194c66f42c5a2ad7cdeec7ea66d4461fd1a0c','frozen helper manifest')
selb=read(D/'SELECTION16.json');sel=json.loads(selb);capb=read(D/'CAPTURE16.json');cap=json.loads(capb);rec=js(D/'FRESH_GIT_RECOVERY16.json')
ck(sha(selb)==cap['selection']['sha256']=='86473a6f3a5a824519e7d08153ef2e082409948d1e90dcab38b66ff1d535c959','selection capture hash join')
ck(sha(capb)==rec['capture']['sha256']=='52b63e2427d2ea52c1191e1c411800290a7ae2b629a93e62264333d6f94264ff','capture recovery hash join')
ck(cap['selection']['path']==str((D/'SELECTION16.json').relative_to(R)) and rec['capture']['path']==str((D/'CAPTURE16.json').relative_to(R)),'receipt paths')
ck(rec['source']==rec['actual_remote_head']==rec['actual_fetch_head']=='41b55367bd226c7292c1f4a802c200cc5cd1f841','actual source identities')
expected=(27217920,'aa118384a578c7e66c2080ce8f4ffb823b9db69e75fb309d5b41e64c7bb1e827')
for row in (cap['archive'],rec['returned_archive']):ck((row['bytes'],row['sha256'])==expected and digest(R/row['path'],32*1024**2)==expected,'actual complete archive byte/hash join')
ops=js(D/'GIT_OPERATIONS16.json');ck(ops==rec['operations'] and len(ops)==13,'all actual operation receipts')
expected_ops=['local_head','remote_get_url','remote_actual_branch_readback','local_archive_git_tree_join','fresh_bare_init','fresh_remote_add','set_promisor','set_tree_zero_filter','actual_external_commit_only_fetch','fetched_head_readback','actual_external_commit_body','actual_external_selected_blob_fetch','actual_external_archive_blob_return']
ck([x['operation'] for x in ops]==expected_ops,'exact operation sequence')
for op in ops:
    ck(op['exit_code']==0,'actual successful operation '+op['operation'])
    for suffix in ('stdout','stderr'):
        p=D/(op['operation']+'.'+suffix);ck(digest(p,32*1024**2)==(op[suffix+'_bytes'],op[suffix+'_sha256']),'actual raw operation output '+p.name)
ck(read(D/'local_head.stdout').decode().strip()==read(D/'fetched_head_readback.stdout').decode().strip()==rec['source'],'raw local/fetched source identities')
ck(read(D/'remote_actual_branch_readback.stdout').decode().strip()==rec['source']+'\trefs/heads/research/onchain-paper-replication-2026-09-24','raw remote branch source')
ck(read(D/'remote_get_url.stdout').decode().strip()==rec['actual_external_source']=='git@github.com:malecada/TradingAgents.git','raw remote identity')
ck(read(D/'local_archive_git_tree_join.stdout').decode().strip()==rec['local_commit_tree_join']==f"100644 blob {rec['archive_git_blob_oid']}\t{cap['archive']['path']}",'raw committed regular blob join')
commit=read(D/'actual_external_commit_body.stdout');ck(sha(commit)==rec['commit_body_sha256'] and hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest()==rec['source'],'independent commit object encoding')
returned=R/rec['returned_archive']['path'];blob=hashlib.sha1(b'blob '+str(expected[0]).encode()+b'\0')
with returned.open('rb') as f:
    while part:=f.read(65536):blob.update(part)
ck(blob.hexdigest()==rec['archive_git_blob_oid'],'independent archive blob object encoding')
bare=Path(rec['fresh_bare']);ck(bare==R.parent/'onchain-pilot-recovery/real-pilot-full29-outcome-20261011-16.git' and bare.is_dir() and not bare.is_symlink() and not os.path.lexists(bare/'objects/info/alternates') and rec['no_alternates'] is True,'actual exact bare path and absence of alternates (metadata only)')
rows=sorted(sel['rows']+sel['directories'],key=lambda r:r['path']);index={r['path']:r for r in rows}
ck(len(rows)==len(index)==1124 and len(sel['rows'])==sel['files']==cap['files']==1023 and len(sel['directories'])==cap['directories']==101,'complete member denominator')
ck(sum(r['type']=='regular' for r in rows)==1022 and sum(r['type']=='symlink' for r in rows)==sel['symlinks']==1 and sum(r.get('bytes',0) for r in rows)==sel['body_bytes']==cap['regular_bytes']==25241412,'typed/body denominator')
for key in ('original_alias_members','excluded_synthetic_git_subtrees'):ck(sel[key]==cap[key]==rec[key]==manifest[key],'exact metadata propagation '+key)
for r in rows:
    path=PurePosixPath(r['path']);ck(not path.is_absolute() and '..' not in path.parts and not ({'.git','.venv','node_modules','keys','apis'}&set(path.parts)),'safe relative public member '+r['path'])
    ck(not any(r['path']==p or r['path'].startswith(p+'/') for p in sel['excluded_synthetic_git_subtrees']),'finite excluded subtree absent')
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
            if '/matching/' in member.name or member.name.endswith('/stream/closure-tokens.bin') or member.name.endswith('/failed.json') or member.name==str((T/'REVIEW01.json').relative_to(R)) or member.name in manifest['original_alias_members']:
                ck(n<=1024**2,'bounded retained proof body');kept[member.name]=original.extractfile(member).read()
        typed.append({'path':member.name,'type':row['type'],'mode':row['mode'],'bytes':member.size})
ck((sink.size,sink.h.hexdigest())==expected,'independent whole PAX reencoding reproduces returned bytes')
for name,metadata in sel['original_alias_members'].items():
    row=index[name];ck(row['original_alias']==metadata and row['type']=='regular' and row['bytes']==14 and row['mode']=='0664' and sha(kept[name])==metadata['sha256'],'actual separate14B regular alias provenance')
baseline=js(R/sel['baseline_actual_recovery']['path']);ck(sha(read(R/sel['baseline_actual_recovery']['path']))==sel['baseline_actual_recovery']['sha256']=='4b78e2df7d12a414920f18e121712d7d6a0b26150204c69fb94b19de68fbff25','accepted14 receipt anchor')
oldcap=js(R/baseline['capture']['path']);ck(sha(read(R/baseline['capture']['path']))==baseline['capture']['sha256'],'accepted14 capture reference')
oldselb=read(R/oldcap['selection']['path']);ck(sha(oldselb)==oldcap['selection']['sha256'],'accepted14 selection reference');oldrows={r['path']:r for r in json.loads(oldselb)['rows']}
ck(baseline['source']==sel['baseline_source']=='f58540f5e55ca701bab4b20969a5b77ad43e5260','reused accepted14 source')
reused=sel['exact_unchanged_prior_rows_reused'];ck(len(reused)==len(set(reused))==51 and not set(reused)&set(index),'reused51 unique and disjoint')
for name in reused:
    row=oldrows[name];p=R/name;ck(row['type']=='regular' and stat.S_IMODE(p.lstat().st_mode)==int(row['mode'],8) and digest(p,64*1024**2)==(row['bytes'],row['sha256']),'actual unchanged accepted14 row '+name)
ck(set(sel['exact_already_recovered_duplicate_exclusions'])=={oldcap['archive']['path'],baseline['returned_archive']['path'],str((Path(sel['baseline_actual_recovery']['path']).parent/'actual_external_archive_blob_return.stdout'))} and not set(sel['exact_already_recovered_duplicate_exclusions'])&set(index),'three prior archive duplicates only (accepted14 scope reused)')
terminal=json.loads(kept[str((T/'REVIEW01.json').relative_to(R))]);ck(terminal['disposition']=='ACCEPT_ACTUAL_FAILED_TERMINAL_AND_BOUNDED_PARTIAL_PROGRESS','returned accepted terminal review')
for name,body in kept.items():
    if name.startswith('research_artifacts/onchain_representations/') and '/matching/' in name:
        ck(index[name]['sha256']==terminal['inventory'][name]['sha256'],'tail original evidence anchor '+name)
tailnames=sorted(n for n in kept if n.startswith('research_artifacts/onchain_representations/') and '/matching/' in n)
ck(len(tailnames)==12,'exact four-tail12 original members')
matching=tailnames[0].rsplit('/',1)[0];tokenname=matching.rsplit('/',1)[0]+'/stream/closure-tokens.bin';tokens=kept[tokenname]
ck(len(tokens)==52*3*56,'original closure token extent52')
for i in range(48,52):
    names=[matching+f'/{i:08d}'+suffix for suffix in ('.pending.json','.records.bin','.complete.json')];b=[kept[n] for n in names];pending=json.loads(b[0]);complete=json.loads(b[2])
    ck((pending['start'],pending['stop'])==(i*4096,(i+1)*4096) and complete['pending_sha256']==sha(b[0]) and complete['payload_sha256']==sha(b[1]) and complete['payload_bytes']==len(b[1])==92+4096*53,'actual returned tail closure '+str(i))
    for j,body in enumerate(b):
        dev,ino,size,h=struct.unpack_from('>QQQ32s',tokens,(i*3+j)*56);ck(size==len(body) and h.hex()==sha(body),'original tail token body join '+str(i)+'/'+str(j))
failedname='research_runs/eth-paper-real-data-end-to-end-resource-20261009-29/failed.json';failed=json.loads(kept[failedname])
ck(failed['status']=='failed' and sha(kept[failedname])==terminal['failed_sha256'] and failed['claim_sha256']==terminal['claim_sha256'],'actual returned failed claim evidence')
ck(not any(name in index for name in terminal['absent_terminal_paths']) and terminal['financial_fits']==0 and terminal['whole_mcm_graphs_completed']==0 and terminal['training_complete'] is False,'returned scope retains failure and no fabricated completion')
out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'decision':'ACCEPT_ACTUAL_OUTCOME16_DECLARED_PUBLIC_INCREMENT_RETURN','source':rec['source'],'archive':rec['returned_archive'],'archive_git_blob_oid':rec['archive_git_blob_oid'],'members':1124,'regular':1022,'symlinks':1,'directories':101,'regular_bytes':25241412,'reused_prior14_rows':51,'actual_tail_batches':[48,49,50,51],'actual_tail_cells':16384,'whole_pax_reencoding_exact':True,'no_alternates_metadata_verified':True,'checks':checks,'references':refs,'streamed_bytes_accounted':streamed,'source_review_unchanged':True,'limits':{'address_space_bytes':384*1024**2,'cpu_seconds':30,'per_output_bytes':4*1024**2,'streamed_read_cap_bytes':192*1024**2},'scope_limitations':['Public declared increment and authenticated accepted14 reuse only; three synthetic Git subtrees omitted.','Two aliases returned as separate regular bodies; original inode/nlink metadata only; no POSIX reconstruction or deletion authority.','Actual raw Git outputs authenticated; no new Git/network operation or remote freshness claim after recorded recovery.','Four tail batches preserved as opaque bodies with closure hashes; mathematical score correctness, arrays, scientific results, compiled04 qualification and financial claims not tested.','Original failed terminal review reused; no whole-MCM/training completion and no historical experiment rerun.']}
with (P/'REVIEW01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('checks','references','scope_limitations')},sort_keys=True));print('checks',len(checks))
