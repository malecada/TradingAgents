"""User-authorized8GiB sampled process-tree guard; two CPUs and no elapsed kill."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from tradingagents.research_amended import admit

RSS_LIMIT_BYTES=8*1024**3


def run_with_limit(command,guard,root):
    env=dict(os.environ,PYTHONPATH=str(root),OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',
             MKL_NUM_THREADS='2',NUMEXPR_NUM_THREADS='2')
    begin=time.monotonic()
    try:
        process=subprocess.Popen(command,cwd=root,env=env,preexec_fn=guard._limits,start_new_session=True)
    except (OSError,subprocess.SubprocessError) as exc:
        return {'child_exit_code':None,'limit_reason':'launch/setup failed: '+str(exc),
                'elapsed_seconds':time.monotonic()-begin,'elapsed_time_kill':False,
                'peak_sampled_tree_rss_bytes':None,'rss_limit_bytes':RSS_LIMIT_BYTES,'retry':False}
    peak,reason=0,None
    while process.poll() is None:
        try:
            peak=max(peak,guard.tree_rss(process.pid))
            if peak>RSS_LIMIT_BYTES:reason='sampled aggregate RSS limit exceeded'
        except (OSError,RuntimeError,ValueError) as exc:
            reason='resource monitor failed: '+str(exc)
        if reason:
            try:os.killpg(process.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                process.wait()
            break
        time.sleep(.02)
    return {'child_exit_code':process.wait(),'limit_reason':reason,'elapsed_seconds':time.monotonic()-begin,
            'elapsed_time_kill':False,'peak_sampled_tree_rss_bytes':peak,'rss_limit_bytes':RSS_LIMIT_BYTES,
            'sample_interval_seconds':.02,'qualification':'Sampled RSS can miss brief peaks; cap is not a memory reservation. Two logical CPUs; no elapsed/CPU-duration kill.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',required=True)
    args=parser.parse_args();here=Path(__file__).resolve().parent;root=here.parents[2]
    admit(root=root,registration='research/onchain-graph-2026-09-16/motifs8gib/gates-v2.json',
          experiment='eth-temporal-motifs-8gib-20260916',source=args.source)
    spec=importlib.util.spec_from_file_location('retained_two_cpu_guard',root/'research/strategy-search-2026-09-11/resource_guard_v2.py')
    guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
    with (here/'resource.json').open('x') as f:
        result=run_with_limit([sys.executable,'-B',str(here/'run.py'),'--source',args.source],guard,root)
        result['source']=args.source;json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))
    return int(result['child_exit_code']!=0 or result['limit_reason'] is not None)


if __name__=='__main__':raise SystemExit(main())
