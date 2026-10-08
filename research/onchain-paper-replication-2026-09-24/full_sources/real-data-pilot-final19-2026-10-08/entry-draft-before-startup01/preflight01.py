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
NAME='eth-paper-real-data-end-to-end-resource-20261008-19'
GATE=str((HERE/'gate01.json').relative_to(ROOT))
SUCCESSOR={'path': 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-fixed19-metadata-successor01-2026-10-08/successor02.py', 'sha256': '4cb59a54f4627e5236c63a35b734d44b174f108ebc86bd3ad803f1090ee88927'}
EXPECTED_RESOURCES={'disk_floor_bytes': 10737418240, 'disk_paths': ['/home/malecada/master_thesis/TradingAgents-audit-fixes'], 'memory_high_bytes': 5368709120, 'memory_max_bytes': 6442450944, 'native_unit_limits': {'file_size_bytes': 1073741824}, 'reserve_bytes': 2684354560, 'start_reserve_bytes': 9126805504, 'storage_budget': {'authority_root': '/home/malecada/master_thesis/TradingAgents-audit-fixes', 'experiment': 'eth-paper-real-data-end-to-end-resource-20261008-19', 'kind': 'real-pilot-writable-union', 'limits': {'max_allocated_bytes': 21474836480, 'max_depth': 64, 'max_entries': 1000000, 'max_logical_bytes': 17179869184, 'max_scan_seconds': 5}, 'roots': ['/home/malecada/master_thesis/TradingAgents-audit-fixes/research_artifacts', '/home/malecada/master_thesis/TradingAgents-audit-fixes/research_runs/eth-paper-real-data-end-to-end-resource-20261008-19'], 'schema_version': 2, 'shared_files': ['/home/malecada/master_thesis/TradingAgents-audit-fixes/research_runs/.lock']}, 'wall_seconds': 28800}
BINDER={'path': 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-transport-binding-preparation01-2026-10-06/bind01.py', 'sha256': 'bcca66a6c7daba762a629dff84b9f16e48e7b9c2ffe51f77511942816ee444cb'}
INDEX_CAPACITY={'path': 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-index-capacity01-2026-10-07/candidate/index_capacity.py', 'sha256': '977e5a6c37041caef7064f83dd6c3a749141451ef7bd42166a7aaca0c67bdaa5'}
OPAQUE_ROLE='archive_transport'
GRAPH_METADATA_SHA='73779a7d29bdf98530b3886282339f76edb4feac28b11470a8c147250fe34247'


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

def projected(inventory,observation,limits):
    logical=inventory['new_logical_bytes'];allocated=logical+inventory['allocation_overhead_bytes']
    entries=inventory['regular_file_slots']+inventory['directory_slots']+inventory['filesystem_assumption']['extra_entries']
    need(all(type(v) is int and v>0 for v in (logical,allocated,entries)),'finite projected growth required')
    for key,growth,limit in (('logical_file_bytes',logical,'max_logical_bytes'),('allocated_bytes',allocated,'max_allocated_bytes'),('entries',entries,'max_entries')):
        need(observation[key]+growth<=limits[limit],'fresh writable union plus complete projected growth exceeds '+limit)
    return {'new_logical_growth_bytes':logical,'new_allocated_growth_bytes':allocated,'new_entries':entries,
            'projected_logical_bytes':observation['logical_file_bytes']+logical,
            'projected_allocated_bytes':observation['allocated_bytes']+allocated,
            'projected_entries':observation['entries']+entries,
            'qualification':'Residual subsets already included, never double charged. Allocation overhead is the accepted model, not measured future blocks.'}

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


def prepared_inputs(binding,release,admission,job):
    draft=read(binding['draft']);saved=read(binding['preparation']);baseline=read(binding['baseline']);review=read(binding['binding_review'])
    need(hashlib.sha256(json.dumps(draft['graphs'],sort_keys=True).encode()).hexdigest()==GRAPH_METADATA_SHA,'genuine seven graph metadata differs')
    need(review['decision']=='accepted' and review['identity']==NAME,'actual independent final binding review required')
    for role in ('gate','draft','preparation','baseline','transport','transport_binding'):
        need(review['evidence'].get(binding[role]['path'])==binding[role]['sha256'],'final binding review join differs')
    need(draft['protocol']['physical_baseline']['evidence']==binding['baseline'],'baseline reference differs')
    observed=baseline['result']['observation'];declared=draft['protocol']['physical_baseline']
    need(all(declared[k]==observed[o] for k,o in (('logical_bytes','logical_file_bytes'),('allocated_bytes','allocated_bytes'),('entries','entries'))),'baseline declared totals differ')
    path=reference(SUCCESSOR);raw=read_path(path)
    need(hashlib.sha256(raw).hexdigest()==SUCCESSOR['sha256'] and release['evidence'].get(SUCCESSOR['path'])==SUCCESSOR['sha256'],'accepted metadata preparer source differs')
    dependencies=path.with_name('DEPENDENCIES02.json');depref=str(dependencies.relative_to(ROOT))
    need(release['evidence'].get(depref)==hashlib.sha256(read_path(dependencies)).hexdigest(),'metadata dependency closure unreviewed')
    for ref in json.loads(read_path(dependencies)).values():need(release['evidence'].get(ref['path'])==ref['sha256'],'metadata helper unreviewed')
    module=types.ModuleType('packed_final_metadata');module.__file__=str(path);exec(compile(raw,str(path),'exec'),vars(module))
    actual=module.prepare(ROOT,draft);need(actual==saved,'fresh metadata preparation differs from reviewed body')
    need(actual['inventory']['storage_budget_unchanged']==job['resources']['storage_budget'],'packed inventory storage policy differs')
    bound=read(binding['transport_binding'])
    binder_path=reference(BINDER);binder_raw=read_path(binder_path)
    need(hashlib.sha256(binder_raw).hexdigest()==BINDER['sha256'] and release['evidence'].get(BINDER['path'])==BINDER['sha256'],'exact accepted binder source required')
    binder=types.ModuleType('accepted_offline_binder');binder.__file__=str(binder_path)
    exec(compile(binder_raw,str(binder_path),'exec'),vars(binder))
    archive_role=actual['builder03_spec']['template_roles']['archive']
    archive=read(actual['builder03_spec']['references'][archive_role])
    need(bound['source_request']['prepared']==binding['preparation'] and bound['source_request']['archive_policy']==actual['builder03_spec']['references'][archive_role],'actual binder source request differs')
    need(bound['source_request']['connection']['path']==binder.CONNECTION and bound['source_request']['connection']['sha256']==binder.CONNECTION_SHA,'accepted opaque connection reference differs')
    inverse_binding(actual,archive,bound,binding['transport'],binder.raw,binder.sha)
    docs=bound['inputs']
    for role,ref in draft['protocol']['references'].items():
        if role not in docs and role!=OPAQUE_ROLE:need(all(admission.inputs[role][k]==ref[k] for k in ('path','sha256')),'unchanged prepared input reference differs: '+role)
    need(next(iter(job['payload']['representation_jobs'].values()))['compact_archive_transport_input']==OPAQUE_ROLE,'fixed sole opaque role differs')
    need(all(admission.inputs[OPAQUE_ROLE][k]==binding['transport'][k] for k in ('path','sha256')),'admitted opaque input differs')
    validate_opaque(binding['transport'])
    for role,expected in docs.items():
        need(read(admission.inputs[role])==expected,'admitted bound input differs: '+role)
    return actual


def check():
    binding=json.loads((HERE/'BINDING01.json').read_bytes())
    need(binding['identity']==NAME and binding['schema_version']==1,'fixed final binding required')
    for role in ('prior_outcome_review','prior_preservation_complete','prior_recovery_review'):
        reference(binding.get(role))
    # Unknown draft references refuse before admission, subprocesses or scans.
    for role in ('gate','draft','preparation','baseline','transport','binding_review','transport_binding'):reference(binding[role])
    need(binding['gate']['path']==GATE,'fixed gate path differs')
    source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    release_path=HERE/'RELEASE_REVIEW01.json';release=json.loads(read_path(release_path))
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
    if not admission.ready or admission.effective_attempt_budget!=90:raise ValueError('exact pilot admission/budget differs')
    for relative,expected in admission.experiment['source_files'].items():
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
    prepared=prepared_inputs(binding,release,admission,job)
    storage=WritableUnion(budget,ROOT).check()
    scopes=projected(prepared['inventory'],storage,budget['limits'])
    startup=scopes['new_allocated_growth_bytes']+job['resources']['disk_floor_bytes']
    free=shutil.disk_usage(ROOT).free; available=mem_available()
    if free<startup:raise ValueError('full projected source/scratch plus disk floor unavailable')
    if available<job['resources']['start_reserve_bytes']:raise ValueError('frozen startup RAM reserve unavailable')
    return args,{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':source,'experiment':NAME,
        'registration_sha256':file_hash(HERE/'gate01.json'),'release_sha256':file_hash(release_path),'effective_attempt_budget':90,
        'source_pins':len(admission.experiment['source_files']),'compact_input_pins':len(admission.inputs),
        'index_capacity':index_capacity,'projected_reservations':scopes,'host_mem_available_bytes':available,'free_disk_bytes':free,
        'startup_free_requirement_bytes':startup,'storage_observation':storage,
        'qualification':'Read-only source/metadata/namespace/resource check; original scientific reads remain in the admitted worker. Packed reservations include typed, retained, residual and scratch declarations. Sampled storage and modeled allocation are not hard quotas or scan-time proof.'}


if __name__=='__main__':print(json.dumps(check()[1],sort_keys=True))
