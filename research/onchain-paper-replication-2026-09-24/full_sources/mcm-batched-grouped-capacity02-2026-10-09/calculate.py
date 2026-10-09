"""Healthy selected-route envelope, not a reservation or runtime observation."""
import ast,hashlib,json,os,resource
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(30,30));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2]);os.nice(10)
P=Path(__file__).resolve().parent;F=P.parent;R=P.parents[3];S=R/'tradingagents/research/onchain_replication'
prior_path=F/'mcm-batched-grouped-capacity01-2026-10-09/CAPACITY01.json';baseline_path=F/'mcm-batched-grouped-root-install01-2026-10-09/BASELINE01.json'
a=json.loads(prior_path.read_text());base=json.loads(baseline_path.read_text());t=a['totals'];G=t['groups'];commands=5*G;policycommands=12*G
# Actual capacity validator, AST-extracted without importing runtime or authority.
source=(S/'archive_control_history.py').read_text();tree=ast.parse(source);ns={}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Assign,ast.FunctionDef)) and (not isinstance(n,ast.FunctionDef) or n.name in ('need','validate','capacity'))],type_ignores=[]),'<actual history validator>','exec'),ns)
p=dict(schema_version=1,format=ns['FORMAT'],assumption=ns['ASSUMPTION'],success_control_bytes=16384,success_diagnostic_bytes=2048,shard_bytes=4*1024**2,full_interval_ms=10000,max_stale_ms=60000,max_callbacks_between_full=10000)
logical_policy=ns['capacity'](p,policycommands)
H='h'*64;N=2**63-1;name='command-'+'9'*16+'.bin';spent=dict(rounded_bytes=N,logical_bytes=N,commands=N)
size=lambda x:len(json.dumps(x,sort_keys=True,separators=(',',':')).encode())
command=size(dict(kind='mkdir',spent=spent,claim=H));reservation=size(dict(spent=spent,bytes=N,claim=H))
entry=dict(signature=[N]*7,sha256=H,bytes=0)
empty=dict(name=name,stat=[N]*7,sha256=H,bytes=0)
result_empty=size(dict(status='complete',spent=spent,diagnostics={name:entry},empty_staging=[empty]));result_get=size(dict(status='complete',spent=spent,diagnostics={},empty_staging=[]))
# Each typed claim wraps the <=7539B emitter envelope plus spent and object syntax.
claim=a['full_group_body_envelope']['largest_typed_body']+size(dict(claim=None,spent=spent))+16
assert max(command,reservation,result_empty,result_get,claim)<16384 and claim>1024
# Per group: mkdir,put,3get; command+result each; reserve once put and eachget;2claims.
counts=dict(command=5*G,result_empty=2*G,result_get=3*G,reservation=4*G,typed_claim=2*G)
bodies=dict(command=command,result_empty=result_empty,result_get=result_get,reservation=reservation,typed_claim=claim)
control_records=sum(counts.values());assert control_records==16*G<=4*policycommands
# Exact name frame bound source OVERHEAD296; no double-count cap per actual body.
control_encoded=sum(counts[k]*(bodies[k]+296) for k in counts);diagnostic_encoded=commands*(2048+296)
def alloc(total,maxframe):
 shards=1+total//(p['shard_bytes']-maxframe)
 return dict(encoded_bytes=total,shards_upper=shards,allocated4096_upper=total+4095*shards)
