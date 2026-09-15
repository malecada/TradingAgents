"""One inert synthetic upload/extract/recovery proof; no collector execution."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shlex,subprocess
ROOT=Path(__file__).resolve().parents[1]
LOCAL=Path('/home/malecada/master_thesis/research-deployment/options-timing-20260915/synthetic')
REMOTE='/opt/thesis-research/options-timing-20260915/synthetic-return-proof'
PYTHON='/opt/thesis-research/options-episode-20260911/runtime/cpython-3.13.13-linux-x86_64-gnu/bin/python3.13'
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','root@46.225.169.184']
SCP=['scp','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes']
REPORT=ROOT/'research/strategy-search-2026-09-11/reviews/options-timing-vps-roundtrip-20260915.json'
STEPS=REPORT.with_suffix('.steps.jsonl')
if REPORT.exists() or STEPS.exists():raise SystemExit('retained attempt exists')
def run(args,payload=None):
    r=subprocess.run(args,input=payload,text=True,capture_output=True,timeout=55)
    row={'at':datetime.now(timezone.utc).isoformat(),'command':args,'input_sha256':hashlib.sha256(payload.encode()).hexdigest() if payload else None,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
    with STEPS.open('a') as f:f.write(json.dumps(row)+'\n')
    if r.returncode:raise RuntimeError('external step failed; retained receipt')
    return r.stdout
def remote(code):return run(SSH+[shlex.join([PYTHON,'-I','-B','-'])],code)
report={'scope':'Inert invented engineering fixture VPS round-trip; no market requests, claim, actual data root or collector execution','pass':False,'remote':REMOTE}
try:
    setup="from pathlib import Path\np=Path("+repr(REMOTE)+")\nassert not p.exists() and not p.is_symlink()\nassert not p.parent.is_symlink()\np.parent.mkdir(exist_ok=True)\np.mkdir()\nprint('created sole inert proof directory')\n"
    remote(setup)
    names=['options-timing-synthetic-20260915.tar.gz','options-timing-synthetic-20260915.members.json']
    for name in names:run(SCP+[str(LOCAL/name),'root@46.225.169.184:'+REMOTE+'/'+name])
    code=r"""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import hashlib,json,os,stat,tarfile
root=Path('/opt/thesis-research/options-timing-20260915/synthetic-return-proof')
archive=root/'options-timing-synthetic-20260915.tar.gz'
manifest=root/'options-timing-synthetic-20260915.members.json'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='54f38f5c87ed3adfd9a4c64e03a59272b129e4ebed75fe2bf8dc0873803c18eb'
assert hashlib.sha256(manifest.read_bytes()).hexdigest()=='6d5d239116cf1065bbea41068e7feb8c6a8212827adf688cbb8a6bcde1cc17e0'
expected=json.loads(manifest.read_bytes());dest=root/'returned';dest.mkdir()
with tarfile.open(archive,'r:gz') as tf:
    members=tf.getmembers();assert len(members)==len(expected['members'])==38686
    assert len({m.name for m in members})==len(members)
    for m in members:
        path=PurePosixPath(m.name)
        assert m.isfile() and not path.is_absolute() and '..' not in path.parts and m.name in expected['members']
        assert m.size==expected['members'][m.name]['bytes']
    tf.extractall(dest,filter='data')
seen={}
for current,dirs,names in os.walk(dest,followlinks=False):
    for n in dirs:assert not (Path(current)/n).is_symlink()
    for n in names:
        p=Path(current)/n;assert stat.S_ISREG(p.lstat().st_mode)
        seen[p.relative_to(dest).as_posix()]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
assert seen==expected['members']
print(json.dumps({'checked_at':datetime.now(timezone.utc).isoformat(),'host':os.uname().nodename,'member_count':len(seen),'member_bytes':sum(x['bytes'] for x in seen.values()),'inventory_sha256':hashlib.sha256(json.dumps(seen,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'archive_sha256':expected['archive_sha256'],'assignment_sha256':expected['assignment_sha256'],'source_seal_sha256':expected['source_seal_sha256'],'all_remote_extracted_members_match':True,'collector_executed':False}))
"""
    report['remote_verification']=json.loads(remote(code))
    # Return the remote archive to a fresh local filename, then compare bytes.
    returned=LOCAL/'vps-returned-options-timing-synthetic-20260915.tar.gz'
    if returned.exists():raise ValueError('returned archive already exists')
    run(SCP+['root@46.225.169.184:'+REMOTE+'/'+names[0],str(returned)])
    report['returned_archive_sha256']=hashlib.sha256(returned.read_bytes()).hexdigest()
    report['local_returned_archive']=str(returned)
    report['pass']=report['returned_archive_sha256']==report['remote_verification']['archive_sha256']
except Exception as exc:report['error']=type(exc).__name__+': '+str(exc)
with REPORT.open('x') as f:f.write(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
raise SystemExit(0 if report['pass'] else 1)
