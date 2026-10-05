"""Only the two final receipt comparisons; original witnesses and one fatal cleanup check."""
from verify_capture01 import *
import ast
P=F/'financial-wrapper-compatibility-complete100-outcome-recovery-preparation03-2026-10-05';OLD=F/'financial-wrapper-compatibility-complete100-outcome-recovery-preparation02-2026-10-05';rd=Reader();seal=json.loads(rd.read(P/'MANIFEST01.json','084bfbf4bc831b3943ee79a9f1befae8b31b7da137e371151cf72b5d19c5e24a'));inv=json.loads(rd.read(P/'INVERSE01.json'))
for row in seal['members']:
 p=P/row['path'];rd.pin(p);rd.need(stat.S_IMODE(p.lstat().st_mode)==row['mode'],'source03 sealed typed modes')
 if row['kind']=='file':rd.need(len(rd.read(p,row['sha256']))==row['bytes'],'complete source03 sealed bodies')
for n,change in inv.items():
 s=rd.read(P/n).decode();rd.need(s.count(change['new'])==1,'one declared literal publication edit');rd.need(s.replace(change['new'],change['old']).encode()==rd.read(OLD/n,change['original_sha256']),'complete source03 literal inverse '+n)
for row in seal['members']:
 n=row['path']
 if row['kind']=='file' and (OLD/n).is_file() and n.endswith('.py') and n not in inv:rd.need(rd.read(P/n)==rd.read(OLD/n),'unchanged helper '+n)
sys.path[:0]=[str(P),str(P/'utilities')];from cohort01 import VerifiedCohort
results=[]
for filename,fn in [('outcome01.py','run'),('join01.py','join')]:
 s=rd.read(P/filename).decode();f=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name==fn)
 idx=next(i for i,n in enumerate(f.body) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='receipt');nodes=f.body[idx:idx+4]
 rd.need(len(nodes)==4 and isinstance(nodes[-1],ast.Expr),'exact corrected publication block')
 for case in ('healthy','corrupt','fatal'):
  d=HERE/('receipt03-'+fn+'-'+case);d.mkdir(mode=0o700);inputs=VerifiedCohort();ns={'R':R,'HERE':d,'CAPTURE':'engineering-only-no-authority','request_sha':'engineering-only','i':0,'LANES':((0,),),'results':{},'SOURCE':'engineering-only-no-authority','inputs':inputs,'boundary':lambda:None}
  target=d/('LANE_RECOVERY01.json' if fn=='run' else 'FOUR_LANE_RECOVERY01.json');code=compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(P/filename),'exec');realclose=os.close;fired=[];fatal=MemoryError('owned-close-opaque');caught=None
  def close(fd):
   name=os.readlink('/proc/self/fd/'+str(fd));realclose(fd)
   if name==str(target) and not fired:
    fired.append(fd)
    if case=='corrupt':
     with target.open('wb') as out:out.write(b'{"engineering_only":true,"corrupted_after_close":true}\n')
    if case=='fatal':raise fatal
  try:
   os.close=close
   try:exec(code,ns);inputs.check()
   except BaseException as e:caught=e
  finally:os.close=realclose
  rd.need(len(fired)==1,'actual receipt descriptor closed exactly once')
  if case=='healthy':rd.need(caught is None and target.read_bytes()==R.encode(ns['receipt']),'healthy intended canonical receipt')
  elif case=='corrupt':rd.need(type(caught)is ValueError and str(caught)=='published receipt differs from intended canonical bytes','original real-close witness now refuses')
  else:rd.need(caught is fatal,'exact actual fatal retained')
  results.append({'function':fn,'case':case,'actual_receipt_fd_closed_once':True,'result':'passed' if caught is None else type(caught).__name__,'authority':False})
rd.finish();result={'schema_version':1,'decision':'ACCEPTED_CORRECTED_FOUR_LANE_SOURCE_ONLY_PENDING_ACTUAL_ENTRY_BINDINGS','sources':{n:R.digest((P/n).read_bytes()) for n in inv},'literal_AST_inverse_to02':True,'signing02_and_all_other_source_unchanged':True,'original_receipt_witnesses_now_refuse':True,'controls':results,'checks':rd.checks,'capture_proof_sha256':R.digest((HERE/'ACTUAL_CAPTURE_REVIEW01.json').read_bytes()),'actual_network_or_recovery_entry':False,'numerical_authority':False}
(HERE/'SOURCE03_CHECKS.json').write_bytes(R.encode(result));print(json.dumps(result))
