"""Resolve this pilot's four residual domains; source maxima vs chosen ceilings.

No Main/runtime imports, no numerical bodies, no admission. `resolve` takes the
already selected compact stage policy, native per-file limit and prospective
runtime domain reservation. The existing union provides sampled enforcement;
this helper neither chooses grants nor creates a hard filesystem quota.
"""
import argparse,hashlib,json
from pathlib import Path
C=16384
M=65536
WEEKS=7
RUNTIME_PATHS=('tmp','cache','torch','matplotlib','hf','torch-extensions',
               'torchinductor','triton','numba','cuda','config','data')

def need(ok,msg):
    if not ok:raise ValueError(msg)
def positive(x):need(type(x) is int and 0<x<2**63,'positive finite selected integer required')
def digest():return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
def declaration(logical,files,dirs,maximum,scratch=0,scratch_files=0,scratch_max=0,*,basis):
    return {'logical_bytes':logical,'regular_files':files,'directories':dirs,'max_file_bytes':maximum,
        'additional_scratch_bytes':scratch,'scratch_files':scratch_files,'scratch_max_file_bytes':scratch_max,
        'evidence_sha256':digest(),'bound_basis':basis}

def resolve(stage,*,native_file_bytes,training_checkpoint_bytes,runtime_reservation):
    positive(native_file_bytes);positive(training_checkpoint_bytes)
    need(training_checkpoint_bytes<=4*1024**2<=native_file_bytes,'original training/native file limits differ')
    need(type(stage) is dict and 'restart_retention' in stage,'this concrete route requires explicit original restart retention')
    p=stage['restart_retention'];pair=stage['pair'];schedule=stage['schedule']
    need(p['schema_version']==1 and p['format']=='archived-restart-retention-v1','original restart retention format')
    for k in ('max_stores','max_generations','max_control_bytes','max_cumulative_bytes','max_live_bytes','max_replay_bytes','max_input_bytes','max_replays'):positive(p[k])
    K=pair['max_checkpoint_bytes'];positive(K);G=schedule['max_total_checkpoints'];positive(G)
    need(p['max_generations']>=G and p['max_replays']>=2,'original generation/endpoint replay reservations absent')
    S=min(p['max_stores'],G) # stores born only at first checkpoint, never per all C pairs
    need(p['max_live_bytes']>=p['max_control_bytes']+p['max_input_bytes']+p['max_replay_bytes']+2*K,'original restart live reservation insufficient')
    need(max(K,p['max_input_bytes'])<=native_file_bytes,'checkpoint/input file ceiling underfunded')
    # Successful stage root/control bound: 3G+5S+15 JSON, including two
    # selected endpoints, reservation/progress/completion chains and failure.
    # Each store <=4 fixed controls, four/generation, one replay record.
    # Snapshot retirement leaves <=3 engine manifests/generation. At most
    # two 7-file replay snapshots, twelve original endpoint input arrays,
    # and two active 4-array generations are included below.
    checkpoint_files=7*(10*G+9*S+51)
    checkpoint_dirs=7*(11+S+4*G)
    checkpoint_logical=7*(p['max_control_bytes']+p['max_input_bytes']+p['max_replay_bytes']+2*C)
    checkpoint=declaration(checkpoint_logical,checkpoint_files,checkpoint_dirs,
        max(M,K,p['max_input_bytes']),2*K,8,K,basis=
        'Seven actual MCM retention stages only: reserved controls+inputs+replays retained; two live generation bodies overlap globally under serial execution. File slots include three metadata manifests per retired generation and failed/partial states. Imported dictionary has no new matching stage. Selected policy reservations are not measured bytes.')
    # Journal owner/start/claim/complete/failed=5; compact owner owner/complete=2;
    # import intent/complete=2; seven MCM intent/stage-complete=14:23.
    # Journal namespace parents <=16. Forty-two dirs includes journal/owner/
    # import/seven stages plus fixed producer/output/lifecycle ancestor margin;
    # detailed domain roots remain disjoint from inventory01's graph subdirs.
    imported=declaration(23*M,23,42,M,basis=
        '23 bounded current metadata slots: journal5 + compact owner2 + import2 + seven MCM stage pairs14. Preparation/materialization and original512/32 evidence are read-only. Directory allowance42 includes sixteen journal-parent slots and finite fixed-path ancestor margin; not another copy of original samples or motifs.')
    # Worker and monitor are bounded by actual read-back L before writes.
    # Keep a deliberately conservative finite slot inventory, not L per loop:
    # training4; run claim/terminal3 and six selected outputs6; root lock1;
    # job launch/owner/file-readbacks/observer/postmortem/unsealed8;
    # guard live/cpu_ready/release/child_exit/final/failure/observer-death/log8;
    # 30 additional fixed pending/atomic slots and outer launcher controls.
    # Some paths cannot coexist; charging them all avoids relying on success.
    # Parent observer copies bounded monitor/journal state but is not itself
    # RLIMIT capped. L below is an explicit prospective receipt ceiling,
    # whose actual serialized size remains checked by current whole-union scan.
    lifecycle_file_cap=native_file_bytes
    lifecycle=declaration(64*lifecycle_file_cap+training_checkpoint_bytes+4096,
        68,16,lifecycle_file_cap,basis=
        'One update; checkpoint/phase/complete/failed four slots; run claim/terminal and six outputs (four caller plus archive receipt/terminal); lock; job/guard fixed receipts, child.log, atomic/pending and outer controls. Worker AND monitor inherit/read back L. Parent receipt/outer-log ceiling is prospective within sampled union, not an installed independent per-file hard cap. No per-poll append of guard state.')
    d=runtime_reservation
    need(type(d) is dict and set(d)=={'logical_bytes','regular_files','directories','max_file_bytes'},'explicit runtime domain reservation required')
    for v in d.values():positive(v)
    need(d['directories']>=13,'runtime root plus twelve actual paths must be reserved')
    need(d['max_file_bytes']<=native_file_bytes and d['logical_bytes']<=d['regular_files']*d['max_file_bytes'],'runtime finite extent declaration inconsistent')
    runtime=declaration(**dict(logical=d['logical_bytes'],files=d['regular_files'],dirs=d['directories'],maximum=d['max_file_bytes']),basis=
        'Prospective explicit domain ceiling, not source writer maximum or measured cache demand. Twelve actual forwarded paths are under research_artifacts/real_pilot_runtime. Existing sampled common writable-union limits and10GiB floor remain enforced; inter-sample overshoot is unbounded by this declaration. No separate quota or per-domain runtime enforcement is claimed.')
    result={'checkpoint_retention':checkpoint,'import_owner_stage_journal':imported,'training_and_lifecycle':lifecycle,'runtime_temp_cache':runtime}
    for v in result.values():
        for k,x in v.items():
            if k not in ('evidence_sha256','bound_basis'):need(type(x) is int and 0<=x<2**63,'finite residual arithmetic overflow')
    return {'status':'DRAFT_RESIDUAL_DECLARATIONS_NOT_ADMITTED','residual_domains':result,
        'runtime_relative_paths':['research_artifacts/real_pilot_runtime/'+x for x in RUNTIME_PATHS],
        'source_bounds':{'matching_stages':7,'original_import_recomputation':False,'generations_per_stage':G,'stores_per_stage':S,'selected_endpoints_per_stage':2,'global_live_checkpoint_scratch_bytes':2*K,'current_import_metadata_files':23,'current_import_metadata_bytes':23*M},
        'prospective_ceilings':['training_and_lifecycle parent/outer receipt headroom','runtime_temp_cache'],
        'integration':'Insert residual_domains into inventory01 input. Parent/outer receipt reservations use the same finite L as an explicit prospective ceiling, without claiming the parent has RLIMIT enforcement. Exact root budget, directory/block model and baseline remain required. No seven graph counts are invented.',
        'enforcement':'Current full writable-union sampling/floor, worker and monitor RLIMIT_FSIZE. This is a finite reservation draft, not a guarantee against theoretical inter-sample overshoot.'}

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('input');args=a.parse_args()
    with Path(args.input).open('rb') as f:raw=f.read(4*1024**2+1)
    need(len(raw)<=4*1024**2,'metadata input too large');v=json.loads(raw)
    print(json.dumps(resolve(**v),sort_keys=True,indent=2))
