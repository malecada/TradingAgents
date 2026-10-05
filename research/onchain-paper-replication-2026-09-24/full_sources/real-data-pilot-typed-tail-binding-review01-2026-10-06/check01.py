"""Independent offline changed-seam checks; no actual native/transport capability."""
import ast,hashlib,importlib.util,io,json,resource,sys,tempfile,types
from pathlib import Path
D=Path(__file__).parent; F=D.parent; A=F/'real-data-pilot-typed-tail-binding01-2026-10-06'; M=F.parents[2]
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(A/'MANIFEST01.json')=='7ce0f20f09e399ef6f12d17a42905daf73ff2c632b0db0106e7a69bfa08e0497'
manifest=json.loads((A/'MANIFEST01.json').read_bytes())
for name,row in manifest['files'].items(): assert h(A/name)==row['sha256'] and (A/name).stat().st_size==row['bytes'],name
for name,sha in json.loads((A/'DEPENDENCIES_FINAL01.json').read_bytes()).items(): assert h(M/name)==sha,name
spec=importlib.util.spec_from_file_location('author_fixture_only',A/'test_binding01.py'); fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture); a=fixture.a
# Actual source branches; imports replaced solely with explicit offline test doubles.
tree=ast.parse((A/'typed_tail_binding.py').read_text()); funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
class NoImports(ast.NodeTransformer):
 def visit_Import(self,node): return ast.copy_location(ast.Pass(),node)
 def visit_ImportFrom(self,node): return ast.copy_location(ast.Pass(),node)
transport_tree=ast.parse((M/'tradingagents/research/onchain_replication/archive_transport.py').read_text())
classes=[n for n in transport_tree.body if isinstance(n,ast.ClassDef) and n.name in ('Transport','Budget')]
classenv={};exec(compile(ast.fix_missing_locations(ast.Module(body=classes,type_ignores=[])),'original-class-AST','exec'),classenv)
Budget,Transport=classenv['Budget'],classenv['Transport']
readback=[4*1024**2,4*1024**2]; calls=[]
spy=types.SimpleNamespace(preserve=lambda **kw:(calls.append(('preserve',kw)) or {'synthetic':True}))
env=dict(vars(a));env.update(Transport=Transport,Budget=Budget,archive_chunks=spy,resource=types.SimpleNamespace(RLIMIT_FSIZE=resource.RLIMIT_FSIZE,getrlimit=lambda _:tuple(readback)))
selected=[NoImports().visit(funcs[n]) for n in ('_transport','preserve_chunk','retrieve_chunk')]
exec(compile(ast.fix_missing_locations(ast.Module(body=selected,type_ignores=[])),'actual-wrapper-AST-offline-imports','exec'),env)
def refuses(fn,expected=ValueError):
 try:fn()
 except expected:return
 raise AssertionError('expected refusal')
with tempfile.TemporaryDirectory(dir=D) as scratch:
 root=Path(scratch); b,body,payload,_=fixture.fixture(root); chunks=[]
 result=a.verify(b,io.BytesIO(body).read,io.BytesIO(payload).read,lease=lambda:None,max_seconds=10,emit=chunks.append)
 assert result['records']==544 and result['authority'] is None and not result['whole_roster_verified']
 provisional=[]
 refuses(lambda:a.verify(b,io.BytesIO(body+b'X').read,io.BytesIO(payload).read,lease=lambda:None,max_seconds=10,emit=provisional.append))
 assert len(provisional)==1 and provisional[0].descriptor()['provisional'] is True and provisional[0].raw==body[:40960]
 assert a.verify_recovery(b,iter(chunks),io.BytesIO(payload).read,lease=lambda:None,max_seconds=10)==result
 pluszero=b'\x00'*8+payload[8:]
 refuses(lambda:a.verify_recovery(b,iter(chunks),io.BytesIO(pluszero).read,lease=lambda:None,max_seconds=10))
 c=a.bank.decode(b.contract_raw);t=object.__new__(Transport);t.identity=c['transport_identity'];t.budget=Budget(1000000);t.max_seconds=10;t.rate_bytes=1024;t.live=lambda:None
 # Real class AST + selected field branches, but no constructor/SSH/native calls.
 env['_transport'](b,c,t)
 for invalid in [(-1,-1),(65536,4*1024**2),(4*1024**2,-1)]:
  readback[:]=invalid;refuses(lambda:env['_transport'](b,c,t))
 readback[:]=[4*1024**2,4*1024**2]
 t.budget.remaining=-1;refuses(lambda:env['_transport'](b,c,t));t.budget.remaining=1000000
 args=dict(source=root/'source',attempt=root/'attempt',remote=c['remote']+'-part-000000',transport=t,lease=lambda:None,free_floor_bytes=1)
 refuses(lambda:env['preserve_chunk'](b,chunks[0],**{**args,'remote':c['remote']+'-part-000001'}));assert not calls
 env['preserve_chunk'](b,chunks[0],**args)
 kw=calls[-1][1];d=chunks[0].descriptor();assert kw['scope']==a.bank.digest(a.bank.encode(d)) and kw['expected_sha256']==d['sha256'] and kw['expected_bytes']==40960 and kw['transport'] is t
 # Tiny synthetic receipt and payload exercise typed retrieval gate, not archive/network proof.
 receipt=root/'receipt';receipt.mkdir();recovered=root/'recovered';recovered.mkdir();p=recovered/'payload.bin';p.write_bytes(chunks[0].raw)
 v=dict(schema_version=1,format='archive-chunk-v1',transport_identity=t.identity,remote=args['remote'],member=args['remote']+'/payload.bin',scope=kw['scope'],source_sha256=d['sha256'],bytes=d['bytes'])
 def retrieval(*pos,**kw):calls.append(('retrieve',kw));return p
 spy.retrieve=retrieval
 def retrieve():
  raw=a.bank.encode(v);(receipt/'complete.json').write_bytes(raw)
  return env['retrieve_chunk'](b,d,receipt_root=receipt,receipt_sha256=a.bank.digest(raw),attempt=root/'recovery-attempt',transport=t,lease=lambda:None,free_floor_bytes=1)
 assert retrieve()==chunks[0]
 count=len(calls);v['remote']=c['remote']+'-part-000001';refuses(retrieve);assert len(calls)==count
 refuses(lambda:a.activate(b))
assert not {'numpy','torch','scipy','networkx'}&set(sys.modules)
result={'decision':'passed-focused-offline-seams','candidate_sha256':h(A/'typed_tail_binding.py'),'manifest_sha256':h(A/'MANIFEST01.json'),'members_authenticated':len(manifest['files']),'checks':['late EOF failure leaves emitted chunks provisional and returns no completion','original -0.0 versus +0.0 batch bits refuse, ordered recovery succeeds','exact Transport/Budget AST fields and finite native-readback branches','preserve/retrieve remote-index and descriptor binding before transport call'],'qualification':'Synthetic original append fixture; extracted transport branches use offline mocks. No original authority, native limit change, transport process, raw graph, credentials, or numerical imports.'}
(D/'CHECK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
