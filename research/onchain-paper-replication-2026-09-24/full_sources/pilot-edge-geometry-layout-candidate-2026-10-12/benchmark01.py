"""Root-only synthetic geometry comparison; no Run/Owner/claim/registration.
Reuses accepted full matching harness; unexecuted by candidate author.
"""
from pathlib import Path
import argparse,ast,hashlib,importlib.util,json,struct,sys,resource,tempfile
P=Path(__file__).resolve().parent
HARNESS=P.parent/'pilot-matching-weight-cache-candidate-2026-10-12/numeric_harness.py'
HARNESS_SHA='fdc0940ca0b18d75cb933bbaa58c4a0fd38824b638f6ed09d0d1adc3ad3729e8'
SOURCE_SHA='b77d6ee6093047715024b9f1cd8033b02f24f06bb1461b854a659e0a336f8f91'

def main():
 p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--config-sha256',required=True);p.add_argument('--focused',action='store_true');args=p.parse_args()
 if hashlib.sha256(HARNESS.read_bytes()).hexdigest()!=HARNESS_SHA:raise ValueError('accepted original matching harness differs')
 spec=importlib.util.spec_from_file_location('geometry_original_harness',HARNESS);h=importlib.util.module_from_spec(spec);sys.modules[spec.name]=h;spec.loader.exec_module(h)
 raw=(P/'matching_annealing.py').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:raise ValueError('candidate source differs')
 if Path(h.ann.__file__).read_bytes()!=(P/'BASELINE_matching_annealing.py').read_bytes():raise ValueError('installed annealing baseline differs')
 baseline=h.ann._advance_checked
 node=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='_advance_checked')
 try:
  exec(compile(ast.Module(body=[node],type_ignores=[]),str(P/'matching_annealing.py'),'exec'),h.ann.__dict__)
  candidate=h.ann._advance_checked
 finally:h.ann._advance_checked=baseline
 c=h.config(args.config,args.config_sha256)
 def exact(old,new):
  report=h.compare(old,new);a=old[0];b=new[0]
  if a.soft_assignment.dtype!=b.soft_assignment.dtype or a.soft_assignment.shape!=b.soft_assignment.shape or a.soft_assignment.tobytes()!=b.soft_assignment.tobytes():raise AssertionError('bitwise soft mismatch')
  if a.assignment.tobytes()!=b.assignment.tobytes():raise AssertionError('bitwise assignment mismatch')
  if struct.pack('!d',a.score)!=struct.pack('!d',b.score):raise AssertionError('bitwise production score mismatch')
  if old[1]!=new[1]:raise AssertionError('exact operation/cursor history mismatch')
  return report
 def pair(left,right,budget=1000000,checkpoint=False):
  a=h.graph(left);b=h.graph(right,.031)
  h.ann._advance_checked=baseline
  old=h.solve(a,b,c,2,budget=budget)
  h.ann._advance_checked=candidate
  if checkpoint:
   with tempfile.TemporaryDirectory() as temp:new=h.solve(a,b,c,2,budget=budget,checkpoint=Path(temp)/'checkpoint')
  else:new=h.solve(a,b,c,2,budget=budget)
  joined=exact(old,new);joined.update(left_edges=left,right_edges=right,edge_products=left*right,baseline=old[2],candidate=new[2]);return joined
 rows=[];focused=[]
 try:
  for left,right in ((32,32),(128,128),(256,512),(1024,1024)):rows.append(pair(left,right))
  if args.focused:
   # Complete graphs repeat Q destinations across product chunks; 1024 budget
   # additionally covers partial advances and a real checkpoint recomputation.
   focused.append(pair(130,130,budget=1024,checkpoint=True))
 finally:h.ann._advance_checked=baseline
 print(json.dumps({'scope':'synthetic exact geometry delta only; no live authority','source_sha256':SOURCE_SHA,'harness_sha256':HARNESS_SHA,'config_sha256':args.config_sha256,'numeric_kernel_policy':'v2 both routes','budget':1000000,'iterations':48,'cases':rows,'focused':focused,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},sort_keys=True,indent=2))
if __name__=='__main__':main()
