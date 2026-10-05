from pathlib import Path
import importlib.util,hashlib,json,tempfile,ast
D=Path(__file__).resolve().parent;A=D.parent/'real-data-pilot-first-graph-preservation-worker01-2026-10-06';M=D.parents[3]
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(A/'MANIFEST01.json')=='2178a962c6f91f9821430b010eb39dfaec4fd6d09778d30bfa28452ddc23d2ac'
m=json.loads((A/'MANIFEST01.json').read_text())
assert {p.name for p in A.iterdir()}==set(m['files'])|{'MANIFEST01.json'}
for name,pin in m['files'].items():assert h(A/name)==pin and (A/name).stat().st_mode&0o777==0o444
inv=json.loads((A/'INVERSE01.json').read_text());old=Path(inv['baseline']).read_text();new=(A/'keep.py').read_text()
assert h(Path(inv['baseline']))==inv['baseline_sha256']
old_tree=ast.parse(old);new_tree=ast.parse(new)
a=next(n for n in old_tree.body if isinstance(n,ast.FunctionDef) and n.name=='offload_one');b=next(n for n in new_tree.body if isinstance(n,ast.FunctionDef) and n.name=='keep_one')
assert ast.get_source_segment(old,a)+'\n'==inv['original_function'];assert ast.get_source_segment(new,b)+'\n'==inv['candidate_function']
assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('unlink','remove','rmdir','rmtree','rename','replace') for n in ast.walk(new_tree))
spec=importlib.util.spec_from_file_location('independent_keep',A/'keep.py');k=importlib.util.module_from_spec(spec);spec.loader.exec_module(k);base=k.bind_primitives(M)
class SyntheticTransport:
 def __init__(self,source):self.data={};self.source=source;self.calls=[]
 def put(self,path,key):self.data[key]=path.read_bytes();self.calls.append(('put',key))
 def get(self,key,path):
  path.write_bytes(self.data[key]);self.calls.append(('get',key))
  if key.endswith('-restore.json'):self.source.write_bytes(b'externally changed tiny original')
with tempfile.TemporaryDirectory(dir=D) as tmp:
 root=Path(tmp);here=root/'preserve';here.mkdir();source=root/'tiny';original=b'tiny original';source.write_bytes(original)
 row={'path':'tiny','bytes':len(original),'sha256':h(source),'stat_identity':base.identity(source.stat()),'mode':source.stat().st_mode,'nlink':1};t=SyntheticTransport(source)
 try:k.keep_one(root,here,row,0,'synthetic-no-network',t,primitives=base)
 except ValueError as e:assert 'source identity changed' in str(e);refusal=str(e)
 else:raise AssertionError('changed original accepted')
 assert source.exists() and (here/'00-recovered.bin').read_bytes()==original
 assert (here/'00-restore.json').read_bytes()==(here/'00-recovered-restore.json').read_bytes()
 assert not (here/'00-verified.json').exists() and not (here/'00-kept.json').exists()
 assert not list(root.glob('*.remote.json'))
record={'schema_version':1,'source_sha256':h(A/'keep.py'),'source_manifest_sha256':h(A/'MANIFEST01.json'),'authenticated_members':len(m['files']),'exact_original_and_derivative_function_bodies':True,'no_delete_or_replace_calls':True,'independent_post_get_source_drift_refusal':refusal,'successful_fullget_copies_retained_on_drift':True,'real_payload_reads':False,'real_network_native_or_claims':False}
(D/'SOURCE_CHECK01.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n');print(json.dumps(record))
