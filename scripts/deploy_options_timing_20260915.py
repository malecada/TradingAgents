"""Transfer and verify only the reviewed raw release; does not launch it."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,shlex,subprocess
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'research/strategy-search-2026-09-11';R='/opt/thesis-research/options-timing-20260915';P='/opt/thesis-research/options-episode-20260911/runtime/cpython-3.13.13-linux-x86_64-gnu/bin/python3.13'
REPORT=B/'reviews/options-timing-actual-deployment-20260915.json';STEPS=REPORT.with_suffix('.steps.jsonl')
if REPORT.exists() or STEPS.exists():raise SystemExit('retained deployment attempt exists')
release=json.loads((B/'reviews/options-timing-actual-release-20260915-v2.json').read_bytes())
opts=['-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes']
result={'scope':'Exact approved research-only release transfer and verification; no collector launch, market requests or production edits','pass':False}
def call(args,code=None):
    r=subprocess.run(args,input=code,text=True,capture_output=True,timeout=55)
    with STEPS.open('a') as f:f.write(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'command':args,'input_sha256':hashlib.sha256(code.encode()).hexdigest() if code else None,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})+'\n')
    if r.returncode:raise RuntimeError('external step failed; see immutable receipt')
    return r.stdout
def remote(code):return call(['ssh',*opts,'root@46.225.169.184',shlex.join([P,'-I','-B','-'])],code)
try:
    code="from pathlib import Path\nr=Path("+repr(R)+")\nassert r.is_dir() and not r.is_symlink()\nassert not (r/'data').exists() and not (r/'data').is_symlink()\nassert not (r/'release-22bdf6c').exists()\nassert not (r/'launch-options-timing-20260915-v2.sh').exists()\n(r/'release-staging').mkdir()\nprint('reserved isolated release staging; actual data absent')\n"
    remote(code)
    archive=Path(release['local_archive']);launcher=ROOT/release['launcher']['path']
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==release['archive_sha256']
    assert hashlib.sha256(launcher.read_bytes()).hexdigest()==release['launcher']['sha256']
    call(['scp',*opts,str(archive),'root@46.225.169.184:'+R+'/release-staging/'+archive.name])
    call(['scp',*opts,str(launcher),'root@46.225.169.184:'+R+'/'+launcher.name])
    code="expected="+repr(release)+"\n"+r"""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import hashlib,json,os,stat,tarfile
r=Path('/opt/thesis-research/options-timing-20260915');archive=r/'release-staging/release-22bdf6c.tar.gz';launcher=r/'launch-options-timing-20260915-v2.sh'
assert hashlib.sha256(archive.read_bytes()).hexdigest()==expected['archive_sha256']
assert hashlib.sha256(launcher.read_bytes()).hexdigest()==expected['launcher']['sha256']
dest=r/'release-22bdf6c';dest.mkdir()
with tarfile.open(archive,'r:gz') as tf:
    members=tf.getmembers();assert len(members)==len(expected['members'])==10
    assert {m.name for m in members}==set(expected['members'])
    for m in members:
        p=PurePosixPath(m.name);assert m.isfile() and not p.is_absolute() and '..' not in p.parts and m.size==expected['members'][m.name]['bytes']
        body=tf.extractfile(m).read();assert hashlib.sha256(body).hexdigest()==expected['members'][m.name]['sha256']
        target=dest/m.name;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(body)
        target.chmod(0o444)
seen={}
for p in dest.rglob('*'):
    assert not p.is_symlink()
    if p.is_dir():continue
    assert stat.S_ISREG(p.lstat().st_mode);seen[p.relative_to(dest).as_posix()]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
assert seen==expected['members']
st=os.statvfs(r);assert st.f_bavail*st.f_frsize>=8*1024**3 and st.f_favail>=1200258 and st.f_frsize<=4096
assert not os.path.lexists(r/'data') and not os.path.lexists(r/'launch-options-timing-20260915.log')
print(json.dumps({'checked_at':datetime.now(timezone.utc).isoformat(),'host':os.uname().nodename,'members':seen,'all_members_equal':True,'launcher_sha256':hashlib.sha256(launcher.read_bytes()).hexdigest(),'data_root_absent':True,'launch_log_absent':True,'free_bytes':st.f_bavail*st.f_frsize,'free_inodes':st.f_favail,'allocation_unit':st.f_frsize,'worker_launched':False},sort_keys=True))
"""
    result['remote_release']=json.loads(remote(code))
    runtime='/opt/thesis-research/options-episode-20260911/runtime/cpython-3.13.13-linux-x86_64-gnu'
    code="import sys\nsys.argv=['-',"+repr(runtime)+"]\n"+(ROOT/'scripts/options_runtime_fingerprint.py').read_text()
    result['runtime']=json.loads(remote(code))
    assert result['runtime']['inventory_sha256']=='cb70f90810dd532e244f23c37c8b2ba2e4ac2da3485ad69cb84b00ff2abeb5df'
    assert result['remote_release']['host']=='pck-preds-1';result['pass']=True
except Exception as exc:result['error']=type(exc).__name__+': '+str(exc)
with REPORT.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='remote_release'},indent=2));raise SystemExit(0 if result['pass'] else 1)
