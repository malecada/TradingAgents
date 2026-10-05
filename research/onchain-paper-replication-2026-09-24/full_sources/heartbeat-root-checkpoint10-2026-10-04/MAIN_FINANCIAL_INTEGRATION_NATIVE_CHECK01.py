"""Finite existing offline regression subset inside one owned native test unit."""
import hashlib,json,os,resource,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent/'main-financial-integration-native-check01'
PIN=HERE/'SOURCE_PINS01.json'
TESTS=['tests/research/onchain_replication/test_training.py','tests/research/onchain_replication/test_checkpoint.py','tests/research/onchain_replication/test_replay.py','tests/research/onchain_replication/test_registry.py','tests/research/onchain_replication/test_evaluation.py','tests/research/onchain_replication/test_run.py']
assert sys.executable==str(ROOT/'.venv/bin/python')
assert os.sched_getaffinity(0)=={0,1}
assert resource.getrlimit(resource.RLIMIT_FSIZE)==(4194304,4194304)
mapping=json.loads(PIN.read_bytes())
for name,pin in mapping.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==pin,name
cg=next(line.split(':',2)[2] for line in Path('/proc/self/cgroup').read_text().splitlines() if line.startswith('0::'))
group=Path('/sys/fs/cgroup')/cg.lstrip('/')
controls={n:(group/n).read_text().strip() for n in ('memory.high','memory.max','memory.swap.max')}
assert controls=={'memory.high':'1073741824','memory.max':'1073741824','memory.swap.max':'0'}
available=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
assert available>=4*1024**3,'ordinary 1GiB test unit plus3GiB host reserve'
sys.path.insert(0,str(ROOT))
from scripts.verify_offline import offline_paths
assert set(TESTS)<=set(offline_paths())
print(json.dumps({'kind':'ordinary existing synthetic offline tests; no paper fit or empirical pilot','controls':controls,'fsize':list(resource.getrlimit(resource.RLIMIT_FSIZE)),'cpus':sorted(os.sched_getaffinity(0)),'cgroup':str(group),'sources_checked':len(mapping),'tests':TESTS}),flush=True)
import pytest
result=pytest.main(['-q','-p','no:cacheprovider','--import-mode=importlib','--basetemp',str(HERE/'test-output'),*TESTS])
for name,pin in mapping.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==pin,name
sys.exit(result)
