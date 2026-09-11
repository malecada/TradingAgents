"""Read-only actual closed-history verification, never admission or financial math."""
from pathlib import Path
import hashlib,json,sys,time
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from tradingagents.research_extended.verify import verify_run
name='dated-book-amended-20260911'
directory=ROOT/'research_runs'/name
start=time.monotonic()
claim=json.loads((directory/'claim.json').read_bytes())
certificate=json.loads((ROOT/claim['experiment']['budget_amendment']['path']).read_bytes())
inventory={key:{'claim_sha256':hashlib.sha256((ROOT/'research_runs'/key/'claim.json').read_bytes()).hexdigest(),'terminal':value['terminal'],'terminal_sha256':hashlib.sha256((ROOT/'research_runs'/key/value['terminal']).read_bytes()).hexdigest()} for key,value in certificate['prior_claims'].items()}
assert inventory==certificate['prior_claims']
result=verify_run(directory)
assert result['status']=='complete' and result['cell_count']==8
report={'passed':True,'scope':'Read-only existing claims, committed source and output byte hashes. No target admission, network, financial-value interpretation or economic rerun.','result':result,'historical_inventory':inventory,'certificate_sha256':hashlib.sha256((ROOT/claim['experiment']['budget_amendment']['path']).read_bytes()).hexdigest(),'snapshot_source_sha256':hashlib.sha256((ROOT/'tradingagents/research_extended/verify_v1_snapshot.py').read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-start}
with (Path(__file__).parent/'dated-v1-actual-snapshot-result.json').open('x') as out:json.dump(report,out,indent=2);out.write('\n')
print(json.dumps(report,indent=2))
