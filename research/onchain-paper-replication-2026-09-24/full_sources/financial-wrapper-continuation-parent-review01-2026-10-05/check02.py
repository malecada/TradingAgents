from pathlib import Path
import ast,copy,hashlib,importlib.util,json,stat,sys
D=Path(__file__).resolve().parent;P=D.parent/'financial-wrapper-continuation-parent-preparation01-2026-10-05';sys.path.insert(0,str(P));import build01 as B;import parent01 as A
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();checks=[]
def ck(n,v):
 assert v,n;checks.append(n)
def refuse(n,f):
 try:f()
 except (ValueError,TypeError,KeyError):checks.append(n);return
 raise AssertionError(n)
m=json.loads((P/'MANIFEST01.json').read_bytes());ck('sealed manifest',h(P/'MANIFEST01.json').startswith('7a18c277'))
for r in m['members']:
 p=P/r['path'];s=p.lstat();ck('mode '+r['path'],stat.S_IMODE(s.st_mode)==r['mode'])
 if r['kind']=='file':ck('body '+r['path'],stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and h(p)==r['sha256'])
ck('whole membership',{r['path'] for r in m['members']}=={str(p.relative_to(P)) for p in P.rglob('*') if p.name!='MANIFEST01.json'})
a=(P/'original_parent01.py').read_text();b=(P/'parent01.py').read_text();inv=json.loads((P/'INVERSE01.json').read_bytes());ck('13 edits',len(inv['edits'])==13);back=b
for e in reversed(inv['edits']):ck('unique inverse '+e['old'][:30],back.count(e['new'])==1);back=back.replace(e['new'],e['old'])
ck('literal inverse',back==a);ck('AST inverse',ast.dump(ast.parse(back))==ast.dump(ast.parse(a)))
f=lambda s:{n.name:ast.dump(n) for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
for n,v in f(a).items():
 if n not in ('validate_release','preflight'):ck('unchanged native/lifecycle AST '+n,f(b)[n]==v)
oldroot=Path(str(A.PARENT).replace('continue100-compatibility-root-launch-20261005-01','complete100-compatibility-root-launch-20261004-01'))
for name in ('supervisor01.py','descendants01.py','recovery04.py','owned_io.py','bounded_git01.py','PROTOCOL_PINS01.json'):ck('actual helper '+name,(P/name).read_bytes()==(oldroot/name).read_bytes())
prior=D.parent/'financial-wrapper-continuation-proof-reuse-review01-2026-10-05';pr=json.loads((prior/'MACHINE01.json').read_bytes());ck('reuse accepted review',h(prior/'MACHINE01.json')=='e7b347fc0242d488636eeea80f5c3aa367a476871a6169e21aabf4ddf519db92');ck('reuse same helper',h(P/'preclaim01.py')==pr['source_sha256'])
q=json.loads((P/'REQUEST_DRAFT01.json').read_bytes());refuse('unbound Parent draft',lambda:A.validate_release(q));ck('29 null future roles',q['input_hashes'] is None)
refuse('full builder authentic dependencies then missing source',lambda:B.build({'path':str(P/'SOURCE_MANIFEST_DRAFT01.json'),'sha256':h(P/'SOURCE_MANIFEST_DRAFT01.json')},{'path':str(P/'proof_reuse_contract01.json'),'sha256':h(P/'proof_reuse_contract01.json')}))
g=json.loads((P/'GATE4_DRAFT01.json').read_bytes());oldraw=(B.CAP/B.OLD_GATE).read_bytes();old=json.loads(oldraw);ck('actual old13 exact',len(old['experiments'])==13 and hashlib.sha256(oldraw).hexdigest()==B.OLD_GATE_SHA)
ck('4 definitions',len(g['experiments'])==4);ck('29 roles',len(g['experiments'][B.ID]['inputs'])==29)
for identity,e in g['experiments'].items():
 if identity not in (B.ID,B.PRED):ck('exact original parent '+identity,e==old['experiments'][identity])
ck('15 distinct definitions',len(set(g['experiments'])|set(old['experiments']))==15)
for label,fn in [('parent',lambda x:x['experiments'][B.ID].update(parent=None)),('budget',lambda x:x['families'][x['experiments'][B.ID]['family']].update(attempt_budget=21)),('role',lambda x:x['experiments'][B.ID]['inputs'].pop('model')),('hash',lambda x:x['experiments'][B.ID]['inputs']['reference_state'].update(sha256='0'*64))]:
 x=copy.deepcopy(g);fn(x);refuse(label,lambda:B.validate_gate(x,g,g['experiments'][B.ID]['source_files']))
c=json.loads((P/'proof_reuse_contract01.json').read_bytes());refuse('missing recovery',lambda:B.validate_reuse(c,c,None,B.Reads()))
ck('global accounting reused genuine4/20',pr['global_claims']==4 and pr['ceiling']==20)
ck('runtime251',len(q['runtime_mapping']['distribution_records'])==251)
ck('no numerical import',not set(('numpy','torch','pandas')).intersection(sys.modules))
(D/'CHECKS01.json').write_text(json.dumps({'checks':checks,'count':len(checks),'public_preflight':False,'builder_success':False,'prior_review_reused':h(prior/'MACHINE01.json')},indent=2)+'\n');print(len(checks))
