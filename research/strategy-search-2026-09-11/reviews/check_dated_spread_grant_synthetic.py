"""Independent invented predecessor/cutoff attack; never uses a real ledger."""
from pathlib import Path
from datetime import datetime,timedelta
import hashlib,importlib.util,json,shutil,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
s=importlib.util.spec_from_file_location('grant_fixture_independent',ROOT/'tests/research/test_spread_lifecycle.py');fixture=importlib.util.module_from_spec(s);s.loader.exec_module(fixture)
from tradingagents.research.verify import verify_run as original
from tradingagents.research_spread.verify import verify_run as successor
results=[]
with tempfile.TemporaryDirectory(prefix='independent-grant-history-')as folder:
 root,spec,cert,commit=fixture.build_spread(Path(folder))
 base=root/'research_runs/original-a';intruder=root/'research_runs/unrun-baseline';shutil.copytree(base,intruder)
 claim=json.loads((intruder/'claim.json').read_bytes());oldspec=json.loads(subprocess.check_output(['git','show',claim['source']+':'+claim['registration']],cwd=root))
 claim['experiment_id']='unrun-baseline';claim['experiment']=oldspec['experiments']['unrun-baseline']
 parent=root/'research_runs/dated-mark-20260911';parent_claim=json.loads((parent/'claim.json').read_bytes());cutoff=datetime.fromisoformat(parent_claim['started_at'])
 for order,delta in [('prior',-1),('later',1)]:
  claim['started_at']=(cutoff+timedelta(seconds=delta)).isoformat();(intruder/'claim.json').write_text(json.dumps(claim))
  terminal=json.loads((intruder/'failed.json').read_bytes());terminal['experiment_id']='unrun-baseline';terminal['claim_sha256']=hashlib.sha256((intruder/'claim.json').read_bytes()).hexdigest();(intruder/'failed.json').write_text(json.dumps(terminal))
  assert original(intruder)['status']=='failed'
  try:successor(parent)
  except ValueError as error:snapshot={'rejected':True,'reason':str(error)}
  else:snapshot={'rejected':False}
  assert snapshot['rejected']==(order=='prior')
  try:fixture.start(root,commit)
  except ValueError as error:grant={'rejected':True,'reason':str(error)}
  else:raise AssertionError('extra current claim admitted by target grant')
  assert not (root/'research_runs'/fixture.TARGET).exists()
  results.append({'unbound_claim':order,'closed_v2_snapshot':snapshot,'current_full_inventory_grant':grant})
report={'passed':True,'cases':results,'scope':'One disposable invented Git history with an independently constructed structurally valid extra failed claim. No actual claim/source inputs, financial arithmetic or network. Historical later-claim exclusion is accepted only by the historical snapshot; complete current inventory still rejects it.','source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in (ROOT/'tradingagents/research_spread').glob('*.py')}}
(Path(__file__).parent/'dated-spread-grant-synthetic-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
