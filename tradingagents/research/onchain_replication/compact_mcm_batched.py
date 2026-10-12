"""Explicit batched MCM closure; genuine owner boundaries, never old pair seals.

Selected local/typed-offload route. No registration or empirical admission.
"""
import hashlib
import importlib.util
import json
import mmap
import os
import re
import stat
from contextlib import contextmanager
from pathlib import Path
from . import adaptive_edge_policy
from . import phase_timing
from . import compiled_normalization_policy
from . import compiled_edge_owner
from . import matching_numeric_policy
import numpy as np
from . import compact_owner as owners, compact_mcm as producer
from . import compact_mcm_publication as publication, score_batches as io
from . import matching_checkpoint as engine, compact_policy
from . import geometry_publication, matching_owner
from .cache import cache_key
from .provenance import freeze, thaw, durable_mkdir, file_hash

FORMAT = 'ordered-mcm-batch-closure-v2'
PACKAGE = 'tradingagents.research.onchain_replication'
MODULES = {'driver':'batched_driver','journal':'batched_journal','executor':'batched_pair_executor','numeric_execution':'batched_numeric_execution','numeric_reuse':'batched_numeric_reuse'}
BACKEND_INPUT_POLICY = 'source-checked-backend-role-bundle-v1'
require = io._require
ENTRY_QUALIFICATION = 'genuine-mcm-entry-preparation-only-v1'


class EntryPreparationComplete(RuntimeError):
    """Registered engineering stop; outer attempt remains FAILED and spent."""


def _entry_qualification(policy):
    if 'entry_qualification' not in policy:return None
    value=policy['entry_qualification']
    require(type(value) is dict and set(value)=={'format','experiment_id','graph_hash'}
        and type(value['format']) is str and value['format']==ENTRY_QUALIFICATION,
        'explicit entry qualification required')
    require(type(value['experiment_id']) is str and re.fullmatch(
        r'eth-paper-real-data-end-to-end-resource-[0-9]{8}-[0-9]{2}',value['experiment_id']) is not None,
        'fixed resource qualification identity required')
    require(type(value['graph_hash']) is str and len(value['graph_hash'])==64
        and all(c in '0123456789abcdef' for c in value['graph_hash']),
        'fixed entry graph required')
    batched=policy.get('batched');execution=batched.get('execution') if type(batched) is dict else None
    require(type(policy.get('schema_version')) is int and policy['schema_version']==6
        and type(execution) is dict and 'compiled_normalization_policy' in execution,
        'entry qualification requires selected serial backend route')
    return tuple(sorted(value.items()))


def _stop_after_entry(target,policy):
    selected=_entry_qualification(policy)
    if selected is None:return
    from .imported_mcm_identity import Target
    from .imported_authority_lease import Lease
    require(type(target) is Target,'genuine qualification Target required')
    value=dict(selected);ad=target.owner.bound._run.admission
    require(ad.experiment_id==value['experiment_id'] and target.key==value['graph_hash'],
        'qualification experiment/first graph differs')
    lease=getattr(target.execution,'_sampled_authority_lease',None)
    require(type(lease) is Lease and not lease.closed and not lease.scheduler.closed,
        'genuine live qualification lease required')
    require(lease.execution is target.execution and lease.owner is target.owner
        and lease.target is target and lease.targets.get(id(target)) is target,
        'qualification target/lease join differs')
    lease._identity()
    owner=target.owner
    require(owner.active is None and len(owner.required)>1
        and owner.required[:2]==('dictionary-import','mcm-'+target.key)
        and set(owner.stages)=={'dictionary-import'} and owner.stages['dictionary-import'].closed,
        'qualification requires first unstarted MCM after imported dictionary')
    scheduler=lease.scheduler
    require(scheduler.policy['max_stale_ms']==60000 and scheduler.full is not None,
        'qualification requires unchanged60s full validation')
    require(0<=(scheduler.now()-scheduler.full)*1000<=60000,
        'qualification entry became stale')
    raise EntryPreparationComplete('registered first-graph entry prepared; no MCM stage or financial fit completed')


def selected(policy):
    return type(policy) is dict and type(policy.get('schema_version')) is int and policy['schema_version'] in (5,6)


