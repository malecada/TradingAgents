"""Fresh remote recovery of complete neural04 failure evidence; never replay."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = HERE/'failure-remote-recovery04-01'
BRANCH = 'research/onchain-paper-replication-2026-09-24'
NAMES = ('retained-tree04.tar.gz','retained-tree04.json','execution-result04.json',
    'REVIEW_EXECUTION04.md','pid-closure-addendum04.json','admission02.json',
    'readiness02.json','launch-intent02.json','launch02.log','unit-journal04.txt',
    'kernel-journal04.txt','unit-properties04.txt','collect_execution04.py',
    'collect_execution04_02.py','collector04-generation01.log','gate.json',
    'source-manifest01.json','neural-plan.json','resource-amendment.json',
    'launch_once.py','readiness.py','execution-job.json','launch_scheduling.json',
    'CHARTER.md','recover_execution04_01.py')


def digest(raw): return hashlib.sha256(raw).hexdigest()


def invoke(command, cwd):
    result = subprocess.run(command,cwd=cwd,capture_output=True,timeout=60)
    if result.returncode or max(len(result.stdout),len(result.stderr)) > 4*1024**2:
        raise RuntimeError('bounded remote recovery command failed')
    return result.stdout


def main():
    resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
    assert shutil.disk_usage(ROOT).free >= 10*1024**3
    source = invoke(['git','rev-parse','HEAD'],ROOT).decode().strip()
    remote = invoke(['git','ls-remote','origin','refs/heads/'+BRANCH],ROOT).decode().split()[0]
    assert remote == source
    for name in NAMES:
        path = HERE/name; raw = path.read_bytes(); assert len(raw) <= 1024**2
        assert digest(raw) == digest(invoke(['git','show',source+':'+str(path.relative_to(ROOT))],ROOT))
    url = invoke(['git','remote','get-url','origin'],ROOT).decode().strip()
    OUT.mkdir(mode=0o700); repo = OUT/'repository.git'
    invoke(['git','init','--bare',str(repo)],ROOT)
    invoke(['git','remote','add','origin',url],repo)
    invoke(['git','config','remote.origin.promisor','true'],repo)
    invoke(['git','config','remote.origin.partialclonefilter','blob:none'],repo)
    invoke(['git','fetch','--depth=1','--filter=blob:none','origin',source],repo)
    assert invoke(['git','rev-parse','FETCH_HEAD'],repo).decode().strip() == source
    refs = {}
    for name in NAMES:
        relative = str((HERE/name).relative_to(ROOT))
        raw = invoke(['git','show',source+':'+relative],repo)
        assert len(raw) <= 1024**2 and digest(raw) == digest((HERE/name).read_bytes())
        with (OUT/name).open('xb') as output:
            output.write(raw); output.flush(); os.fsync(output.fileno())
        refs[relative] = {'bytes':len(raw),'sha256':digest(raw)}
    manifest = json.loads((OUT/'retained-tree04.json').read_bytes())
    rows = {}
    for row in manifest['members']:
        name = 'retained/'+row['role']+('' if row['path']=='.' else '/'+row['path'])
        assert name not in rows; rows[name] = row
    assert len(rows) == 32
    seen = set(); files = directories = body_bytes = 0
    with tarfile.open(OUT/'retained-tree04.tar.gz',mode='r|gz') as archive:
        for member in archive:
            assert member.name in rows and member.name not in seen
            seen.add(member.name); row=rows[member.name]; assert member.mode==row['mode']
            if row['type']=='directory': assert member.isdir(); directories+=1
            else:
                assert row['type']=='file' and member.isfile() and member.size==row['bytes']<=8*1024**2
                stream=archive.extractfile(member); assert stream is not None
                with stream: raw=stream.read(member.size+1)
                assert len(raw)==row['bytes'] and digest(raw)==row['sha256']
                files+=1; body_bytes+=len(raw); assert body_bytes<=128*1024**2
    assert seen==set(rows) and (files,directories,body_bytes)==(21,11,145567)
    result=json.loads((OUT/'execution-result04.json').read_bytes())
    additive=json.loads((OUT/'pid-closure-addendum04.json').read_bytes())
    assert result['status']=='closed_failed_kernel_oom_retained_review_pending'
    assert result['source']=='8631cbcce34cf827f0551dad04f6822ca8e1e1ec'
    assert additive['original_result_sha256']==digest((OUT/'execution-result04.json').read_bytes())
    report={'schema_version':1,'status':'fresh_remote_failed04_recovery_verified',
        'identity':'eth-paper-neural-resource-20261002-04','remote_source':source,
        'execution_source':result['source'],'verified_at_utc':datetime.now(timezone.utc).isoformat(),
        'retrieved_blob_count':len(refs),'retrieved_refs':refs,'files':files,
        'directories_including_each_root':directories,'members':len(seen),'symlinks':0,
        'regular_body_bytes':body_bytes,'original_allocated_bytes_including_directories':manifest['allocated_bytes_including_directories'],
        'qualification':'Fresh remote shallow partial bare fetch, then all25 selected closure/release/source blobs and all32 archived raw members verified without extraction, numerical import, deserialization or replay. Directory modes retained; original allocation is not recovery-media usage. Execution source8631 and failed nine-cell disposition remain unchanged. All249 production/source and109 input bodies are not separately recovered by this limited selected closure proof. This does not establish numerical capacity or financial completion.'}
    raw=(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n').encode(); assert len(raw)<1024**2
    with (HERE/'REMOTE_FAILURE_RECOVERY04_01.json').open('xb') as output:
        output.write(raw); output.flush(); os.fsync(output.fileno())
    print(json.dumps({'status':report['status'],'source':source,'blobs':len(refs),
        'members':len(seen),'regular_body_bytes':body_bytes}))


if __name__=='__main__': main()
