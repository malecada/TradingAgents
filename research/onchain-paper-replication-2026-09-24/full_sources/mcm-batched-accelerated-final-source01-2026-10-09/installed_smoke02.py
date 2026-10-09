"""Normal pinned-runtime import/source check, no scientific inputs or Run.start.

Prior source harness AS1GiB could not map libtorch_cpu.so; its failure remains.
This check uses the ordinary runtime address space, no numerical/resource cap
change. Numerical native job envelope remains unchanged and unreleased.
"""
from pathlib import Path
import os,resource,signal,json
resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]));os.nice(10);signal.alarm(60)
from tradingagents.research.onchain_replication import compact_mcm_batched as producer,batched_numeric_reuse as reuse,batched_journal as journal,batched_offload_semantics as semantics
modules=producer._modules(Path.cwd());assert modules['journal'] is journal and modules['numeric_reuse'] is reuse
assert producer.selected({'schema_version':5}) and not producer.selected({'schema_version':4})
c=dict(beta0=.2,beta_final=.5,beta_rate=.1,max_iterations=3,alpha=.7,max_pair_entries=10000,normalization_iterations=1,solver='algorithm1_literal');p=dict(max_state_bytes=65536,normalization_chunk_entries=8,hardening_chunk_entries=8,hardening_buffer_bytes=65536,max_score_buffer_bytes=65536,chunk_edges=8,max_checkpoint_bytes=262144,max_publications=100,total_checkpoint_bytes=1048576);s=dict(max_checkpoints=100,calls_per_checkpoint=2,operations_per_call=3,max_total_checkpoints=1000,max_total_checkpoint_bytes=500000000)
x=reuse.NumericReuseExecutor(c,p,s,lambda *args:None,max_entries=8,max_retained_bytes=16384,max_key_bytes=4096);x.begin_batch();x.end_batch();counts=dict(x.counters);x.close()
result={'decision':'PASS','installed_package_imports':True,'actual_source_attestation':counts,'numerical_arrays_or_calls':False,'genuine_run_owner_or_claim':False,'full_capacity_or_speedup':False,'source_check_self_maxrss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'qualification':'ordinary source import smoke; fixed empirical native envelope unchanged; prior AS mapping refusal retained'}
H=Path('research/onchain-paper-replication-2026-09-24/full_sources/mcm-batched-accelerated-final-source01-2026-10-09');(H/'INSTALLED_SMOKE02.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
