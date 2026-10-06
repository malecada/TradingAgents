"""Independent changed seams, stdlib metadata only; no genuine authority mocked."""
import ast,copy,hashlib,importlib.util,json,struct,sys,tempfile,types
from pathlib import Path
D=Path(__file__).parent;F=D.parent;M=F.parents[2];P=Path('tradingagents/research/onchain_replication')
T=F/'real-data-pilot-typed-score-tail-live-integration01-2026-10-06';O=F/'real-data-pilot-batch-output-live-integration01-2026-10-06';OC=O/'candidate'/P
h=lambda b:hashlib.sha256(b).hexdigest(); results={}
for name,root,pin in [('tail',T,'d81c1277e1e6639c6b0123949f6111975e7c567d8c64d861da1c6575819166bc'),('output',O,'7d83dfd16230ba55c5b9c397ff38fc6bdac0c9f590a5e6eab4e1979dd11b38c1')]:
 assert h((root/'MANIFEST01.json').read_bytes())==pin
 manifest=json.loads((root/'MANIFEST01.json').read_bytes())
 for member,row in manifest['files'].items():
  raw=(root/member).read_bytes();assert h(raw)==row['sha256'] and len(raw)==row['bytes'],member
 results[name+'_manifest_members']=len(manifest['files']); inverse=[]
 delta=json.loads((root/'SOURCE_DELTA01.json').read_bytes())
 for member,row in delta.items():
  source=(root/member if root==T else OC/member).read_bytes();assert h(source)==row['candidate_sha256'];ast.parse(source)
  if row.get('baseline'):
   original=Path(row['baseline']).read_bytes();assert h(original)==row['baseline_sha256'];lines=source.decode().splitlines(True)
   for edit in reversed(row['edits']):
    assert lines[edit['new_start']:edit['new_end']]==edit['new'];lines[edit['new_start']:edit['new_end']]=edit['old']
   assert ''.join(lines).encode()==original;inverse.append(member)
 results[name+'_exact_literal_ast_inverses']=inverse
for name in ('score_tail_archive.py','score_tail_semantics.py'):
 assert (T/name).read_bytes()==(F/'real-data-pilot-typed-tail-binding01-2026-10-06'/name).read_bytes()
deps=json.loads((O/'DEPENDENCIES_FINAL01.json').read_bytes());assert h((M/deps['manifest']['path']).read_bytes())==deps['manifest']['sha256']
for path,row in deps['sources'].items(): assert h((M/path).read_bytes())==row['sha256']
# Load the author's stdlib-only CONTENT fixture helpers; do not run prior test suite.
spec=importlib.util.spec_from_file_location('prior_content_fixture',O/'test_selected01.py');fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
m,typed,pol=fixture.m,fixture.typed,fixture.pol
# Cross: live operation history -> output reader, exact final read bound after a successful first part.
with tempfile.TemporaryDirectory(dir=D) as tmp:
 root,ref,args,body,ledger,ih=fixture.Controls().fixture(tmp)
 oldread=m.read_exact;calls=[]
 def observed(fd,n):calls.append(n);return oldread(fd,n)
 m.read_exact=observed
 m.inspect_output(root,ref,args);assert calls==[8,8]
 # Corrupt only final part content in local output; ordered earlier bytes don't authorize success.
 original=(root/'matrix.f32').read_bytes();(root/'matrix.f32').write_bytes(original[:8]+bytes([original[8]^1])+original[9:])
 try:m.inspect_output(root,ref,args)
 except ValueError:pass
 else:raise AssertionError('late final output mutation accepted')
 (root/'matrix.f32').write_bytes(original)
 # Cross-kind swap with a re-anchored tiny metadata fixture still fails kind/binding checks.
 ip=ledger/('typed-'+ih+'.json');v=json.loads(ip.read_bytes());v['kind']='score-tail-f64';badraw=pol.raw(v);badsha=pol.sha(badraw);(ledger/('typed-'+badsha+'.json')).write_bytes(badraw)
 oldproof=json.loads((root/'storage.json').read_bytes());history=dict(oldproof['history'],intent='typed-'+badsha+'.json',intent_sha256=badsha)
 try:typed.check_history(history,binding=oldproof['binding'],kind='mcm-output-f32')
 except ValueError:pass
 else:raise AssertionError('cross-kind history accepted')
 m.read_exact=oldread
