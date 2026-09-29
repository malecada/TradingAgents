"""One finite local relocation of four inactive failed-transport archives.

Preserve bytes and original readable paths. No source raw/graph/SQLite data or
historical receipt is changed. Invoke only under the documented fresh capacity,
closed-owner and independent-review conditions; never repeat this identity.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat

ROOT=Path.cwd()
BASE=ROOT/'research/onchain-paper-replication-2026-09-24/storage'
HERE=Path(__file__).resolve().parent
DEST=Path('/home/malecada/Data/onchain-research/preserved-failed-transports-2026-09-29-01')
FILES=[('raw-preservation-2026-09-25-03/bulk03','bundle.tar',536811520),
       ('raw-preservation-2026-09-25-04/bulk01','bundle.tar',536811520),
       ('raw-preservation-2026-09-25-04/bulk01','recovered.tar',212402176),
       ('raw-preservation-2026-09-25-03/bulk03','recovered.tar',482181120)]
FLOOR=20*1024**3


def sync_dir(p):
    fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def publish(p,value):
    with p.open('x') as f:
        json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    sync_dir(p.parent)


def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        while chunk:=f.read(1024**2):h.update(chunk)
    return h.hexdigest()


def identity(s):return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)


assert ROOT.resolve()==Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
assert not DEST.exists() and not (HERE/'relocation-intent.json').exists()
for relative,_,_ in FILES:
    terminal=json.loads((BASE/relative/'guard/final.json').read_bytes())
    assert terminal['phase']=='failed' and terminal['cleanup_verified']
    assert not Path(terminal['cgroup']).exists(), 'old owned cgroup still exists'
assert shutil.disk_usage(DEST.parent).free>=FLOOR+sum(n for _,_,n in FILES)+1024**2
DEST.mkdir();sync_dir(DEST.parent)
publish(HERE/'relocation-intent.json',{'destination':str(DEST),'files':FILES,
        'rule':'copy, fsync, hash-verify and preserve original paths as symlinks; no automatic retry'})
records=[]
for i,(relative,name,size) in enumerate(FILES):
    source=BASE/relative/'batch-0034'/name
    target=DEST/f'{i:02d}-{name}'
    link=source.with_name(source.name+'.relocation-link')
    assert not link.exists() and not link.is_symlink()
    fd=os.open(source,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as src:
        before=os.fstat(src.fileno())
        assert stat.S_ISREG(before.st_mode) and before.st_size==size
        h=hashlib.sha256()
        with target.open('xb') as dst:
            while chunk:=src.read(1024**2):
                h.update(chunk);dst.write(chunk)
            dst.flush();os.fsync(dst.fileno())
        os.chmod(target,stat.S_IMODE(before.st_mode))
        os.utime(target,ns=(before.st_atime_ns,before.st_mtime_ns))
        assert target.stat().st_size==size and digest(target)==h.hexdigest()
        assert identity(before)==identity(os.fstat(src.fileno()))==identity(source.lstat())
        sync_dir(DEST)
        record={'original_path':str(source),'destination':str(target),'bytes':size,
                'sha256':h.hexdigest(),'original_stat_identity':identity(before),
                'original_mode':stat.S_IMODE(before.st_mode)}
        publish(HERE/f'relocation-{i:02d}-verified-copy.json',record)
        os.symlink(target,link)
        # Keep the no-follow opened source alive until the verified destination
        # has durably replaced its path; interruption before this retains both.
        os.replace(link,source);sync_dir(source.parent)
        assert source.is_symlink() and source.resolve()==target and digest(source)==h.hexdigest()
        publish(HERE/f'relocation-{i:02d}-complete.json',record)
        records.append(record)
publish(HERE/'relocation-complete.json',{'files':records,'bytes':sum(r['bytes'] for r in records),
        'qualification':'Local byte-preserving relocation, not a new external backup; old path bytes and historical receipts preserved.'})
print(json.dumps({'files':len(records),'bytes':sum(r['bytes'] for r in records),'root_free':shutil.disk_usage(ROOT).free,'data_free':shutil.disk_usage(DEST).free}))
