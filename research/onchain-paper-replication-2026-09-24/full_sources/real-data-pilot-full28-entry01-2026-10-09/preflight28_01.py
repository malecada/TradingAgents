"""Read-only entry checks for the fixed final seven-graph real-data pilot."""
from pathlib import Path
from types import SimpleNamespace
import datetime
import copy
import os
import stat
import sys
import hashlib
import types
import json
import shutil
import subprocess

from tradingagents.research.onchain_replication.job import _admitted, PREFIX
from tradingagents.research.onchain_replication.environment import inventory
from tradingagents.research.onchain_replication.provenance import file_hash
from tradingagents.research.onchain_replication.resources import mem_available
from tradingagents.research.onchain_replication.real_pilot_storage import WritableUnion

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
NAME='eth-paper-real-data-end-to-end-resource-20261009-28'
GATE=str((HERE/'gate01.json').relative_to(ROOT))
EXPECTED_RESOURCES={'disk_floor_bytes': 10737418240, 'disk_paths': ['/home/malecada/master_thesis/TradingAgents-audit-fixes'], 'memory_high_bytes': 5368709120, 'memory_max_bytes': 6442450944, 'native_unit_limits': {'file_size_bytes': 1073741824}, 'reserve_bytes': 2684354560, 'start_reserve_bytes': 2684354560, 'storage_budget': {'authority_root': '/home/malecada/master_thesis/TradingAgents-audit-fixes', 'experiment': 'eth-paper-real-data-end-to-end-resource-20261009-28', 'kind': 'real-pilot-writable-union', 'limits': {'max_allocated_bytes': 21474836480, 'max_depth': 64, 'max_entries': 1000000, 'max_logical_bytes': 17179869184, 'max_scan_seconds': 5}, 'roots': ['/home/malecada/master_thesis/TradingAgents-audit-fixes/research_artifacts', '/home/malecada/master_thesis/TradingAgents-audit-fixes/research_runs/eth-paper-real-data-end-to-end-resource-20261009-28'], 'schema_version': 2, 'shared_files': ['/home/malecada/master_thesis/TradingAgents-audit-fixes/research_runs/.lock']}, 'wall_seconds': 28800}
INDEX_CAPACITY={'path': 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-index-capacity02-2026-10-08/candidate/index_capacity.py', 'sha256': 'f486a3b7d8930378df7e17bd347c0f70d61355b657da30c7bad338f31b0de9bb'}
BINDER={'path': 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-transport-binding-preparation01-2026-10-06/bind01.py', 'sha256': 'bcca66a6c7daba762a629dff84b9f16e48e7b9c2ffe51f77511942816ee444cb'}
OPAQUE_ROLE='archive_transport'


def need(ok,message):
    if not ok:raise ValueError(message)

def reference(ref):
    need(type(ref) is dict and {'path','sha256'}<=set(ref),'actual bound reference required')
    q=Path(ref['path']);pin=ref['sha256']
    need(not q.is_absolute() and '..' not in q.parts and str(q)==ref['path'] and '\n' not in str(q) and '\r' not in str(q),'canonical relative evidence required')
    need(type(pin) is str and len(pin)==64 and all(c in '0123456789abcdef' for c in pin),'actual reference digest required')
    return ROOT/q

def read_path(path):
    need(path.resolve(strict=True)==path and path.is_file() and path.stat().st_nlink==1 and path.stat().st_size<=4*1024**2,'canonical bounded control required')
    raw=path.read_bytes();need(len(raw)<=4*1024**2,'bounded control changed');return raw

def read(ref):
    raw=read_path(reference(ref));need(hashlib.sha256(raw).hexdigest()==ref['sha256'],'bound evidence changed');return json.loads(raw)

def authenticate_committed(source,refs):
    """One Git batch authenticates every exact local body, including the release."""
    bodies=[];queries=[]
    for path,pin in refs.items():
        raw=read_path(reference({'path':path,'sha256':pin}))
        need(hashlib.sha256(raw).hexdigest()==pin,'reviewed entry changed: '+path)
        bodies.append(raw);queries.append(source+':'+path)
    output=subprocess.check_output(['git','cat-file','--batch'],cwd=ROOT,input=('\n'.join(queries)+'\n').encode())
    pos=0
    for query,body in zip(queries,bodies):
        end=output.find(b'\n',pos);need(end>=pos,'missing Git batch header');header=output[pos:end].split();pos=end+1
        need(len(header)==3 and header[1]==b'blob','reviewed body is missing or non-blob: '+query)
        size=int(header[2]);need(size==len(body) and output[pos:pos+size]==body and output[pos+size:pos+size+1]==b'\n','reviewed body not committed: '+query)
        pos+=size+1
    need(pos==len(output),'unexpected Git batch suffix')


def committed_refs(refs,binding):
    """Exactly one fixed private dispatch body stays local; its ref stays committed."""
    ref=binding['transport'];reference(ref)
    need(type(ref.get('bytes')) is int and 0<ref['bytes']<=4*1024**2,'bounded private dispatch reference required')
    path=reference(ref)
    need(path.is_relative_to(ROOT/'research_artifacts/real_pilot_runtime') and path.suffix=='.json','fixed private runtime dispatch scope required')
    need(refs.get(ref['path'])==ref['sha256'],'opaque digest must be released')
    for role,value in binding.items():
        if role!='transport' and type(value) is dict and 'path' in value:need(value['path']!=ref['path'],'public binding cannot use opaque exception')
    result=dict(refs);del result[ref['path']]
    need(len(result)+1==len(refs),'exactly one opaque body exception required')
    return result

def validate_opaque(ref):
    """Hash bytes without decoding/printing connection metadata; stable descriptor."""
    path=reference(ref)
    need(type(ref.get('bytes')) is int and 0<ref['bytes']<=4*1024**2 and path.is_relative_to(ROOT/'research_artifacts/real_pilot_runtime') and path.suffix=='.json','fixed bounded opaque dispatch required')
    need(path.resolve(strict=True)==path and path.parent.resolve(strict=True)==path.parent,'opaque route redirected')
    parent=path.parent.lstat()
    need(stat.S_IMODE(parent.st_mode)==0o700 and parent.st_uid==os.getuid(),'private owned parent required')
    def signature(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC);primary=None
    try:
        before=os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and stat.S_IMODE(before.st_mode)==0o600 and before.st_uid==os.getuid() and before.st_size==ref['bytes'],'private dispatch identity differs')
        digest=hashlib.sha256();count=0
        while count<=ref['bytes']:
            block=os.read(fd,min(65536,ref['bytes']+1-count))
            if not block:break
            count+=len(block);digest.update(block)
        need(count==ref['bytes'] and digest.hexdigest()==ref['sha256'],'private dispatch bytes/hash differ')
        need(signature(before)==signature(os.fstat(fd))==signature(path.lstat()) and signature(parent)==signature(path.parent.lstat()),'private dispatch changed')
    except BaseException as error:primary=error;raise
    finally:
        try:os.close(fd)
        except BaseException as error:
            if primary is None:raise
            primary.add_note('Opaque dispatch close failure: '+repr(error))





def inverse_binding(prepared,archive,bound,private_ref,raw,sha):
    """Inverse only the accepted binder's three scoped public modifications."""
    need(bound['status']=='BOUND_DRAFT_NOT_REGISTERED_NOT_ADMITTED' and bound['independent_approval'] is False,'actual binder output required')
    need(bound['private_input']=={OPAQUE_ROLE:private_ref},'exactly one actual private dispatch reference required')
    req=bound['source_request'];need(str(Path(req['private_parent'])/req['private_leaf'])==private_ref['path'],'published opaque destination differs')
    docs=copy.deepcopy(bound['inputs']);roles=prepared['builder03_spec']['template_roles'];bridge=bound['binding']
    need(bridge['transport_role']==OPAQUE_ROLE and bridge['archive_role']==roles['archive'],'bound role mapping differs')
    policy=docs.pop(roles['archive'])
    need(policy['transport_identity']==bridge['transport_identity'] and sha(raw(policy))==bridge['archive_policy_sha256'],'actual bound policy digest differs')
    policy['transport_identity']=None;need(policy==archive,'binder changed unrelated archive policy')
    selected=next(iter(docs[roles['job']]['payload']['representation_jobs'].values()));item=docs[roles['producer_plan']]['producers'][selected['producer']]
    for value in (selected,item):
        need(value['compact_archive_transport_input']==OPAQUE_ROLE and value['descriptor']['compact_archive_execution']=={'backend':archive['backend'],'policy_sha256':bridge['archive_policy_sha256']},'bound descriptor digest differs')
        value['descriptor']['compact_archive_execution']['policy_sha256']=bridge['prior_descriptor_policy_sha256']
    expected=copy.deepcopy(prepared['builder03_result']['inputs'])
    need(OPAQUE_ROLE not in docs and expected[OPAQUE_ROLE]['connection'] is None,'only opaque connection transform allowed')
    docs[OPAQUE_ROLE]=expected[OPAQUE_ROLE]
    need(docs==expected,'binder changed unrelated prepared documents')
    return docs


def _encoded(value):
    if type(value) is dict:
        for key,child in value.items():
            need(type(key) is str,'plain metadata key required');_encoded(child)
    elif type(value) in (list,tuple):
        for child in value:_encoded(child)
    elif type(value) is int:need(-(2**63)<value<2**63,'encoded integer bound differs')
    elif value is None or type(value) in (str,float,bool):pass
    else:raise ValueError('plain registered metadata required')

def _path_envelope(path):
    import re
    need(type(path) is str and len(path.encode('ascii'))<=512 and re.fullmatch(r'[A-Za-z0-9_./-]+',path) and '..' not in Path(path).parts,'actual path encoding envelope differs')

def _capacity_source(capacity,public,admitted_sources,current_source):
    """Immutable prospective policy ancestry; live eligibility is sampled in check()."""
    anchor=capacity.get('source_anchor');pins=capacity.get('source_body_pins')
    need(type(anchor) is str and len(anchor)==40 and all(c in '0123456789abcdef' for c in anchor),'actual committed capacity source anchor required')
    need(type(pins) is dict and pins==public['source_pins'] and len(pins)>=365,'exact accepted public04 source body map required')
    need(all(admitted_sources.get(path)==pin for path,pin in pins.items()),'capacity source bodies differ from current admission')
    need('source' not in capacity and 'max_age_seconds' not in capacity,'capacity declaration must not impersonate current-source measurement')
    declared=datetime.datetime.fromisoformat(capacity['at']);now=datetime.datetime.now(datetime.timezone.utc)
    need(declared.tzinfo is not None and declared<=now,'capacity declaration timestamp missing timezone/future')
    ancestry=subprocess.run(['git','merge-base','--is-ancestor',anchor,current_source],cwd=ROOT,check=False)
    need(ancestry.returncode==0,'capacity source anchor is not an ancestor of current admission')
    authenticate_committed(anchor,pins)


def prepared_inputs(binding,release,admission,job):
    """Exact independently reviewed current inputs; no obsolete builder replay."""
    review=read(binding['binding_review']);core=read(binding['core_manifest']);public=read(binding['public_manifest']);prior=read(binding['public_refs'])
    need(review['decision']=='accepted' and review['identity']==NAME,'actual final input binding review required')
    actual={role:{key:info[key] for key in ('path','sha256')} for role,info in admission.inputs.items()}
    need(len(actual)==64 and review['input_refs']==actual and binding['input_refs']==actual,'exact genuine64-role input closure differs')
    need(public['experiment']==NAME and public['all_input_roles']==64,'accepted public04 identity/roster differs')
    for role,ref in binding.items():
        if type(ref) is dict and {'path','sha256'}<=set(ref):
            need(release['evidence'].get(ref['path'])==ref['sha256'],'binding evidence absent from release')
            if role!='binding_review':need(review['evidence'].get(ref['path'])==ref['sha256'],'current binding evidence not independently joined')
    for role,info in actual.items():
        need(len(role.encode('ascii'))<=128,'actual input role encoding differs');_path_envelope(str(ROOT/info['path']))
    bound=read(binding['transport_binding'])
    changed={'archive_transport','matching_ordered_edge_scratch'}|set(bound['inputs'])
    need(set(prior)==set(actual),'public04 original role roster differs')
    for role,ref in prior.items():
        if role not in changed:need(actual[role]['sha256']==ref['sha256'],'unrelated public04 input changed: '+role)
    need(admission.experiment['cumulative_budget_extension']['review']==binding['budget_review'],'genuine budget96 review differs')
    prepared=read(binding['preparation']);unbound=read(binding['unbound_archive'])
    need(prepared['preparation_origin']['public_manifest']==binding['public_manifest'],'prepared public04 origin differs')
    need(bound['source_request']['prepared']==binding['preparation'] and bound['source_request']['archive_policy']==binding['unbound_archive'],'actual binder source request differs')
    need(prepared['builder03_spec']['references']['archive_policy']==binding['unbound_archive'],'unbound archive role differs')
    binder_body=read_path(reference(BINDER));need(hashlib.sha256(binder_body).hexdigest()==BINDER['sha256'] and release['evidence'].get(BINDER['path'])==BINDER['sha256'],'unchanged accepted binder source required')
    import ast
    binder_tree=ast.parse(binder_body);scope={'json':json,'hashlib':hashlib}
    exec(compile(ast.Module(body=[n for n in binder_tree.body if isinstance(n,ast.FunctionDef) and n.name in ('raw','sha')],type_ignores=[]),str(reference(BINDER)),'exec'),scope)
    inverse_binding(prepared,unbound,bound,binding['transport'],scope['raw'],scope['sha'])
    for role,document in bound['inputs'].items():
        _encoded(document);need(read(actual[role])==document,'actual bound public body differs: '+role)
    need(all(actual[OPAQUE_ROLE][key]==binding['transport'][key] for key in ('path','sha256')),'actual opaque role differs')

    # Immutable four core documents must be literal core03 bodies.
    for role,ref in core['inputs'].items():need(read(actual[role])==read(ref),'accepted core03 body changed: '+role)
    selected=next(iter(job['payload']['representation_jobs'].values()))
    pilot=read(actual[selected['real_pilot_input']]);mcm=read(actual[selected['compact_mcm_input']]);output=read(actual[selected['compact_mcm_output_input']]);compact=read(actual[selected['compact_policy_input']])
    need(mcm['schema_version']==6 and mcm['batched']['group_batches']==16 and mcm['batched']['batch_cells']==4096 and mcm['batched']['max_body_bytes']==1024 and mcm['batched']['max_checkpoint_bytes']==269114368,'exact grouped/single fatal snapshot policy differs')
    need(output['schema_version']==1 and 'partial_progress' not in pilot and 'scoring_diagnostic' not in pilot and 'diagnostic' not in pilot['outputs'],'full route cannot select diagnostic stop')
    schedule=compact['stage_policy']['schedule']
    need(schedule['max_total_checkpoints']==160 and schedule['max_total_checkpoint_bytes']==43058298880 and schedule['max_checkpoints']==1,'original cumulative checkpoint schedule differs')
    capacity=read(binding['capacity_observation'])
    need(capacity['identity']==NAME and capacity['decision']=='accepted','authenticated Root prospective capacity declaration required')
    _capacity_source(capacity,public,admission.experiment['source_files'],admission.source)
    for field in ('new_logical_growth_bytes','new_allocated_growth_bytes','non_directory_new_allocated_growth_bytes','new_entries','directory_allocated_bound_bytes','other_writer_reserved_bytes'):
        need(type(capacity.get(field)) is int and capacity[field]>=0,'missing explicit capacity term: '+field)
    need(capacity.get('allocation_semantics')=='prospective-headroom-sampled-aggregate-guards','explicit guarded prospective headroom semantics required')
    need(capacity['new_allocated_growth_bytes']>=capacity['non_directory_new_allocated_growth_bytes']+capacity['directory_allocated_bound_bytes']+capacity['other_writer_reserved_bytes'],'declared growth omits prospective headroom')
    need(capacity['directory_and_other_writers_included'] is True and capacity['runtime_residuals_included'] is True,'complete physical closure unjoined')
    need(type(capacity.get('owned_paths')) is list and bool(capacity['owned_paths']),'actual owned path roster required')
    for path in capacity['owned_paths']:_path_envelope(path)
    return capacity

def projected(capacity,observation,limits):
    logical=capacity['new_logical_growth_bytes'];allocated=capacity['new_allocated_growth_bytes'];entries=capacity['new_entries']
    need(logical>0 and allocated>=logical and entries>0,'actual reviewed growth required')
    for key,growth,limit in (('logical_file_bytes',logical,'max_logical_bytes'),('allocated_bytes',allocated,'max_allocated_bytes'),('entries',entries,'max_entries')):
        need(observation[key]+growth<=limits[limit],'current union plus complete growth exceeds '+limit)
    return {'new_logical_growth_bytes':logical,'new_allocated_growth_bytes':allocated,'new_entries':entries,'projected_logical_bytes':observation['logical_file_bytes']+logical,'projected_allocated_bytes':observation['allocated_bytes']+allocated,'projected_entries':observation['entries']+entries,'qualification':'Authenticated Root growth includes prospective directory/other-writer headroom, not observed future usage or a hard quota; aggregate union/floor refusals remain sampled.'}


def check(*,binding_ref=None,release_ref=None):
    if binding_ref is not None:need(reference(binding_ref)==HERE/'BINDING01.json','fixed binding path differs')
    if release_ref is not None:need(reference(release_ref)==HERE/'RELEASE_REVIEW01.json','fixed release path differs')
    binding=read(binding_ref) if binding_ref is not None else json.loads(read_path(HERE/'BINDING01.json'))
    need(binding['identity']==NAME and binding['schema_version']==1,'fixed final binding required')
    for role in ('prior_outcome_review','prior_preservation_complete','prior_recovery_review'):
        reference(binding.get(role))
    # Unknown draft references refuse before admission, subprocesses or scans.
    for role in ('gate','core_manifest','public_manifest','public_refs','capacity_observation','transport','binding_review','transport_binding','preparation','unbound_archive','budget_review'):reference(binding[role])
    need(binding['gate']['path']==GATE,'fixed gate path differs')
    source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    release_path=HERE/'RELEASE_REVIEW01.json';release=read(release_ref) if release_ref is not None else json.loads(read_path(release_path))
    need(release.get('decision')=='accepted' and release['identity']==NAME,'exact source/entry review missing')
    refs=dict(release['evidence'])
    for ref in binding.values():
        if type(ref) is dict and set(ref)>={'path','sha256'}:need(refs.get(ref['path'])==ref['sha256'],'final binding ref not independently released')
    for path in (release_path,HERE/'BINDING01.json',Path(__file__)):
        relative=str(path.relative_to(ROOT));digest=hashlib.sha256(read_path(path)).hexdigest()
        if path!=release_path:need(refs.get(relative)==digest,'exact entry/binding not independently released')
        refs[relative]=digest
    authenticate_committed(source,committed_refs(refs,binding))
    args=SimpleNamespace(root=ROOT,registration=GATE,experiment=NAME,source=source)
    admission,job=_admitted(args)
    if not admission.ready or admission.effective_attempt_budget!=99:raise ValueError('exact pilot admission/budget differs')
    need(len(admission.experiment['source_files'])>=365,'complete installed source plus entry registration pins required')
    for relative,expected in admission.experiment['source_files'].items():
        _path_envelope(str(ROOT/relative))
        need(relative!=binding['transport']['path'],'source cannot use opaque exception')
        need(refs.get(relative)==expected,'admitted source absent from authenticated release')
        if file_hash(ROOT/relative)!=expected:raise ValueError('source pin changed: '+relative)
    for role,info in admission.inputs.items():
        need(refs.get(info['path'])==info['sha256'],'admitted input absent from authenticated release')
        if role==OPAQUE_ROLE:
            need(all(info[k]==binding['transport'][k] for k in ('path','sha256')),'sole opaque admission reference differs')
            validate_opaque(binding['transport']);continue
        need(info['path']!=binding['transport']['path'],'opaque path reused under another input role')
        path=ROOT/info['path']
        if path.stat().st_size>4*1024**2 or file_hash(path)!=info['sha256']:
            raise ValueError('compact input pin changed: '+info['path'])
    # Exact new bounded ordered-edge scratch declaration; native envelope remains fixed.
    scratch=read({'path':admission.inputs['matching_ordered_edge_scratch']['path'],
                  'sha256':admission.inputs['matching_ordered_edge_scratch']['sha256']})
    need(scratch['experiment']==NAME and scratch['chunk_edge_products']==1024
         and scratch['incremental_explicit_numeric_scratch_bytes']==262144,
         'registered ordered-edge scratch reservation differs')
    need(scratch['installed_source']['path']=='tradingagents/research/onchain_replication/matching_annealing.py'
         and admission.experiment['source_files'][scratch['installed_source']['path']]==scratch['installed_source']['sha256'],
         'scratch reservation installed source differs')
    need(scratch['native_memory_max_bytes_unchanged']==job['resources']['memory_max_bytes']
         and scratch['native_memory_high_bytes_unchanged']==job['resources']['memory_high_bytes']
         and scratch['native_wall_seconds_unchanged']==job['resources']['wall_seconds'],
         'scratch reservation cannot raise native limits')
    # Validate the genuine resource-owner schema before graph loading or reservation.
    from tradingagents.research.onchain_replication.matching_owner import _pair_limits
    pair_limits=json.loads(read_path(ROOT/admission.inputs['pair_policy']['path']))['limits']
    compact_limits=json.loads(read_path(ROOT/admission.inputs['compact_policy']['path']))['stage_policy']['pair']
    need(pair_limits==compact_limits,'resource-owner and compact limits differ')
    _pair_limits(pair_limits,resource=True)
    # Scalar/header-only capacity refusal precedes torch inventory and RootIO.
    capacity_path=reference(INDEX_CAPACITY)
    capacity_body=read_path(capacity_path)
    need(hashlib.sha256(capacity_body).hexdigest()==INDEX_CAPACITY['sha256']
        and refs.get(INDEX_CAPACITY['path'])==INDEX_CAPACITY['sha256'],
        'exact released index capacity helper differs')
    capacity_module=types.ModuleType('pilot19_index_capacity')
    capacity_module.__file__=str(capacity_path)
    exec(compile(capacity_body,str(capacity_path),'exec'),capacity_module.__dict__)
    capacity_plan=next(iter(job['payload']['representation_jobs'].values()))
    capacity_descriptor=capacity_plan['descriptor']
    capacity_numeric=json.loads(read_path(ROOT/admission.inputs[capacity_plan['compact_mcm_input']]['path']))['numeric']
    index_capacity=capacity_module.validate(ROOT,admission.inputs,
        capacity_descriptor['resource_graph_inputs'],capacity_numeric,
        capacity_descriptor['configs']['dictionary'])
    runtime_inventory=subprocess.check_output([sys.executable,'-B','-c',"import json; from pathlib import Path; from tradingagents.research.onchain_replication.environment import inventory; print(json.dumps(inventory(Path.cwd(),include_torch=True),sort_keys=True))"],cwd=ROOT,timeout=30)
    if json.loads(runtime_inventory)!=json.loads((ROOT/admission.inputs['environment']['path']).read_bytes()):raise ValueError('installed runtime inventory differs')
    for path in (ROOT/'research_runs'/NAME,ROOT/PREFIX/'runs'/NAME,ROOT/PREFIX/'sources'/NAME,ROOT/PREFIX/'pilot-parent'/NAME,HERE/'launch-attempt01.json',HERE/'outer-exit01.json'):
        if path.exists() or path.is_symlink():raise ValueError('fixed namespace already reserved: '+str(path))
    units=subprocess.check_output(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],text=True)
    if units.strip():raise ValueError('another native resource process is active')
    for claim_path in (ROOT/'research_runs').glob('*/claim.json'):
        claim=json.loads(claim_path.read_bytes())
        if claim.get('program_id')==admission.spec['program_id'] and not any((claim_path.parent/name).exists() for name in ('complete.json','failed.json')):
            raise ValueError('another program claim is active: '+str(claim_path.parent))
    selected_plan=next(iter(job['payload']['representation_jobs'].values()))
    # _admitted already authenticates the installed selected route and eligibility.
    plan=json.loads(read_path(ROOT/admission.inputs[selected_plan['real_pilot_input']]['path']))
    need(plan['schema_version']==2 and plan['resource_policy']==job['resources'],'selected schema2 resource plan differs')
    budget=job['resources']['storage_budget']
    need(budget['schema_version']==2 and job['resources']==EXPECTED_RESOURCES,'fixed original resource envelope differs')
    capacity=prepared_inputs(binding,release,admission,job)
    storage=WritableUnion(budget,ROOT,experiment=admission.experiment_id).check()
    scopes=projected(capacity,storage,budget['limits'])
    startup=scopes['new_allocated_growth_bytes']+job['resources']['disk_floor_bytes']
    free=shutil.disk_usage(ROOT).free; available=mem_available()
    if free<startup:raise ValueError('full projected source/scratch plus disk floor unavailable')
    if available<job['resources']['start_reserve_bytes']:raise ValueError('frozen startup RAM reserve unavailable')
    return args,{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':source,'experiment':NAME,
        'registration_sha256':file_hash(HERE/'gate01.json'),'release_sha256':file_hash(release_path),'effective_attempt_budget':98,
        'source_pins':len(admission.experiment['source_files']),'compact_input_pins':len(admission.inputs),
        'index_capacity':index_capacity,'projected_reservations':scopes,'host_mem_available_bytes':available,'free_disk_bytes':free,
        'startup_free_requirement_bytes':startup,'storage_observation':storage,
        'qualification':'Read-only source/metadata/namespace/resource check; original scientific reads remain in the admitted worker. Packed reservations include typed, retained, residual and scratch declarations. Sampled storage and modeled allocation are not hard quotas or scan-time proof.'}


if __name__=='__main__':print(json.dumps(check()[1],sort_keys=True))
