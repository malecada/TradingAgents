"""Append failure-only terminal after immutable reboot preservation; no replay."""
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from tradingagents.research import ResearchRun
from tradingagents.research.admission import admit
from tradingagents.research.lifecycle import _immutable
from tradingagents.research.verify import verify_claim, verify_run

HERE=Path(__file__).resolve().parent
ROOT=Path('/home/malecada/Data/onchain-research/TradingAgents-onchain-fullpanel')
BASE=Path('research/onchain-graph-2026-09-16/fullpanel')
EXPERIMENT='eth-full-history-feature-panel-20260922'
SOURCE='fdb33cf27ca97b8d32926f046be422d8b8b45b6f'
HASHROOT=Path('/home/malecada/master_thesis/onchain-fullpanel-hash-scratch-20260922')
REASON='User reported shared-host OOM followed by reboot. Cause and responsible process are undetermined. Original executor is absent, resource receipt empty, no terminal. Preserve206published source days/205graph days and partialJuly26evidence; append failure only, never replay original claim.'

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def absent():
    targets={str(ROOT/BASE/n) for n in ('launch.py','run.py','day.py','check_day.py')}
    for p in Path('/proc').iterdir():
        if not p.name.isdigit() or int(p.name)==os.getpid():continue
        try:
            if (p/'cwd').resolve()!=ROOT:continue
            if any(x.decode(errors='replace') in targets for x in (p/'cmdline').read_bytes().split(b'\0')):raise ValueError('old worker remains live')
        except (FileNotFoundError,PermissionError,ProcessLookupError):pass

def snapshot():
    run=ROOT/'research_runs'/EXPERIMENT
    paths=[run/'claim.json',*sorted((run/'outputs').iterdir())]
    paths += [ROOT/BASE/n for n in ('resource.json','compute.log','hash-owner.json','launch-observation.json','admission-observation.json')]
    paths += [p for folder in ('artifacts','sparse-scratch') for p in (ROOT/BASE/folder).rglob('*') if p.is_file()]
    if any(p.is_symlink() for p in paths):raise ValueError('evidence symlink')
    return {str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(paths)}

def hash_snapshot():
    if any(p.is_symlink() or not p.is_file() for p in HASHROOT.iterdir()):raise ValueError('hashroot partial lock or unexpected path')
    return {p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(HASHROOT.iterdir())}

def prepare():
    absent();run=ROOT/'research_runs'/EXPERIMENT
    assert not (run/'complete.json').exists() and not (run/'failed.json').exists()
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==SOURCE
    c=verify_claim(run);assert c['source']==SOURCE and c['family']['attempt_budget']==14
    files=snapshot();assert len(list((run/'outputs').iterdir()))==206 and (ROOT/BASE/'resource.json').stat().st_size==0
    obs=json.loads((ROOT/BASE/'launch-observation.json').read_bytes());boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();assert obs['boot_id']!=boot
    hashes=hash_snapshot();assert 'append.lock' not in hashes
    _immutable(HERE/'interruption-observation.json',dict(observed_at=datetime.now(timezone.utc).isoformat(),old_boot=obs['boot_id'],current_boot=boot,user_report='OOM occurred with other processes also running; restart requested. Responsible process and exact cause undetermined.',kernel_prior_boot_oom_query='No entries',original_resource_bytes=0,peak_rss=None,child_exit_code=None,signal=None,original_files=files,hash_root=str(HASHROOT),hash_files=hashes,preservation_only=True))
    _immutable(HERE/'failure-closure-bindings.json',dict(source=SOURCE,experiment=EXPERIMENT,closure_script_sha256=sha(__file__),observation_sha256=sha(HERE/'interruption-observation.json'),failure_reason=REASON))
    print(json.dumps(dict(prepared=True,files=len(files),hash_files=len(hashes))))

def close():
    absent();binding=json.loads((HERE/'failure-closure-bindings.json').read_bytes());obs=json.loads((HERE/'interruption-observation.json').read_bytes())
    assert binding['source']==SOURCE and binding['closure_script_sha256']==sha(__file__) and binding['observation_sha256']==sha(HERE/'interruption-observation.json')
    assert snapshot()==obs['original_files'] and hash_snapshot()==obs['hash_files']
    a=admit(root=ROOT,registration=str(BASE/'gates.json'),experiment=EXPERIMENT,source=SOURCE,_own_claim=EXPERIMENT)
    run=ResearchRun(a);run._claim_sha256=sha(run.directory/'claim.json');run._check_source();run._check_inputs();absent()
    run.fail(binding['failure_reason'])
    assert snapshot()==obs['original_files'] and hash_snapshot()==obs['hash_files']
    result=verify_run(run.directory);assert result['status']=='failed'
    _immutable(HERE/'failure-closure.json',dict(closed_at=datetime.now(timezone.utc).isoformat(),source=SOURCE,failed_sha256=sha(run.directory/'failed.json'),verification=result,original_files_preserved=len(obs['original_files']),hash_files_preserved=len(obs['hash_files']),replay=False,new_claim=False,resource_peak_unknown=True,responsible_process_undetermined=True))
    print(json.dumps(dict(closed=True,verification=result)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['prepare','close']);a=p.parse_args();{'prepare':prepare,'close':close}[a.operation]()
