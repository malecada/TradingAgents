"""Deterministic stdout-only unavailable prediction binding; no authority creation."""
import copy,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
PREP=HERE.parent/'financial-wrapper-serialized-prediction-preparation01-2026-10-05'
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
GATE=CAP/'fixture_inputs/financial_wrapper_serialized_storage01/gates.json'
DEST='fixture_inputs/financial_wrapper_serialized_prediction01/'
BASE=set('environment execution_job model runtime_mapping source_closure synthetic_recipe training wrapper_plan operational_source_compatibility operational_source_compatibility_review operational_source_compatibility_recovery'.split())
CONT=set('continuation_source_successor continuation_source_successor_review continuation_source_successor_recovery successor_original_closure successor_refusal successor_previous_recovery successor_original_refusal'.split())
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def read(p):return json.loads(p.read_bytes())
def insert_case(body,key,value):
    # Locate only the experiments object; leave every historical byte untouched.
    decoder=json.JSONDecoder(); start=body.index('{',body.index('"experiments"')+len('"experiments"'))
    previous,end=decoder.raw_decode(body,start)
    assert key not in previous and previous
    return body[:end-1]+','+json.dumps(key)+':'+raw(value).decode().rstrip()+body[end-1:]
def build():
    assert sha((PREP/'DRAFT_INPUTS02.json').read_bytes())=='2dc13a4360f4569636bbd95e8bcd7996369d55e28c126b79aee5f8ee375b9a68'
    d=read(PREP/'DRAFT_INPUTS02.json');parent=d['parent'];identity=d['prediction_identity']
    gate_raw=GATE.read_bytes();assert sha(gate_raw)=='b61f834005dc622b166303962d387f77a8100c54ce3b7159e84ddd2926ce1774'
    gate=json.loads(gate_raw);old=gate['experiments'][parent]
    inputs={k:copy.deepcopy(old['inputs'][k]) for k in BASE|CONT}; bodies={};origins={}
    def new(role,name,value):
        path=DEST+name;body=None if value is None else raw(value)
        inputs[role]={'dataset':'synthetic','path':path,'sha256':None if body is None else sha(body)}
        bodies[path]=None if body is None else body.decode()
    edge=d['prediction_edge_candidate'];new('prediction_source_successor','prediction-edge.json',edge)
    for role in ('prediction_source_successor_review','prediction_source_successor_recovery','prediction_parent_recovery'):new(role,role+'.json',None)
    inputs['prediction_continuation_closure']=copy.deepcopy(old['inputs']['source_closure'])
    closure=read(CAP/old['inputs']['source_closure']['path']);closure['installed']=edge['installed'];new('source_closure','source-closure.json',closure)
    plan=read(CAP/old['inputs']['wrapper_plan']['path']);plan.update(experiment_id=identity,namespace=identity,phase='predict',reference_input=None)
    # Preserve the actual schema's experiment key (no extra invented field).
    if 'experiment' in plan:plan['experiment']=identity;del plan['experiment_id']
    else:assert 'experiment_id' in read(CAP/old['inputs']['wrapper_plan']['path'])
    new('wrapper_plan','predict-plan.json',plan)
    observations=d['observed_parent_completion'];artifact_refs={'continued_claim':d['actual_parent_claim'],'continued_terminal':observations['complete_terminal'],'continued_checkpoint':observations['checkpoint_manifest'],'continued_completion':observations['fit_completion'],'continued_state':observations['checkpoint_members'][0]}
    for role,ref in artifact_refs.items():
        path=Path(ref['path']);body=path.read_bytes();assert sha(body)==ref['sha256']
        inputs[role]={'dataset':'synthetic','path':path.relative_to(CAP).as_posix(),'sha256':ref['sha256']}
    prior={'parent':parent,'claim_input':'continued_claim','terminal_input':'continued_terminal','checkpoint_input':'continued_checkpoint','completion_input':'continued_completion','provenance':observations['original_checkpoint_provenance']}
    new('wrapper_prior','prior.json',prior)
    assert len(inputs)==29
    case=copy.deepcopy(old);case['parent']=parent;case['inputs']=dict(sorted(inputs.items()));case['question']='Synthetic financial-wrapper prediction from the genuine serialized-storage continued COMPLETE parent; no empirical or economic claim.'
    case['source_files'].update(edge['installed'])
    for path,body in bodies.items():case['source_files'][path]=None if body is None else sha(body.encode())
    gate_text=insert_case(gate_raw.decode(),identity,case)
    assert all(json.loads(gate_text)['experiments'][k]==v for k,v in gate['experiments'].items())
    # Unique-path physical reads, with the existing final reread multiplier.
    sizes={}
    for info in inputs.values():
        p=info['path'];body=bodies.get(p)
        if p in bodies:sizes[p]=None if body is None else len(body.encode())
        else:sizes[p]=(CAP/p).stat().st_size
    source_sizes={}
    for p,pin in edge['installed'].items():
        if p in sizes:continue
        if p in edge['installed'] and any(x['path']==p for x in edge['allowed_delta']):source_sizes[p]=(PREP/Path(p).name).stat().st_size
        elif (CAP/p).is_file():source_sizes[p]=(CAP/p).stat().st_size
        else:source_sizes[p]=None
    known_input=sum(x for x in sizes.values() if x is not None)
    recovery={'kind':'continue100_outcome_recovery','decision':None,'source':d['actual_parent_source'],'identity':parent,'claim_sha256':d['actual_parent_claim']['sha256'],'terminal_sha256':observations['complete_terminal']['sha256'],'checkpoint_sha256':observations['checkpoint_manifest']['sha256'],'independent_outcome_review':None,'accepted_full_external_byte_recovery':None}
    return {'schema_version':1,'status':'DRAFT_UNAVAILABLE_NO_ADMISSION_OR_RELEASE','identity':identity,'required_roles':sorted(inputs),'role_count':29,'new_input_bodies':bodies,'gate_base':{'path':str(GATE),'sha256':sha(gate_raw)},'gate_literal_insert':{identity:case},'gate_candidate_text':gate_text,'historical_gate_bytes_preserved':True,'source_adoption':{'installed':edge['installed'],'allowed_delta':edge['allowed_delta'],'source_commit':None,'preclaim_sha256':sha((PREP/'preclaim01.py').read_bytes())},'parent_binding':{'experiment':identity,'phase':'predict','dependency_parent':parent,'input_roles':sorted(inputs),'input_count':29,'source':None,'design_source':None,'registration_sha256':None,'gate_sha256':None,'release_refs':None,'proof_reuse_contract':None,'launch_authority':False},'recovery_bridge_unaccepted_template':recovery,'recovery_bridge_required_decision_after_independent_acceptance':'accepted-actual-continue100-byte-recovery','accounting_observed':{'base':18,'prior':0,'highest':20,'spent':5,'complete':2,'failed':3,'remaining':15,'budget_amendment':False,'refund':False,'transfer':False},'byte_estimate':{'unique_input_path_sizes':sizes,'known_input_bytes_with_final_reread':2*known_input,'unknown_input_paths':[p for p,v in sizes.items() if v is None],'source_only_path_sizes':source_sizes,'gate_candidate_bytes':len(gate_text.encode()),'known_inputs_sources_gate_twice':2*(known_input+sum(v for v in source_sizes.values() if v is not None)+len(gate_text.encode())),'reader_cap':8388608,'complete_reader_estimate':None,'reason':'External release, reuse-contract and genuine missing proof bodies are unresolved. Known subtotal is not an admission or a complete Reader bound.'}}
if __name__=='__main__':print(json.dumps(build(),sort_keys=True,indent=2))
