"""Apply documentation-only replay-rule clarification; preserve revision01 first."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
R=P.parents[3]
def load(n):return json.loads((P/n).read_bytes())
def write(n,x):(P/n).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
p=load('POLICY.draft.json');v=load('REVIEW_ACCEPTANCE.json');a=load('REGISTRATION_AMENDMENT.draft.json')
rule=P/'REPLAY_RULE.draft.md'
p['document_revision']=2
p['proposed_replay_rule_document_pin']={'path':str(rule.relative_to(R)),'sha256':hashlib.sha256(rule.read_bytes()).hexdigest(),'bytes':rule.stat().st_size}
p['replay_selection_rule_sha256_reason']='Outcome-independent proposed rule is pinned separately; independently adopted executable rule/selection manifest remains unadopted.'
p['proposed_replay_selection']={
    'status':'PROPOSED_FOR_INDEPENDENT_REVIEW',
    'general':'first_and_last_distinct_ordered_pair_identities_deduplicated',
    'mcm':{'exact_denominator':'N*K from frozen actual nodes and ordered motifs','ordinals':['0','N*K-1'],'one_pair':'select_once'},
    'dictionary_single_block':{'exact_denominator':'n*(n-1)','loop':'i ascending, j < i ascending, directions(i,j),(j,i)',
        'n512_exact_count':261632,'n512_ordinals':[0,261631],'n512_sample_pairs':[[1,0],[510,511]]},
    'adaptive_dictionary':{'selector_population':'deterministically ordered initial eligible sample ordered-pair identifiers from frozen seeded initial partitions',
        'selection':'first_and_last_distinct(left_sample_id,right_sample_id) with initial block ordinal/subset hash',
        'claims_last_realized_whole_stage_comparison':False,
        'capacity_is_exact_denominator':False,
        'later_actual_denominator':'output verified against full algorithm/reuse/matrix provenance; never disguised as preknown'},
    'checkpoint':'first_unchanged_scheduled_safe_checkpoint_if_any',
    'early_complete_disposition':'completed_before_first_scheduled_checkpoint',
    'absent_or_reused_member':'retain exact absence/reuse reason and source-score lineage; never substitute or create comparison',
    'force_extra_checkpoint':False,'outcome_based_substitution':False,
    'retained_inputs':'exact neighborhood/config/source/runtime/RNG and completed score for bounded independent from-start replay',
    'coverage_claim':{'empirical':'endpoints_only','max_shape_and_phase_boundaries':'fixed_independent_synthetic_corpus','maximum_shape_empirical_member_selected':False}}
for c in v['criteria']:
 if c['id']=='BR02':
    c['acceptance']='Same immutable scientific inputs/config/seed/cadence under old retention and new candidate; force at least three snapshot generations and annealing/hardening states. Exact numerical array hashes, scalar scores, iterations, convergence, RNG and semantic scientific identities match. Each variant independently validates its own provenance. Expected source/retention-policy/workload/owner/receipt and metadata-file hash changes are explicitly listed; do not require impossible equality of provenance-bearing artifact hashes or permit numeric changes.'
 if c['id']=='BR03':
    c['acceptance']='Apply REPLAY_RULE.draft.md: freeze first/last distinct stage pair ordinals when exact schedule is known; for adaptive dictionary use frozen first/last initial eligible sample ordered-pair identifiers, not capacity or discovered completed count. Retain first scheduled safe checkpoint if any; explicit early-completion/absence/reuse/failure disposition, no extra cadence or substitution. Full input/config/source/runtime and exact score evidence required. Independently frozen synthetic corpus separately covers largest-shape and phase-boundary/tie/zero-edge cases; empirical endpoints do not claim that coverage.'
v['document_revision']=2
v['fixture_seed_and_identity_selection']='Freeze empirical endpoint selectors and separate synthetic phase/shape fixtures before affected numeric outcomes; no favorable selection. See proposed rule, subject to independent acceptance.'
a['document_revision']=2
a['replay_selection_sha256_reason']='Proposed first/last endpoint rule is documented; independent adopted rule and stage-specific frozen selection manifest not yet committed.'
a['proposed_replay_rule']=p['proposed_replay_rule_document_pin']
write('POLICY.draft.json',p);write('REVIEW_ACCEPTANCE.json',v);write('REGISTRATION_AMENDMENT.draft.json',a)
print(json.dumps({'status':'REPLAY_RULE_PROPOSED_REVISION02','dictionary512_count':261632,'mcm_selection':'0,N*K-1','empirical_max_shape_claim':False,'execution_admitted':False},sort_keys=True))
