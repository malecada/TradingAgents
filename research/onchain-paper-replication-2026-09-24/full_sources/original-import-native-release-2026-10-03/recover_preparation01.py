"""Fresh remote recovery of frozen preparation bodies; no execution or replay."""
import hashlib,json,shutil,subprocess,time
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.cwd()
HERE=Path(__file__).resolve().parent
BRANCH='research/onchain-paper-replication-2026-09-24'
EXPECTED='6cd7acb281c393357aaa933e646c3e27d77ec0e9'

def call(args,cwd=ROOT):
    result=subprocess.run(['git',*args],cwd=cwd,capture_output=True,timeout=60)
    if result.returncode or max(len(result.stdout),len(result.stderr))>4*1024**2:
        raise RuntimeError('bounded recovery Git command failed')
    return result.stdout

def main():
    started=time.monotonic()
    assert shutil.disk_usage(ROOT).free>=10*1024**3
    assert call(['ls-remote','origin','refs/heads/'+BRANCH]).decode().split()[0]==EXPECTED
    paths=call(['diff-tree','--no-commit-id','--name-only','-r',EXPECTED]).decode().splitlines()
    inventory=json.loads((HERE.parent/'original-import-fixture-native-preparation03-2026-10-03/source_inventory03.json').read_bytes())
    paths=sorted(set(paths)|{row['origin'] for row in inventory['source_inventory']})
    expected={name:hashlib.sha256(call(['show',EXPECTED+':'+name])).hexdigest() for name in paths}
    out=HERE/'source-recovery01'
    out.mkdir(mode=0o700)
    repo=out/'repository.git'
    call(['init','--bare',str(repo)])
    call(['remote','add','origin',call(['remote','get-url','origin']).decode().strip()],repo)
    call(['config','remote.origin.promisor','true'],repo)
    call(['config','remote.origin.partialclonefilter','blob:none'],repo)
    call(['fetch','--depth=1','--filter=blob:none','origin',EXPECTED],repo)
    assert call(['rev-parse','FETCH_HEAD'],repo).decode().strip()==EXPECTED
    rows=[]
    for name,pin in expected.items():
        assert time.monotonic()-started<900
        raw=call(['show',EXPECTED+':'+name],repo)
        assert hashlib.sha256(raw).hexdigest()==pin
        rows.append({'path':name,'bytes':len(raw),'sha256':pin})
    receipt={'schema_version':1,'status':'fresh_remote_selected_source_recovery_verified',
        'remote_commit':EXPECTED,'fetched_commit':EXPECTED,'selected_bodies':rows,
        'body_count':len(rows),'body_bytes':sum(row['bytes'] for row in rows),
        'verified_utc':datetime.now(timezone.utc).isoformat(),
        'qualification':'Fresh independent shallow partial bare repository, all156 changed preparation/evidence bodies plus all153 selected-source origins joined against their actual remote Git bodies. No capsule Git/runtime/raw empirical store recovery, numerical import, claim, job or replay. Withheld source dispositions remain withheld.'}
    with (HERE/'REMOTE_PREPARATION_RECOVERY01.json').open('x') as stream:
        json.dump(receipt,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps({key:receipt[key] for key in ('status','remote_commit','body_count','body_bytes')}))

if __name__=='__main__':main()
