import ast,hashlib,importlib,importlib.util,json,os,resource,sys,types
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT))
assert resource.getrlimit(resource.RLIMIT_AS)[0]==268435456 and resource.getrlimit(resource.RLIMIT_FSIZE)[0]==4194304 and len(os.sched_getaffinity(0))==2
package=types.ModuleType('offload02_fixture');package.__path__=[str(P),str(ROOT/'tradingagents/research/onchain_replication')];sys.modules[package.__name__]=package
policy=importlib.import_module('offload02_fixture.typed_payload_policy');semantic=importlib.import_module('offload02_fixture.batched_offload_semantics');adapter=importlib.import_module('offload02_fixture.registered_offload')
spec=importlib.util.spec_from_file_location('journal03',P.parent/'mcm-batched-execution03-2026-10-09/batch_journal.py');jmod=importlib.util.module_from_spec(spec);spec.loader.exec_module(jmod)
budget=dict(max_operations=10,max_preserved_bytes=1000000,max_recovered_bytes=2000000,max_chunks=30,chunk_bytes=524288)
base={'schema_version':1,'format':'typed-payload-budget-v1','assumption':policy.ASSUMPTION,'graphs':{'a'*64:{'rows':1,'chunk_cells':32,'kinds':{k:dict(budget) for k in policy.LEGACY_KINDS}}},'local_free_floor_bytes':0,'max_control_bytes':1000000}
policy.validate(base);v2=json.loads(json.dumps(base));v2.update(schema_version=2,format='typed-payload-budget-v2');v2['graphs']['a'*64]['kinds'][policy.BATCHED_KIND]=dict(budget);policy.validate(v2)
bad=json.loads(json.dumps(v2));bad.update(schema_version=1,format='typed-payload-budget-v1')
try:policy.validate(bad)
except ValueError:pass
else:raise AssertionError('legacy silently grants newkind')
# No fake Owner/Stage: actual missing-selection route refuses, never transport/deletion.
try:adapter._selected(None,None)
except ValueError as e:assert 'not genuinely selected' in str(e)
else:raise AssertionError('unselected admitted')
j=jmod.BatchJournal(P/'source',batch_cells=2,max_cells=2,max_bytes=100000,max_body_bytes=8192,boundary=lambda:None)
j.run_batch_stream(2,iter([({'ordinal':i},None,None) for i in range(2)]),lambda *x:(0.,1,'iteration_cap'),{'fixture':True})
tokens=bytearray();rows=[]
for suffix in semantic.SUFFIXES:
 raw,pin=j._read('00000000'+suffix);tokens.extend(semantic.TOKEN.pack(*pin,len(raw),hashlib.sha256(raw).digest()));path=j.root/('00000000'+suffix)
 rows.append({'source_path':str(path),'resolved_path':str(path),'bytes':len(raw),'mtime_ns':path.stat().st_mtime_ns,'expected_sha256':semantic.sha(raw)})
manifest=semantic.preservation.build_bundle(rows,P/'bundle.tar',allowed_roots=[j.root]);data=(P/'bundle.tar').read_bytes()
evidence=semantic.recover(data,manifest,j,0,tokens,P/'recovered')
assert evidence['start']==0 and evidence['stop']==2 and semantic.current(j,0,tokens)
# Current-original drift refuses prior to source-code retirement; no deletion tested.
f=j.root/'00000000.records.bin';raw=f.read_bytes();f.write_bytes(raw+b'x')
try:semantic.current(j,0,tokens)
except ValueError:pass
else:raise AssertionError('drift accepted')
j.close()
# Source-level actual transport/destruction path; not a claim of authorized execution.
tree=ast.parse((P/'typed_payload_operations.py').read_text());method=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='retire_batched_sources')
text=ast.get_source_segment((P/'typed_payload_operations.py').read_text(),method)
assert text.index('self.recover(')<text.index('semantic.recover(')<text.index('semantic.current(')<text.index('os.unlink(')
assert 'numpy' not in sys.modules
result={'status':'PASS','schema1_preserved_schema2_explicit':True,'unselected_real_route_refused':True,'actual_semantic_filesystem_recovery':True,'changed_source_refused':True,'all_source_files_still_present':len(list((P/'source').iterdir()))==3,'transport_and_retirement_not_executed':True,'no_synthetic_owner_stage_view':True,'no_numerical_imports':True,'actual_transport_call_source_order_checked':True,'affinity':sorted(os.sched_getaffinity(0))}
(P/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
