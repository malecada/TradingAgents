from pathlib import Path
H=Path(__file__).resolve().parent
exec(compile((H/'verify.py').read_text().split("root=H/'tiny-stage'")[0],str(H/'verify.py'),'exec'))
config={'rows':2,'cells':64,'motifs':32,'graph_hash':graph_hash(g),'node_order_hash':node_order_hash(g.node_ids),'workload_sha256':'d'*64,'purpose_schema_version':2}
work=H/'failure-fixture';work.mkdir();j=mods['journal'].BatchJournal(work/'matching',batch_cells=48,max_cells=64,max_bytes=200000,max_body_bytes=1024,boundary=lambda:None)
def fail(*args):raise RuntimeError('synthetic selected hook failure')
try:mods['driver'].drive(g,dictionary,descriptor=config,policy={'max_buffer_bytes':100000,'edge_chunk':2,'extraction_limit':3},journal=j,executor=Executor(None,None,None,None),consumer=lambda *a:None,max_chunk_bytes=128,max_closure_token_bytes=336,post_batch=fail,final_batches=lambda *a:None)
except RuntimeError as error:
 assert str(error)=='synthetic selected hook failure';notes=error.__notes__;assert '"confirmed_post_sink_cells": 0' in notes[0] and '"journal_completed_cells": 48' in notes[0]
else:raise AssertionError('hook failure hidden')
assert j.closed and indices[-1].closed;gc.collect();assert refs[-1]() is None
# Closed01 source inverse and exact shared journal/executor copies.
F=H.parent
assert (H/'batched_journal.py').read_bytes()==(F/'mcm-batched-execution03-2026-10-09/batch_journal.py').read_bytes()
assert (H/'batched_pair_executor.py').read_bytes()==(F/'mcm-batched-execution03-2026-10-09/pair_executor.py').read_bytes()
for name in ('typed_payload_policy.py','typed_payload_operations.py','batched_offload_semantics.py'):
 assert (H/name).read_bytes()==(F/'mcm-batched-offload02-2026-10-09'/name).read_bytes()
report={'synthetic_only':True,'hook_error_primary':True,'journal_and_index_closed':True,'local_released':True,'delivery_failure_notes':notes,'unchanged_shared_sources':5,'affinity':sorted(os.sched_getaffinity(0))}
(H/'FAILURE_RESULT01.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
