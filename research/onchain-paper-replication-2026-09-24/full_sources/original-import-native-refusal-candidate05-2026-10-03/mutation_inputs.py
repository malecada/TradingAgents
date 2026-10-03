"""Deterministic per-variant draft inputs; no writes, admission or imports of numerics."""
import ast,copy,hashlib,json
from pathlib import Path
from resource_policy05 import NUMERIC,validate,CONSTRUCTOR_PATH,CONSTRUCTOR_SHA256
from refusal_cases import NAMES,PRECLAIM,policy,identity

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def render(base,variant,package_sources):
    """base is generator01.inputs(case='success', ...) with real pinned metadata.

    Final package_sources includes the two new refusal modules. Root supplies
    actual committed source anchor; this function never invents that value.
    """
    if variant not in NAMES or len(package_sources)!=144:raise ValueError('exact refusal variant/full144 package sources required')
    value=copy.deepcopy(base);files={};rename=lambda name:name.replace('fixture_inputs/success/','fixture_inputs/refusal-'+variant+'/')
    for name,raw in value['files'].items():files[rename(name)]=raw
    for row in value['inputs'].values():row['path']=rename(row['path'])
    def get(name):return json.loads(files[value['inputs'][name]['path']])
    def put(name,item):
        raw=canonical(item);files[value['inputs'][name]['path']]=raw;value['inputs'][name]['sha256']=sha(raw)
    if package_sources.get(CONSTRUCTOR_PATH)!=CONSTRUCTOR_SHA256:raise ValueError('registered neighborhood constructor source differs')
    numeric=get('mcm_policy');numeric['numeric']=dict(NUMERIC)
    for n in (2,3):validate(numeric['numeric'],n,n,32,16)
    put('mcm_policy',numeric)
    pair=get('pair_policy');pair['numerical_source']['files']=dict(package_sources);put('pair_policy',pair)
    job=get('execution_job');selected=next(iter(job['payload']['representation_jobs'].values()));descriptor=selected['descriptor'];descriptor['resource_fixture']['case']='refusal-'+variant
    descriptor['pair_execution']['policy_sha256']=value['inputs']['pair_policy']['sha256']
    if variant=='reservation':
        envelope=get('compact_policy');envelope['max_workflow_retained_logical_bytes']=262144+65536;put('compact_policy',envelope)
        descriptor['compact_execution']['policy_sha256']=value['inputs']['compact_policy']['sha256']
    plan=get('producer_plan');item=plan['producers'][selected['producer']]
    for key,val in selected.items():item[key]=copy.deepcopy(val)
    put('producer_plan',plan)
    if variant=='kind':job['kind']='fit'
    put('execution_job',job)
    if variant in ('job-input','job-hash'):
        alternate=copy.deepcopy(job);alternate['resources']['memory_high_bytes']-=1048576
        alternate_path='fixture_inputs/refusal-'+variant+'/alternate-job.json';raw=canonical(alternate);files[alternate_path]=raw;value['inputs']['alternate_execution_job']={'path':alternate_path,'sha256':sha(raw),'dataset':'synthetic'}
    control='fixture_inputs/refusal-'+variant+'/mutation.json';files[control]=canonical(policy(variant));value['inputs']['refusal_mutation']={'path':control,'sha256':sha(files[control]),'dataset':'synthetic'}
    value.update(files=files,variant=variant,identity=identity(variant),status='unregistered-negative-inputs',workflow_identity=sha(canonical(descriptor)),job_path=value['inputs']['execution_job']['path'])
    return value

def selected_imported_paths(source_files,identity_source):
    target='tradingagents/research/onchain_replication/imported_mcm_identity.py'
    if type(identity_source) is not bytes or len(identity_source)>65536 or source_files.get(target)!=sha(identity_source):raise ValueError('selected imported identity source body differs')
    values={}
    for node in ast.parse(identity_source).body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('KERNEL','HELPER'):
            name=node.targets[0].id
            if name in values:raise ValueError('duplicate selected imported source')
            value=ast.literal_eval(node.value)
            if type(value) is not str or Path(value).is_absolute() or '..' in Path(value).parts or source_files.get(value) is None:raise ValueError('selected imported kernel/helper absent from exact closure')
            values[name]=value
    if set(values)!={'KERNEL','HELPER'}:raise ValueError('selected imported constants missing')
    return values

def draft_gate(primary_gate,rendered,source_files,runtime_hashes,*,imported_identity_source):
    if set(rendered)!=set(NAMES):raise ValueError('all27 finite variants required')
    gate=copy.deepcopy(primary_gate);gate['experiments']={};gate['program_id']='original-import-refusal-engineering-20261003'
    gate['families']={'import-refusal-engineering':{'mechanism_id':'original-import-refusal-engineering-v1','attempt_budget':23,'prior_attempts':0,'history_reference':'Separate unexecuted refusal engineering family.27 variants:4 must fail before claim;23 maximum genuine failed claims. No transfer/refund/reopening of original scientific or primary engineering claims.'}}
    files={};template=next(iter(primary_gate['experiments'].values()))
    selected_sources=selected_imported_paths(source_files,imported_identity_source);kernel=selected_sources['KERNEL'];helper=selected_sources['HELPER']
    for variant in NAMES:
        item=rendered[variant];exp=copy.deepcopy(template);exp.update(family='import-refusal-engineering',inputs=item['inputs'],source_files=dict(source_files),runtime_hashes=runtime_hashes,question='Does the genuine registered '+variant+' mutation refuse at its frozen boundary before target publication?')
        if variant in ('source','kernel','helper'):
            target={'source':'tradingagents/research/onchain_replication/compact_mcm.py','kernel':kernel,'helper':helper}[variant]
            if target not in exp['source_files']:raise ValueError('negative source member missing')
            exp['source_files'][target]='0'*64
        path='fixture_inputs/refusal-'+variant+'/charter.md';files[path]=('Unexecuted synthetic negative fixture '+variant+'. '+json.dumps(policy(variant),sort_keys=True)+'. No financial inference or empirical budget authority. No retry/reset after a claim or poisoned Owner.\n').encode()
        exp['charter']={'path':path,'sha256':sha(files[path])};gate['experiments'][identity(variant)]=exp
    return gate,files
