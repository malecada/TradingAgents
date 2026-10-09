"""Finite sidecar roster and remaining directory constraint; never capacity admission."""
import hashlib,json,os,resource
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(30,30));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2]);os.nice(10)
P=Path(__file__).resolve().parent;F=P.parent;R=P.parents[3];S=R/'tradingagents/research/onchain_replication'
prior=F/'mcm-batched-grouped-capacity02-2026-10-09/CAPACITY01.json';baseline=F/'mcm-batched-grouped-root-install01-2026-10-09/BASELINE01.json';review=F/'mcm-batched-checkpoint-reconciliation-review01-2026-10-09/SOURCE_REVIEW01.json';gate=F/'real-data-pilot-final23-2026-10-09/gate03.json'
a=json.loads(prior.read_text());b=json.loads(baseline.read_text());ck=json.loads(review.read_text());g=json.loads(gate.read_text());ad=g['experiments']['eth-paper-real-data-end-to-end-resource-20261009-23'];assert ck['decision']=='accepted' and ck['independent_checks']['plus_failure_and_training']==273838080
# Named source publish sites, complete+failure charged even where mutually exclusive.
roster=[
 ('binding claim.json',1,65536,'matching_owner.bind resource import_metadata.write'),
 ('FeatureJournal owner/start/complete.json',3,65536,'feature_journal._publish resource metadata'),
 ('compact Owner owner/complete.json',2,65536,'compact_owner constructor/_finish import_metadata.write'),
 ('dictionary-import intent/import-complete.json',2,65536,'original_import_stage complete_import'),
 ('seven MCM stage intent/stage-complete.json',14,8192,'compact_owner.Stage; compact_mcm_batched.produce'),
 ('seven compact producer start/complete/failed.json',21,8192,'compact_mcm_batched.produce'),
 ('seven publication receipt/artifact manifest.json',14,8192,'compact_mcm_publication._publish; compact_mcm_output.publish'),
 ('archive ledger fixed start/closed/failure headroom',4,8192,'archive_owner_operations4-record initial reservation'),
 ('one fatal typed operation failure',1,131072,'typed_payload_operations.operation typed-failed publication'),
]
sidecar=sum(n*cap for _,n,cap,_ in roster);sidecar_files=sum(n for _,n,cap,_ in roster)
res=b['observation']['residual_domains']['training_and_lifecycle'];training_growth=res['policy']['logical_bytes']-res['logical_file_bytes'];training_alloc_growth=res['allocated_threshold_bytes']-res['allocated_bytes']
# Exact actual limits already enforce whole residual domain; existing roots in baseline not recharged.
logical_replacement=sidecar+training_growth
allocated_replacement=sidecar+4095*sidecar_files+training_alloc_growth
j=a['physical_join'];new_logical=j['whole_writer_logical']-j['other_selected_lifecycle_and_legacy_controls_allowance']+logical_replacement
non_directory_increment=j['increment_allocated']-j['conditional_directory_allowance']-j['other_selected_lifecycle_and_legacy_controls_allowance']+allocated_replacement
non_directory_whole=j['baseline_allocated']+non_directory_increment
# This is residual room, NOT predicted directory usage or a new enlarged allowance.
writer_room=j['fixed_allocated_cap']-non_directory_whole
floor_room=j['baseline_filesystem_free']-j['floor']-non_directory_increment
directory_and_otherwriter_room=min(writer_room,floor_room)
assert new_logical<=16*1024**3 and directory_and_otherwriter_room>0
paths={k:v for k,v in ad['inputs'].items() if k in ('execution_job','pilot','compact_policy','archive_policy')}
for v in paths.values():assert hashlib.sha256((R/v['path']).read_bytes()).hexdigest()==v['sha256']
out={'status':'SOURCE_JOIN_WITH_EXPLICIT_DIRECTORY_CURRENTNESS_GAP_NOT_ADMITTED','sidecar_roster':[dict(scope=x,count=n,max_body_bytes=cap,source=src) for x,n,cap,src in roster],'sidecar_logical_upper':sidecar,'sidecar_files':sidecar_files,'training_lifecycle_residual':{'source_policy':res['policy'],'sampled_in_baseline_logical':res['logical_file_bytes'],'sampled_in_baseline_allocated':res['allocated_bytes'],'growth_logical':training_growth,'growth_allocated':training_alloc_growth,'training_snapshot_also_in_checkpoint_contribution':'Conservative overlap retained; no downward capacity credit.'},'legacy_transport_route':{'additional_successful_legacy_operations':0,'condition':'schema6 grouped retention, output schema1, imported dictionary, no alternate old archive stage writer/read/seal calls','original_cumulative_allowances_unchanged':True,'unsupported_route':'refuse/recalculate; original final23 legacy route is not this successor'},'joined':{'whole_logical_source_upper':new_logical,'fixed_logical_cap':16*1024**3,'logical_margin':16*1024**3-new_logical,'non_directory_increment_allocated_upper':non_directory_increment,'non_directory_whole_allocated_upper':non_directory_whole,'fixed_allocated_cap':20*1024**3,'remaining_under_writer_cap':writer_room,'remaining_under_recorded_free_minus_floor':floor_room,'directory_plus_unmodeled_concurrent_writer_remaining_bytes':directory_and_otherwriter_room,'floor_bytes':10*1024**3,'directory_bytes_assumed':None,'other_writer_bytes_assumed':None},'runtime_constraint':{'existing_enforcement':'WritableUnion.check sums regular-file and directory st_blocks*512 and refuses whole max_allocated_bytes20GiB/max_logical_bytes16GiB; native guard separately enforces10GiB filesystem floor','required_before_entry':'Fresh original union and filesystem observations; source pin/policy/whole path joins; measure actual directory allocated growth, subtract ALL other writer reservation/growth from remaining room. If unknown, not admitted.','during_execution':'Keep same native watcher and fatal storage refusals, including partial files and residual domains; no monitoring frequency/cap changes.','limitation':'Sampled checks are not quota/reservation/writer exclusion; no source-only upper bound for filesystem directory allocation or unbounded inter-sample external growth.'},'source_inputs':paths,'checkpoint_review_sha256':hashlib.sha256(review.read_bytes()).hexdigest(),'checkpoint_contribution':273838080,'cumulative_checkpoint_allowance_unchanged':43058298880,'source_pins':{}}
files=[prior,baseline,review,gate]+[S/x for x in ('matching_owner.py','feature_journal.py','compact_owner.py','original_import_stage.py','compact_mcm_batched.py','compact_mcm_publication.py','compact_mcm_output.py','archive_owner_operations.py','archive_owner_seal.py','typed_payload_operations.py','real_pilot_storage.py','workflow_storage.py','resources.py','real_pilot_import_caller.py','real_pilot_population.py','import_metadata.py','score_batches.py')]
out['source_pins']={str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
(P/'CAPACITY01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'sidecar_bytes':sidecar,'sidecar_files':sidecar_files,'joined':out['joined']}))
