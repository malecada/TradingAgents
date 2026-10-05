from pathlib import Path
import ast,copy,json,sys,hashlib,os
D=Path(__file__).resolve().parent;P=D.parent/'financial-wrapper-compatibility-complete100-outcome-recovery-preparation03-2026-10-05';sys.path[:0]=[str(D),str(D/'utilities')];import outcome01 as O;import receipt01 as E
checks=[]
def ck(n,v):assert v,n;checks.append(n)
def refuses(n,f):
 try:f()
 except ValueError:checks.append(n);return
 raise AssertionError(n)
raw=(O.ROOT/O.CAPTURE_PATH).read_bytes();c=O.context(raw);seen=set()
for i in range(4):
 old=O.F/('financial-wrapper-compatibility-complete100-outcome-remote-lane%02d-2026-10-05'%(i+1));q=json.loads((old/'ROOT_REQUEST01.json').read_bytes());generated=O.generate(q,raw)
 tree=ast.parse(generated['receiver']);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('encode','validate_fixed_selection')];ns={'json':json,'Path':Path,'require':O.R.require,'REQUIRED':q['required'],'FINAL_POPULATION_COUNT':len(q['required']),'FILE':O.R.FILE};exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-receiver-functions','exec'),ns)
 selection=json.loads(generated['selection_body']);ns['validate_fixed_selection'](selection);ck('actual encoder lane'+str(i),ns['encode'](selection)==generated['selection_body']==E.encode(selection))
 ck('old style genuine refusal '+str(i),ns['encode'](json.loads((old/'SELECTED_BODIES01.json').read_bytes()))!=(old/'SELECTED_BODIES01.json').read_bytes())
 ck('original required bodies unchanged '+str(i),O.selected_required(q,i,c)==q['required'])
 digest=O.R.digest(generated['selection_body']);fn=next(n for n in ast.parse((D/'receipt01.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='validate_remote');prefix=fn.body[1:3];env={'selection':selection,'required':q['required'],'selection_sha256':digest,'selection_rows':E.selection_rows,'hexpin':E.hexpin,'encode':E.encode,'R':O.R};code=compile(ast.Module(body=prefix,type_ignores=[]),'actual-receipt-canonical-prefix','exec');exec(code,env);checks.append('actual receipt canonical prefix '+str(i));env['selection_sha256']=O.R.digest(json.dumps(selection,separators=(',',':')).encode());refuses('compact digest refuses '+str(i),lambda:exec(code,env))
 for phase in ('remote','flat'):
  root=O.lane_root(i,phase);ck('fresh name '+root.name,root in O.W.ROOTS and not os.path.lexists(root));ck('generated caller root '+phase,str(root) in generated['callers'][phase]);seen.add(str(root));ast.parse(generated['callers'][phase])
 ck('fresh Git/status '+str(i),'compatibility-complete100-outcome-lane%02d-canonical02'%(i+1) in generated['receiver'] and 'compatibility-complete100-outcome-lane%02d-canonical02'%(i+1) in generated['receipt'])
 x=copy.deepcopy(selection);x['rows'].pop();refuses('missing row '+str(i),lambda:ns['validate_fixed_selection'](x))
 ck('no live mutation '+str(i),not os.path.lexists(O.lane_root(i,'remote')))
ck('8 distinct roots',len(seen)==8)
inv=json.loads((D/'INVERSE01.json').read_bytes())
for name,changes in inv.items():
 s=(D/name).read_text()
 for old,new in reversed(changes):assert new in s;s=s.replace(new,old)
 ck('literal inverse '+name,s==(P/name).read_text());ck('AST inverse '+name,ast.dump(ast.parse(s))==ast.dump(ast.parse((P/name).read_text())))
for p in D.rglob('*'):
 if p.is_file() and (P/p.relative_to(D)).is_file() and p.name not in inv and p.name not in ('check01.py','INVERSE01.json'):ck('unchanged '+str(p.relative_to(D)),p.read_bytes()==(P/p.relative_to(D)).read_bytes())
enc=next(n for n in ast.parse((D/'recover.template01.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='encode');actual=next(n for n in ast.parse((D/'receipt01.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='encode');ck('encoder AST exact original',ast.dump(enc)==ast.dump(actual))
ck('no numerical imports',not set(('numpy','pandas','torch')).intersection(sys.modules))
(D/'CHECKS01.json').write_bytes(O.R.encode({'count':len(checks),'checks':checks,'scope':'read-only original failed selections + actual source functions; no public main, remote evidence or authority invented','new_review_proof_pending':True}));print(len(checks))
