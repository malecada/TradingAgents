"""Root-only finite synthetic hook. No Run/Owner/claim/admission/network.
Do not infer native release/capacity from this engineering comparison.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,struct,sys,resource,tempfile,time
P=Path(__file__).resolve().parent
HARNESS=P.parent/'pilot-matching-weight-cache-candidate-2026-10-12/numeric_harness.py'
HARNESS_SHA='fdc0940ca0b18d75cb933bbaa58c4a0fd38824b638f6ed09d0d1adc3ad3729e8'

def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
 sys.modules[name]=module;spec.loader.exec_module(module);return module

def exact(h,old,new):
 row=h.compare(old,new);a,b=old[0],new[0]
 assert a.soft_assignment.dtype==b.soft_assignment.dtype and a.soft_assignment.shape==b.soft_assignment.shape
 assert a.soft_assignment.tobytes()==b.soft_assignment.tobytes(),'soft bits differ'
 assert a.assignment.tobytes()==b.assignment.tobytes(),'assignment bits differ'
 assert struct.pack('!d',a.score)==struct.pack('!d',b.score),'packed production score differs'
 assert old[1]==new[1],'cursor history differs'
 # Compare original scalar/chunk counters, not timers.
 for key in ('agreement_scalar_entries','agreement_scalar_chunks','chunk_8to255_calls','chunk_256to1023_calls','chunk_1024_calls'):
  assert old[2]['phases']['numeric_counts'].get(key,0)==new[2]['phases']['numeric_counts'].get(key,0),key
 return row

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);parser.add_argument('--config-sha256',required=True)
 parser.add_argument('--normalization-policy',required=True,help='exact compiled policy JSON for existing engineering BackendOwner; no research Owner')
 parser.add_argument('--focused',action='store_true');args=parser.parse_args()
 assert hashlib.sha256(HARNESS.read_bytes()).hexdigest()==HARNESS_SHA
 manifest=json.loads((P/'SOURCE_MANIFEST01.json').read_bytes())
 for name in ('serial_advance.py','BASELINE_matching_annealing.py'):
  assert hashlib.sha256((P/name).read_bytes()).hexdigest()==manifest['files'][name]['sha256']
 h=load(HARNESS,'serial_numeric_original_harness');baseline=h.ann._advance_checked
 assert Path(h.ann.__file__).read_bytes()==(P/'BASELINE_matching_annealing.py').read_bytes()
 candidate=load(P/'serial_advance.py','serial_candidate');assert candidate.ORIGINAL is baseline
 c=h.config(args.config,args.config_sha256)
 original_session=h.Session
 normalizer_raw=Path(args.normalization_policy).read_bytes()
 assert hashlib.sha256(normalizer_raw).hexdigest()=='648654607c166911bfec4b0b276cf7f8c148ff7bf9f62621faf12b1ef1b5a8f6'
 selected=json.loads(normalizer_raw)
 from tradingagents.research.onchain_replication.compiled_normalization_policy import BackendOwner
 def solve_owned(a,b,budget,checkpoint=None):
  start=time.perf_counter();owner=BackendOwner(selected)
  h.Session=lambda *args,**kw:original_session(*args,compiled_normalization_policy_value=selected,_normalization_owner=owner,**kw)
  primary=None
  try:result=h.solve(a,b,c,2,budget=budget,checkpoint=checkpoint)
  except BaseException as error:primary=error;raise
  finally:
   try:owner.close()
   except BaseException as cleanup:
    if primary is None:raise
    try:BaseException.add_note(primary,'hook owner cleanup failed: '+repr(cleanup))
    except BaseException:pass
   h.Session=original_session
  result[2]['wall_seconds']=time.perf_counter()-start
  result[2]['timing_interval']='cold engineering BackendOwner + create/session + full solver/score + session/state/BackendOwner cleanup'
  return result
 def pair(le,re,budget=1000000,checkpoint=False):
  a,b=h.graph(le),h.graph(re,.031)
  h.ann._advance_checked=baseline;old=solve_owned(a,b,budget)
  h.ann._advance_checked=candidate.advance_checked
  if checkpoint:
   with tempfile.TemporaryDirectory() as temp:new=solve_owned(a,b,budget,checkpoint=Path(temp)/'checkpoint')
  else:new=solve_owned(a,b,budget)
  joined=exact(h,old,new);joined.update(left_edges=le,right_edges=re,budget=budget,baseline=old[2],candidate=new[2]);return joined
 rows=[];checks=[]
 try:
  for le,re in ((0,1),(1,1),(1,4),(1,7),(2,4),(4,4),(16,16),(32,32)):rows.append(pair(le,re))
  if args.focused:
   for le,re in ((2,4),(32,32)):
    n=h.graph(le).node_features.shape[0];m=h.graph(re).node_features.shape[0]
    needed=n*m+48*(le*re+5)
    checks.extend((pair(le,re,needed),pair(le,re,needed+1)))
   checks.append(pair(32,32,1024,True))
   checks.append(pair(1,1)) # unsupported tiny original fallback
   checks.append(pair(33,32)) # unsupported edge product extent
 finally:
  h.ann._advance_checked=baseline;h.Session=original_session
 print(json.dumps({'scope':'one-pair synthetic C05v2; no genuine authority or capacity proof',
  'cases':rows,'focused':checks,'normalizer_selected':bool(args.normalization_policy),
  'extra_scratch_reservation_bytes':candidate.SCRATCH_RESERVATION,
  'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},sort_keys=True,indent=2))
if __name__=='__main__':main()
