"""Package the exact reviewed closed-pilot delta; no empirical execution."""
from pathlib import Path
import hashlib, io, json, os, subprocess, tarfile
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = '7aa1c0ca7e5df42113b29ea55d77b244859d131c'
COMMIT = '288363eae4fc1115aba2059a53846b6fd44f7e96'
env = dict(os.environ, GIT_NO_LAZY_FETCH='1')
def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, env=env, text=True).strip()
def main():
    if git('rev-parse','HEAD') != COMMIT: raise ValueError('checkpoint HEAD changed')
    if git('diff','--name-only','--diff-filter=D',BASE,COMMIT): raise ValueError('unexpected deletion')
    names = git('diff','--name-only',BASE,COMMIT).splitlines()
    allowed = ('research/onchain-paper-replication-2026-09-24/',
      'research_runs/eth-paper-resource-pilot-20260924-02/', 'docs/research/EVIDENCE_INDEX.md')
    if any(not name.startswith(allowed) or '..' in Path(name).parts for name in names):
        raise ValueError('unexpected delta path')
    archive = HERE/'preparation-snapshot-05-delta.tar.gz'
    members = {}; total = 0
    proc = subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,env=env,
        stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    try:
      with archive.open('xb') as output, tarfile.open(fileobj=output,mode='w:gz') as tar:
        for name in names:
          proc.stdin.write((COMMIT+':'+name+'\n').encode());proc.stdin.flush()
          header = proc.stdout.readline().decode().split()
          if len(header)!=3 or header[1]!='blob': raise ValueError('not a blob')
          size=int(header[2])
          if not 0<=size<=128*1024**2-total: raise ValueError('byte bound before allocation')
          body=proc.stdout.read(size)
          if len(body)!=size or proc.stdout.read(1)!=b'\n': raise ValueError('short Git body')
          total+=size
          info=tarfile.TarInfo(name);info.size=size;info.mode=0o644
          tar.addfile(info,io.BytesIO(body))
          members[name]={'bytes':size,'sha256':hashlib.sha256(body).hexdigest()}
      proc.stdin.close()
      if proc.wait()!=0: raise ValueError('Git reader failure')
    finally:
      if proc.poll() is None: proc.kill();proc.wait()
    manifest={'schema_version':1,'source_commit':COMMIT,'base_commit':BASE,
       'members':members,'member_count':len(members),'total_bytes':total,
       'archive':str(archive.relative_to(ROOT)),'archive_bytes':archive.stat().st_size,
       'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
       'scope':'exact closed-pilot checkpoint delta; prior independently recovered chain required; large graph/scratch/raw stores remain excluded'}
    with (HERE/'preparation-snapshot-05-delta.json').open('x') as stream:
        json.dump(manifest,stream,indent=2,sort_keys=True)
    print(json.dumps({k:v for k,v in manifest.items() if k!='members'}))
if __name__=='__main__':main()
