"""Stdlib parser and extracted forwarding checks; no authority/numerics."""
import ast,builtins,copy,hashlib,json,os,resource,signal,types
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3];F=P.parent
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(20,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(25);assert os.sched_getaffinity(0)=={3}
checks=[]
def ok(n,v=True):assert v,n;checks.append(n)
original=builtins.__import__
def guarded(name,*a,**kw):
 assert name.split('.')[0] not in {'numpy','scipy','torch','ctypes','tradingagents'},name
 return original(name,*a,**kw)
builtins.__import__=guarded
policy=types.ModuleType('metadata');exec(compile((F/'matching-compiled-normalization-connected04-2026-10-10/compiled_normalization_policy.py').read_text(),'accepted04 parser','exec'),policy.__dict__)
tree=ast.parse((P/'compact_mcm_batched.py').read_text());functions={x.name:x for x in tree.body if isinstance(x,ast.FunctionDef)}
ns=dict(compiled_normalization_policy=policy,require=policy.require,FORMAT='ordered-mcm-batch-closure-v2',adaptive_edge_policy=types.SimpleNamespace(freeze=lambda x:tuple(x.items())))
for name in ('selected','_compiled_policy','validate'):
 exec(compile(ast.Module(body=[copy.deepcopy(functions[name])],type_ignores=[]),'actual candidate '+name,'exec'),ns)
base=dict(schema_version=5,max_entries=32,max_workflow_metadata_bytes=65536,numeric={},batched=dict(format=ns['FORMAT'],authority_boundaries='entry-batch-checkpoint-final',batch_cells=32,max_journal_bytes=100000,max_body_bytes=1024,max_closure_token_bytes=1000,max_checkpoint_bytes=65536,retention='local-v2',max_spool_bytes=1024,max_offload_metadata_bytes=1024,max_offload_entries=32,max_offload_anchor_bytes=0,execution=dict(route='immutable-input-session+exact-byte-reuse-v1',max_entries=2,max_retained_bytes=4096,max_key_bytes=1024,max_origin_bytes=288,max_summary_bytes=8192)))
value=json.loads((F/'matching-compiled-runtime-input01-2026-10-10/POLICY01.json').read_text())
roles=dict(source='compiled_source',library='compiled_library',runtime='compiled_runtime')
ok('legacy schema unchanged',ns['validate'](base,32) is base['batched'] and ns['_compiled_policy'](base['batched']['execution']) is None)
selected=copy.deepcopy(base);selected['batched']['execution'].update(compiled_normalization_policy=value,compiled_normalization_inputs=roles)
ok('selected metadata parser accepts exact04 policy',ns['validate'](selected,32) is selected['batched'] and dict(ns['_compiled_policy'](selected['batched']['execution']))==value)
for label,mutate in (
 ('none',lambda e:e.update(compiled_normalization_policy=None)),
 ('false',lambda e:e.update(compiled_normalization_policy=False)),
 ('missing roles',lambda e:e.pop('compiled_normalization_inputs')),
 ('orphan roles',lambda e:e.pop('compiled_normalization_policy')),
 ('unknown execution key',lambda e:e.update(unregistered=1)),
 ('duplicate roles',lambda e:e.update(compiled_normalization_inputs=dict(source='x',library='x',runtime='z'))),
 ('environment role reused',lambda e:e.update(compiled_normalization_inputs=dict(source='environment',library='x',runtime='z'))),
 ('path role',lambda e:e.update(compiled_normalization_inputs=dict(source='../x',library='x',runtime='z'))),
 ('bad policy',lambda e:e['compiled_normalization_policy'].update(library_sha256='0'*64))):
 test=copy.deepcopy(selected);mutate(test['batched']['execution'])
 try:ns['validate'](test,32)
 except (ValueError,TypeError,KeyError):ok('refusal '+label)
 else:raise AssertionError(label)
# Evaluate exact actual kwargs expression only, never NumericExecution itself.
call=next(n for n in ast.walk(functions['_compute']) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='NumericExecution')
keyword=next(k.value for k in call.keywords if k.arg is None and 'compiled_normalization_policy_value' in ast.unparse(k.value))
for execution,expected in ((base['batched']['execution'],{}),(selected['batched']['execution'],{'compiled_normalization_policy_value':value})):
 ok('actual conditional forwarding '+str(bool(expected)),eval(compile(ast.Expression(keyword),'actual forwarding','eval'),dict(ns,execution=execution))==expected)
for name,tokens in {
 '_compiled_inputs':("run.read_input(role)","run.read_input('environment')","info['sha256']", "runtime['runtime_inventory_sha256']",'path.resolve() == path','owned=kind == \'library\''),
 '_modules':("'compiled_normalization_policy'","'compiled_small_lse'","'matching_annealing'","'matching_checkpoint'","admission.experiment['source_files']"),
 'produce':('_compiled_inputs',"compiled_normalization_policy.freeze(binding['numeric_execution'].get('compiled_normalization_policy')) == normalization",'_compiled_policy(b[\'execution\']) == normalization','owner.boundary()', 'target.check()'),
 'stage_content':('_compiled_inputs', 'stage.owner.bound._run.read_input'),
 'verify_content':("binding['numeric_execution'].get('compiled_normalization_policy')",'numeric_execution')}.items():
 source=ast.unparse(functions[name])
 for token in tokens:ok('genuine connection source '+name+': '+token,token in source)
# Exact inverse and AST preservation of every unrelated top-level body.
s=(P/'compact_mcm_batched.py').read_text();inverse=json.loads((P/'LITERAL_INVERSE01.json').read_text())
for change in reversed(inverse['changes']):assert s.count(change['after'])==1;s=s.replace(change['after'],change['before'],1)
original_body=(R/inverse['baseline_path']).read_text();ok('exact current installed inverse',s==original_body and hashlib.sha256(s.encode()).hexdigest()==inverse['baseline_sha256'])
changed={'validate','_modules','verify_content','stage_content','_compute','produce','_compiled_policy','_compiled_inputs'}
a=ast.parse(original_body);b=ast.parse((P/'compact_mcm_batched.py').read_text())
for t in (a,b):t.body=[n for n in t.body if not isinstance(n,ast.FunctionDef) or n.name not in changed]
b.body=[n for n in b.body if not (isinstance(n,ast.ImportFrom) and any(x.name=='compiled_normalization_policy' for x in n.names))]
ok('unchanged AST outside enumerated seams',ast.dump(a)==ast.dump(b))
result=dict(status='PASS_STDLIB_SOURCE_PARSER_FORWARDING_ONLY',checks=checks,count=len(checks),actual_authority=False,scientific_imports=False,numerical_execution=False)
(P/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],len(checks))
