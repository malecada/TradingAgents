"""Fresh bounded recovery of five closed engineering cases; no extraction or replay."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import tarfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
BASE=HERE.parent
OUT=HERE/'joint-remote-recovery01'
BRANCH='research/onchain-paper-replication-2026-09-24'
CASES=[
    ('diagnostic01',BASE/'neural-streamed-gat-diagnosis-2026-10-02',
     ('retained-tree01.tar.gz','retained-tree01.json','execution-result01.json','REVIEW_DIAGNOSTIC_EXECUTION01.md'),(10,5,0,15,175021,225280)),
    ('green02',BASE/'neural-streamed-gat-candidate-2026-10-02',
     ('green-retained-tree02.tar.gz','green-retained-tree02.json','green-execution-result02.json','REVIEW_GREEN_EXECUTION02.md'),(10,5,0,15,32406,81920)),
    ('cleanup01',BASE/'neural-streamed-gat-candidate-2026-10-02/cleanup-smoke-preparation01',
     ('retained-tree01.tar.gz','retained-tree01.json','execution-result01.json','REVIEW_CLEANUP_OWNER_EXECUTION01.md'),(11,4,0,15,17767,65536)),
    ('adapter01',HERE,
     ('retained-tree01.tar.gz','retained-tree01.json','execution-result01.json','REVIEW_ADAPTER_EXECUTION01.md','CLOSURE_RECEIPT_ADDENDUM01.json'),(135,42,3,180,72046,745472)),
    ('adapter02',HERE,
     ('retained-tree02.tar.gz','retained-tree02.json','execution-result02.json','REVIEW_ADAPTER_EXECUTION02.md'),(193,59,0,252,605418,1536000)),
]


def digest(raw):return hashlib.sha256(raw).hexdigest()


def invoke(args,cwd):
    result=subprocess.run(args,cwd=cwd,capture_output=True,timeout=60)
    if result.returncode or max(len(result.stdout),len(result.stderr))>4*1024**2:
        raise RuntimeError('bounded Git recovery failed')
    return result.stdout


def verify_archive(directory,names,expected):
    manifest=json.loads((directory/names[1]).read_bytes());rows={}
    for row in manifest['members']:
        name='retained/'+row['role']+('' if row['path']=='.' else '/'+row['path'])
        assert name not in rows;rows[name]=row
    assert len(rows)<=12000
    seen=set();files=directories=links=body_bytes=link_bytes=0
    with tarfile.open(directory/names[0],mode='r|gz') as archive:
        for member in archive:
            assert member.name in rows and member.name not in seen
            seen.add(member.name);row=rows[member.name];assert member.mode==row['mode']
            if row['type']=='directory':assert member.isdir();directories+=1
            elif row['type']=='symlink':
                assert member.issym() and member.linkname==row['link_target']
                raw=os.fsencode(member.linkname)
                assert len(raw)==row['link_bytes'] and digest(raw)==row['link_sha256']
                links+=1;link_bytes+=len(raw)
            else:
                assert row['type']=='file' and member.isfile() and member.size==row['bytes']<=4*1024**2
                stream=archive.extractfile(member);assert stream is not None
                with stream:raw=stream.read(member.size+1)
                assert len(raw)==row['bytes'] and digest(raw)==row['sha256']
                files+=1;body_bytes+=len(raw)
            assert body_bytes+link_bytes<=64*1024**2
    assert seen==set(rows)
    actual=(files,directories,links,len(seen),body_bytes,manifest['allocated_bytes_including_directories'])
    assert actual==expected
    assert files==manifest['files'] and directories==manifest['directories_including_each_root']
    assert links==manifest.get('symlinks',0) and len(seen)==manifest['entries_including_each_root']
    assert body_bytes==manifest['logical_bytes'] and link_bytes==manifest.get('logical_link_target_bytes',0)
    return {'files':files,'directories_including_each_root':directories,'symlinks':links,
            'members':len(seen),'regular_body_bytes':body_bytes,'symlink_target_bytes':link_bytes,
            'original_allocated_bytes_including_directories':actual[-1]}


def main():
    resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
    assert shutil.disk_usage(ROOT).free>=10*1024**3
    source=invoke(['git','rev-parse','HEAD'],ROOT).decode().strip()
    remote=invoke(['git','ls-remote','origin','refs/heads/'+BRANCH],ROOT).decode().split()[0]
    assert remote==source
    # Verify exact local committed bytes before creating the fresh recovery namespace.
    for _,original,names,_ in CASES:
        for name in names:
            raw=(original/name).read_bytes();assert len(raw)<=1024**2
            committed=invoke(['git','show',source+':'+str((original/name).relative_to(ROOT))],ROOT)
            assert digest(raw)==digest(committed)
    url=invoke(['git','remote','get-url','origin'],ROOT).decode().strip()
    OUT.mkdir(mode=0o700);repo=OUT/'repository.git'
    invoke(['git','init','--bare',str(repo)],ROOT)
    invoke(['git','remote','add','origin',url],repo)
    invoke(['git','config','remote.origin.promisor','true'],repo)
    invoke(['git','config','remote.origin.partialclonefilter','blob:none'],repo)
    invoke(['git','fetch','--depth=1','--filter=blob:none','origin',source],repo)
    assert invoke(['git','rev-parse','FETCH_HEAD'],repo).decode().strip()==source
    reports={}
    for identity,original,names,expected in CASES:
        directory=OUT/identity;directory.mkdir();refs={}
        for name in names:
            relative=str((original/name).relative_to(ROOT))
            raw=invoke(['git','show',source+':'+relative],repo)
            assert len(raw)<=1024**2 and digest(raw)==digest((original/name).read_bytes())
            with (directory/name).open('xb') as output:output.write(raw);output.flush();os.fsync(output.fileno())
            refs[relative]={'bytes':len(raw),'sha256':digest(raw)}
        reports[identity]={**verify_archive(directory,names,expected),'retrieved_refs':refs}
    report={'schema_version':1,'status':'fresh_remote_five_case_recovery_verified',
            'source':source,'verified_utc':datetime.now(timezone.utc).isoformat(),
            'retrieved_blob_count':sum(len(case['retrieved_refs']) for case in reports.values()),'cases':reports}
    # Explicit aggregate derived from verified members avoids handwritten count drift.
    report['aggregate']={key:sum(case[key] for case in reports.values()) for key in ('files','directories_including_each_root','symlinks','members','regular_body_bytes','symlink_target_bytes')}
    report['qualification']='Fresh partial bare Git fetch from actual remote, then21 exact selected blobs including independent reviews and adapter01 receipt correction. Every per-case file body/directory mode/symlink target string verified by streaming the complete archives without extraction, link following, numerical import or checkpoint deserialization. Allocation describes original host, not recovery media. Other outer refs/source/runtime pins are not all separately retrieved. Closed failed parent dispositions stay unchanged.'
    raw=(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n').encode();assert len(raw)<1024**2
    with (HERE/'JOINT_REMOTE_RECOVERY01.json').open('xb') as output:output.write(raw);output.flush();os.fsync(output.fileno())
    print(json.dumps({'source':source,'blobs':report['retrieved_blob_count'],'aggregate':report['aggregate']}))


if __name__=='__main__':main()
