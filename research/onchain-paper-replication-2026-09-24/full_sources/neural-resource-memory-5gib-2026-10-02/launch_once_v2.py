"""One concrete admitted neural launch; never retries an attempted namespace."""
import argparse
from importlib import util
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
EXPERIMENT='eth-paper-neural-resource-20261002-02'
REGISTRATION=str((HERE/'gate-coordinator02.json').relative_to(ROOT))


def save(path,value):
    raw=(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    if len(raw)>262144:raise ValueError('outer metadata exceeds bounded encoding')
    with path.open('xb') as output:
        output.write(raw);output.flush();os.fsync(output.fileno())


def absent():
    for prefix in ('research_runs','research_artifacts/onchain-paper-replication-2026-09-24/runs',
                   'research_artifacts/onchain-paper-replication-2026-09-24/sources'):
        if os.path.lexists(ROOT/prefix/EXPERIMENT):
            raise ValueError('launch identity is active, terminal or already reserved; no retry')


def log_limit():
    resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024**2,16*1024**2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True)
    parser.add_argument('--observation',required=True,type=int)
    args=parser.parse_args()
    if args.observation<=0 or args.observation>999:raise ValueError('finite observation index required')
    if Path.cwd().resolve()!=ROOT:raise ValueError('launch from admitted checkout only')
    sys.path.insert(0,str(ROOT))
    from tradingagents.research.onchain_replication import job
    from tradingagents.research.lifecycle import _encode,_now
    admitted,selected=job._admitted(SimpleNamespace(root=str(ROOT),registration=REGISTRATION,
        experiment=EXPERIMENT,source=args.source))
    if selected['kind']!='neural_resource':raise ValueError('explicit neural job required')
    for p in (Path(__file__),HERE/'readiness.py'):
        relative=str(p.relative_to(ROOT))
        if hashlib.sha256(p.read_bytes()).hexdigest()!=admitted.experiment['source_files'].get(relative):
            raise ValueError('coordinator/helper source not pinned by exact admission')
    absent()
    claim={'schema_version':1,'program_id':admitted.spec['program_id'],'experiment_id':EXPERIMENT,
        'started_at':_now(),'source':args.source,'registration':REGISTRATION,
        'registration_sha256':admitted.registration_sha256,'design_source':admitted.design_source,
        'bindings':admitted.bindings,'bindings_sha256':admitted.bindings_sha256,'inputs':admitted.inputs,
        'family':admitted.family,'experiment':admitted.experiment,
        'effective_attempt_budget':admitted.effective_attempt_budget,'windows':admitted.windows,
        'prior_exposures':[{**v,'identity':d['identity']} for d in admitted.spec['datasets'].values() for v in d['exposures']]}
    claim_bytes=len(_encode(claim));rpc_bytes=len(_encode({'anchor_sha256':'0'*64,'op':'claim','value':claim}))
    if max(claim_bytes,rpc_bytes)>262144:raise ValueError('claim/authority request exceeds bounded encoding')
    number=f'{args.observation:02d}'
    save(HERE/f'admission{number}.json',{'ready':admitted.ready,'experiment':EXPERIMENT,'source':args.source,
        'registration':REGISTRATION,'registration_sha256':admitted.registration_sha256,
        'effective_attempt_budget':admitted.effective_attempt_budget,'claim_bytes':claim_bytes,'rpc_bytes':rpc_bytes,
        'research_run_started':False,'namespace_reserved':False})
    spec=util.spec_from_file_location('neural_readiness_release',HERE/'readiness.py')
    helper=util.module_from_spec(spec);spec.loader.exec_module(helper)
    info=admitted.inputs['launch_scheduling'];raw=(ROOT/info['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=info['sha256']:raise ValueError('registered scheduling policy changed')
    policy=json.loads(raw)
    report=helper.observe(policy)
    report.update(experiment=EXPERIMENT,source=args.source,registration_sha256=admitted.registration_sha256,
        namespace_reserved=False,qualification='new in-process observation after actual admission; no saved permit')
    save(HERE/f'readiness{number}.json',report)
    if not helper.fresh(report,policy,time.monotonic()):
        print(json.dumps({'status':'readiness_deferred','namespace_reserved':False,'reason':report['reason']}));return 3
    absent()
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!=args.source:
        raise ValueError('source HEAD moved before launch')
    free=os.statvfs(ROOT).f_bavail*os.statvfs(ROOT).f_frsize
    if free<selected['resources']['disk_floor_bytes']:raise ValueError('disk free floor fell before launch')
    command=[sys.executable,'-B','-m',job.MODULE,'--mode','launch','--root',str(ROOT),
        '--registration',REGISTRATION,'--experiment',EXPERIMENT,'--source',args.source]
    save(HERE/f'launch-intent{number}.json',{'experiment':EXPERIMENT,'source':args.source,
        'registration':REGISTRATION,'registration_sha256':admitted.registration_sha256,
        'last_readiness_monotonic':report['observations'][-1]['monotonic'],
        'free_disk_bytes':free,'command':command,'automatic_retry':False,
        'outer_log_max_bytes':16*1024**2,'outer_log_qualification':'outside three owned roots; finite additional launcher stdout/stderr cap'})
    # No second admission, sleep or expensive preparation between freshness and exec.
    if not helper.fresh(report,policy,time.monotonic()):
        print(json.dumps({'status':'readiness_expired','namespace_reserved':False}));return 3
    with (HERE/f'launch{number}.log').open('xb') as output:
        # The exclusive log open may block; recheck only after it completes.
        if not helper.fresh(report,policy,time.monotonic()):
            print(json.dumps({'status':'readiness_expired','namespace_reserved':False}));return 3
        code=subprocess.call(command,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT,preexec_fn=log_limit)
    print(json.dumps({'status':'launcher_returned','exit_code':code,'experiment':EXPERIMENT}))
    return code


if __name__=='__main__':raise SystemExit(main())
