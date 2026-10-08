import ast,hashlib,json,os,resource,signal
from pathlib import Path
os.sched_setaffinity(0,{3,4});os.nice(10);resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(60)
H=Path(__file__).resolve().parent;F=H.parent;R=Path.cwd();N=F/'real-data-pilot-final22-2026-10-08';checks=[];pins={}
def read(p):
 s=p.read_text();pins[str(p.relative_to(R))]=hashlib.sha256(s.encode()).hexdigest();return s
def ck(n,v):
 assert v,n
 checks.append(n)
base=read(F/'real-data-pilot-outcome21-scope01-2026-10-08/select01.py');new=read(F/'real-data-pilot-outcome22-scope01-2026-10-09/select01.py')
inv=new.replace('20261008-22','20261008-21').replace('real-data-pilot-final22','real-data-pilot-final21').replace('57f440b1f12a5b495f9a346a787441d334b9a8723fb97482adcfb6a04a64fb80','db8a30b46d4a51935c063f6ab718cab337aca2e15be0d9c49460466aae02ca15').replace("for i in (2,4,5)]","for i in range(2,11)] + [f'DIAGNOSTIC_SAMPLE{i:02d}.json' for i in range(1,4)]")
class Qual(ast.NodeTransformer):
 def visit_Dict(self,n):
  for i,k in enumerate(n.keys):
   if isinstance(k,ast.Constant) and k.value=='qualification':n.values[i]=ast.Constant('reviewed scope prose')
  return self.generic_visit(n)
ck('selector_full_AST_inverse_except_scope_prose',ast.dump(Qual().visit(ast.parse(inv)))==ast.dump(Qual().visit(ast.parse(base))))
fixed=['ROOT_LAUNCH01.stdout','ROOT_LAUNCH01.stderr','ROOT_IO_CLOSED01.json','FINAL_STORAGE01.json','ACTIVE_OBSERVATION01.json','EXEC_HANDLE01.json','launch-attempt01.json','ROOT_TERMINAL01.json']+[f'ACTIVE_OBSERVATION{i:02d}.json' for i in (2,4,5)]
ck('all11actual_fixed_controls_exist',all((N/n).is_file() and not (N/n).is_symlink() for n in fixed))
D=F/'real-data-pilot-twentysecond-failed-increment01-2026-10-09';O=F/'real-data-pilot-twentyfirst-failed-increment01-2026-10-08'
for name in ('capture01.py','recover01.py'):
 a=read(D/name);b=read(O/name);inverse=a.replace('real-data-pilot-outcome22-scope01-2026-10-09','real-data-pilot-outcome21-scope01-2026-10-08').replace('20261008-22-01.git','20261008-21-01.git').replace('failed22','failed21');ck(name+'_full_literal_inverse',inverse==b)
x={'decision':'accepted-source-scope-before-capture','identity':'eth-paper-real-data-end-to-end-resource-20261008-22','source_pins':pins,'checks':checks,'scope':'Six exact public roots including workflow57f440b1 and11actual fixed Root controls; no fabricated03 or diagnostic sample. Existing typed opaque hashing/schema/capture and13operation commitonly remote recovery preserved. Qualification prose explicitly includes generated failure-owned descendant bodies as opaque data.','qualification':'Actual selection/capture/fresh return still pending. No source arrays interpreted, original raw/private/runtime scope included, network, claim or Main mutation. No binarysemantic/POSIX/deletion proof.'}
(H/'SOURCE_SCOPE03.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({'sha256':hashlib.sha256((H/'SOURCE_SCOPE03.json').read_bytes()).hexdigest(),'checks':len(checks)}))
