"""One append-only interrupted-run failure closure; no acquisition or computation."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import os
import subprocess

from tradingagents.research import ResearchRun
from tradingagents.research.admission import admit
from tradingagents.research.lifecycle import _immutable
from tradingagents.research.verify import verify_claim, verify_run

HERE=Path(__file__).resolve().parent
EXPECTED_ROOT=Path('/home/malecada/master_thesis/TradingAgents-onchain-pilot')
SOURCE='dcbd80e38db4b1bf2ea88689dc1eb1cbe53f31ca'
EXPERIMENT='eth-seven-day-pilot-20260916'
REL=Path('research/onchain-graph-2026-09-16/pilot')
REASON=('External/session interruption left the pilot without a lifecycle terminal and with an empty original resource receipt. '
        'No pilot executor was observed alive at preservation/closure checks. Terminating signal, exit code, peak RSS and guard '
        'disposition are unknown; an 8 GiB breach is not established. Append-only failure closure preserves claim, five published '
        'outputs, partial binary evidence and original empty resource file. No replay, new claim, finish, network or motif computation.')


def now():return datetime.now(timezone.utc).isoformat()


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def head(root):return subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()


def absent(root):
    matches=[]
    expected={str(root/REL/name) for name in ('launch.py','run.py','day.py')}
    for item in Path('/proc').iterdir():
        if not item.name.isdigit() or int(item.name)==os.getpid():continue
        try:
            # Inspect command lines only for the dedicated execution checkout.
            if (item/'cwd').resolve()!=root:continue
            argv=(item/'cmdline').read_bytes().split(b'\0')
            if any(arg.decode(errors='replace') in expected for arg in argv):matches.append(int(item.name))
        except (FileNotFoundError,PermissionError,ProcessLookupError):continue
    if matches:raise ValueError('pilot executor remains alive: '+str(matches))
    return {'observed_at':now(),'matching_pilot_executor_pids':[],
            'qualification':'Current /proc observation only; it does not determine the earlier signal, exit code or resource peak.'}


def snapshot(root):
    run=root/'research_runs'/EXPERIMENT
    paths=[run/'claim.json',root/REL/'resource.json',*sorted((run/'outputs').iterdir()),
           *sorted(p for p in (root/REL/'artifacts').rglob('*') if p.is_file())]
    if any(p.is_symlink() or not p.is_file() for p in paths):raise ValueError('unexpected evidence path type')
    return {str(p.relative_to(root)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in paths}


def verify_original(root,binding):
    if head(root)!=SOURCE:raise ValueError('execution HEAD changed')
    run=root/'research_runs'/EXPERIMENT
    if any((run/name).exists() for name in ('complete.json','failed.json')):raise ValueError('run already terminal')
    if snapshot(root)!=binding['original_files']:raise ValueError('original evidence inventory or bytes changed')
    if sha(Path(__file__))!=binding['closure_script_sha256']:raise ValueError('reviewed closure source changed')
    if sha(HERE/'interruption-observation.json')!=binding['interruption_observation_sha256']:raise ValueError('observation changed')
    return absent(root)


def prepare(root):
    if head(root)!=SOURCE:raise ValueError('execution HEAD differs')
    run=root/'research_runs'/EXPERIMENT
    if any((run/name).exists() for name in ('complete.json','failed.json')):raise ValueError('already terminal')
    process_check=absent(root);claim=verify_claim(run)
    if claim['source']!=SOURCE or claim['family']['prior_attempts']!=5 or claim['family']['attempt_budget']!=6:
        raise ValueError('claim lineage differs')
    if {p.name for p in (run/'outputs').iterdir()}!={'context.json','boundary.json','source-2024-01-02.json','source-2024-01-03.json','source-2024-01-04.json'}:
        raise ValueError('published progress changed; review current evidence first')
    resource=root/REL/'resource.json'
    if resource.stat().st_size!=0:raise ValueError('resource receipt no longer empty; review new evidence first')
    original=snapshot(root)
    spec=importlib.util.spec_from_file_location('independent_partial_blob_check',HERE/'check_independent.py')
    checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
    files=[dict(path=p,**v) for p,v in original.items() if p.startswith(str(REL/'artifacts')+'/')]
    tree=checker.check_tree(root,{'files':files,'bytes':sum(x['bytes'] for x in files)},strict=False)
    if snapshot(root)!=original:raise ValueError('evidence changed during preservation')
    _immutable(HERE/'interruption-observation.json',{
        'observed_at':now(),'source':SOURCE,'execution_root':str(root),'experiment':EXPERIMENT,
        'process_absence':process_check,'original_resource_path':str(REL/'resource.json'),
        'original_resource_bytes':0,'original_resource_sha256':sha(resource),
        'child_exit_code':None,'terminating_signal':None,'peak_sampled_tree_rss_bytes':None,
        'resource_limit_reason':None,'memory_limit_breach_established':False,
        'reported_context':'Coordinator reported tool-session interruption after a new user message; exact process termination cause is not established by retained executor evidence.',
        'reported_tool_session':48956,'tool_session_final_status':'unknown',
        'artifact_verification':tree,'independent_checker_sha256':sha(HERE/'check_independent.py'),
        'unpublished_pending_files':[p for p in original if any(part.startswith('.') for part in Path(p).parts)],
        'replay':False,'network_requests':0,'motif_computation':False})
    binding={'execution_root':str(root),'source':SOURCE,'experiment':EXPERIMENT,
        'claim_sha256':sha(run/'claim.json'),'original_files':original,
        'interruption_observation_sha256':sha(HERE/'interruption-observation.json'),
        'closure_script_sha256':sha(Path(__file__)),'failure_reason':REASON,
        'operation':'append failed.json through original ResearchRun.fail only; preserve all existing bytes'}
    _immutable(HERE/'failure-closure-bindings.json',binding)
    print(json.dumps({'prepared':True,'original_files':len(original),'artifact_verification':tree,
        'binding_sha256':sha(HERE/'failure-closure-bindings.json')}))


def close(root):
    binding=json.loads((HERE/'failure-closure-bindings.json').read_bytes())
    if binding['execution_root']!=str(root) or binding['source']!=SOURCE or binding['experiment']!=EXPERIMENT:
        raise ValueError('binding target differs')
    verify_original(root,binding)
    admitted=admit(root=root,registration=str(REL/'gates.json'),experiment=EXPERIMENT,source=SOURCE,_own_claim=EXPERIMENT)
    run=ResearchRun(admitted);run._claim_sha256=binding['claim_sha256'];run._check_inputs();run._check_source()
    process_check=verify_original(root,binding)
    run.fail(binding['failure_reason']+' Preservation binding SHA256 '+sha(HERE/'failure-closure-bindings.json'))
    if snapshot(root)!=binding['original_files'] or head(root)!=SOURCE:raise ValueError('closure changed original evidence')
    checked=verify_run(root/'research_runs'/EXPERIMENT)
    if checked['status']!='failed':raise ValueError('failure terminal missing')
    output_names=[p.name for p in sorted((root/'research_runs'/EXPERIMENT/'outputs').iterdir())]
    _immutable(HERE/'failure-closure.json',{
        'closed_at':now(),'operation':'append-only failure closure','source':SOURCE,
        'failure_reason':binding['failure_reason'],'process_absence_before_terminal':process_check,
        'binding_sha256':sha(HERE/'failure-closure-bindings.json'),
        'interruption_observation_sha256':sha(HERE/'interruption-observation.json'),
        'claim_sha256':binding['claim_sha256'],'failed_sha256':sha(root/'research_runs'/EXPERIMENT/'failed.json'),
        'original_files_preserved':len(binding['original_files']),'verification':checked,
        'published_outputs':output_names,'registered_cells':len(admitted.experiment['cells']),
        'registered_outputs':len(admitted.experiment['outputs']),
        'qualification':'Failed receipt completed-cell count is zero. Existing phase receipts describe pre-interruption progress, not successful pilot completion. Original empty resource file remains unchanged.',
        'replay':False,'new_claim':False,'finish_called':False,'new_network_requests':0,'motif_computation':False,
        'cumulative_allowance_consumed':'6/6','successor_authorized':False})
    print(json.dumps({'closed':True,'verification':checked,'failed_sha256':sha(root/'research_runs'/EXPERIMENT/'failed.json')}))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True)
    parser.add_argument('--operation',choices=['prepare','close'],required=True);args=parser.parse_args()
    root=Path(args.root).resolve()
    if root!=EXPECTED_ROOT:raise ValueError('wrong dedicated execution checkout')
    if len(os.sched_getaffinity(0))>2:raise ValueError('closure must use reviewed two-CPU guard')
    {'prepare':prepare,'close':close}[args.operation](root)


if __name__=='__main__':main()
