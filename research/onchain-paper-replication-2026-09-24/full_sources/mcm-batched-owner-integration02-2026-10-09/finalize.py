from pathlib import Path
import ast,hashlib,json,difflib
H=Path(__file__).resolve().parent;F=H.parent;R=Path.cwd();old=F/'mcm-batched-owner-integration01-2026-10-09';off=F/'mcm-batched-offload02-2026-10-09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
installed=['compact_mcm_batched.py','compact_mcm.py','compact_owner.py','compact_mcm_output.py','batched_driver.py','batched_journal.py','batched_pair_executor.py','registered_offload.py','typed_payload_policy.py','typed_payload_operations.py','batched_offload_semantics.py']
baselines={n:old/n for n in installed[:4]}
baselines.update(batched_driver=F/'mcm-batched-driver03-2026-10-09/driver.py')
baselines['batched_driver.py']=baselines.pop('batched_driver')
baselines.update({n:off/n for n in ('batched_journal.py','registered_offload.py','typed_payload_policy.py','typed_payload_operations.py','batched_offload_semantics.py')})
baselines['batched_pair_executor.py']=F/'mcm-batched-execution03-2026-10-09/pair_executor.py'
rows={}
for n in installed:
 p=H/n;ast.parse(p.read_text());base=baselines[n]
 delta=''.join(difflib.unified_diff(base.read_text().splitlines(True),p.read_text().splitlines(True),fromfile=str(base.relative_to(R)),tofile=str(p.relative_to(R))))
 (H/(n+'.patch')).write_text(delta)
 rows[n]={'source_sha256':sha(p),'baseline':str(base.relative_to(R)),'baseline_sha256':sha(base),'unchanged':p.read_bytes()==base.read_bytes()}
# Exact inverse for original legacy edits reuses closed01 inverses, only schema3→4 differs.
assert (H/'compact_owner.py').read_bytes()==(old/'compact_owner.py').read_bytes()
assert (H/'compact_mcm_output.py').read_bytes()==(old/'compact_mcm_output.py').read_bytes()
assert (H/'compact_mcm.py').read_text().replace("policy['schema_version'] in (1,2,4)","policy['schema_version'] in (1,2,3)")==(old/'compact_mcm.py').read_text()
# Unchanged arithmetic loop: driver changes only selected hooks before credit/final check.
s=(H/'batched_driver.py').read_text()
s=s.replace('max_chunk_bytes, max_closure_token_bytes, post_batch=None, final_batches=None):','max_chunk_bytes, max_closure_token_bytes):')
s=s.replace("        require((post_batch is None and final_batches is None) or (callable(post_batch) and callable(final_batches)), 'paired explicit offload hooks required')\n",'')
s=s.replace('            if post_batch is not None:post_batch(journal,batch,token,original_root)\n','')
a=s.index('        if final_batches is None:');b=s.index("        require(delivered ==",a)
s=s[:a]+'''        for batch in range(batch_count):
            start = batch*3*TOKEN.size
            _rejoin(journal, batch, memoryview(tokens)[start:start+3*TOKEN.size], original_root)
'''+s[b:]
assert s==baselines['batched_driver.py'].read_text()
result={'source_only':True,'sources':rows,'inverses':{'driver03_literal':True,'legacy_compact_owner_output_identical01':True,'compact_mcm_only_schema3_to4_delta_from01':True},'evidence':{p.name:sha(p) for p in [H/'RESULT02.json',H/'RECOVERY_RESULT01.json',H/'FAILURE_RESULT01.json',H/'TEST01.log',H/'TEST02.log',H/'RECOVERY_TEST01.log',H/'FAILURE_TEST01.log',H/'BOUNDS_RESULT01.json',H/'BOUNDS_TEST01.log',H/'REPORT.md']},'genuine_owner_or_transport_executed':False,'admission':False}
(H/'MANIFEST.json').write_text(json.dumps(result,indent=2)+'\n');print(sha(H/'MANIFEST.json'));print(json.dumps({n:row['source_sha256'] for n,row in rows.items()},indent=2))
