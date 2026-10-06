"""One concrete metadata preparation handoff; never independent self-approval."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
PINS={
 'builder':('real-data-pilot-resource-input-builder03-2026-10-06/build_inputs03.py','e100a1fa2f8caaa6baf6cde85d5f50aa667ed6e04b6470d9c8368d5424748a2d'),
 'controls':('real-data-pilot-feature-control-inventory01-2026-10-06/controls01.py','d6b3bac4b71fc7cd6d2dfaf63d8aa395fb87e47eef5dbc2b7bd501fd385e59f3'),
 'residuals':('real-data-pilot-selected-feature-protocol01-2026-10-06/residuals02.py','34aeb5b492680bb804d3777e15ec4c640fe2a25517faf309563e58d265a751ac')}

def need(ok,msg):
    if not ok:raise ValueError(msg)
def load(name):
    rel,expected=PINS[name];path=HERE.parent/rel
    raw=path.read_bytes();need(hashlib.sha256(raw).hexdigest()==expected,'sealed source differs: '+name)
    spec=importlib.util.spec_from_file_location('pilot_metadata_'+name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def require_protocol(v):
    keys={'references','template_roles','typed_input_role','typed_allocations','transport_limits','physical_baseline','filesystem','runtime_reservation'}
    need(type(v) is dict and set(v) in (keys,keys|{'lifecycle_reservation'}),'missing exact selected protocol/reference/baseline declarations')
    need(all(v[k] is not None for k in keys),'absent selected protocol field')
    return v

def prepare(root,draft):
    b=load('builder');root=Path(root).resolve()
    need(type(draft) is dict and set(draft)=={'status','graphs','protocol'},'concrete draft fields differ')
    need(draft['status']=='DRAFT_NOT_RELEASED','draft status differs')
    need(set(draft['graphs'])==set(b.WEEKS),'exact seven weekly draft slots required')
    missing=[w for w in b.WEEKS if draft['graphs'][w] is None]
    need(not missing,'missing genuine graph/count metadata: '+', '.join(missing))
    # Genuine metadata shapes/refs first, before protocol or any output creation.
    graphs=b.graphs(root,draft['graphs']);p=require_protocol(draft['protocol'])
    roles=p['template_roles'];need(set(roles)=={'pilot','population','job','producer_plan','dictionary','compact','archive','output'},'exact eight template roles required')
    templates={key:b.metadata(root,p['references'][role]) for key,role in roles.items()}
    stage=templates['compact']['stage_policy'];job=templates['job'];pilot=templates['pilot'];archive=templates['archive']
    resource=job['resources'];budget=resource['storage_budget'];native=resource['native_unit_limits']['file_size_bytes']
    typed=p['typed_allocations'];need(stage['score_chunk_cells']==typed['chunk_cells'],'same original batch chunk selection required')
    r=load('residuals').resolve(stage,native_file_bytes=native,training_checkpoint_bytes=pilot['max_checkpoint_bytes'],runtime_reservation=p['runtime_reservation'],lifecycle_reservation=p.get('lifecycle_reservation'))
    base=p['physical_baseline'];need(set(base)=={'evidence','logical_bytes','allocated_bytes','entries'},'exact current baseline declaration required')
    b.ref_path(root,base['evidence']) # stat/reference only, no scan or credential read
    tr=p['transport_limits'];c=load('controls')
    counted={}
    for week,g in graphs.items():
        kinds=typed['by_week'][week]
        counted[week]={'rows':g['rows'],'count_evidence_sha256':g['node_count']['sha256'],
            'tail_part_bytes':kinds['score-tail-f64']['chunk_bytes'],'output_part_bytes':kinds['mcm-output-f32']['chunk_bytes'],
            'allowances':{name:{k:v for k,v in value.items() if k!='chunk_bytes'} for name,value in kinds.items()}}
    inventory={'schema_version':1,'graphs':counted,'chunk_cells':typed['chunk_cells'],'typed_control_bytes':typed['max_control_bytes'],
        'stage':{k:stage['log'][k] for k in ('max_events','chunk_events')}|{'max_total_checkpoints':stage['schedule']['max_total_checkpoints']},
        'archive':{k:archive[k] for k in ('max_stage_verifications','max_writer_metadata_bytes','max_read_metadata_bytes','max_stage_bytes','max_workflow_metadata_bytes')},
        'transport':{k:tr[k] for k in ('max_commands','max_payload_bytes','max_diagnostic_bytes','max_control_bytes')},
        'residual_domains':r['residual_domains'],'filesystem':p['filesystem'],
        'baseline':{k:base[k] for k in ('logical_bytes','allocated_bytes','entries')}|{'evidence_sha256':base['evidence']['sha256']},'storage_budget':budget}
    need(p['filesystem']['max_native_file_bytes']==native,'same registered native limit required')
    totals=c.calculate(inventory)
    store=totals['builder03_physical_fragment']|{'baseline_evidence':base['evidence'],'baseline_logical_bytes':base['logical_bytes'],'baseline_allocated_bytes':base['allocated_bytes']}
    spec={k:p[k] for k in ('references','template_roles','typed_input_role','typed_allocations','transport_limits')}|{'graphs':draft['graphs'],'physical_store':store}
    built=b.build(root,spec)
    return {'status':'DRAFT_NOT_REGISTERED_NOT_ADMITTED','builder03_spec':spec,'builder03_result':built,'inventory':totals,'residuals':r,'independent_approval':False}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--input',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    with Path(a.input).open('rb') as f:raw=f.read(4*1024**2+1)
    need(len(raw)<=4*1024**2,'metadata draft too large')
    result=prepare(a.root,json.loads(raw))
    with Path(a.output).open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
