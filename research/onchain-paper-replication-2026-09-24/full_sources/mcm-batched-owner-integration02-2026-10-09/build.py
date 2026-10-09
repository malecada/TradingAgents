from pathlib import Path
import shutil
H=Path(__file__).resolve().parent;F=H.parent;old=F/'mcm-batched-owner-integration01-2026-10-09';off=F/'mcm-batched-offload02-2026-10-09'
for name in ('compact_mcm.py','compact_owner.py','compact_mcm_output.py','compact_mcm_batched.py'):
 shutil.copyfile(old/name,H/name)
for name in ('batched_journal.py','batched_offload_semantics.py','typed_payload_policy.py','typed_payload_operations.py','registered_offload.py'):
 shutil.copyfile(off/name,H/name)
shutil.copyfile(F/'mcm-batched-execution03-2026-10-09/pair_executor.py',H/'batched_pair_executor.py')
s=(F/'mcm-batched-driver03-2026-10-09/driver.py').read_text()
s=s.replace('max_chunk_bytes, max_closure_token_bytes):','max_chunk_bytes, max_closure_token_bytes, post_batch=None, final_batches=None):')
s=s.replace("        require(callable(executor) and callable(consumer)","        require((post_batch is None and final_batches is None) or (callable(post_batch) and callable(final_batches)), 'paired explicit offload hooks required')\n        require(callable(executor) and callable(consumer)")
s=s.replace('            delivered += count','            if post_batch is not None:post_batch(journal,batch,token,original_root)\n            delivered += count')
s=s.replace('        for batch in range(batch_count):\n            start = batch*3*TOKEN.size\n            _rejoin(journal, batch, memoryview(tokens)[start:start+3*TOKEN.size], original_root)',"        if final_batches is None:\n            for batch in range(batch_count):\n                start = batch*3*TOKEN.size\n                _rejoin(journal, batch, memoryview(tokens)[start:start+3*TOKEN.size], original_root)\n        else:\n            final_batches(journal,tokens,batch_count,original_root)\n            _root(journal,original_root)")
(H/'batched_driver.py').write_text(s)
s=(H/'registered_offload.py').read_text()
s=s.replace('def fresh_recover(owner,stage,*,record,journal,work):','def fresh_recover(owner,stage,*,record,journal,work,consume=None):')
s=s.replace("        semantic.dispose_recovery(work/'semantic',manifest,batch,tokens)","""        if consume is not None:
            # Actual recovered files, exact same registered journal class. This
            # is a read-only handle; no journal birth or authority is invented.
            reader=object.__new__(type(journal));reader.root=work/'semantic/tree'
            reader.pin=tuple(evidence['root_pin']);reader.batch_cells=4096
            reader.max_cells=2**63;reader.max_body=1024**2
            import os
            reader.fd=os.open(reader.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
            try:
                rows=reader._read_complete(batch)
                consume(batch,rows)
                require(rows==reader._read_complete(batch),'recovered records changed during consumer')
                reader._root()
            finally:os.close(reader.fd)
        semantic.dispose_recovery(work/'semantic',manifest,batch,tokens)""")
s=s.replace('def finalize(owner,stage,*,records,batch_count,journal,work):','def finalize(owner,stage,*,records,batch_count,journal,work,consume=None):')
s=s.replace("work=work/f'{batch:08d}')","work=work/f'{batch:08d}',consume=consume)")
(H/'registered_offload.py').write_text(s)
