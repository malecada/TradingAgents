"""Preserve the oomd-stopped continuation and append only its failed terminal."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,subprocess,os
from tradingagents.research import ResearchRun
from tradingagents.research.admission import admit
from tradingagents.research.lifecycle import _immutable
from tradingagents.research.verify import verify_claim,verify_run
HERE=Path(__file__).resolve().parent
ROOT=Path('/home/malecada/Data/onchain-research/TradingAgents-onchain-fullpanel-resume')
BASE=Path('research/onchain-graph-2026-09-16/fullpanel_resume')
EXPERIMENT='eth-full-history-feature-panel-resume-20260922'
SOURCE='c739b6f0958e23b90ff5038dd46c9356581369c3'
HASHROOT=Path('/home/malecada/master_thesis/onchain-fullpanel-resume-hash-scratch-20260922')
UNIT='onchain-resume-6c8905d1544d46efbf56c676221a8722.service'
REASON='systemd-oomd killed this continuation at2026-09-22T18:05:58UTC for user ancestor memory pressure52.41%>50%for>20seconds with reclaim. Recorded kernelOOM/max counters zero; memory.high events16136. All206seed days preserved; first newJuly26partial evidence retained. Append failure only, no replay. This finding does not determine the earlier reboot cause.'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def absent():
 props=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','--user','show',UNIT,'--property=MainPID,ActiveState,ControlGroup'],text=True).splitlines())
 assert props['MainPID']=='0' and props['ActiveState'] in ('inactive','failed') and props['ControlGroup']=='',props
 for p in Path('/proc').iterdir():
  if not p.name.isdigit() or int(p.name)==os.getpid():continue
  try:
   args=(p/'cmdline').read_bytes().split(b'\0')
   if any(x.decode(errors='replace').startswith(str(ROOT)) and x.endswith(b'.py') for x in args):raise ValueError('predecessor process remains')
  except (FileNotFoundError,PermissionError,ProcessLookupError):pass
 return props

def snapshot():
 run=ROOT/'research_runs'/EXPERIMENT
 paths=[run/'claim.json',*sorted((run/'outputs').iterdir())]
 paths += [ROOT/BASE/n for n in ('outer.log','hash-owner.json','launch-observation.json','admission-observation.json')]
 paths += [p for folder in [ROOT/BASE/'resources',ROOT/'research/onchain-graph-2026-09-16/fullpanel/artifacts'] for p in folder.rglob('*') if p.is_file()]
 assert not any(p.is_symlink() for p in paths)
 return {str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(paths)}

def prepare():
 props=absent();run=ROOT/'research_runs'/EXPERIMENT;c=verify_claim(run)
 assert c['source']==SOURCE and c['family']['attempt_budget']==15
 assert not (run/'failed.json').exists() and not (run/'complete.json').exists()
 assert list(HASHROOT.iterdir())==[]
 guard=json.loads((ROOT/BASE/'resources/compute/final.json').read_bytes())
 assert guard['phase']=='failed' and guard['cleanup_verified'] is True and guard['unit']==UNIT
 assert guard['memory_events']['oom']==guard['memory_events']['max']==0
 files=snapshot();assert len(list((run/'outputs').iterdir()))==206
 plan=json.loads((ROOT/BASE/'plan.json').read_bytes())
 for day in plan['seed_dates']:
  p=run/'outputs'/f'day-{day}.json';assert sha(p)==plan['seed_files'][f"research_runs/{plan['prior_run_id']}/outputs/{p.name}"]['sha256']
 journal=subprocess.check_output(['journalctl','-u','systemd-oomd','--since','2026-09-22 17:50:00 UTC','--until','2026-09-22 18:10:00 UTC','--no-pager'],text=True)
 assert UNIT in journal and '52.41%' in journal
 _immutable(HERE/'interruption-observation.json',dict(observed_at=datetime.now(timezone.utc).isoformat(),source=SOURCE,experiment=EXPERIMENT,original_files=files,empty_hash_root=str(HASHROOT),guard=guard,unit=props,oomd_journal=journal,earlier_reboot_cause='undetermined',new_completed_days=0,preservation_only=True))
 _immutable(HERE/'failure-closure-bindings.json',dict(script_sha256=sha(__file__),observation_sha256=sha(HERE/'interruption-observation.json'),reason=REASON))
 print(json.dumps(dict(prepared=True,files=len(files),bytes=sum(m['bytes'] for m in files.values()))))

def close():
 absent();binding=json.loads((HERE/'failure-closure-bindings.json').read_bytes());obs=json.loads((HERE/'interruption-observation.json').read_bytes())
 assert binding['script_sha256']==sha(__file__) and binding['observation_sha256']==sha(HERE/'interruption-observation.json')
 assert snapshot()==obs['original_files'] and list(HASHROOT.iterdir())==[]
 a=admit(root=ROOT,registration=str(BASE/'gates.json'),experiment=EXPERIMENT,source=SOURCE,_own_claim=EXPERIMENT)
 run=ResearchRun(a);run._claim_sha256=sha(run.directory/'claim.json');run._check_source();run._check_inputs();absent();run.fail(binding['reason'])
 assert snapshot()==obs['original_files'] and list(HASHROOT.iterdir())==[]
 result=verify_run(run.directory);assert result['status']=='failed'
 _immutable(HERE/'failure-closure.json',dict(closed_at=datetime.now(timezone.utc).isoformat(),source=SOURCE,verification=result,failed_sha256=sha(run.directory/'failed.json'),files_preserved=len(obs['original_files']),new_claim=False,replay=False,resource_outcome='systemd-oomd kill; recorded kernel OOM counters zero; child terminal snapshot unavailable'))
 print(json.dumps(result))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('operation',choices=['prepare','close']);args=p.parse_args();{'prepare':prepare,'close':close}[args.operation]()
