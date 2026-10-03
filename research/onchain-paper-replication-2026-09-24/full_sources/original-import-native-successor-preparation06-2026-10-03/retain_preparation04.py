"""Retain a complete prospective capsule; neither admission nor numerical work."""
import hashlib,json,shutil,stat,subprocess,tarfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;CAP=HERE/'capsule04'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    assert shutil.disk_usage(HERE).free>=10*1024**3
    draft=json.loads((HERE/'release-draft01.json').read_bytes());assert draft['status']=='prospective-NOT-released'
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=CAP,text=True,timeout=10).strip()==draft['capsule_commit']
    assert sha((CAP/draft['registration']).read_bytes())==draft['registration_sha256']
    for name,pin in draft['source_files'].items():assert sha((CAP/name).read_bytes())==pin
    rows=[];started=time.monotonic()
    for path in [CAP,*sorted(CAP.rglob('*'))]:
        assert time.monotonic()-started<60;info=path.lstat();assert path.resolve()==path and info.st_dev==CAP.stat().st_dev
        row={'path':str(path.relative_to(CAP)),'mode':stat.S_IMODE(info.st_mode),'allocated_bytes':info.st_blocks*512}
        if stat.S_ISREG(info.st_mode):
            assert info.st_nlink==1 and info.st_size<=4*1024**2;raw=path.read_bytes();row.update(kind='file',bytes=len(raw),sha256=sha(raw))
        else:assert stat.S_ISDIR(info.st_mode);row.update(kind='directory',bytes=0)
        rows.append(row)
    assert len(rows)<=32768 and sum(x['allocated_bytes'] for x in rows)<=128*1024**2
    archive=HERE/'capsule-source-input-gate01.tar.gz'
    with tarfile.open(archive,'x:gz') as stream:
        for row in rows:stream.add(CAP/row['path'],arcname='capsule04'+('' if row['path']=='.' else '/'+row['path']),recursive=False)
    assert archive.stat().st_size<=4*1024**2
    for row in rows:
        if row['kind']=='file':assert sha((CAP/row['path']).read_bytes())==row['sha256']
    record={'schema_version':1,'status':'complete_prospective_capsule_retained_not_released','capsule_head':draft['capsule_commit'],'source_anchor':draft['source_anchor'],
        'members':rows,'files':sum(x['kind']=='file' for x in rows),'directories':sum(x['kind']=='directory' for x in rows),
        'logical_bytes':sum(x['bytes'] for x in rows),'allocated_bytes':sum(x['allocated_bytes'] for x in rows),'archive_sha256':sha(archive.read_bytes()),'archive_bytes':archive.stat().st_size,
        'historical_closed_claims':3,'new_claims':0,'source_count':162,'package_count':142,
        'qualification':'Complete preparation source/input/gate/Git plus unchanged prior failed raw included; no installed shared runtime or other empirical stores. No new claim/job/execution release or remote recovery inferred.'}
    with (HERE/'CAPSULE_PREPARATION01.json').open('x') as stream:json.dump(record,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps({k:record[k] for k in ['capsule_head','files','directories','logical_bytes','allocated_bytes','archive_sha256','archive_bytes','new_claims']}))
if __name__=='__main__':main()