def validate(policy, pairs):
    require(selected(policy) and set(policy) == {'schema_version','max_entries','max_workflow_metadata_bytes','numeric','batched'} | ({'entry_qualification'} if 'entry_qualification' in policy else set()), 'batched MCM policy schema')
    _entry_qualification(policy)
    b = policy['batched']
    grouped=policy['schema_version']==6
    require(type(b) is dict and set(b) == {'format','authority_boundaries','batch_cells','max_journal_bytes','max_body_bytes','max_closure_token_bytes','max_checkpoint_bytes','retention','max_spool_bytes','max_offload_metadata_bytes','max_offload_entries','max_offload_anchor_bytes','execution'} | ({'group_batches'} if grouped else set()) | ({'continuation'} if 'continuation' in b else set()), 'batched bounds schema')
    require(b['format'] == FORMAT and b['authority_boundaries'] == 'entry-batch-checkpoint-final', 'explicit operational deviation required')
    require(b['retention'] in (('typed-grouped-recover-before-retire-v1',) if grouped else ('local-v2','typed-recover-before-retire-v2')),'explicit batched retention route required')
    if grouped:require(type(b['group_batches']) is int and b['group_batches']==16,'explicit sixteen batch groups required')
    require(type(b['max_spool_bytes']) is int and 4*pairs <= b['max_spool_bytes'] < 2**63 and type(b['max_offload_metadata_bytes']) is int and 0 < b['max_offload_metadata_bytes'] < 2**63 and type(b['max_offload_entries']) is int and 0 < b['max_offload_entries'] <= 4000000,'explicit spool/metadata bounds required')
    for k in ('batch_cells','max_journal_bytes','max_body_bytes','max_closure_token_bytes','max_checkpoint_bytes'):
        require(type(b[k]) is int and 0 < b[k] < 2**63, 'positive batched allowance required')
    require(b['batch_cells'] <= 4096 and 1024 <= b['max_body_bytes'] <= 1024**2 and b['max_closure_token_bytes'] <= 64*1024**2, 'batch bounds differ')
    execution=b['execution']
    require(type(execution) is dict and set(execution)=={'route','max_entries','max_retained_bytes','max_key_bytes','max_origin_bytes','max_summary_bytes'} | ({'geometry'} if 'geometry' in execution else set()) | ({'binding_timing'} if 'binding_timing' in execution else set()) | ({'backend_input_policy'} if 'backend_input_policy' in execution else set()) | ({'edge_cache_policy'} if 'edge_cache_policy' in execution else set()) | ({'compiled_normalization_policy','compiled_normalization_inputs'} if 'compiled_normalization_policy' in execution else set()) | ({'compiled_edge_policy','compiled_edge_inputs'} if 'compiled_edge_policy' in execution else set()) | ({'numeric_kernel_policy'} if 'numeric_kernel_policy' in execution else set()),'explicit numeric execution schema required')
    _compiled_policy(execution)
    _edge_policy(execution)
    _backend_input_policy(execution)
    _numeric_policy(execution)
    if 'edge_cache_policy' in execution:require(adaptive_edge_policy.freeze(execution['edge_cache_policy']) is not None,'explicit adaptive selection required')
    require(execution['route']=='immutable-input-session+exact-byte-reuse-v1','explicit numerical operation deviation required')
    require(all(type(execution[k]) is int for k in ('max_entries','max_retained_bytes','max_key_bytes','max_origin_bytes','max_summary_bytes')),'finite numeric execution allowances required')
    require(1<=execution['max_entries']<=4096 and 1024<=execution['max_retained_bytes']<=64*1024**2 and 0<execution['max_key_bytes']<=min(execution['max_retained_bytes'],8*1024**2),'bounded exact result cache required')
    require(9*pairs<=execution['max_origin_bytes']<2**63 and 0<execution['max_summary_bytes']<2**63,'full numeric provenance reservation required')
    count = (pairs+b['batch_cells']-1)//b['batch_cells']
    _continuation_policy(b,count)
    if 'binding_timing' in execution:
        require(grouped and matching_owner.binding_timing_policy(execution['binding_timing']) is not None,'selected schema6 binding timing required')
        require(execution['max_summary_bytes']>=count*8192,'full timing summary reservation required')
    if 'geometry' in execution:
        require(geometry_publication.policy(execution['geometry']) is not None,'selected geometry policy required')
        require(execution['max_summary_bytes']>=count*8192,'full geometry summary reservation required')
    require(type(b['max_offload_anchor_bytes']) is int and 0 <= b['max_offload_anchor_bytes'] <= 16*1024**2 and (b['retention']=='local-v2' or ((count+15)//16 if grouped else count)*32<=b['max_offload_anchor_bytes']),'offload anchor memory allowance exceeded')
    require(count*168 <= b['max_closure_token_bytes'] and count*(2*b['max_body_bytes']+92)+pairs*53 <= b['max_journal_bytes'], 'full batch denominator not reserved')
    return b


def _continuation_policy(b,count):
    if 'continuation' not in b:return None
    value=b['continuation']
    require(type(value) is dict and set(value)=={'format','manifest_input','max_commit_bytes'} | ({'graph_manifest_inputs'} if 'graph_manifest_inputs' in value else set())
            and value['format']=='completed-prefix-v1','explicit continuation selection required')
    role=value['manifest_input']
    require(role is None or type(role) is str and 0<len(role)<=128 and role.isascii()
            and all(c.isalnum() or c in '_-' for c in role),'finite continuation input required')
    graph_roles=value.get('graph_manifest_inputs',{})
    require(type(graph_roles) is dict and len(graph_roles)<=7 and all(
        type(graph) is str and len(graph)==64 and all(c in '0123456789abcdef' for c in graph)
        and type(name) is str and 0<len(name)<=128 and name.isascii()
        and all(c.isalnum() or c in '_-' for c in name) for graph,name in graph_roles.items()),
        'finite graph-specific continuation inputs required')
    require(role is None or not graph_roles,'single and graph-specific continuation routes conflict')
    require(type(value['max_commit_bytes']) is int and count*b['max_body_bytes']<=value['max_commit_bytes']<2**63,
            'complete prefix commit reservation required')
    require(count*(3*b['max_body_bytes']+92)+53*pairs_for_batches(b,count)<=b['max_journal_bytes'],
            'prefix commits exceed journal reservation')
    return tuple(sorted((key,tuple(sorted(item.items())) if key=='graph_manifest_inputs' else item)
                        for key,item in value.items()))


def pairs_for_batches(b,count):
    # Conservative full last batch: logical reservation, never completed credit.
    return count*b['batch_cells']


def _compiled_policy(execution):
    if 'compiled_normalization_policy' not in execution:
        require('compiled_normalization_inputs' not in execution,'normalization roles without selection')
        return None
    value=compiled_normalization_policy.freeze(execution['compiled_normalization_policy'])
    require(value is not None,'explicit compiled normalization selection required')
    roles=execution.get('compiled_normalization_inputs')
    require(type(roles) is dict and set(roles)=={'source','library','runtime'},'exact registered normalization roles required')
    require(all(type(role) is str and 0<len(role)<=128 and role.isascii() and all(c.isalnum() or c in '_-' for c in role) for role in roles.values()) and len(set(roles.values()))==3 and 'environment' not in roles.values(),'distinct finite registered normalization roles required')
    return value


def _compiled_inputs(execution,run,*,registered=None):
    value=_compiled_policy(execution)
    if value is None:return None
    policy=dict(value);ad=run.admission;runtime=None
    for kind in ('source','library','runtime'):
        role=execution['compiled_normalization_inputs'][kind]
        require(role in ad.inputs,'normalization role not admitted')
        info=ad.inputs[role];path=ad.root/info['path']
        require(str(path)==policy[kind+'_path'] and path.resolve()==path and info['sha256']==policy[kind+'_sha256'],'normalization registered path/hash differs')
        limit=4096 if kind=='runtime' else 65536
        bounded=compiled_normalization_policy.read_reference(path,info['sha256'],limit,policy['runtime_bytes'] if kind=='runtime' else None,owned=kind=='library')
        require((run.read_input(role) if registered is None else registered[role])==bounded,'normalization genuine input bytes differ')
        if kind=='runtime':runtime=compiled_normalization_policy.runtime_metadata(bounded)
    require('environment' in ad.inputs and runtime['runtime_inventory_sha256']==ad.inputs['environment']['sha256'],'normalization inventory not joined to genuine environment input')
    environment=ad.inputs['environment'];path=ad.root/environment['path']
    bounded=compiled_normalization_policy.read_reference(path,environment['sha256'],1024**2)
    require((run.read_input('environment') if registered is None else registered['environment'])==bounded,'normalization environment input changed')
    return value



def _edge_policy(execution):
    if 'compiled_edge_policy' not in execution:
        require('compiled_edge_inputs' not in execution,'edge roles without selection')
        return None
    value=compiled_edge_owner.freeze(execution['compiled_edge_policy'])
    require(value is not None,'explicit edge selection required')
    roles=execution.get('compiled_edge_inputs')
    require(type(roles) is dict and set(roles)=={'source','adapter','library','runtime','abi'},'exact five edge roles required')
    require(all(type(role) is str and 0<len(role)<=128 and role.isascii() and all(c.isalnum() or c in '_-' for c in role) for role in roles.values()) and len(set(roles.values()))==5 and 'environment' not in roles.values(),'distinct finite edge roles required')
    return value

def _edge_inputs(execution,run,*,registered=None):
    value=_edge_policy(execution)
    if value is None:return None
    policy=dict(value);ad=run.admission;runtime=None
    for kind in ('source','adapter','library','runtime','abi'):
        role=execution['compiled_edge_inputs'][kind]
        require(role in ad.inputs,'edge role not admitted')
        info=ad.inputs[role];path=ad.root/info['path']
        require(str(path)==policy[kind+'_path'] and path.resolve()==path and info['sha256']==policy[kind+'_sha256'],'edge registered path/hash differs')
        limit=4096 if kind in ('runtime','abi') else 65536
        size=policy[kind+'_bytes'] if kind in ('runtime','abi') else ((21920 if policy['format']=='cpython-two-attribute-edge-owner-v1' and policy['library_sha256']=='adead75d8f74f77b7d70164dab5465fef8a0e7ec06255b3dcd599f721745df97' else 17072) if kind=='library' else None)
        body=compiled_edge_owner.read_reference(path,info['sha256'],limit,size,owned=kind=='library')
        require((run.read_input(role) if registered is None else registered[role])==body,'edge genuine input body differs')
        if kind=='runtime':runtime=compiled_normalization_policy.runtime_metadata(body)
        if kind=='abi':compiled_edge_owner.abi_metadata(body)
        if kind=='adapter':
            require(path==ad.root/'tradingagents/research/onchain_replication/edge_chunk_adapter.py' and ad.experiment['source_files'].get('tradingagents/research/onchain_replication/edge_chunk_adapter.py')==info['sha256'],'edge adapter input/source join differs')
    require('environment' in ad.inputs and runtime['runtime_inventory_sha256']==ad.inputs['environment']['sha256'],'edge runtime inventory/environment differs')
    info=ad.inputs['environment'];body=compiled_edge_owner.read_reference(ad.root/info['path'],info['sha256'],1024**2)
    require((run.read_input('environment') if registered is None else registered['environment'])==body,'edge environment genuine input differs')
    return value

def _backend_input_policy(execution):
    if 'backend_input_policy' not in execution:return False
    require(type(execution['backend_input_policy']) is str and execution['backend_input_policy']==BACKEND_INPUT_POLICY,'unsupported backend input selection')
    require(_compiled_policy(execution) is not None or _edge_policy(execution) is not None,'backend input bundle requires selected backend')
    return True


def _numeric_policy(execution):
    if 'numeric_kernel_policy' not in execution:return None
    value=matching_numeric_policy.freeze(execution['numeric_kernel_policy'])
    require(value is not None,'explicit fixed C05 numeric selection required')
    return value


def _backend_inputs(execution,run):
    """Opt-in compound admission; retain each original bounded role readback.

    Only the genuine run owns the two fresh source checks. The returned bytes
    replace repeated admissions, never registered paths, hashes or ABI checks.
    """
    with phase_timing.measure('backend_setup'):
        if not _backend_input_policy(execution):
            return _compiled_inputs(execution,run),_edge_inputs(execution,run)
        roles={'environment'}
        if _compiled_policy(execution) is not None:roles.update(execution['compiled_normalization_inputs'].values())
        if _edge_policy(execution) is not None:roles.update(execution['compiled_edge_inputs'].values())
        names=tuple(sorted(roles))
        require(all(name in run.admission.inputs for name in names),'backend bundle role not admitted')
        registered=run.read_inputs(names,max_each_bytes=2*1024**2,max_total_bytes=4*1024**2)
        require(type(registered) is dict and set(registered)==roles and all(type(body) is bytes for body in registered.values()),'backend bundle exact immutable role bodies required')
        phase_timing.add_bytes('backend_setup',sum(len(body) for body in registered.values()))
        return _compiled_inputs(execution,run,registered=registered),_edge_inputs(execution,run,registered=registered)


def _modules(root, admission=None, *, grouped=False, geometry=False, binding_timing=False, compiled=False, edge=False, numeric=False, continuation=False):
    import importlib
    result={name:importlib.import_module(PACKAGE+'.'+module) for name,module in MODULES.items()}
    # ONE packaged journal class is shared with the exact typed semantics helper.
    if admission is not None:
        names=tuple(MODULES.values())+('matching_immutable_session','compact_mcm_batched','registered_offload','batched_offload_semantics','typed_payload_policy','typed_payload_operations','adaptive_edge_policy','phase_timing')
        if grouped:names+=('grouped_offload','grouped_offload_semantics')
        if geometry:names+=('geometry_summary','geometry_publication')
        if binding_timing:names+=('matching_owner','compact_owner','imported_authority_lease')
        if compiled:names+=('compiled_normalization_policy','compiled_small_lse','matching_annealing','matching_checkpoint')
        if edge:names+=('compiled_edge_owner','edge_chunk_adapter','compiled_normalization_policy','matching_annealing','matching_checkpoint')
        if numeric:names+=('matching_numeric_policy','matching_numeric_kernel','matching_annealing','matching_checkpoint')
        if continuation:names+=('batched_continuation',)
        for name in names:
            module=importlib.import_module(PACKAGE+'.'+name)
            relative='tradingagents/research/onchain_replication/'+name+'.py'
            require(Path(module.__file__).resolve()==root/relative and admission.experiment['source_files'].get(relative)==file_hash(root/relative),'batched installed source not registered/current')
    return result


def _continuation_contract(target,start,policy,descriptor):
    """Stable scientific identity and separately reviewed current execution pins."""
    owner=target.owner;ad=owner.bound._run.admission;p=thaw(owner.policy)
    extraction=thaw(target.dictionary.config)
    extraction['maximum_neighborhood_nodes']=policy['numeric']['extraction_limit']
    scientific={'graph_hash':start['graph_hash'],'node_order_hash':start['scope']['node_order'],
        'dictionary_sha256':target.dictionary.identity,'ordered_motifs_sha256':start['scope']['ordered_motifs'],
        'matching':target.dictionary.matching_config_hash,'extraction':extraction,
        'schedule':p['schedule'],'execution_matching':compact_policy.effective_matching(thaw(owner.matching),p['pair']),
        'precision':{'internal':'float64','output':'float32','atol':1e-8,'rtol':1e-6}}
    return {'source_sha256':cache_key(ad.experiment['source_files']),
        'config_sha256':cache_key({'mcm':policy,'owner':p,'matching':thaw(owner.matching)}),
        'dictionary_sha256':target.dictionary.identity,'graph_hash':start['graph_hash'],
        'node_order_hash':start['scope']['node_order'],'descriptor_sha256':io._hash(io._json(descriptor)),
        'workflow_identity':start['scope']['workflow'],'cells':start['cells'],
        'batch_cells':policy['batched']['batch_cells'],'numerical_contract_sha256':io._hash(io._json(scientific))}


@contextmanager
def _reader(root, binding, modules):
    """Read-only handle using journal03 validators; creates no journal/authority."""
    class Reader:
        _root = modules['journal'].BatchJournal._root
        _read = modules['journal'].BatchJournal._read
        read_complete = modules['journal'].BatchJournal._read_complete
    r = Reader(); r.root = root; r.pin = tuple(binding['journal_inode'])
    r.batch_cells = binding['batch_cells']; r.max_cells = binding['cells']; r.max_body = binding['max_body_bytes']
    r.fd = os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:r._root();yield r;r._root()
    finally:io._release(lambda:os.close(r.fd))


def _checkpoint_inventory(root, *, max_entries=65536):
    """Typed complete tree, including empty dirs; bounded opaque-body hashing."""
    with phase_timing.measure('checkpoint_inventory'):
        require(root.is_dir() and root.resolve()==root,'inventory root redirected')
        digest=hashlib.sha256();files=total=directories=entries=0
        def visit(path):
            nonlocal files,total,directories,entries
            entries+=1;require(entries<=max_entries,'inventory entry ceiling exceeded')
            st=path.lstat();relative=str(path.relative_to(root))
            require(not stat.S_ISLNK(st.st_mode),'inventory symlink refused')
            row={'name':relative,'identity':list(io._signature(st))}
            if stat.S_ISDIR(st.st_mode):
                row['type']='directory';directories+=1;digest.update(io._json(row))
                with os.scandir(path) as scan:
                    names=[]
                    for entry in scan:
                        require(len(names)<min(max_entries,400000) and len(entry.name)<=128,'directory entry/name ceiling exceeded');names.append(entry.name)
                for name in sorted(names):visit(path/name)
            else:
                require(stat.S_ISREG(st.st_mode) and st.st_nlink==1,'inventory special/link refused')
                body_hash=hashlib.sha256();child=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
                try:stream=os.fdopen(child,'rb')
                except BaseException as primary:
                    try:os.close(child)
                    except BaseException as failure:primary.add_note('Inventory acquisition cleanup failed: '+repr(failure))
                    raise
                with stream:
                    require(io._signature(os.fstat(stream.fileno()))==io._signature(st),'inventory opened inode differs')
                    for block in iter(lambda:stream.read(262144),b''):body_hash.update(block)
                    require(io._signature(os.fstat(stream.fileno()))==io._signature(st),'inventory opened body changed')
                row.update(type='regular',sha256=body_hash.hexdigest());digest.update(io._json(row));files+=1;total+=st.st_size
            require(io._signature(path.lstat())==io._signature(st),'inventory changed during hash')
        visit(root)
        return {'files':files,'directories':directories,'entries':entries,'bytes':total,'sha256':digest.hexdigest()}


def _children(root, expected, *, directories=()):
    require(root.resolve()==root and root.is_dir(),'child inventory root redirected')
    expected=set(expected);directories=set(directories);require(directories<=expected,"explicit child directory roster");found=set()
    with os.scandir(root) as scan:
        for entry in scan:
            require(entry.name in expected and entry.name not in found,'unexpected batched child')
            st=entry.stat(follow_symlinks=False)
            require((stat.S_ISDIR(st.st_mode) if entry.name in directories else stat.S_ISREG(st.st_mode) and st.st_nlink==1),'batched child type differs')
            found.add(entry.name)
    require(found==expected,'missing batched child')


def _spool(root,binding, *, chunks=False):
    path=root/'stream/scores.f32';fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        st=os.fstat(fd);sig=io._signature(st)
        require(stat.S_ISREG(st.st_mode) and stat.S_IMODE(st.st_mode)==0o600 and st.st_nlink==1 and sig[:2]==tuple(binding['spool_inode']) and st.st_size==4*binding['cells'],'spool identity/extent differs')
        digest=hashlib.sha256();remaining=st.st_size
        while remaining:
            block=os.read(fd,min(4*binding['batch_cells'],remaining));require(block and len(block)%4==0,'short/misaligned spool')
            digest.update(block);remaining-=len(block)
            if chunks:yield block
        require(not os.read(fd,1) and digest.hexdigest()==binding['spool_sha256'],'spool bytes differ')
        require(sig==io._signature(os.fstat(fd))==io._signature(path.lstat()),'spool changed')
    finally:os.close(fd)


def _token_file(root, binding):
    require((root/'stream').resolve()==root/'stream','token parent redirected')
    fd = os.open(root/'stream/closure-tokens.bin',os.O_RDONLY|os.O_NOFOLLOW)
    try:
        s = os.fstat(fd)
        require(stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==0o600 and io._signature(s)[:2] == tuple(binding['token_inode']) and s.st_size == binding['batches']*168 and s.st_nlink == 1, 'closure token inode/extent differs')
        return fd, io._signature(s)
    except BaseException:
        os.close(fd);raise


def _tokens(root, binding, modules, records=False):
    fd, sig = _token_file(root,binding); digest = hashlib.sha256()
    try:
        with _reader(root/'matching',binding,modules) as journal:
            for index in range(binding['batches']):
                token = os.read(fd,168);require(len(token)==168,'short closure token');digest.update(token)
                modules['driver']._rejoin(journal,index,token,(str(journal.root),journal.pin))
                if records:yield journal.read_complete(index)
            require(not os.read(fd,1) and digest.hexdigest()==binding['tokens_sha256'],'closure token digest differs')
        require(io._signature(os.fstat(fd)) == sig == io._signature((root/'stream/closure-tokens.bin').lstat()), 'closure tokens changed')
    finally:io._release(lambda:os.close(fd))


def _prefix_names(root,binding):
    if 'continuation_contract' not in binding:return ()
    names=[]
    for index in range(binding['batches']):
        regular=f'{index:08d}.prefix.json';legacy=f'{index:08d}.legacy-prefix-counter.json'
        first=os.path.lexists(root/'matching'/regular);second=os.path.lexists(root/'matching'/legacy)
        require(first!=second,'exactly one durable prefix body required')
        names.append(regular if first else legacy)
    return tuple(names)


def _prefix_inventory(root,binding,modules):
    """Join retained controls to original score tokens and actual numeric bodies."""
    names=_prefix_names(root,binding);digest=hashlib.sha256();total=legacy=0
    token_fd=origin_fd=summary_fd=None;primary=None
    try:
        token_fd,token_sig=_token_file(root,binding)
        origin_fd=os.open(root/'stream/numeric-origins.bin',os.O_RDONLY|os.O_NOFOLLOW)
        numeric_signature=modules['numeric_execution'].sig
        origin_sig=numeric_signature(os.fstat(origin_fd))
        require(list(origin_sig)==binding['numeric_execution']['origin_signature'],'prefix origin signature differs')
        summary_fd=os.open(root/'stream/numeric-batches',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        summary_sig=numeric_signature(os.fstat(summary_fd))
        require(list(summary_sig)==binding['numeric_execution']['batches_signature'],
                'prefix numeric directory signature differs')
        with _reader(root/'matching',binding,modules) as journal:
            for index,name in enumerate(names):
                raw,pin=journal._read(name);value=json.loads(raw)
                require(io._json(value)==raw,'canonical prefix control required')
                token=os.read(token_fd,168);require(len(token)==168,'short prefix score tokens')
                hashes=[modules['driver'].TOKEN.unpack_from(token,offset*56)[3].hex() for offset in range(3)]
                summary,_=modules['numeric_execution'].read_file(summary_fd,f'{index:012d}.json',8192)
                counters=json.loads(summary);start=index*binding['batch_cells'];stop=min(binding['cells'],start+binding['batch_cells'])
                origins=os.pread(origin_fd,9*(stop-start),9*start)
                old=name.endswith('.legacy-prefix-counter.json');legacy+=old
                require(value['policy']==('legacy-recovered-prefix-v1' if old else 'completed-prefix-v1')
                    and value['batch']==index and value['start']==start and value['stop']==stop
                    and value['contract_sha256']==binding['continuation_contract']['numerical_contract_sha256']
                    and value['score_sha256']==hashes and value['summary_sha256']==io._hash(summary)
                    and value['origin_sha256']==io._hash(origins)==counters['origin_sha256']
                    and value['counters']==counters['counters'],'prefix score/numeric/contract join differs')
                journal._read(name,raw,pin=pin)
                digest.update(io._json({'name':name,'sha256':io._hash(raw),'inode':list(pin),'bytes':len(raw)}));total+=len(raw)
        require(token_sig==io._signature(os.fstat(token_fd))==io._signature((root/'stream/closure-tokens.bin').lstat())
            and not os.read(token_fd,1),'prefix tokens changed')
        require(origin_sig==numeric_signature(os.fstat(origin_fd))==numeric_signature((root/'stream/numeric-origins.bin').lstat()),'prefix origins changed')
        require(summary_sig==numeric_signature(os.fstat(summary_fd))==numeric_signature((root/'stream/numeric-batches').lstat()),
                'prefix numeric directory changed')
        return {'files':len(names),'bytes':total,'sha256':digest.hexdigest(),'legacy_counter_files':legacy}
    except BaseException as error:primary=error;raise
    finally:
        failure=None
        for descriptor in (token_fd,origin_fd,summary_fd):
            if descriptor is not None:
                try:os.close(descriptor)
                except BaseException as error:
                    if primary is not None:primary.add_note('prefix descriptor cleanup: '+type(error).__name__)
                    elif failure is None:failure=error
                    else:failure.add_note('prefix descriptor cleanup: '+type(error).__name__)
        if primary is None and failure is not None:raise failure


def verify_content(root, contract, reference, modules=None):
    require(contract.get('batched',{}).get('format') == FORMAT, 'explicit batched closure required')
    root = Path(root);path,fd=io._open(root)
    try:
        require(io._signature(os.fstat(fd))[:2] == tuple(contract['batched']['stage_inode']), 'batched stage inode differs')
        raw=io._read(fd,'stage-complete.json',io.META_LIMIT)
        require(io._hash(raw)==reference and json.loads(raw)==contract,'batched stage contract differs')
        owners.entries(root,{'intent.json','matching','checkpoints','stream','stage-complete.json'},required={'intent.json','matching','checkpoints','stream','stage-complete.json'})
        binding=contract['batched']
        require(type(binding['rows']) is int and binding['rows']>0 and 0<binding['batch_cells']<=4096 and binding['batches']==(binding['cells']+binding['batch_cells']-1)//binding['batch_cells'] and binding['batches']*168<=64*1024**2,'batched closure bounds differ')
        require(_checkpoint_inventory(root/'checkpoints')==binding['checkpoint_inventory'] and binding['checkpoint_inventory']['bytes']<=binding['checkpoint_reserved_bytes'],'retained checkpoint body changed')
        require(binding['cells']==contract['pairs']==binding['rows']*32,'full MCM closure denominator differs')
        modules = modules or _modules(producer.ROOT)
        for child,signature in binding['child_directories'].items():
            require(child in ('matching','stream') and stat.S_ISDIR((root/child).lstat().st_mode) and list(io._signature((root/child).lstat()))==signature,'batched child directory identity differs')
        require(set(binding['child_directories'])=={'matching','stream'},'child directory roster differs')
        require(io._signature((root/'matching').lstat())[:2]==tuple(binding['journal_inode']),'matching root inode differs')
        _children(root/'stream',{'closure-tokens.bin','scores.f32','numeric-origins.bin','numeric-batches'},directories={'numeric-batches'})
        require(compiled_normalization_policy.freeze(binding.get('compiled_normalization_policy'))==compiled_normalization_policy.freeze(binding['numeric_execution'].get('compiled_normalization_policy')),'batched/numeric normalization selection differs')
        require(compiled_edge_owner.freeze(binding.get('compiled_edge_policy'))==compiled_edge_owner.freeze(binding['numeric_execution'].get('compiled_edge_policy')),'batched/numeric edge selection differs')
        require(matching_numeric_policy.freeze(binding.get('numeric_kernel_policy'))==matching_numeric_policy.freeze(binding['numeric_execution'].get('numeric_kernel_policy')),'batched/numeric kernel selection differs')
        numeric=modules['numeric_execution'].verify(root/'stream',binding['numeric_execution'])
        require(numeric['cells']==binding['cells'] and binding['numeric_execution']['batch_cells']==binding['batch_cells'],'numeric occurrence/full MCM denominator differs')
        if binding['retention']=='local-v2':
            _children(root/'matching',tuple(f'{i:08d}'+suffix for i in range(binding['batches']) for suffix in modules['driver'].SUFFIXES)+_prefix_names(root,binding))
            for _ in _tokens(root,binding,modules):pass
        elif binding['retention']=='typed-grouped-recover-before-retire-v1':
            _verify_grouped(root,contract,binding)
        else:
            require(binding['retention']=='typed-recover-before-retire-v2','retention schema differs')
            _children(root/'matching',_prefix_names(root,binding))
            external=binding['external']
            require(external['coverage']['owner']==contract['owner'] and external['coverage']['cells']==contract['pairs'] and external['coverage']['batches']==binding['batches'],'external owner/full coverage differs')
            from . import registered_offload as offload
            work=Path(external['directory'])
            require(_checkpoint_inventory(work,max_entries=external['max_entries'])==external['inventory'],'anchored external metadata changed')
            require(json.loads(offload.typed._read(work/'final/accepted-coverage.json'))==external['coverage'],'actual final recovery receipt differs')
            # Original token file is preserved although source files retired.
            token_fd,token_sig=_token_file(root,binding)
            try:
                digest=hashlib.sha256();aggregate=hashlib.sha256();cursor=0
                for i in range(binding['batches']):
                    token=os.read(token_fd,168);require(len(token)==168,'short original tokens');digest.update(token)
                    encoded=offload.typed._read(work/f'preserve/{i:08d}/offload.json');record=json.loads(encoded)
                    require(record['binding']['source_tokens']==token.hex() and record['batch']==i and record['start']==cursor and record['binding']['root']==str(root/'matching') and record['binding']['root_pin']==binding['journal_inode'],'anchored original source tokens differ')
                    parts=list(offload.typed.iter_history_parts(record['history'],binding=record['binding'],kind=offload.KIND))
                    require(len(parts)==1 and parts[0]['receipt']==record['receipt'],'original typed transport history differs')
                    fresh_raw=offload.typed._read(work/f'final/{i:08d}/complete.json');fresh=json.loads(fresh_raw)
                    require(fresh['original_history']==record['history'] and fresh['source_binding']==record['binding'] and fresh['start']==cursor and fresh['stop']==record['stop'],'fresh recovery history join differs')
                    complete=offload.typed.check_history(fresh['history'],binding=record['binding'],kind=offload.KIND)
                    require(complete['parts']==0 and complete['recovered_bytes']==record['manifest']['archive_bytes'],'actual fresh recovered byte denominator differs')
                    for _ in offload.typed.iter_history_parts(fresh['history'],binding=record['binding'],kind=offload.KIND):pass
                    aggregate.update(hashlib.sha256(encoded).digest());aggregate.update(hashlib.sha256(fresh_raw).digest());cursor=record['stop']
                require(cursor==binding['cells'] and aggregate.hexdigest()==external['coverage']['original_and_fresh_history_aggregate_sha256'],'external aggregate/full denominator differs')
                require(digest.hexdigest()==binding['tokens_sha256'] and token_sig==io._signature(os.fstat(token_fd))==io._signature((root/'stream/closure-tokens.bin').lstat()),'original tokens changed')
            finally:os.close(token_fd)
        if 'continuation_contract' in binding:
            require(_prefix_inventory(root,binding,modules)==binding['prefix_inventory'],'retained prefix controls changed')
        for _ in _spool(root,binding):pass
        io._root(path,fd)
        return {'completed_pairs':contract['pairs'],'rows':binding['rows'],'motifs':32,'scope':binding['scientific_scope'],'chunk_cells':binding['batch_cells']}
    finally:io._release(lambda:os.close(fd))


def _verify_grouped(root,contract,binding):
    from . import grouped_offload as offload
    _children(root/'matching',_prefix_names(root,binding))
    external=binding['external'];coverage=external['coverage'];work=Path(external['directory'])
    groups=(binding['batches']+15)//16
    require(external['group_batches']==16 and coverage['format']=='registered-grouped-final-coverage-v1' and coverage['groups']==groups and coverage['owner']==contract['owner'] and coverage['stage']==root.name and coverage['cells']==binding['cells'] and coverage['batches']==binding['batches'],'grouped owner/full coverage differs')
    anchors_hash=hashlib.sha256()
    require(_checkpoint_inventory(work,max_entries=external['max_entries'])==external['inventory'],'anchored group inventory changed')
    require(json.loads(offload.typed._read(work/'final/accepted-coverage.json'))==coverage,'actual grouped final receipt differs')
    fd,sig=_token_file(root,binding)
    try:
        digest=hashlib.sha256();aggregate=hashlib.sha256();cursor=batch=0
        for group in range(groups):
            encoded=offload.typed._read(work/f'preserve/{group:08d}/offload.json');record=json.loads(encoded)
            anchors_hash.update(hashlib.sha256(encoded).digest())
            items=offload.semantic.from_binding(record['binding']);count=min(16,binding['batches']-batch)
            require(len(items)==count and record['format']=='registered-grouped-offload-v1' and record['first_batch']==batch and record['batches']==count and record['start']==cursor and record['stop']==min(binding['cells'],(batch+count)*binding['batch_cells']) and record['cells']==record['stop']-cursor and record['retired_files']==3*count,'group partition/range differs')
            require(record['binding']['root']==str(root/'matching') and record['binding']['root_pin']==binding['journal_inode'] and record['binding']['manifest_sha256']==offload.semantic.sha(offload.semantic.raw(record['manifest'])),'group source binding differs')
            for index,expected in items:
                token=os.read(fd,168);require(index==batch and len(token)==168 and token==expected,'original grouped token differs');digest.update(token);batch+=1
            parts=list(offload.typed.iter_history_parts(record['history'],binding=record['binding'],kind=offload.KIND))
            require(len(parts)==1 and parts[0]['receipt']==record['receipt'],'actual grouped preservation history differs')
            fresh_raw=offload.typed._read(work/f'final/{group:08d}/complete.json');fresh=json.loads(fresh_raw)
            require(fresh['format']=='registered-grouped-fresh-recovery-v1' and fresh['original_history']==record['history'] and fresh['source_binding']==record['binding'] and fresh['start']==cursor and fresh['stop']==record['stop'] and fresh['first_batch']==record['first_batch'] and fresh['batches']==count,'actual grouped recovery join differs')
            complete=offload.typed.check_history(fresh['history'],binding=record['binding'],kind=offload.KIND)
            require(complete['parts']==0 and complete['recovered_bytes']==record['manifest']['archive_bytes'],'fresh group recovered byte denominator differs')
            for _ in offload.typed.iter_history_parts(fresh['history'],binding=record['binding'],kind=offload.KIND):pass
            aggregate.update(hashlib.sha256(encoded).digest());aggregate.update(hashlib.sha256(fresh_raw).digest());cursor=record['stop']
        require(anchors_hash.hexdigest()==external['group_anchors_sha256'] and batch==binding['batches'] and cursor==binding['cells'] and not os.read(fd,1) and digest.hexdigest()==binding['tokens_sha256'] and aggregate.hexdigest()==coverage['original_and_fresh_history_aggregate_sha256'],'group full original denominator differs')
        require(sig==io._signature(os.fstat(fd))==io._signature((root/'stream/closure-tokens.bin').lstat()),'original group tokens changed')
        require(_checkpoint_inventory(work,max_entries=external['max_entries'])==external['inventory'],'group inventory changed during join')
    finally:io._release(lambda:os.close(fd))


def stage_content(stage):
    require(type(stage) is owners.Stage and stage.closed and stage.owner.stages.get(stage.name) is stage, 'actual closed batched stage required')
    stage.integrity();contract=thaw(stage.contract)
    require(contract['owner']==stage.owner.identity and contract['scope']==thaw(stage.scope) and contract['policy']==thaw(stage.owner.policy) and contract['pairs']==stage.pairs and contract['kind']==stage.kind=='mcm','batched owner contract differs')
    binding=contract['batched']
    require(binding['scientific_scope']['graph']==stage.name[4:] and binding['scientific_scope']['workflow']==stage.scope['workflow'],'batched stage scientific scope differs')
    info=stage.owner.bound._run.admission.inputs[binding['mcm_policy_input']]
    require(info['sha256']==binding['mcm_policy_sha256'],'batched policy admission pin differs')
    if 'compiled_normalization_policy' in binding:
        policy=json.loads(stage.owner.bound._run.read_input(binding['mcm_policy_input']))
        execution=validate(policy,binding['cells'])['execution']
        require(_compiled_inputs(execution,stage.owner.bound._run)==compiled_normalization_policy.freeze(binding['compiled_normalization_policy']),'closed normalization policy differs from admitted input')
    if 'compiled_edge_policy' in binding:
        policy=json.loads(stage.owner.bound._run.read_input(binding['mcm_policy_input']))
        execution=validate(policy,binding['cells'])['execution']
        require(_edge_inputs(execution,stage.owner.bound._run)==compiled_edge_owner.freeze(binding['compiled_edge_policy']),'closed edge policy differs from admitted input')
    return verify_content(stage.root,contract,stage.reference)


def output_source(args):
    require('storage_policy' not in args,'batched external archive route not implemented/admitted')
    result=verify_content(args['stage_root'],args['contract'],args['stage_sha256'])
    require(result['scope']==args['expected_scope'] and 4*result['completed_pairs']+io.META_LIMIT<=args['max_output_bytes'],'batched output scope/allowance differs')
    return {k:result[k] for k in ('rows','motifs','scope','chunk_cells')}


def output_chunks(args, start):
    binding=args['contract']['batched']
    yield from _spool(Path(args['stage_root']),binding,chunks=True)


def _compute(target, stage, graph, policy, start, modules, boundary, progress=None):
    """Shared functional core; genuine authority supplied only by produce()."""
    b=validate(policy,start['cells']);p=thaw(target.owner.policy)
    authority_poll=target.lease if policy['schema_version']==6 and getattr(target.execution,'_sampled_authority_lease',None) is not None else None
    timing=b['execution'].get('binding_timing')
    if timing is not None:
        require(authority_poll is not None,'binding timing requires selected genuine sampled lease')
        target.owner.select_binding_timing(timing)
    checkpoints=stage.root/'checkpoints';checkpoints.mkdir();stream=stage.root/'stream';stream.mkdir()
    checkpoint_bytes=0;pair_ordinal=0;checkpoint_count=0
    checkpoint_inventory=_checkpoint_inventory(checkpoints)
    def checkpoint(purpose,ordinal,state,a,m,config,pair_policy):
        with phase_timing.measure('checkpoint'):
            nonlocal checkpoint_bytes,checkpoint_count,checkpoint_inventory
            boundary()
            require(_checkpoint_inventory(checkpoints)==checkpoint_inventory,'prior checkpoint changed')
            allowance=pair_policy['max_checkpoint_bytes']+2*io.META_LIMIT
            require(checkpoint_bytes+allowance<=b['max_checkpoint_bytes'],'batched checkpoint retention exhausted')
            checkpoint_bytes+=allowance
            current_ordinal=executor.ordinal if 'continuation' in b else pair_ordinal
            path=checkpoints/f'pair-{current_ordinal:012d}-checkpoint-{ordinal:08d}'
            reference=engine.save(state,path,a,m,config,max_checkpoint_bytes=pair_policy['max_checkpoint_bytes'],**({'checkpoint_layout':pair_policy['checkpoint_layout']} if 'checkpoint_layout' in pair_policy else {}))
            require(file_hash(path/'manifest.json')==reference,'actual checkpoint manifest readback differs')
            meta={'schema_version':1,'purpose_sha256':purpose,'pair_ordinal':current_ordinal,'checkpoint_ordinal':ordinal,'manifest_sha256':reference,'resumable':False}
            q,fd=io._open(checkpoints)
            try:io._write(fd,path.name+'.json',io._json(meta))
            finally:io._release(lambda:os.close(fd))
            checkpoint_count+=1;checkpoint_inventory=_checkpoint_inventory(checkpoints)
            require(checkpoint_inventory['bytes']<=checkpoint_bytes,'actual checkpoint bytes exceed reservation')
            boundary();require(_checkpoint_inventory(checkpoints)==checkpoint_inventory,'checkpoint changed at boundary')
    executor=None
    def execute(a,m,purpose):
        nonlocal pair_ordinal
        result=executor(a,m,purpose);pair_ordinal+=1;return result
    journal=None; fd=None; spool_fd=None; primary=None
    try:
        journal=modules['journal'].BatchJournal(stage.root/'matching',batch_cells=b['batch_cells'],max_cells=start['cells'],max_bytes=b['max_journal_bytes'],max_body_bytes=b['max_body_bytes'],boundary=boundary)
        original=(str(journal.root),tuple(journal.pin));fd=os.open(stream/'closure-tokens.bin',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        token_pin=io._signature(os.fstat(fd))[:2];token_hash=hashlib.sha256();seen=0
        spool_fd=os.open(stream/'scores.f32',os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        spool_pin=io._signature(os.fstat(spool_fd))[:2];spool_hash=hashlib.sha256()
        execution=b['execution']
        durable_scores=0
        def observe_numeric(value):
            progress.poll_batched(value,journal_cells=journal.cells,score_cells=durable_scores)
        executor=modules['numeric_execution'].NumericExecution(stream,compact_policy.effective_matching(thaw(target.owner.matching),p['pair']),compact_policy.pair_policy(p['pair']),p['schedule'],checkpoint,cells=start['cells'],batch_cells=b['batch_cells'],authority_poll=authority_poll,**{k:execution[k] for k in ('max_entries','max_retained_bytes','max_key_bytes','max_origin_bytes','max_summary_bytes')},**({'geometry':execution['geometry']} if 'geometry' in execution else {}),**({'binding_timing':execution['binding_timing'],'binding_owner':target.owner} if 'binding_timing' in execution else {}),**({'edge_cache_policy':execution['edge_cache_policy']} if 'edge_cache_policy' in execution else {}),**({'compiled_normalization_policy_value':dict(_compiled_policy(execution))} if 'compiled_normalization_policy' in execution else {}),**({'compiled_edge_policy_value':dict(_edge_policy(execution))} if 'compiled_edge_policy' in execution else {}),**({'numeric_kernel_policy':dict(_numeric_policy(execution))} if 'numeric_kernel_policy' in execution else {}),**({'progress':observe_numeric} if progress is not None else {}))
        external=None;post_batch=final_batches=None
        if b['retention']=='typed-recover-before-retire-v2':
            from . import registered_offload as offload
            offload._selected(target.owner,stage)
            work=target.owner.bound._run.admission.root/'research_artifacts/onchain_batched_offload'/target.owner.identity/stage.name
            durable_mkdir(work.parent);work.mkdir();(work/'preserve').mkdir()
            anchors=bytearray(((start['cells']+b['batch_cells']-1)//b['batch_cells'])*32)
            def post_batch(j,batch,token,original):
                boundary();require(type(j) is modules['journal'].BatchJournal,'shared actual journal class differs')
                record=offload.preserve_and_retire(target.owner,stage,journal=j,batch=batch,tokens=token,work=work/f'preserve/{batch:08d}')
                encoded=offload.typed._read(work/f'preserve/{batch:08d}/offload.json')
                require(json.loads(encoded)==record,'actual offload receipt differs')
                anchors[batch*32:(batch+1)*32]=hashlib.sha256(encoded).digest()
                boundary()
            def consume(batch,rows):
                with np.errstate(over='raise',invalid='raise'):
                    expected=np.asarray([row[2] for row in rows],dtype='<f8').astype('<f4').tobytes()
                require(os.pread(spool_fd,len(expected),4*rows[0][0])==expected,'fresh recovered f64/cast differs from original spool')
            def final_batches(j,tokens,batch_count,original):
                nonlocal external
                boundary();os.fsync(spool_fd)
                records=((work/f'preserve/{i:08d}/offload.json',bytes(anchors[i*32:(i+1)*32]).hex()) for i in range(batch_count))
                coverage=offload.finalize(target.owner,stage,records=records,batch_count=batch_count,journal=j,work=work/'final',consume=consume)
                inventory=_checkpoint_inventory(work,max_entries=b['max_offload_entries'])
                require(inventory['bytes']<=b['max_offload_metadata_bytes'],'offload retained metadata allowance exceeded')
                external={'directory':str(work),'coverage':coverage,'inventory':inventory,'max_entries':b['max_offload_entries']}
                boundary();require(_checkpoint_inventory(work,max_entries=b['max_offload_entries'])==inventory,'external closure changed after final boundary')
        elif b['retention']=='typed-grouped-recover-before-retire-v1':
            from . import grouped_offload as grouped_offload
            grouped_offload.original._selected(target.owner,stage)
            work=target.owner.bound._run.admission.root/'research_artifacts/onchain_batched_offload'/target.owner.identity/stage.name
            durable_mkdir(work.parent);work.mkdir();(work/'preserve').mkdir()
            batch_total=(start['cells']+b['batch_cells']-1)//b['batch_cells']
            group_total=(batch_total+15)//16
            anchors=bytearray(group_total*32);pending=[];groups=0;next_batch=0
            def flush_group(j):
                nonlocal groups
                require(0<len(pending)<=16 and groups<group_total,'finite group flush required')
                items=tuple(pending)
                record=grouped_offload.preserve_and_retire(target.owner,stage,journal=j,items=items,work=work/f'preserve/{groups:08d}',target=target)
                encoded=grouped_offload.typed._read(work/f'preserve/{groups:08d}/offload.json')
                require(json.loads(encoded)==record,'actual grouped receipt differs')
                anchors[groups*32:(groups+1)*32]=hashlib.sha256(encoded).digest()
                groups+=1;pending.clear()
            def post_batch(j,batch,token,original):
                nonlocal next_batch
                boundary();require(type(j) is modules['journal'].BatchJournal,'shared actual journal class differs')
                require(type(batch) is int and batch==next_batch<batch_total and type(token) is bytes and len(token)==168,'ordered grouped batch/token differs')
                pending.append((batch,token));next_batch+=1
                if len(pending)==16:flush_group(j)
                boundary()
            def final_batches(j,tokens,batch_count,original):
                nonlocal external
                boundary();os.fsync(spool_fd)
                require(batch_count==next_batch==batch_total,'group batch denominator differs')
                if pending:flush_group(j)
                require(groups==group_total,'group denominator differs')
                records=((work/f'preserve/{i:08d}/offload.json',bytes(anchors[i*32:(i+1)*32]).hex()) for i in range(groups))
                coverage=grouped_offload.finalize(target.owner,stage,records=records,group_count=groups,batch_count=batch_count,journal=j,work=work/'final',spool_fd=spool_fd,target=target)
                inventory=_checkpoint_inventory(work,max_entries=b['max_offload_entries'])
                require(inventory['bytes']<=b['max_offload_metadata_bytes'],'offload retained metadata allowance exceeded')
                external={'directory':str(work),'coverage':coverage,'inventory':inventory,'max_entries':b['max_offload_entries'],'group_batches':16,'group_anchors_sha256':hashlib.sha256(anchors).hexdigest()}
                boundary();require(_checkpoint_inventory(work,max_entries=b['max_offload_entries'])==inventory,'external closure changed after final boundary')
        def sink(ordinal,center,motif,payload):
            nonlocal seen
            with phase_timing.measure('publication'):
                require(ordinal==seen and ordinal==center*32+motif and 0<len(payload)<=128 and len(payload)%4==0,'ordered bounded publication sink differs')
                view=memoryview(payload)
                while view:
                    written=os.write(spool_fd,view);require(written>0,'short spool write');view=view[written:]
                spool_hash.update(payload);seen+=len(payload)//4
                require(4*seen<=b['max_spool_bytes'],'spool reservation exceeded')
                if seen==journal.cells:
                    batch=journal.batch-1;records=journal.read_complete(batch)
                    token=modules['driver']._capture(journal,batch,records,original)
                    view=memoryview(token)
                    while view:
                        n=os.write(fd,view);require(n>0,'zero token write');view=view[n:]
                    token_hash.update(token);os.fsync(fd)
        descriptor={'rows':start['rows'],'cells':start['cells'],'motifs':32,'graph_hash':start['graph_hash'],'node_order_hash':start['scope']['node_order'],'workload_sha256':start['scope']['workflow'],'purpose_schema_version':2}
        continuation=None;prefix=None;continuation_options={}
        if 'continuation' in b:
            from . import batched_continuation
            continuation=_continuation_contract(target,start,policy,descriptor)
            role=b['continuation'].get('graph_manifest_inputs',{}).get(start['graph_hash'],b['continuation']['manifest_input'])
            if role is not None:
                prefix=batched_continuation.verify_prefix(target.owner.bound._run,role,expected_contract=continuation,target=target)
            continuation_options={'completed_prefix':prefix,'numeric':executor,
                'continuation_contract_sha256':continuation['numerical_contract_sha256']}
        result=modules['driver'].drive(graph,target.dictionary,descriptor=descriptor,policy={k:policy['numeric'][k] for k in ('max_buffer_bytes','edge_chunk','extraction_limit')},journal=journal,executor=executor if continuation is not None else execute,consumer=sink,max_chunk_bytes=128,max_closure_token_bytes=b['max_closure_token_bytes'],post_batch=post_batch,final_batches=final_batches,authority_poll=authority_poll,**continuation_options)
        require(seen==result['completed_cells']==start['cells'],'batched sink coverage differs')
        numeric_binding=executor.finish()
        os.fsync(spool_fd)
        if progress is not None:
            durable_scores=seen
            observe_numeric(executor.progress_snapshot())
        require(io._signature(os.fstat(fd))[:2]==token_pin and io._signature(os.fstat(spool_fd))[:2]==spool_pin,'token/spool descriptor replaced')
    except BaseException as error:
        primary=error
        raise
    finally:
        # Attempt every acquired resource even if an earlier cleanup fails.
        # Preserve the originating exception; cleanup-only failure still refuses.
        actions=[]
        if fd is not None:actions.append(lambda:os.close(fd))
        if spool_fd is not None:actions.append(lambda:os.close(spool_fd))
        if journal is not None and not journal.closed:actions.append(journal.close)
        if executor is not None:actions.append(executor.close)
        cleanup_error=None
        for action in actions:
            try:action()
            except BaseException as failure:
                if primary is not None:primary.add_note('Batched resource cleanup failed: '+repr(failure))
                elif cleanup_error is None:cleanup_error=failure
                else:cleanup_error.add_note('Batched resource cleanup failed: '+repr(failure))
        if primary is None and cleanup_error is not None:raise cleanup_error
    binding={'child_directories':{name:list(io._signature((stage.root/name).lstat())) for name in ('matching','stream')},'numeric_execution':numeric_binding,'retention':b['retention'],'external':external,'spool_inode':list(spool_pin),'spool_sha256':spool_hash.hexdigest(),'format':FORMAT,'rows':start['rows'],'cells':start['cells'],'batch_cells':b['batch_cells'],'batches':journal.batch,'max_body_bytes':b['max_body_bytes'],'journal_inode':list(original[1]),'token_inode':list(token_pin),'tokens_sha256':token_hash.hexdigest(),'stage_inode':list(stage.inode),'scientific_scope':start['scope'],'checkpoint_inventory':checkpoint_inventory,'checkpoint_count':checkpoint_count,'checkpoint_reserved_bytes':checkpoint_bytes,'restart_permitted':False,'authority_boundaries':'entry-batch-checkpoint-final'}
    if continuation is not None:
        binding['continuation_contract']=continuation
        binding['prefix_inventory']=_prefix_inventory(stage.root,binding,modules)
        require(binding['prefix_inventory']['bytes']<=b['continuation']['max_commit_bytes'],'prefix commit reservation exceeded')
    return binding


def _entry_lease(target, execution):
    """Complete genuine validation between selected entry preparation phases.

    The original scheduler owns all timestamps and rejects already stale work.
    No grace period, clock assignment or previous validation is reused here.
    """
    if 'compiled_normalization_policy' not in execution:return
    if getattr(target.execution,'_sampled_authority_lease',None) is None:return
    from .imported_authority_lease import target_lease
    target_lease(target,boundary=True)


def produce(target, *, graph_hash,input_name,output_input,held,progress=None):
    from .imported_mcm_identity import Target
    require(type(target) is Target,'genuine imported Target required')
    if progress is not None:
        from .real_pilot_partial_progress import MCMProgress
        require(type(progress) is MCMProgress,'exact optional batched telemetry required')
    owner=target.owner;held.check(owner);root=None;fd=None;stage=None;mapped=None;matrix=None
    try:
        with phase_timing.measure('entry'):
            graph,kernel,policy,start=producer._prepare(target,graph_hash,input_name,output_input)
            b=validate(policy,start['cells'])
            _entry_lease(target,b['execution'])
            with phase_timing.measure('module_auth'):
                modules=_modules(owner.bound._run.admission.root,owner.bound._run.admission,grouped=policy['schema_version']==6,geometry='geometry' in b['execution'],binding_timing='binding_timing' in b['execution'],compiled='compiled_normalization_policy' in b['execution'],edge='compiled_edge_policy' in b['execution'],numeric='numeric_kernel_policy' in b['execution'],continuation='continuation' in b)
            output_policy,_=publication._output_policy(owner,output_input,start['cells'])
            require(output_policy['schema_version']==1,'batched local producer requires explicit local output policy; external route unadmitted')
            own_source='tradingagents/research/onchain_replication/compact_mcm_batched.py'
            ad=owner.bound._run.admission
            require(ad.experiment['source_files'].get(own_source)==file_hash(ad.root/own_source),'batched adapter source not installed/registered')
            _entry_lease(target,b['execution'])
            normalization,edge_selection=_backend_inputs(b['execution'],owner.bound._run)
            numeric_selection=_numeric_policy(b['execution'])
            _entry_lease(target,b['execution'])
            owner.boundary();target.check()
        _stop_after_entry(target,policy)
        root=producer.directory(target,graph_hash);durable_mkdir(root.parent);root.mkdir();root,fd=io._open(root);inode=io._signature(os.fstat(fd))[:2]
        start_sha=io._write(fd,'start.json',io._json(start))
        from . import stage_retention
        selection=stage_retention.mcm_selection(graph,target.dictionary) if 'restart_retention' in owner.policy else None
        stage=owner._begin('mcm-'+graph_hash,start['scope']['workflow'],start['cells'],None,retention_selection=selection)
        require(b['max_journal_bytes']+b['max_closure_token_bytes']+b['max_checkpoint_bytes']+b['max_spool_bytes']+b['max_offload_metadata_bytes']+b['execution']['max_origin_bytes']+b['execution']['max_summary_bytes']+4*io.META_LIMIT<=stage.reservation,'new batched retained bytes exceed genuine stage reservation')
        def boundary():
            with phase_timing.measure('authority_boundary'):
                held.check(owner);target.check();owner.boundary();stage.lease();target.final();io._root(root,fd)
                require(_compiled_policy(b['execution'])==normalization,'batched normalization selection changed')
                require(_edge_policy(b['execution'])==edge_selection,'batched edge selection changed')
                require(_numeric_policy(b['execution'])==numeric_selection,'batched numeric selection changed')
                require(io._read(fd,'start.json',io.META_LIMIT)==io._json(start),'batched producer start changed')
        if progress is not None:progress.begin(graph_hash,start['rows'],start['motifs'])
        boundary();binding=_compute(target,stage,graph,policy,start,modules,boundary,**({'progress':progress} if progress is not None else {}));boundary()
        require(compiled_normalization_policy.freeze(binding['numeric_execution'].get('compiled_normalization_policy'))==normalization,'completed numeric normalization selection differs')
        require(compiled_edge_owner.freeze(binding['numeric_execution'].get('compiled_edge_policy'))==edge_selection,'completed numeric edge selection differs')
        if normalization is not None:binding['compiled_normalization_policy']=dict(normalization)
        if edge_selection is not None:binding['compiled_edge_policy']=dict(edge_selection)
        require(matching_numeric_policy.freeze(binding['numeric_execution'].get('numeric_kernel_policy'))==numeric_selection,'completed numeric kernel selection differs')
        if numeric_selection is not None:binding['numeric_kernel_policy']=dict(numeric_selection)
        binding.update(mcm_policy_input=input_name,mcm_policy_sha256=start['policy_sha256'])
        with phase_timing.measure('publication'):
            contract={'owner':owner.identity,'scope':thaw(stage.scope),'policy':thaw(owner.policy),'kind':'mcm','pairs':start['cells'],'batched':binding}
            stage.closing=True;sr,sd=io._open(stage.root)
            try:reference=io._write(sd,'stage-complete.json',io._json(contract))
            finally:io._release(lambda:os.close(sd))
            verify_content(stage.root,contract,reference,modules);boundary()
            stage.reference=reference;stage.contract=freeze(contract);stage.closed=True;owner.active=None
            ticket=publication._publish(owner,stage,output_input=output_input,expected_scope=start['scope'])
            attempt,args,proof,lease=publication._prepare(owner,stage,output_input,start['scope'])
            artifact=Path(ticket['directory'])/'artifact';matrix_fd=os.open(artifact/'matrix.f32',os.O_RDONLY|os.O_NOFOLLOW)
            try:
                require(os.fstat(matrix_fd).st_size==4*start['cells'],'published matrix extent differs')
                mapped=mmap.mmap(matrix_fd,0,access=mmap.ACCESS_READ)
            finally:io._release(lambda:os.close(matrix_fd))
            matrix=np.ndarray((start['rows'],32),dtype='<f4',buffer=mapped)
            record=start|{'start_sha256':start_sha,'stage_sha256':reference,'stage_inode':list(stage.inode),'matrix_sha256':producer._matrix(matrix,start['rows'],32),'completed_cells':start['cells'],'completed_rows':start['rows'],'output':ticket,'output_args':args|{'stage_root':str(args['stage_root'])},'output_proof':proof}
            receipt=io._write(fd,'complete.json',io._json(record))
        result=producer.Produced(target,graph,stage,matrix,policy,start,record,root,inode,receipt);result._check();return result
    except BaseException as error:
        if fd is not None:
            try:io._write(fd,'failed.json',io._json({'schema_version':1,'status':'failed','owner':owner.identity,'error_type':type(error).__name__}))
            except BaseException as later:error.add_note('Batched failed receipt: '+repr(later))
        owner.poisoned=True
        matrix=None
        if mapped is not None:
            try:mapped.close()
            except BaseException as later:error.add_note('Batched mmap cleanup: '+repr(later))
        raise
    finally:
        if fd is not None:io._release(lambda:os.close(fd))
