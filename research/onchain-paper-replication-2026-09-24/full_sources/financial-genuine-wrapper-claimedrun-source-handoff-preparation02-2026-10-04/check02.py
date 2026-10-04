import ast,copy,json,sys
import generate01 as G
checks=[]
def ok(v,n):assert v,n;checks.append(n)
def refuse(f,n):
 try:f()
 except ValueError:checks.append(n)
 else:raise AssertionError(n)
r=G.OLD/'fixture_inputs/financial_wrapper_recordfix01'
c,j,p=[json.loads(G.read(r/(n+'.json'))) for n in ('source_closure','execution_job','wrapper_plan')]
candidate=G.read(G.H/'candidate.py');a,b,d=G.derive(c,j,p,candidate)
z=copy.deepcopy(a);z['installed'][G.WRAPPER]=c['installed'][G.WRAPPER];ok(z==c,'closure one-body inverse')
z=copy.deepcopy(b);z['resources']['disk_paths']=j['resources']['disk_paths'];z['resources']['storage_budget']['root']=j['resources']['storage_budget']['root'];ok(z==j,'job exact root-only inverse')
z=copy.deepcopy(d);z['experiment']=p['experiment'];z['namespace']=p['namespace'];ok(z==p,'plan exact identity-only inverse')
for n in c['installed']:
 if n!=G.WRAPPER:ok(a['installed'][n]==c['installed'][n],'unchanged '+n)
for k in list(c['installed'])[:8]:
 v=copy.deepcopy(c);v['installed'].pop(k);refuse(lambda:G.derive(v,j,p,candidate),'missing '+k)
refuse(lambda:G.derive(c,j,p,candidate+b'\n'),'wrong candidate')
v=copy.deepcopy(c);v['installed']['extra.py']='0'*64;refuse(lambda:G.derive(v,j,p,candidate),'extra source')
# Actual pure schema functions only; no admission, Run or numerical imports.
tree=ast.parse(candidate);names={'require','validate_plan','schema'};body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
ns={'Unavailable':ValueError,'PHASES':('agreement','interrupt1','complete100','continue100','predict'),'FILE':G.FILE,'GIB':1024**3}
exec(compile(ast.Module(body=body,type_ignores=[]),'<actual wrapper pure schemas>','exec'),ns)
ns['schema'](b);ns['validate_plan'](d);ok(True,'actual wrapper job and plan schema')
for key in ('memory_high_bytes','memory_max_bytes','reserve_bytes','start_reserve_bytes','wall_seconds','disk_floor_bytes'):
 v=copy.deepcopy(b);v['resources'][key]=0;refuse(lambda:ns['schema'](v),'native refusal '+key)
for n,raw in G.build().items():ok(G.read(G.H/'generated01'/n)==raw,'deterministic '+n)
ok(not any(n.split('.')[0] in ('numpy','torch','pandas') for n in sys.modules),'no numerical imports')
(G.H/'CHECKS02.json').write_bytes(G.enc({'count':len(checks),'checks':checks,'actual_admission':False,'target_created':False,'claims':0}))
print(json.dumps({'checks':len(checks),'status':'passed'}))