controls=alloc(control_encoded,claim+296);diagnostics=alloc(diagnostic_encoded,2048+296)
headroom=8*131072+131072+8*1024**2
context_logical=control_encoded+diagnostic_encoded+headroom
context_alloc=controls['allocated4096_upper']+diagnostics['allocated4096_upper']+headroom+10*4095
# Prior selected payload logical replaces file rounding; includes summaries at complete8192 caps.
selected_logical=t['numeric_origins_bytes']+t['numeric_summary_bytes']+t['closure_tokens_bytes']+t['spool_and_output_bytes']+t['work_body_bytes']+t['typed_body_bytes']
# Shared parent/old residual observations already in baseline. Charge only remaining full residual allowance.
res=base['observation']['residual_domains'];runtime_growth=268435456-res['runtime_temp_cache']['logical_file_bytes'];runtime_alloc_growth=288354304-res['runtime_temp_cache']['allocated_bytes']
# Supplied reconciled fatal-attempt bound covers matching AND training snapshots; old cumulative43GB remains logicalIO.
checkpoint=273838080
# New logical transient original journal + three archives, 48files worst512round added separately.
scratch=max(v['live_original_journal_payload_upper'] for v in a['graphs'].values())+3*4*1024**2
scratch_alloc=scratch+64*4095
# Explicit conditional directory allocation allowances, not ext4 guarantees. Large flat directories separate.
new_work_dirs=t['work_dirs'];directory_alloc=new_work_dirs*16384+64*1024**2
# Other new scalar/lifecycle/control receipts: root must check finite selected bound, not implicit zero.
other=64*1024**2
increment_logical=selected_logical+context_logical+checkpoint+scratch+runtime_growth+other
increment_alloc=t['selected_persistent_alloc4096']+context_alloc+checkpoint+scratch_alloc+runtime_alloc_growth+directory_alloc+other
whole_logical=base['observation']['logical_file_bytes']+increment_logical;whole_alloc=base['observation']['allocated_bytes']+increment_alloc
out=dict(status='CONDITIONAL_SOURCE_RECONCILIATION_NOT_ADMITTED',counts=counts,body_envelopes=bodies,control_history_policy_candidate=p,source_policy_capacity=logical_policy,selected_success_control=controls,selected_success_diagnostic=diagnostics,context_failure_headroom_bytes=headroom,context_logical_upper=context_logical,context_allocated_upper=context_alloc,source_trace={'command_and_result':'Context._call one each per mkdir/put/get','reservation':'Transport.put once; Transport.get once; mkdir none','typed_claim':'_Operation.__init__ Context._publish once for each of2G operations','diagnostic':'Context._receive_control exactly one per command;2048 cap','other_legacy_operations':'NOT included in16G; must fit explicit other allowance or separately add exact source counts'},physical_join=dict(baseline_logical=base['observation']['logical_file_bytes'],baseline_allocated=base['observation']['allocated_bytes'],selected_persistent_logical=selected_logical,selected_persistent_allocated=t['selected_persistent_alloc4096'],checkpoint_fatal_attempt=checkpoint,old_cumulative_checkpoint_allowance_unchanged=43058298880,scratch_logical=scratch,scratch_allocated=scratch_alloc,runtime_residual_growth_logical=runtime_growth,runtime_residual_growth_allocated=runtime_alloc_growth,work_directory_count=new_work_dirs,conditional_directory_allowance=directory_alloc,other_selected_lifecycle_and_legacy_controls_allowance=other,increment_logical=increment_logical,increment_allocated=increment_alloc,whole_writer_logical=whole_logical,whole_writer_allocated=whole_alloc,fixed_logical_cap=16*1024**3,fixed_allocated_cap=20*1024**3,logical_margin=16*1024**3-whole_logical,allocated_margin=20*1024**3-whole_alloc,baseline_filesystem_free=base['filesystem_available_bytes'],floor=10*1024**3,remaining_after_increment_and_floor=base['filesystem_available_bytes']-increment_alloc-10*1024**3),constraints=a['entry_constraints'],unclosed=['Actual final selected original/legacy operations count and lifecycle payload must fit explicit64MiB; no ignored legacy claims','Actual allocated directory growth bounded by16KiB/workdir plus64MiB flat/other directories; not a filesystem guarantee','Finite one-fatal-attempt checkpoint bound supplied by Root must bind actual schedule/source, not assumed from old cumulativecap','Actual current writer baseline/free space/other concurrent reservations and native memory required before entry','typed ledger in-memory203534275B body envelope plus dict/keys/digests, control journal101632 names/pins and repeated full audits remain unmeasured','Source01 ASCII/512-byte path and1024-byte journal body restrictions need actual admission-side check','Remote quota/full recovery/transport credentials remain uninspected; no real run'],source_pins={})
files=[prior_path,baseline_path]+[S/x for x in ('archive_control_history.py','archive_dispatch.py','archive_transport.py','typed_payload_operations.py')]
out['source_pins']={str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
(P/'CAPACITY01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'counts':counts,'body_envelopes':bodies,'physical_join':out['physical_join'],'policy_capacity':logical_policy}))
