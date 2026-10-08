"""One returned tar body read; bounded offline Git metadata; no extraction."""
from pathlib import Path
import datetime, hashlib, io, json, os, stat, subprocess, tarfile
H=Path(__file__).resolve().parent; P=H.parent; R=H.parents[4]
CAP=P.parent/'real-data-pilot-sixteenth-resource-failed-increment01-2026-10-08'
ORIGINAL=CAP/'failed-increment01.tar'; RETURNED=CAP/'fresh-git-recovered-increment01.tar'
SOURCE='f791519f65619eee0b879dbf8fd0e43992a91965'
cache={}
def raw(p):
    assert p!=ORIGINAL
    if p not in cache:
        s=p.lstat(); assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4*1024**2
        b=p.read_bytes();z=p.lstat()
        assert len(b)==s.st_size and (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
        cache[p]=b
    return cache[p]
def ref(p): return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(raw(p)).hexdigest()}
def obj(p): return json.loads(raw(p))
def write(n,v):
    p=H/n
    with p.open('x') as f: json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
    return p
selection=obj(P/'INCREMENT_SELECTION01.json'); capture=obj(CAP/'CAPTURE01.json'); fresh=obj(CAP/'FRESH_GIT_RECOVERY01.json')
assert ref(P/'INCREMENT_SELECTION01.json')['sha256']=='9fdc7aec3bd8aff167e49ffb8e08dfae76101f3d3250f2bf87ace3e9ec1c517b'
assert {k:capture['selection'][k] for k in ('path','sha256')}==ref(P/'INCREMENT_SELECTION01.json')
assert selection['decision']=='accepted' and selection['regular_count']==32 and selection['directory_count']==9 and selection['original_regular_bytes']==419085
assert capture['archive']==fresh['archive'] and fresh['archive']['path']==str(ORIGINAL.relative_to(R))
assert fresh['source']==fresh['actual_remote_head']==SOURCE
assert fresh['regular_file_count']==capture['regular_file_count']==32 and fresh['directory_count']==capture['directory_count']==9
assert fresh['regular_bytes']==capture['regular_bytes']==419085 and fresh['typed_member_count']==capture['typed_member_count']==41
bare=Path(fresh['fresh_bare_repository']); assert bare==Path('/home/malecada/master_thesis/onchain-pilot-recovery/real-pilot-sixteenth-resource-failed-20261008-01.git') and bare.resolve(strict=True)==bare
assert not (bare/'objects/info/alternates').exists() and not (bare/'objects/info/http-alternates').exists()
remote='git@github.com:malecada/TradingAgents.git';branch='refs/heads/research/onchain-paper-replication-2026-09-24';prefix=['git','--git-dir='+str(bare)]
expected_ops=[['git','remote','get-url','origin'],['git','ls-remote',remote,branch],['git','init','--bare',str(bare)],prefix+['config','remote.origin.url',remote],prefix+['config','remote.origin.promisor','true'],prefix+['config','remote.origin.partialclonefilter','blob:none'],prefix+['fetch','--depth=1','--filter=blob:none','origin',branch],prefix+['rev-parse','FETCH_HEAD'],prefix+['cat-file','blob',SOURCE+':'+str(ORIGINAL.relative_to(R))]]
ops=fresh['operation_receipts']; assert fresh['operations']==len(ops)==9 and all(o['exit_code']==0 for o in ops) and [o['argv'] for o in ops]==expected_ops
env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
env.update(GIT_NO_LAZY_FETCH='1',GIT_NO_REPLACE_OBJECTS='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_TERMINAL_PROMPT='0')
checks=[]
def git(*args):
    result=subprocess.run(prefix+list(args),env=env,capture_output=True,check=True)
    checks.append({'args':list(args),'exit_code':0,'stdout':result.stdout.decode().strip()})
    return result.stdout.strip()
assert git('rev-parse','--is-bare-repository')==b'true'
assert git('rev-parse','FETCH_HEAD').decode()==SOURCE
assert git('config','--get','remote.origin.url').decode()==remote
assert git('config','--get','remote.origin.promisor')==b'true'
assert git('config','--get','remote.origin.partialclonefilter')==b'blob:none'
tree=git('ls-tree','-z',SOURCE,'--',str(ORIGINAL.relative_to(R))).rstrip(b'\0');header,path=tree.split(b'\t');mode,kind,oid=header.split()
assert kind==b'blob' and mode in (b'100644',b'100755') and path.decode()==str(ORIGINAL.relative_to(R))
assert git('cat-file','-t',oid.decode())==b'blob' and git('cat-file','-s',oid.decode())==b'481280'
b=raw(RETURNED)
assert fresh['returned_archive']['path']==str(RETURNED.relative_to(R)) and len(b)==fresh['returned_archive']['bytes']==fresh['archive']['bytes']==481280
assert hashlib.sha256(b).hexdigest()==fresh['returned_archive']['sha256']==fresh['archive']['sha256']=='4f93b6102a9b54792c6b551ab54fbbd7f0e520342fef118cd3f0f30e13721b15'
assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid.decode()
expected={v['path']:v for v in selection['files']+selection['directories']};assert len(expected)==41
members=[]
with tarfile.open(fileobj=io.BytesIO(b),mode='r:') as tf:
    seen=set()
    for m in tf.getmembers():
        name=m.name.rstrip('/');assert name in expected and name not in seen and not Path(name).is_absolute() and '..' not in Path(name).parts
        seen.add(name);v=expected[name];assert m.mode==v['mode']
        item={'path':name,'kind':v['kind'],'mode':m.mode}
        if v['kind']=='directory': assert m.isdir() and m.size==0
        else:
            assert m.isfile() and not m.issym() and not m.islnk() and m.size==v['bytes']
            with tf.extractfile(m) as stream: body=stream.read(m.size+1)
            digest=hashlib.sha256(body).hexdigest();assert len(body)==m.size and digest==v['sha256'];item.update(bytes=m.size,sha256=digest)
        members.append(item)
    assert seen==set(expected)
assert sum(x.get('bytes',0) for x in members)==419085
for v in selection['files']:
    p=R/v['path'];s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==v['nlink']==1
    assert stat.S_IMODE(s.st_mode)==v['mode'] and v['stat_identity']==[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
for v in selection['directories']:
    p=R/v['path'];s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISDIR(s.st_mode) and stat.S_IMODE(s.st_mode)==v['mode']
mp=write('RECOVERED_MEMBERS01.json',dict(schema_version=1,decision='accepted',source=SOURCE,returned_archive=ref(RETURNED),git_blob_oid=oid.decode(),regular_count=32,directory_count=9,total_names=41,regular_bytes=419085,members=members))
rp=write('RECOVERY_REVIEW01.json',dict(schema_version=1,decision='accepted',identity='eth-paper-real-data-end-to-end-resource-20261007-16',at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    recovery_source_commit=SOURCE,selection=ref(P/'INCREMENT_SELECTION01.json'),capture=ref(CAP/'CAPTURE01.json'),fresh_fetch_evidence=ref(CAP/'FRESH_GIT_RECOVERY01.json'),members_review=ref(mp),
    bare_repository=str(bare),current_alternates_absent=True,offline_git_checks=checks,git_lazy_fetch_disabled=True,
    archive=dict(returned_archive=ref(RETURNED),bytes=len(b),git_blob_oid=oid.decode(),regular_count=32,directory_count=9,typed_names=41,regular_bytes=419085,returned_archive_streams=1,original_archive_streams=0),
    original_selected_stat_identities_currently_unchanged=True,actual_external_recovery_accepted=True,originals_retained=True,returned_archive_retained=True,deletion_authorized=False,
    provenance_basis='Nine preserved successful Root operations show fresh bare initialization, promisor configuration, external fetch and actual lazy blob retrieval. Independent offline bare FETCH_HEAD/remote/promisor/tree/blob checks and returned body Git-object SHA1/SHA256 agree.',
    qualification='Only exact public failed16 BYTE recovery: names/types/modes/hashes, zero-byte logs and empty directories. Failed16 remains spent87. No POSIX owner/timestamp/xattr reconstruction, private transport/runtime/raw-store recovery, numerical execution or successor release.',
    not_tested=['No new external fetch or replay; historical external provenance depends on actual recorded operations, not offline state alone.','No original archive/evidence body reread, extraction, deletion or original scientific stores.','No performance/capacity/financial correctness, future remote availability or pilot17 admission.']))
manifest=write('MANIFEST01.json',dict(schema_version=1,decision='accepted',files=[ref(H/'review01.py'),ref(mp),ref(rp)]))
print(json.dumps({'decision':'accepted','review':ref(rp),'manifest':ref(manifest),'blob_oid':oid.decode()},sort_keys=True))
