"""Root-only engineering measurement. No admit/start/Run/Owner/input reader.

This hook calls the same metadata scan used behind the candidate's sealed
run-only interface; its local tuple is not an admission capability. Never run
during a concurrent mutation of the measured history. No claim, registration, outcome or source is written.
"""
import argparse,hashlib,importlib.util,json,sys,time,resource
from pathlib import Path

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--workers',type=int,choices=(1,2),default=2);parser.add_argument('--expected-claims',type=int,choices=(115,),default=115)
 args=parser.parse_args();root=Path(args.root).resolve(strict=True);p=Path(__file__).resolve().parent
 sys.path.insert(0,str(root))
 import tradingagents.research
 spec=importlib.util.spec_from_file_location('tradingagents.research._history_candidate_measurement',p/'admission.py');module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
 module._history_policy({'format':'bounded-claims-v2','workers':args.workers,'max_audit_seconds':300})
 frontier=module._history_frontier(root)
 if len(frontier)!=115:raise ValueError('exact115-claim roster required')
 output={'kind':'engineering-only-history-component-measurement','root':str(root),'candidate_sha256':hashlib.sha256((p/'admission.py').read_bytes()).hexdigest(),'claims':115,'workers':args.workers,'steps':[],'capability_created':False,'measurement_scope':'historical frontier and history audit component only','excludes':['current admission HEAD/source/design/runtime/input-binding/budget checks','warm own-claim verification','production warm _check_source latency']}
 previous=None
 for name,force in (('full_baseline',False),('warm_scan1',False),('warm_scan2',False),('warm_scan3',False),('forced_refresh',True)):
  started=time.perf_counter();cpu=time.process_time();snapshot,prior,full=module._history_scan(root,args.workers,previous,force=force)
  if len(prior)!=115 or snapshot[0]!=frontier:raise ValueError('history changed during bounded benchmark')
  output['steps'].append({'step':name,'full_audit':full,'wall_seconds':time.perf_counter()-started,'own_cpu_seconds':time.process_time()-cpu,'frontier_sha256':hashlib.sha256(module._history_bytes(frontier)).hexdigest(),'verified_metadata_bytes':len(snapshot[1])//2})
  previous=snapshot
 if len(module._HISTORY) or len(module._HISTORY_BUSY):raise ValueError('benchmark must not create run history state')
 output['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 output['limits']={'max_claims':module._HISTORY_MAX_RUNS,'max_body_bytes':module._HISTORY_MAX_BODY,'max_total_bytes':module._HISTORY_MAX_BYTES,'elapsed_audit_seconds':300}
 print(json.dumps(output,sort_keys=True,indent=2))
if __name__=='__main__':main()
