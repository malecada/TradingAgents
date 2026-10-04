import datetime, hashlib, json, os, shutil, sys
from pathlib import Path
M = Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
B = M / 'research/onchain-paper-replication-2026-09-24/full_sources'
H = B / 'financial-genuine-wrapper-root-claimedrun-final-capture02-2026-10-04'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(H / 'capture02.py') == '31f8c7dfdc39fdbadd2149cd0c7d9d18e9d6b766841a7171629d6b5b01e47ab0'
assert sha(H / 'shards01.py') == '9c38c0893790c22e3b0142a8ab175dceb9b14dd0aeeb80edc206e5329ffcbbba'
assert sha(B / 'financial-genuine-wrapper-claimedrun-final-capture-review02-2026-10-04/MANIFEST01.json') == 'e2c313a07bb3051cd95d08931a626301b84c87e004425a33f8ef64e3a1ff5bc9'
assert not any(os.path.lexists(H / n) for n in ['INTENT01.json', 'union-bytes01', 'shards', 'shard-trees', 'SHARD_INDEX01.json', 'UNION_AUTHENTICATION01.json'])
assert shutil.disk_usage(H).free >= 10 * 1024**3
pid = os.getpid()
ticks = int(Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[19])
record = {'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'actual_root_pid': pid, 'actual_start_ticks': ticks, 'actual_pgid': os.getpgid(pid), 'actual_sid': os.getsid(pid), 'disk_free_before': shutil.disk_usage(H).free, 'source': sha(H / 'capture02.py'), 'planner': sha(H / 'shards01.py'), 'qualification': 'ONE fresh actual bounded opaque sharded capture. Original aggregatecapture01 remains terminal FAILED; no empirical job, numerical imports, Owner, Admission or ResearchRun.'}
with (H / 'INTENT01.json').open('x') as f:
    json.dump(record, f, sort_keys=True, indent=2); f.write('\n')
os.execv(sys.executable, [sys.executable, '-B', str(H / 'capture02.py')])
