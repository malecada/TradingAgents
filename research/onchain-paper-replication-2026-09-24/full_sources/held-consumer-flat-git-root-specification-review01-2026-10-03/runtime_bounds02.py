import ast,hashlib,json,platform,sys
from pathlib import Path
O=Path(__file__).resolve().parent;P=O.parent/'held-consumer-flat-git-recovery-preparation01-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest();sys.path.insert(0,str(P));import git_recovery01 as m
expected={'git_recovery01.py':'f0c7bab42387eb75d3f37b45f785de591090e12b49f0fed1e2c67d0c742dbc59','bounded_git_fd01.py':'4f997af0a6bdbe64e588241759ce596d751ee556357793af2f1c63cd0fdef87a','archive03.py':'785b957f93e22b18b1d3c00a73cacc75b6028bab9566d737b40903dcffc4964e','owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb'}
for name,h in expected.items():assert H((P/name).read_bytes())==h
assert platform.python_version()=='3.13.13' and sys.dont_write_bytecode and Path(sys.executable).absolute()==Path('/home/malecada/master_thesis/TradingAgents-audit-fixes/.venv/bin/python')
assert (m.MAX_CALLS,m.WALL,m.TOTAL,m.a.FILE,m.a.BASE,m.a.INFLATED,m.a.PAX,m.a.FLOOR)==(4096,300,134217728,4194304,134217728,201326592,8192,10737418240)
assert not any(n.split('.')[0] in {'numpy','torch','scipy'} for n in sys.modules)
f=Path(sys.executable).resolve();h=hashlib.sha256();n=0
with f.open('rb') as stream:
 while chunk:=stream.read(65536):n+=len(chunk);assert n<=64*1024**2;h.update(chunk)
r={'python':platform.python_version(),'requested_executable':sys.executable,'resolved_executable':str(f),'executable_bytes':n,'executable_sha256':h.hexdigest(),'source_hashes':expected,'finite_limits':{'calls':m.MAX_CALLS,'sampled_seconds':m.WALL,'store_logical_allocated_and_returned_bytes':m.TOTAL,'per_body_bytes':m.a.FILE,'inflated_archive_bytes':m.a.INFLATED,'pax_bytes':m.a.PAX,'disk_floor_bytes':m.a.FLOOR},'native_or_hard_quota_proof':False,'actual_recovered_git_proof':False};(O/'RUNTIME_BOUNDS02.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n');print(json.dumps(r,indent=2))
