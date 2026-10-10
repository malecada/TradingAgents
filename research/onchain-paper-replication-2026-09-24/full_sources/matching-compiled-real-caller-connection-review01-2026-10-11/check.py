import ast,copy,hashlib,json,resource,signal,types
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);signal.alarm(20)
P=Path(__file__).resolve().parent;R=P.parents[3];F=P.parent;C=F/'matching-compiled-real-caller-connection01-2026-10-11'
refs={};checks=[]
def read(p):
 b=p.read_bytes();assert len(b)<262144;refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};return b
def ok(n,v):assert v,n;checks.append(n)
m=json.loads(read(C/'MANIFEST01.json'));ok('manifest Root pin',hashlib.sha256((C/'MANIFEST01.json').read_bytes()).hexdigest()=='5335ced64061c9c96326561f10fedbcb2ed372b712f441cab23cc9ddc0fc826b')
for name,x in m['files'].items():b=read(C/name);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
for name,x in m['references'].items():b=read(F/name);assert hashlib.sha256(b).hexdigest()==x['sha256']
body=read(C/'compact_mcm_batched.py');ok('candidate Root pin',hashlib.sha256(body).hexdigest()=='8f559c4030a1bf69e678337bb68216115943b0a6ae2a0e8100601557c6d81c77')
inverse=json.loads(read(C/'LITERAL_INVERSE01.json'));s=body.decode()
for change in reversed(inverse['changes']):assert s.count(change['after'])==1;s=s.replace(change['after'],change['before'],1)
ok('literal inverse current Main',s.encode()==read(R/inverse['baseline_path']))
t=ast.parse(body);fs={n.name:n for n in t.body if isinstance(n,ast.FunctionDef)};compile(t,'<source-only>','exec')
# Extract only pure metadata parser definitions; no backend or authority module execution.
low=ast.parse(read(F/'matching-compiled-normalization-connected04-2026-10-10/compiled_normalization_policy.py'));ns={'Path':Path}
allowed={'HELPER_SHA256','LIBRARY_SHA256','SOURCE_SHA256','FORMAT','FIELDS'}
nodes=[n for n in low.body if (isinstance(n,ast.Assign) and any(isinstance(a,ast.Name) and a.id in allowed for a in n.targets)) or (isinstance(n,ast.FunctionDef) and n.name in {'require','digest','freeze'})]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<accepted-pure-parser>','exec'),ns)
env={'compiled_normalization_policy':types.SimpleNamespace(freeze=ns['freeze']),'require':ns['require']}
exec(compile(ast.Module(body=[copy.deepcopy(fs['_compiled_policy'])],type_ignores=[]),'<candidate-pure-parser>','exec'),env)
policy={'format':ns['FORMAT'],'library_path':'/synthetic/library.so','library_sha256':ns['LIBRARY_SHA256'],'source_path':'/synthetic/source.c','source_sha256':ns['SOURCE_SHA256'],'runtime_path':'/synthetic/runtime.json','runtime_sha256':'1'*64,'runtime_bytes':100}
# Synthetic strings are parser-only, never a runtime file/policy or authority.
base={'compiled_normalization_policy':policy,'compiled_normalization_inputs':{'source':'c_source','library':'c_library','runtime':'c_runtime'}}
ok('absence no selection',env['_compiled_policy']({}) is None)
ok('parse exact fields',dict(env['_compiled_policy'](base))==policy)
for name,change in [('null',lambda x:x.update(compiled_normalization_policy=None)),('false',lambda x:x.update(compiled_normalization_policy=False)),('orphan',lambda x:x.pop('compiled_normalization_policy')),('missing roles',lambda x:x.pop('compiled_normalization_inputs')),('extra role',lambda x:x['compiled_normalization_inputs'].update(extra='other')),('reserved environment',lambda x:x['compiled_normalization_inputs'].update(source='environment')),('unicode role',lambda x:x['compiled_normalization_inputs'].update(source='α')),('path role',lambda x:x['compiled_normalization_inputs'].update(source='a/b')),('duplicate role',lambda x:x['compiled_normalization_inputs'].update(source='c_runtime')),('boolean bytes',lambda x:x['compiled_normalization_policy'].update(runtime_bytes=True))]:
 x=copy.deepcopy(base);change(x)
 try:env['_compiled_policy'](x)
 except (ValueError,TypeError,KeyError):ok('refuse '+name,True)
 else:raise AssertionError(name)
call=next(n for n in ast.walk(fs['_compute']) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='NumericExecution')
kw=next(k.value for k in call.keywords if k.arg is None and 'compiled_normalization_policy_value' in ast.unparse(k.value))
for x,result in [({},{}),(base,{'compiled_normalization_policy_value':policy})]:ok('actual forwarding '+str(bool(x)),eval(compile(ast.Expression(kw),'<kwargs-only>','eval'),dict(env,execution=x))==result)
changed={'validate','_compiled_policy','_compiled_inputs','_modules','verify_content','stage_content','_compute','produce'}
a=ast.parse(s);b=copy.deepcopy(t)
for q in [a,b]:q.body=[n for n in q.body if not isinstance(n,ast.FunctionDef) or n.name not in changed]
b.body=[n for n in b.body if not (isinstance(n,ast.ImportFrom) and any(x.name=='compiled_normalization_policy' for x in n.names))]
ok('unrelated AST preserved',ast.dump(a)==ast.dump(b))
for file in ['tradingagents/research/lifecycle.py','tradingagents/research/onchain_replication/compact_mcm.py','tradingagents/research/onchain_replication/imported_mcm_identity.py']:read(R/file)
author=json.loads(read(C/'RESULT01.json'));ok('author35 reused',author['count']==35)
result={'status':'PASS_SOURCE_PARSER_FORWARDING_ONLY','checks':checks,'count':len(checks),'references':refs,'authority_or_input_reader_executed':False,'scientific_native_execution':False,'author35_reexecuted':False}
(P/'RESULT01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print('PASS',len(checks))
