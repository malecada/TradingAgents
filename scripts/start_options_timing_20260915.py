"""Exactly one independently reviewed claim and local release; no network capture."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tradingagents.research_options_timing import control,independent_verify
SOURCE='22bdf6c17398425e2a22855e88f9a501b4f2f3f4'
REPORT=ROOT/'research/strategy-search-2026-09-11/reviews/options-timing-actual-start-20260915.json'
if REPORT.exists() or (ROOT/'research_runs'/control.TARGET).exists():raise SystemExit('claim/report already exists; no repeat')
result={'source':SOURCE,'scope':'Exclusive local master claim and package preparation only; no market request or worker launch'}
try:
    remote=subprocess.check_output(['git','ls-remote','--heads','origin','research/strategy-search-2026-09-11'],cwd=ROOT,text=True,timeout=30).split()[0]
    assert remote==SOURCE;result['independently_observed_remote_head']=remote
    now=datetime.now(timezone.utc).isoformat()
    episode=control.Episode.start(root=ROOT,registration='research/strategy-search-2026-09-11/gates-options-timing.json',source=SOURCE,now_utc=now)
    result['claim_sha256']=episode.claim_hash;result['claimed_at']=now
    result['independent_protocol']=independent_verify.verify(root=ROOT,now_utc=datetime.now(timezone.utc).isoformat())
    spec=importlib.util.spec_from_file_location('timing_release',ROOT/'scripts/options_timing_release_package.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    result['release']=builder.build(root=ROOT,destination=Path('/home/malecada/master_thesis/research-deployment/options-timing-20260915/release-22bdf6c'),data_root='/opt/thesis-research/options-timing-20260915/data',host_identity='pck-preds-1',now_utc=datetime.now(timezone.utc).isoformat())
    prior,_=control.inventory(ROOT,control.TARGET,allow_active=True)
    grant=json.loads((ROOT/'research/strategy-search-2026-09-11/options-timing-grant-20260915.json').read_bytes())
    assert prior==grant['prior_claims'];result['prior20_unchanged']=True
    result['identities']={'total':21,'complete':16,'failed':4,'active':1};result['pass']=True
except Exception as exc:result.update(error=type(exc).__name__+': '+str(exc),pass_=False);result['pass']=False
with REPORT.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));raise SystemExit(0 if result['pass'] else 1)
