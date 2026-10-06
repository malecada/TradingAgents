"""One runtime-inventory seam, pure injected module mocks. No real Torch import or admission."""
import ast,copy,hashlib,json,tempfile,types
from pathlib import Path
H=Path(__file__).resolve().parent;F=H.parent;R=F.parents[2];A=F/'real-data-pilot-final-preflight-preparation02-2026-10-06'
old=(A/'preflight01.py').read_bytes();new=(H/'preflight01.py').read_bytes()
assert new.replace(b'inventory(ROOT,include_torch=True)',b'inventory(ROOT)')==old
oldtree=ast.parse(old);newtree=ast.parse(new);calls=[n for n in ast.walk(newtree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='inventory'];assert len(calls)==1 and len(calls[0].keywords)==1 and calls[0].keywords[0].arg=='include_torch' and calls[0].keywords[0].value.value is True
inverse=copy.deepcopy(newtree);next(n for n in ast.walk(inverse) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='inventory').keywords=[];assert ast.dump(inverse)==ast.dump(oldtree)
# Execute the actual inventory function with every external dependency mocked.
env=ast.parse((R/'tradingagents/research/onchain_replication/environment.py').read_bytes());fn=next(n for n in env.body if isinstance(n,ast.FunctionDef) and n.name=='inventory');imports=[]
mocktorch=types.SimpleNamespace(cuda=types.SimpleNamespace(is_available=lambda:False),__version__='invented-torch',version=types.SimpleNamespace(cuda=None))
def mock_import(name,*args,**kwargs):
 assert name=='torch';imports.append(name);return mocktorch
ns={'__builtins__':{'__import__':mock_import},'Path':Path,'platform':types.SimpleNamespace(python_version=lambda:'invented-python'),'os':types.SimpleNamespace(cpu_count=lambda:2),'file_hash':lambda _: '0'*64,'importlib':types.SimpleNamespace(metadata=types.SimpleNamespace(version=lambda _: 'invented-package'))}
exec(compile(ast.Module([fn],type_ignores=[]),'<actual inventory with injected modules>','exec'),ns)
inventory=ns['inventory'];default=inventory(H);assert imports==[];selected=inventory(H,include_torch=True);assert imports==['torch'];assert set(selected)-set(default)=={'cuda_available','cuda_build','torch_version'}
def runtime_if(tree):return next(n for n in ast.walk(tree) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and isinstance(n.test.left,ast.Call) and isinstance(n.test.left.func,ast.Name) and n.test.left.func.id=='inventory')
with tempfile.TemporaryDirectory(dir=H) as tmp:
 root=Path(tmp);p=root/'environment.json';p.write_text(json.dumps(selected));space={'ROOT':root,'admission':types.SimpleNamespace(inputs={'environment':{'path':'environment.json'}}),'inventory':inventory,'json':json}
 try:exec(compile(ast.Module([runtime_if(oldtree)],type_ignores=[]),'<old actual runtime predicate>','exec'),space)
 except ValueError as e:assert str(e)=='installed runtime inventory differs'
 else:raise AssertionError('old must reject Torch-inclusive template')
 exec(compile(ast.Module([runtime_if(newtree)],type_ignores=[]),'<new actual runtime predicate>','exec'),space)
 p.write_text(json.dumps(dict(selected,torch_version='different')))
 try:exec(compile(ast.Module([runtime_if(newtree)],type_ignores=[]),'<new actual runtime predicate>','exec'),space)
 except ValueError:pass
 else:raise AssertionError('mismatch must remain fatal')
worker=ast.parse((R/'tradingagents/research/onchain_replication/job.py').read_bytes());kw=next(k for n in ast.walk(worker) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='inventory' for k in n.keywords if k.arg=='include_torch');assert eval(compile(ast.Expression(kw.value),'<worker selected kind>','eval'),{'job':{'kind':'compact_resource'}}) is True
owner=ast.parse((R/'tradingagents/research/onchain_replication/matching_owner.py').read_bytes());assert all(k.value.value is True for n in ast.walk(owner) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='inventory' for k in n.keywords if k.arg=='include_torch')
result={'decision':'pass','one_literal_inverse':True,'whole_module_ast_inverse':True,'old_runtime_predicate_refuses_actual_inclusive_schema':True,'new_runtime_predicate_accepts_inclusive_schema':True,'new_mismatch_still_refuses':True,'worker_and_owner_include_torch_match':True,'actual_numerical_or_torch_imports':False,'actual_admission_or_native':False,'source_sha256':hashlib.sha256(new).hexdigest()}
(H/'CHECKS03.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
