import ast,copy,json,sys
from pathlib import Path
import bind01 as B
R=B.R;H=Path(__file__).resolve().parent;checks=[]
def ok(n,v):assert v,n;checks.append(n)
def refuse(n,fn):
 try:fn()
 except (ValueError,KeyError,TypeError,FileNotFoundError):ok(n,True)
 else:raise AssertionError(n)
B.prepared();ok('accepted exact verifier/parent/review metadata pins',True)
raw=R.read(H,'original-verifier03.py')
# Pure rewrite projections are not Parent receipts or emitted accepted bindings.
for name in ['REQUEST_FINAL01.json','REQUEST_FINAL03.json','REQUEST_FINAL99.json']:
 code,edits=B.rewrite(raw,'a'*64,name);back=code.decode()
 for e in reversed(edits):back=back.replace(e['new'],e['old'])
 ok('exact synthetic transformation inverse '+name,back.encode()==raw and ast.dump(ast.parse(back))==ast.dump(ast.parse(raw)))
 old={n.name:ast.dump(n) for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)};new={n.name:ast.dump(n) for n in ast.parse(code).body if isinstance(n,ast.FunctionDef)}
 for k in old:
  if k!='verify':ok('unchanged decision function '+name+' '+k,old[k]==new[k])
for pin in [None,'0','g'*64,B.OLD_QHASH]:refuse('invalid/stale hash '+str(pin),lambda:B.rewrite(raw,pin,'REQUEST_FINAL01.json'))
for name in ['../REQUEST_FINAL01.json','/REQUEST_FINAL01.json','REQUEST_FINAL1.json','request.json']:
 refuse('unsafe/unfixed basename '+name,lambda:B.rewrite(raw,'a'*64,name))
refuse('changed old source',lambda:B.rewrite(raw+b'\n','a'*64,'REQUEST_FINAL01.json'))
oldq=json.loads((H.parent/'financial-genuine-wrapper-first-outcome-verifier-preparation03-2026-10-04/REQUEST_FINAL03.json').read_text());refuse('actual old d4e identity refused',lambda:B.fixed(oldq))
refuse('actual stale request before IO',lambda:B.authenticate(Path(B.PARENT)/'REQUEST_FINAL01.json',B.OLD_QHASH))
refuse('outside fixed parent before IO',lambda:B.authenticate(H/'REQUEST_FINAL01.json','a'*64))
refuse('missing actual new request refused',lambda:B.authenticate(Path(B.PARENT)/'MISSING.json','a'*64))
ok('no generated authoritative verifier exists',not (H/'generated-recordfix01').exists())
ok('no numerical imports',all(n not in sys.modules for n in ['numpy','torch','pandas','scipy']))
source=(H/'bind01.py').read_text();emit=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='emit');seg=ast.get_source_segment(source,emit);ok('emission requires actual authentication before output',seg.index('generate(path,pin)')<seg.index('out.mkdir'))
(H/'CHECKS01.json').write_bytes(R.encode({'count':len(checks),'checks':checks,'actual_outcomes':0,'emitted_final_bindings':0,'numerical_imports':0}));print('PASS',len(checks))