results['history_to_output_cross_seam']='ordered local full output and late mutation refusal; foreign kind refuses'
# Pure registered capacity reconstruction for all three kinds: original full populations;
# every preserved part has mkdir+put+fresh get, every explicit restore adds one get.
kinds={k:dict(max_operations=4,max_preserved_bytes=32*w,max_recovered_bytes=64*w,max_chunks=12,chunk_bytes=2560 if k=='score-tail-f64' else 256) for k,w in pol.KINDS.items()}
value=dict(schema_version=1,format='typed-payload-budget-v1',assumption=pol.ASSUMPTION,graphs={'a'*64:dict(rows=1,chunk_cells=32,kinds=kinds)},local_free_floor_bytes=10*1024**3,max_control_bytes=100000)
cap=pol.capacity(value);expected=sum(2*b['max_preserved_bytes']+b['max_recovered_bytes'] for b in kinds.values())
assert cap['logical_bytes']==expected and cap['rounded_bytes']==expected+2*36*65536 and cap['commands']==4*36
for key in ('score-tail-f64','score-batch-f64','mcm-output-f32'):
 bad=copy.deepcopy(value);bad['graphs']['a'*64]['kinds'][key]['max_preserved_bytes']-=1
 try:pol.validate(bad)
 except ValueError:pass
 else:raise AssertionError(key)
results['three_kind_capacity']=cap
# Same shared counter: execute exact reservation arithmetic before the transport try.
tree=ast.parse((T/'typed_payload_operations.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='_Operation');recover=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='recover')
start=next(i for i,n in enumerate(recover.body) if isinstance(n,ast.AugAssign) and ast.unparse(n.target)=="self.counter['recovered']")
end=next(i for i,n in enumerate(recover.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='previous' for t in n.targets))
code=compile(ast.fix_missing_locations(ast.Module(body=recover.body[start:end],type_ignores=[])),'actual-recovery-reservations','exec')
seen=[]; counter={'operations':1,'preserved':80,'recovered':0,'chunks':1};registry={'x':counter};context=types.SimpleNamespace(_spent={'logical_bytes':160},_record={'capacity':{'logical_bytes':240}});self=types.SimpleNamespace(counter=counter,registry=registry,ledger=types.SimpleNamespace(),budget={'max_recovered_bytes':80,'max_chunks':2},context=context,recovered=0,sha='a'*64,_publish=lambda *a:seen.append(a))
g={'self':self,'n':80,'policy':pol,'require':pol.require,'canonical_bytes':lambda v:json.dumps(v,sort_keys=True,separators=(',',':')).encode(),'receipt':{'synthetic':True}}
exec(code,g);assert counter['recovered']==80 and counter['chunks']==2 and context._spent['logical_bytes']==240
try:exec(code,g)
except ValueError:pass
else:raise AssertionError('cumulative recovery refund/bypass')
assert counter['recovered']==160 and counter['chunks']==3 and context._spent['logical_bytes']==240
results['shared_reservation']='accepted first charge, overrun refuses without refund; no transport/Owner constructed'
# Original cast and matrix/memmap expressions remain structurally identical.
out=ast.parse((OC/'compact_mcm_output.py').read_text());fn={n.name:n for n in out.body if isinstance(n,ast.FunctionDef)}
def cast(f):return ast.dump(next(n for n in ast.walk(f) if isinstance(n,ast.With) and any(ast.unparse(x.context_expr).startswith('np.errstate(') for x in n.items)),include_attributes=False)
assert cast(fn['_chunks'])==cast(fn['_archived_chunks'])
assert "imported_result['completed_pairs']==0" in (T/'archive_owner_seal.py').read_text()
assert 'typed_payload_operations, typed_score_store, typed_tail_binding, mcm_raw_parts' in (T/'archive_dispatch.py').read_text()
assert not {'numpy','torch','scipy','networkx'}&set(sys.modules)
results.update(decision='passed-offline-changed-seams',genuine_authority_constructed=False,numerical_imports=False,native_or_network=False)
(D/'CHECK01.json').write_text(json.dumps(results,indent=2,sort_keys=True)+'\n');print(json.dumps(results,sort_keys=True))
