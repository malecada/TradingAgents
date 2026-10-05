"""Exact two production publication expressions, owned opaque fixtures only; no public run."""
from verify_capture01 import *
import ast,importlib.util
P=F/'financial-wrapper-compatibility-complete100-outcome-recovery-preparation02-2026-10-05';sys.path[:0]=[str(P),str(P/'utilities')]
from cohort01 import VerifiedCohort
results=[]
for filename,fn in [('outcome01.py','run'),('join01.py','join')]:
 src=(P/filename).read_text();tree=ast.parse(src);f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==fn)
 idx=next(i for i,n in enumerate(f.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id=='R' and n.value.func.attr=='put')
 nodes=f.body[idx:idx+2];d=HERE/('witness-receipt-'+fn);d.mkdir(mode=0o700);inputs=VerifiedCohort();namespace={'R':R,'HERE':d,'CAPTURE':'engineering-only-no-authority','request_sha':'engineering-only','i':0,'LANES':((0,),),'results':{},'SOURCE':'engineering-only-no-authority','inputs':inputs,'boundary':lambda:None}
 code=compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(P/filename),'exec');realclose=os.close;fired=[];target=d/('LANE_RECOVERY01.json' if fn=='run' else 'FOUR_LANE_RECOVERY01.json');changed=b'{"engineering_only":true,"corrupted_after_close":true}\n'
 def close(fd):
  name=os.readlink('/proc/self/fd/'+str(fd));realclose(fd)
  if name==str(target) and not fired:
   fired.append(fd)
   with target.open('wb') as out:out.write(changed)
 try:
  os.close=close;exec(code,namespace)
 finally:os.close=realclose
 inputs.check();assert len(fired)==1 and target.read_bytes()==changed
 results.append({'source':filename,'function':fn,'original_lines':[nodes[0].lineno,nodes[1].lineno],'real_descriptor_closed_once':fired,'observed':'production publication plus first retained read and final cohort accepted corrupted receipt','public_entry_executed':False,'genuine_receipt_created':False})
(HERE/'RECEIPT_WITNESS01.json').write_bytes(R.encode({'decision':'WITHHELD_LATE_RECEIPT_BODY_UNBOUND','results':results}));print(json.dumps(results))
