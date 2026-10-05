"""Exact publication blocks with real owned FD close; no public authority or entry."""
from pathlib import Path
import ast,os,sys,json,hashlib
D=Path(__file__).resolve().parent;P=D.parent/'financial-wrapper-compatibility-complete100-outcome-recovery-preparation02-2026-10-05'
sys.path[:0]=[str(D),str(D/'utilities')]
import recovery_pax01 as R
from cohort01 import VerifiedCohort
results=[]
for filename,fn,leaf in [('outcome01.py','run','LANE_RECOVERY01.json'),('join01.py','join','FOUR_LANE_RECOVERY01.json')]:
 for version,source in [('old',P),('new',D)]:
  f=next(n for n in ast.parse((source/filename).read_text()).body if isinstance(n,ast.FunctionDef) and n.name==fn)
  idx=next(i for i,n in enumerate(f.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id=='R' and n.value.func.attr=='put')
  nodes=f.body[idx-(2 if version=='new' else 0):idx+2]
  for mode in ('corrupt','intact','fatal'):
   root=D/('fixture-'+fn+'-'+version+'-'+mode);root.mkdir(mode=0o700);target=root/leaf;inputs=VerifiedCohort();realclose=os.close;fired=[];fatal=KeyboardInterrupt('owned engineering close interruption')
   ns={'R':R,'HERE':root,'CAPTURE':'engineering-only','request_sha':'engineering-only','i':0,'LANES':((0,),),'results':{},'SOURCE':'engineering-only','inputs':inputs,'boundary':lambda:None}
   changed=b'{"engineering_only":true,"corrupted_after_close":true}\n'
   def close(fd):
    name=os.readlink('/proc/self/fd/'+str(fd));realclose(fd)
    if name==str(target) and not fired:
     fired.append(fd)
     if mode=='corrupt':
      with target.open('wb') as out:out.write(changed)
     if mode=='fatal':raise fatal
   error=None
   try:
    os.close=close;exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(source/filename),'exec'),ns);inputs.check()
   except BaseException as e:error=e
   finally:os.close=realclose
   assert len(fired)==1
   if mode=='fatal':assert error is fatal
   elif mode=='corrupt':
    assert target.read_bytes()==changed
    if version=='old':assert error is None
    else:assert isinstance(error,ValueError) and str(error)=='published receipt differs from intended canonical bytes'
   else:
    assert error is None
    if version=='new':assert target.read_bytes()==ns['expected_receipt']
   results.append({'source':filename,'version':version,'mode':mode,'error':None if error is None else type(error).__name__,'real_write_fd_closed':True,'public_entry':False})
changes=json.loads((D/'INVERSE01.json').read_text())
for name,c in changes.items():
 old=(P/name).read_text();new=(D/name).read_text();assert new.count(c['new'])==1 and new.replace(c['new'],c['old'])==old
 assert ast.dump(ast.parse(new.replace(c['new'],c['old'])))==ast.dump(ast.parse(old))
 oldnodes={n.name:ast.dump(n) for n in ast.parse(old).body if isinstance(n,ast.FunctionDef)};newnodes={n.name:ast.dump(n) for n in ast.parse(new).body if isinstance(n,ast.FunctionDef)}
 assert all(newnodes[k]==v for k,v in oldnodes.items() if k not in ('run','join'))
unchanged=[]
for p in D.rglob('*'):
 if p.is_file() and (P/p.relative_to(D)).is_file() and p.name not in changes and p.name!='INVERSE01.json':
  assert p.read_bytes()==(P/p.relative_to(D)).read_bytes();unchanged.append(str(p.relative_to(D)))
(D/'CHECKS01.json').write_bytes(R.encode({'publication_cases':results,'cases':len(results),'unchanged':unchanged,'full_literal_AST_inverse':True,'scope':'stdlib owned engineering bytes only; no public run/release/authority'}))
print(json.dumps({'cases':len(results),'unchanged_bodies':len(unchanged),'inverse':True}))
