"""Write only unadopted policy/review documents, never production/run inputs."""
from pathlib import Path
import hashlib,json
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
S='research/onchain-paper-replication-2026-09-24/'
BASE=S+'full_sources/'

def unknown(reason):return {'value':None,'reason':reason}
def write(name,x):(OUT/name).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def pin(path):
    raw=(ROOT/path).read_bytes()
    return {'path':path,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
base={'status':'NONEXECUTABLE_UNADOPTED_DRAFT','execution_admitted':False,'schema_version':1,'prospective_variant':'bounded-matching-restart-v1'}
policy={**base,'kind':'matching_restart_retention_policy_draft',
'route':{'supported_first_slice':'explicitly selected archived matching-event route',
    'selection_input':'compact_restart_retention_input','descriptor_extension':'compact_restart_retention',
    'absent_extension':'retain_existing_variant_exactly','unsupported_route':'reject_before_claim'},
'objects':{
    'scientific_outputs':{'body_retention':'complete_immutable_existing_contracts','retirement_allowed':False},
    'replay_evidence':{'body_retention':'full_recoverable_preselected_bytes','retirement_allowed':False},
    'active_restart_scratch':{'body_retention':'current_plus_candidate','retirement_allowed':True,'max_simultaneous_generations':2,'logical_only':True},
    'failed_evidence':{'body_retention':'all_surviving_and_partial_bodies_at_failure','retirement_allowed':False,'automatic_resume':False},
    'control_evidence':{'body_retention':'all_immutable_progress_transition_and_terminal_records','retirement_allowed':False}},
'rotation':{'max_active_pairs':1,'max_saved_active_generations':2,'max_unacknowledged_transitions':1,
    'candidate_before_retire':'full_snapshot_verification_plus_durable_progress_event_and_proof',
    'superseded_retire_anchor':'verified_current_progress_proof',
    'completed_retire_anchor':'durable_exact_ordered_completion_event',
    'acknowledgement_after':'fsync_exact_inventory_descriptor_rejoin_and_retirement_completion',
    'third_generation_before_retirement_completion':False,
    'metadata_per_checkpoint':'retain_manifest_hashes_extents_identity_progress_and_disposition',
    'retired_flags':{'body_available':False,'restart_eligible':False,'historical_intermediate_replay_available':False},
    'hash_only_recoverability_claim_allowed':False},
'failure':{'cleanup_uncertainty':'fatal_preserve_surviving_bodies_poison_owner_stop_outer_job',
    'crash_after_unlink_before_completion':'incomplete_disposition_never_automatic_success',
    'reuse_failed_identity':False,'automatic_resume':False,'automatic_retry':False,'attempt_refund':False,
    'reconciliation':'read_only_available_body_and_last_verified_progress_record',
    'successor':'separately_reviewed_committed_registration_fresh_identity_and_budget'},
'invariants':['exact_graph_sample_motif_and_cell_population','matching_equations_initialization_and_temperature',
    'hardening_order_ties_and_comparison_direction','floating_point_precision_and_tolerances','all_RNG_states_and_sampling_provenance',
    'checkpoint_cadence','all_final_scientific_scores_outputs_and_failure_dispositions','unchanged_old_local_and_archived_variants'],
'limits':{k:unknown(reason) for k,reason in {
    'max_generation_logical_bytes':'Bound complete M/Q/V and optional hardening state for unchanged largest admitted pair.',
    'max_cumulative_generations':'Freeze whole-stage progress count; no increase in allowed numerical work implicit.',
    'max_cumulative_written_bytes':'Freeze serialization/write budget; successful retirement gives no refund.',
    'max_retained_control_metadata_bytes':'Bound immutable proof and transition ledger growth across all generations.',
    'max_replay_body_bytes':'Deterministic preselected replay population and required bodies unresolved.',
    'max_replay_body_count':'Independent label-free selection rule must be frozen before numeric outcomes.',
    'max_failed_evidence_bytes':'Account failure retaining candidate/current/partial bodies and old failed claims.',
    'max_peak_local_growth_bytes':'Physical blocks, current/candidate, replay/failure bodies, metadata and staging unknown.',
    'max_outer_rss_bytes':'Live engine arrays, serialization copies, parentgraphs, sampler, model, NumPy/Python, pagecache unknown.',
    'max_wall_seconds':'Registered whole-job containment/cadence and verification cost unresolved.'}.items()},
'logical_bound':'active_saved_restart_payload <= 2 * max_generation_logical_bytes; replay/failure/control and transient copies excluded',
'physical_upper_bound_bytes':None,'physical_upper_bound_bytes_reason':'Two-generation cap is logical saved payload only, not live arrays/copy/fs-blocks/RSS or whole-workflow allocation.',
'replay_selection_rule_sha256':None,'replay_selection_rule_sha256_reason':'Independent deterministic metadata-only rule and exact mandatory synthetic/empirical replay sets not yet reviewed.',
'prospective_source_sha256':None,'prospective_source_sha256_reason':'No implementation/source freeze exists for this proposed retention version.',
'adopted_policy_sha256':None,'adopted_policy_sha256_reason':'This is an unadopted document, not a registered policy input.',
'preserved_current_local_score_matrix_payload_bytes':55439818752,
'user_minimum_local_free_bytes':10*2**30,
'authority_pins':[pin(BASE+'archive-retention-readiness-2026-10-02/REPORT.md'),pin(S+'REPLICATION_SPEC.md'),pin(S+'PROTOCOL.md'),pin(S+'IMPLEMENTATION_ASSUMPTIONS.md')]}
write('POLICY.draft.json',policy)
checks=[
('BR01','Independent arithmetic and assignment oracle','Freeze nondegenerate square/rectangular/tie/zero-edge fixtures; independently evaluate scores/objective/feasibility from raw fixture inputs. Preserve C05/C06 tolerances. Expected numbers cannot come from the retention implementation or its verifier.'),
('BR02','Unchanged numerical trajectory','Same immutable inputs/config/seed/cadence under old retention and new candidate; force at least three snapshot generations and both annealing/hardening states. Exact ordered purpose/identity/score/iterations/convergence/RNG and final MCM/dictionary hashes match; any intended numerical change is rejected.'),
('BR03','Deterministic replay set','Freeze label-free selection-rule hash before affected numeric outcomes; include phase boundaries, last partial interval, largest admitted shape and scientific purpose/direction cases plus required C14 saved-neural example. Resolve exact selected identities before observing their values; no outcome-based selection.'),
('BR04','Independent final numeric/replay verification','Recompute preselected pair scores using independent reference arithmetic from retained raw/protocol inputs; independently validate full output shape/denominator/order/finite values and exact event-to-score-to-MCM joins. Do not call manifest agreement alone independent numerical validation. Report which cells were independently recomputed and which had integrity-only checks.'),
('BR05','Replay recoverability','Retrieve/hash full mandatory replay/output bytes and execute bounded offline replay in clean locked environment; retired scratch hashes cannot satisfy availability. Preserve C13/C14 neural/metric outputs and C16 recovery obligations.'),
('BR06','Two-generation lifecycle','Across more than two rotations, never create third heavy active generation before retired predecessor completion; replay exemptions separately reserved. Verify full per-checkpoint immutable metadata remains and retired bodies are explicitly unavailable.'),
('BR07','Crash matrix','Inject interruption before/after candidate save/fsync, progress event/proof, retire-intent, each unlink, descriptor close, parent fsync and retirement completion. Every gap is either a fully verified transition or visible incomplete failure; no false success or old-identity restart.'),
('BR08','Primary and cleanup failures','Inject read/write/fsync/unlink/close and callback-revocation errors, including compound errors. Preserve primary+cleanup evidence, poison owner, stop outer job, retain surviving state, prevent acknowledgement and refund.'),
('BR09','Identity and filesystem attacks','Reject wrong source/runtime/owner/stage/purpose/order/generation/extent/hash, rehashed untrusted proofs, symlink/hardlink/cross-device replacement, extra/missing members and equal-byte inode substitution through final callbacks.'),
('BR10','Historical compatibility','Old local and current archived-stage variants continue requiring every referenced tree; absent new extension behaves identically. New retirement receipt cannot upgrade/reopen an old claim or weaken old verifiers.'),
('BR11','Anchored new postclose verification','Fresh version binds original writer/progress/retirement/replay claims into stage and owner seal. Postclose local check succeeds with remote fetch forbidden, rejects mutation of retained receipts/outputs, and makes no fresh-remote-availability claim.'),
('BR12','Budget and exhaustion','Reserve positive count/logical/control/write/replay/failure/physical/outer limits before mutation; exhaustion preserves failure and every attempted/unavailable cell. Cumulative counters never shrink after successful retirement; current floor and aggregate guard readback remain enforced.'),
('BR13','Full synthetic producer-to-terminal path','Actual dictionary and MCM producers, saved output, graph publication, owner and terminal completion exercise new version; include late failure, selected replay exemption and local/current archive regressions. No production empirical data.'),
('BR14','Independent release and preservation audit','Reviewer independently checks C01–C18 mappings, numerical/replay evidence, old-byte hashes, ledger counts, source/runtime/policy closure and crash outcomes; all critical findings closed before committing prospective registration/assumptions amendment.')]
review={**base,'kind':'required_release_acceptance_draft','tests_run':False,
'criteria':[{'id':i,'requirement':n,'acceptance':a,'status':'NOT_RUN','evidence_sha256':None,'evidence_sha256_reason':'Documentation-only proposal; implementation and release tests not performed.'} for i,n,a in checks],
'criteria_authority':{'C11':S+'REPLICATION_SPEC.md:200','C13':S+'REPLICATION_SPEC.md:202','C14':S+'REPLICATION_SPEC.md:203','C16':S+'REPLICATION_SPEC.md:205','C18':S+'REPLICATION_SPEC.md:207'},
'fixture_seed_and_identity_selection':'Must be frozen in independent review before candidate numerical outcomes; this draft does not choose favorable cases.'}
write('REVIEW_ACCEPTANCE.json',review)
registration={**base,'kind':'prospective_registration_amendment_draft','adoption':False,
'existing_resource_proposal_pin':pin(BASE+'native-resource-admission-2026-10-01/budget-allocation.draft.json'),
'budget':{'spent_preserved':33,'body_batches_preserved':12,'financial_batches_preserved':15,'resource_slots_already_proposed':1,'proposed_cumulative_ceiling_unchanged':61,'additional_slots_requested_here':0,'refunds':0,'maximum_unique_fits_unchanged':1420},
'parent_and_failed_identity_rule':'Preserve original proposal lineage; new unique identity and explicit amendment required; never reuse graph09 or another terminal identity.',
'required_new_binding_fields':['compact_restart_retention_input','descriptor.compact_restart_retention.version','descriptor.compact_restart_retention.policy_sha256','explicit_replay_selection_manifest','full_immutable_source_runtime_closure','outer_physical_storage_and_RSS_limits'],
'scientific_changes':[],'operational_changes':['future_matching_restart_body_lifetime','explicit_retirement_proofs_and_reader_version'],
'old_artifacts_edited_or_deleted':False,'current_archived_variant_preserved':True,
'current_resource_population':'Original32pending requirements and all existing unavailable/failure reasons retained; prospective mapping still independently required.',
'dictionary_reuse_decision':unknown('Original resource MCM reuses2022-01-03dictionary; prospective native route choice remains coordinator decision.'),
'adopted_registration_sha256':None,'adopted_registration_sha256_reason':'No amendment or final executable contract adopted/committed.',
'resource_policy_sha256':None,'resource_policy_sha256_reason':'Physical/RSS/cumulative limits and exact population not finalized.',
'replay_selection_sha256':None,'replay_selection_sha256_reason':'Independent metadata-only selection rule unresolved.',
'prospective_source_commit':None,'prospective_source_commit_reason':'Implementation not authorized by this documentation draft.'}
write('REGISTRATION_AMENDMENT.draft.json',registration)
ownership={**base,'kind':'proposed_future_exclusive_ownership_only','active_assignment':False,
'integration_owner':{'responsibility':'One coherent writer/readers/explicit policy/anchored seal slice after current source freeze and reviewer-approved contract.',
'new_modules_proposed':['tradingagents/research/onchain_replication/restart_retention.py'],
'existing_modules_candidate_scope':{
'compact_matcher.py':'Use new versioned restart writer; preserve advance cadence, score computation and exact completion events.',
'compact_policy.py':'Separate live logical restart cap from cumulative writes/control/replay reservations; legacy policy unchanged.',
'compact_owner.py':'Versioned stage contract and exact original authority routing; historical routes unchanged.',
'compact_training.py':'Bind explicit new selection/descriptor policy hash in both registered input paths.',
'compact_native_producer.py':'Propagate explicit selection only; no inferred default.',
'compact_stage.py':'Add new proof/retirement reader dispatch; original checkpoint tree reader remains strict.',
'archived_stage.py':'Fresh version validates active/replay trees and explicit verified retirement records; old _trees unchanged.',
'archive_owner_seal.py':'Anchor original new retention claims/terminal in stage proof and postclose verification.',
'compact_dictionary.py':'Bind selected new stage version consistently without numerical changes.',
'compact_mcm.py':'Same selected stage/retention contract and original event/score joins.'},
'new_tests_proposed':['tests/research/onchain_replication/test_restart_retention.py','tests/research/onchain_replication/test_restart_retention_integration.py']},
'independent_reviewer':'Read-only independent arithmetic/replay/crash/preservation review, no implementation ownership.',
'out_of_scope':['job_payload transport construction/injection','archive_transport metering implementation','score-tail/batch retention','neural model/optimizer retention','paper scientific changes','historical migrations/deletion','empirical execution'],
'coordinator_decisions':['source ownership release after current frozen tests','deterministic replay rule and exact retained evidence','prospective graph union/dictionary reuse','resource/physical/RSS limits and final registration']}
write('SOURCE_OWNERSHIP.json',ownership)
print(json.dumps({'status':'NONEXECUTABLE_DRAFTS_WRITTEN','variant':'bounded-matching-restart-v1','acceptance_cases':len(checks),'production_edits':0,'tests_run':False,'execution_admitted':False},sort_keys=True))
