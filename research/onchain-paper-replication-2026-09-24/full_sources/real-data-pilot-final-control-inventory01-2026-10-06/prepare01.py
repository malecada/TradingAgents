"""Source/metadata-only selected declaration delta; never admission or execution."""
import ast
import copy
import hashlib
import json
import types
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
F=HERE.parent
PREFIX='tradingagents/research/onchain_replication/'
SUCCESSOR=F/'real-data-pilot-feature-integration-successor01-2026-10-06/successor01.py'
INPUT=F/'real-data-pilot-current-graph-counts05-2026-10-06/INPUT_DRAFT01.json'

def raw(v):return (json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def ref(p):
    b=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def need(v,m):
    if not v:raise ValueError(m)
def load():
    b=SUCCESSOR.read_bytes();need(hashlib.sha256(b).hexdigest()=='710fac4de18630fccdb6aa1531c09c4026a78d8ae38db77285b59720556edd72','accepted successor changed')
    m=types.ModuleType('accepted_successor');m.__file__=str(SUCCESSOR);exec(compile(b,str(SUCCESSOR),'exec'),m.__dict__);return m

def derive(d, successor):
    b=successor.load('builder');sel=successor.load('selected');c=successor.load('controls')
    graphs=b.graphs(ROOT,d['graphs']);p=d['protocol'];counts={w:g['rows'] for w,g in graphs.items()}
    need(sum(counts.values())==12999004,'authentic seven count total changed')
    by=p['typed_allocations']['by_week'];need(all(by[w]==sel.kind_alloc(n) for w,n in counts.items()),'selected allocation changed')
    kinds=[k for v in by.values() for k in v.values()];chunks=sum(k['max_chunks'] for k in kinds);ops=sum(k['max_operations'] for k in kinds)
    typed=(3*ops+chunks)*8192
    compact=copy.deepcopy(b.metadata(ROOT,p['references']['compact_policy']));stage=compact['stage_policy'];G=stage['schedule']['max_total_checkpoints'];C=max(counts.values())*32;E=2*C+G;chunk=stage['log']['chunk_events'];Q=(E+chunk-1)//chunk
    stage['log'].update(max_pairs=C,max_events=E,max_logical_bytes=E*168+2*8192)
    stage['max_retained_logical_bytes']=stage['log']['max_logical_bytes']+stage['restart_retention']['max_live_bytes']+88*C+(4*((C+65535)//65536)+4)*8192
    compact['max_workflow_retained_logical_bytes']=8*(stage['max_retained_logical_bytes']+2*8192)+2*65536
    archive=copy.deepcopy(b.metadata(ROOT,p['references']['archive_policy']));R=archive['max_stage_verifications'];ordinary=8*(1+R)
    archive.update(max_writer_metadata_bytes=(7*Q+8)*8192,max_read_metadata_bytes=(3*Q+8)*8192,max_stage_bytes=(3*Q+8)*8192+40*G+8*8192,max_remote_payload_bytes=8*E*168,max_decoded_transfer_bytes=8*E*168*(3+R))
    archive['max_workflow_metadata_bytes']=(4+3*ordinary+8)*8192+8*(archive['max_writer_metadata_bytes']+8*8192+R*archive['max_stage_bytes'])
    full,last=divmod(E,chunk);rounded=full*((chunk*168//65536+1)*65536)+(0 if not last else (last*168//65536+1)*65536)
    N=4*chunks+8*Q*(4+R);payload=sum(2*k['max_preserved_bytes']+k['max_recovered_bytes']+2*k['max_chunks']*65536 for k in kinds)+8*(E*168+(2+R)*rounded)
    tr=copy.deepcopy(p['transport_limits']);history=successor.load('history').capacity(tr['control_history'],N)
    tr.update(max_commands=N,max_payload_bytes=payload,max_control_bytes=history['control_bytes'],max_diagnostic_bytes=history['diagnostic_bytes'])
    alloc=c.allocation();proof={}
    for w,n in counts.items():
        x=alloc['graph'](n,p['typed_allocations']['chunk_cells'],by[w]['score-tail-f64']['chunk_bytes'],by[w]['mcm-output-f32']['chunk_bytes'],chunk*168)
        alloc['check_typed_allowances'](x,by[w]);proof[w]=x
    job=b.metadata(ROOT,p['references']['execution_job']);pilot=b.metadata(ROOT,p['references']['pilot'])
    residual=successor.load('residuals').resolve(stage,native_file_bytes=job['resources']['native_unit_limits']['file_size_bytes'],training_checkpoint_bytes=pilot['max_checkpoint_bytes'],runtime_reservation=p['runtime_reservation'],lifecycle_reservation=p['lifecycle_reservation'])
    return dict(counts=counts,typed_max_control_bytes=typed,typed_file_slots=3*ops+chunks,typed_operations=ops,typed_chunk_credits=chunks,compact_policy=compact,archive_policy=archive,transport_limits=tr,history_bounds=history,by_week=proof,residual_proposals=residual,resources_unchanged=job['resources'],stage_variables=dict(C=C,E=E,Q=Q,G=G,R=R))

DOMAINS={
 'checkpoint_retention': ['stage_retention','restart_retention','stage_retention_reader','compact_matcher','matching_checkpoint'],
 'import_owner_stage_journal':['compact_owner','original_import_stage','import_metadata','feature_journal','resource_fixture'],
 'training_and_lifecycle':['real_pilot_training','real_pilot_import_caller','real_pilot_partial_progress','job','resources','resource_binding','owned_io'],
 'runtime_temp_cache':['real_pilot_storage'],
}
WRITERS={'write','_write','_write_bytes','_publish','write_json','_immutable','_native_write','_native_atomic','mkdir','durable_mkdir','open','_opened','save','save_component','replace','link','_copy_replay','event','print'}
def inventory():
    # Exact conservative source closure declared by job.required_sources(), without importing it.
    package=ROOT/PREFIX
    closure=sorted(set(package.glob('*.py'))|set(package.parent.glob('*.py'))|{ROOT/'tradingagents/__init__.py'})
    selected={name:[ROOT/(PREFIX+stem+'.py') for stem in stems] for name,stems in DOMAINS.items()}
    selected['training_and_lifecycle'] += [ROOT/'tradingagents/research/lifecycle.py',ROOT/'scripts/research_resource_guard.py']
    result={}
    for domain,paths in selected.items():
        result[domain]=[]
        for path in paths:
            body=path.read_text();tree=ast.parse(body);calls=[]
            for node in ast.walk(tree):
                if isinstance(node,ast.Call):
                    name=node.func.attr if isinstance(node.func,ast.Attribute) else node.func.id if isinstance(node.func,ast.Name) else ''
                    if name in WRITERS:calls.append({'line':node.lineno,'call':ast.get_source_segment(body,node)[:420]})
            result[domain].append(ref(path)|{'writer_call_census':sorted(calls,key=lambda x:x['line'])})
    return {'complete_registered_package_source_closure':[ref(p) for p in closure],'selected_residual_sources':result,'census_qualification':'AST source-call index, not a reachability proof. Branch-specific selected path families and inactive writer exclusions are stated in declaration. Source only: no numeric imports or bodies.'}

def generate():
    need(ref(INPUT)['sha256']=='6023954b1e21b0f86a0155ead15ef588e57c59be65f4ef9f04b71d6d37d7c237','counts05 draft changed')
    successor=load();d=json.loads(INPUT.read_text());a=derive(d,successor);iv=inventory()
    invpath=HERE/'SOURCE_INVENTORY01.json';invpath.write_bytes(raw(iv));evidence=ref(invpath)['sha256']
    proposals=a.pop('residual_proposals');decl=copy.deepcopy(proposals['residual_domains'])
    for v in decl.values():v['evidence_sha256']=evidence
    known={k:decl[k] for k in ('checkpoint_retention','import_owner_stage_journal')}
    unknown={k:{**{field:None for field in decl[k] if field not in ('evidence_sha256','bound_basis')},'evidence_sha256':evidence,'bound_basis':reason} for k,reason in {
       'training_and_lifecycle':'Training subset bounded: checkpoint <=4194304, complete and failed each <=65536; 20 fixed phase records conservatively <=4096. Full domain not bounded by these: lifecycle._immutable serializes unbounded claim/output dictionaries absent an active metadata scope; resources._native_write serializes parent state without length gate, native .tmp duplicates state, child/outer logs may be appended outside worker RLIMIT. Final concrete launcher and encoded-state/path bounds required; 68 slots/32MiB proposal is not a source maximum.',
       'runtime_temp_cache':'real_pilot_storage.environment forwards twelve paths; prepare_environment creates ancestors. Numerical/native library writers can create unknown file counts/sizes/subdirectories and temporary overlap. 256MiB/4096files/256dirs/64MiB proposal is not enforced per-domain. Require exact selected backend writer proof or separately reviewed enforceable bound under unchanged physical limits. Do not infer zero cache from offline metadata.'}.items()}
    declaration={'status':'DRAFT_NOT_ADMITTED_SOURCE_GAPS_EXPLICIT','schema_version':1,'input':ref(INPUT),'successor':ref(SUCCESSOR),'source_inventory':ref(invpath),'required_domains':successor.load('controls').REQUIRED,'residual_domains':known|unknown,'prospective_reservations_not_source_bounds':{k:decl[k] for k in unknown},'source_derived':a,
      'path_families':{
       'checkpoint_retention':{'success':['seven MCM retention roots: claim/seal; reserve-*; events/progress-* and selected/stored completion; bridges/*; selected-*; store-*','stores/pair-*/claim,reservation,progress,retire-intent,retire-complete,completion,terminal; generation-*/state/*; replay-* plus replay JSON','inputs/input-*-{direction}-{node_features,edge_index,edge_features}.npy and input metadata'], 'failure':['stage failed.json','store failure.json','partial generation/input/replay publications'], 'scratch':['two live generation bodies globally: 2*K = 524288 bytes in up to8 arrays; no atomic duplicate in direct O_EXCL writer'], 'ancestors':['stores,bridges,events,inputs; each pair/generation/state/replay directory'], 'derivation':'G=160; S=min(max_stores,G)=160; seven stages: files=7*(10G+9S+51), dirs=7*(11+S+4G), logical=7*(max_control+max_input+max_replay+2*16384). Input/replay retained bytes not charged again in scratch. Terminal pairs without checkpoint/selection create binary archive events only; no160-pair limit. Prior checkpoint scope proof reused.'},
       'import_owner_stage_journal':{'success':['journal owner/start/resource-claim/resource-complete','compact owner/complete','original import intent/import-complete','seven compact MCM intent/stage-complete'], 'failure':['journal failed.json; partial direct metadata leaf remains within same slot'], 'scratch':['direct O_EXCL checked import_metadata writer: no separate temporary body'], 'ancestors':['journal max16 missing ancestors; journal/compact/import/seven stage roots within42 retained directory allowance'], 'derivation':'5 journal +2 owner +2 import +14 stage=23; each bounded65536; 1507328 logical bytes. resource journal numerical __call__ explicitly refused; samples/dictionary remain read-only inputs.'},
       'training_and_lifecycle':{'success':['training checkpoint.pt/phases.jsonl/complete.json','ResearchRun claim/complete and selected six outputs','guard live/cpu_ready/release/child_exit/final, job launch/owner/observer'], 'failure':['training failed.json','ResearchRun failed.json','guard native-finalization-failed/native-owner-death/postmortem/unsealed and retained partial files'], 'scratch':['lifecycle .pending-UUID (linked final aliases same inode)','guard live.tmp/other .tmp may coexist with previous JSON'], 'ancestors':['research_runs parent/shared .lock; run/outputs; artifact job/guard/training roots'], 'unknown':'Concrete launcher + all parent/outer writers require final inventory and serialized bounds; retained snapshot observations are not maxima.'},
       'runtime_temp_cache':{'success':proposals['runtime_relative_paths'],'failure':['partial temporary/cache artifacts retained on interrupted native calls'],'scratch':['unknown simultaneous native temporary bodies; cannot set zero'],'ancestors':['runtime root plus12 base paths; deeper native directories unknown']}
      },'remaining_requirements':['Resolve both null residual domains with source-proven selected bounds; no placeholder/default ceiling admission.','After actual backup recovery/retirement, root obtains fresh whole-writer baseline with exact evidence.','Root binds concrete changed metadata/source closure and genuine OwnerBinding/private Transport, commits gate/resource registration and reviews aggregate budgets.'], 'no_execution_authority':True}
    lower_items={'typed_ledger':a['typed_max_control_bytes'],'archive_workflow_metadata':a['archive_policy']['max_workflow_metadata_bytes'],'dispatch_history':a['history_bounds']['control_bytes'],'transport_diagnostics':a['history_bounds']['diagnostic_bytes'],'retained_matrices':sum(x['retained_matrix_logical_bytes'] for x in a['by_week'].values()),'typed_attempt_metadata':sum(x['typed_attempt_metadata_allowance_bytes'] for x in a['by_week'].values())}
    declaration['known_reservation_conflict']={'source_derived_disjoint_subtotal':lower_items,'subtotal_logical_bytes':sum(lower_items.values()),'unchanged_logical_limit':16*1024**3,'excess_before_baseline_residuals_and_other_categories':sum(lower_items.values())-16*1024**3,'qualification':'Conservative mandatory selected-formula reservation conflict, not measured actual usage; do not infer physical bytes from cumulative transport payload.'}
    declaration['reused_evidence']=[ref(F/'real-data-pilot-current-graph-counts05-2026-10-06/MANIFEST01.json'),ref(F/'real-data-pilot-current-graph-counts05-review01-2026-10-06/MANIFEST01.json'),ref(F/'real-data-pilot-event-scope-investigation01-2026-10-06/pair-checkpoint-scope01/MANIFEST01.json')]
    declaration['native_receipt_fix_candidate']={'source':ref(HERE/'native_receipt_candidate01.py'),'target':'resources._native_write','installed':False,'limit':None,'requirement':'Root must thread one explicit admitted encoded-byte bound through _native_atomic and all direct/failure/parent callers. Oversize refusal occurs before file birth; no state truncation or success coercion. Original exception chains/finalization controls must remain retained and be integration-tested. This candidate alone does not close lifecycle domain, stderr/child.log/outer logging or cache output.'}
    (HERE/'DECLARATION_DRAFT01.json').write_bytes(raw(declaration))
    # Metadata patch is intentionally not an executable full draft: policy reference hashes need root binding.
    (HERE/'BINDING_DELTA_DRAFT01.json').write_bytes(raw({'status':'DRAFT_NOT_ADMITTED','base_input':ref(INPUT),'typed_max_control_bytes':a['typed_max_control_bytes'],'compact_policy':a['compact_policy'],'archive_policy':a['archive_policy'],'transport_limits':a['transport_limits'],'physical_baseline':d['protocol']['physical_baseline'],'residual_domains':declaration['residual_domains'],'apply_requires':'Root regenerated reference hashes/descriptors; missing residuals and baseline remain refusal conditions.'}))
    return declaration
if __name__=='__main__':generate()
