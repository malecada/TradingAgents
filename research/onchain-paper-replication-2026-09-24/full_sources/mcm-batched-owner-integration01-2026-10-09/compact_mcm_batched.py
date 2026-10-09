"""Explicit batched MCM closure; genuine owner boundaries, never old pair seals.

Candidate local-retention route. No registration, empirical or offload admission.
"""
import hashlib
import importlib.util
import json
import mmap
import os
import stat
from contextlib import contextmanager
from pathlib import Path
import numpy as np
from . import compact_owner as owners, compact_mcm as producer
from . import compact_mcm_publication as publication, score_batches as io
from . import matching_checkpoint as engine
from .cache import cache_key
from .provenance import freeze, thaw, durable_mkdir, file_hash

FORMAT = 'ordered-mcm-batch-closure-v1'
BASE = 'research/onchain-paper-replication-2026-09-24/full_sources/'
SOURCES = {'driver': BASE+'mcm-batched-driver03-2026-10-09/driver.py',
 'journal': BASE+'mcm-batched-execution03-2026-10-09/batch_journal.py',
 'executor': BASE+'mcm-batched-execution03-2026-10-09/pair_executor.py'}
require = io._require


def selected(policy):
    return type(policy) is dict and type(policy.get('schema_version')) is int and policy['schema_version'] == 3


def validate(policy, pairs):
    require(selected(policy) and set(policy) == {'schema_version','max_entries','max_workflow_metadata_bytes','numeric','batched'}, 'batched MCM policy schema')
    b = policy['batched']
    require(type(b) is dict and set(b) == {'format','authority_boundaries','batch_cells','max_journal_bytes','max_body_bytes','max_closure_token_bytes','max_checkpoint_bytes'}, 'batched bounds schema')
    require(b['format'] == FORMAT and b['authority_boundaries'] == 'entry-batch-checkpoint-final', 'explicit operational deviation required')
    for k in ('batch_cells','max_journal_bytes','max_body_bytes','max_closure_token_bytes','max_checkpoint_bytes'):
        require(type(b[k]) is int and 0 < b[k] < 2**63, 'positive batched allowance required')
    require(b['batch_cells'] <= 4096 and 1024 <= b['max_body_bytes'] <= 1024**2 and b['max_closure_token_bytes'] <= 64*1024**2, 'batch bounds differ')
    count = (pairs+b['batch_cells']-1)//b['batch_cells']
    require(count*168 <= b['max_closure_token_bytes'] and count*(2*b['max_body_bytes']+92)+pairs*53 <= b['max_journal_bytes'], 'full batch denominator not reserved')
    return b


def _modules(root, admission=None):
    result = {}
    for name, relative in SOURCES.items():
        path = root/relative
        if admission is not None:
            require(admission.experiment['source_files'].get(relative) == file_hash(path), 'batched source not registered/current')
        spec = importlib.util.spec_from_file_location('owned_batched_'+name,path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); result[name] = module
    return result


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


def _checkpoint_inventory(root):
    require(root.is_dir() and root.resolve()==root,'checkpoint root redirected')
    digest=hashlib.sha256();files=total=0
    paths=[]
    for path in root.rglob('*'):
        require(len(paths)<65536,'checkpoint inventory entry ceiling exceeded')
        paths.append(path)
    for path in sorted(paths):
        st=path.lstat();require(not stat.S_ISLNK(st.st_mode),'checkpoint symlink refused')
        if stat.S_ISDIR(st.st_mode):continue
        require(stat.S_ISREG(st.st_mode) and st.st_nlink==1,'checkpoint special/link refused')
        body_hash=hashlib.sha256()
        child=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
        with os.fdopen(child,'rb') as stream:
            require(io._signature(os.fstat(stream.fileno()))==io._signature(st),'checkpoint opened inode differs')
            for block in iter(lambda:stream.read(262144),b''):body_hash.update(block)
            require(io._signature(os.fstat(stream.fileno()))==io._signature(st),'checkpoint opened body changed')
        require(io._signature(path.lstat())==io._signature(st),'checkpoint changed during hash')
        digest.update(io._json({'name':str(path.relative_to(root)),'identity':list(io._signature(st)),'sha256':body_hash.hexdigest()}))
        files+=1;total+=st.st_size
    return {'files':files,'bytes':total,'sha256':digest.hexdigest()}


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
        for _ in _tokens(root,binding,modules):pass
        io._root(path,fd)
        return {'completed_pairs':contract['pairs'],'rows':binding['rows'],'motifs':32,'scope':binding['scientific_scope'],'chunk_cells':binding['batch_cells']}
    finally:io._release(lambda:os.close(fd))


def stage_content(stage):
    require(type(stage) is owners.Stage and stage.closed and stage.owner.stages.get(stage.name) is stage, 'actual closed batched stage required')
    stage.integrity();contract=thaw(stage.contract)
    require(contract['owner']==stage.owner.identity and contract['scope']==thaw(stage.scope) and contract['policy']==thaw(stage.owner.policy) and contract['pairs']==stage.pairs and contract['kind']==stage.kind=='mcm','batched owner contract differs')
    binding=contract['batched']
    require(binding['scientific_scope']['graph']==stage.name[4:] and binding['scientific_scope']['workflow']==stage.scope['workflow'],'batched stage scientific scope differs')
    info=stage.owner.bound._run.admission.inputs[binding['mcm_policy_input']]
    require(info['sha256']==binding['mcm_policy_sha256'],'batched policy admission pin differs')
    return verify_content(stage.root,contract,stage.reference)


def output_source(args):
    require('storage_policy' not in args,'batched external archive route not implemented/admitted')
    result=verify_content(args['stage_root'],args['contract'],args['stage_sha256'])
    require(result['scope']==args['expected_scope'] and 4*result['completed_pairs']+io.META_LIMIT<=args['max_output_bytes'],'batched output scope/allowance differs')
    return {k:result[k] for k in ('rows','motifs','scope','chunk_cells')}


def output_chunks(args, start):
    modules=_modules(producer.ROOT);binding=args['contract']['batched']
    for rows in _tokens(Path(args['stage_root']),binding,modules,records=True):
        # Same original float64 -> float32 publication expression, bounded batch.
        with np.errstate(over='raise',invalid='raise'):
            values=np.asarray([row[2] for row in rows],dtype='<f8').astype('<f4')
        require(np.isfinite(values).all(),'nonfinite batched output')
        yield values.tobytes()


def _compute(target, stage, graph, policy, start, modules, boundary):
    """Shared functional core; genuine authority supplied only by produce()."""
    b=validate(policy,start['cells']);p=thaw(target.owner.policy)
    checkpoints=stage.root/'checkpoints';checkpoints.mkdir();stream=stage.root/'stream';stream.mkdir()
    checkpoint_bytes=0;pair_ordinal=0;checkpoint_count=0
    checkpoint_inventory=_checkpoint_inventory(checkpoints)
    def checkpoint(purpose,ordinal,state,a,m,config,pair_policy):
        nonlocal checkpoint_bytes,checkpoint_count,checkpoint_inventory
        boundary()
        require(_checkpoint_inventory(checkpoints)==checkpoint_inventory,'prior checkpoint changed')
        allowance=pair_policy['max_checkpoint_bytes']+2*io.META_LIMIT
        require(checkpoint_bytes+allowance<=b['max_checkpoint_bytes'],'batched checkpoint retention exhausted')
        checkpoint_bytes+=allowance
        path=checkpoints/f'pair-{pair_ordinal:012d}-checkpoint-{ordinal:08d}'
        reference=engine.save(state,path,a,m,config,max_checkpoint_bytes=pair_policy['max_checkpoint_bytes'],**({'checkpoint_layout':pair_policy['checkpoint_layout']} if 'checkpoint_layout' in pair_policy else {}))
        require(file_hash(path/'manifest.json')==reference,'actual checkpoint manifest readback differs')
        meta={'schema_version':1,'purpose_sha256':purpose,'pair_ordinal':pair_ordinal,'checkpoint_ordinal':ordinal,'manifest_sha256':reference,'resumable':False}
        q,fd=io._open(checkpoints)
        try:io._write(fd,path.name+'.json',io._json(meta))
        finally:io._release(lambda:os.close(fd))
        checkpoint_count+=1;checkpoint_inventory=_checkpoint_inventory(checkpoints)
        require(checkpoint_inventory['bytes']<=checkpoint_bytes,'actual checkpoint bytes exceed reservation')
        boundary();require(_checkpoint_inventory(checkpoints)==checkpoint_inventory,'checkpoint changed at boundary')
    executor=modules['executor'].PairExecutor(thaw(target.owner.matching),p['pair'],p['schedule'],checkpoint)
    def execute(a,m,purpose):
        nonlocal pair_ordinal
        result=executor(a,m,purpose);pair_ordinal+=1;return result
    journal=modules['journal'].BatchJournal(stage.root/'matching',batch_cells=b['batch_cells'],max_cells=start['cells'],max_bytes=b['max_journal_bytes'],max_body_bytes=b['max_body_bytes'],boundary=boundary)
    original=(str(journal.root),tuple(journal.pin));fd=os.open(stream/'closure-tokens.bin',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    token_pin=io._signature(os.fstat(fd))[:2];token_hash=hashlib.sha256();seen=0
    def sink(ordinal,center,motif,payload):
        nonlocal seen
        require(ordinal==seen and ordinal==center*32+motif and 0<len(payload)<=128 and len(payload)%4==0,'ordered bounded publication sink differs')
        seen+=len(payload)//4
        if seen==journal.cells:
            batch=journal.batch-1;records=journal.read_complete(batch)
            token=modules['driver']._capture(journal,batch,records,original)
            view=memoryview(token)
            while view:
                n=os.write(fd,view);require(n>0,'zero token write');view=view[n:]
            token_hash.update(token);os.fsync(fd)
    descriptor={'rows':start['rows'],'cells':start['cells'],'motifs':32,'graph_hash':start['graph_hash'],'node_order_hash':start['scope']['node_order'],'workload_sha256':start['scope']['workflow'],'purpose_schema_version':2}
    try:
        result=modules['driver'].drive(graph,target.dictionary,descriptor=descriptor,policy={k:policy['numeric'][k] for k in ('max_buffer_bytes','edge_chunk','extraction_limit')},journal=journal,executor=execute,consumer=sink,max_chunk_bytes=128,max_closure_token_bytes=b['max_closure_token_bytes'])
        require(seen==result['completed_cells']==start['cells'],'batched sink coverage differs')
        require(io._signature(os.fstat(fd))[:2]==token_pin,'token descriptor replaced')
    finally:
        io._cleanup((lambda:os.close(fd),journal.close) if not journal.closed else (lambda:os.close(fd),))
    return {'format':FORMAT,'rows':start['rows'],'cells':start['cells'],'batch_cells':b['batch_cells'],'batches':journal.batch,'max_body_bytes':b['max_body_bytes'],'journal_inode':list(original[1]),'token_inode':list(token_pin),'tokens_sha256':token_hash.hexdigest(),'stage_inode':list(stage.inode),'scientific_scope':start['scope'],'checkpoint_inventory':checkpoint_inventory,'checkpoint_count':checkpoint_count,'checkpoint_reserved_bytes':checkpoint_bytes,'restart_permitted':False,'authority_boundaries':'entry-batch-checkpoint-final'}


def produce(target, *, graph_hash,input_name,output_input,held):
    from .imported_mcm_identity import Target
    require(type(target) is Target,'genuine imported Target required')
    owner=target.owner;held.check(owner);root=None;fd=None;stage=None
    try:
        graph,kernel,policy,start=producer._prepare(target,graph_hash,input_name,output_input)
        b=validate(policy,start['cells']);modules=_modules(owner.bound._run.admission.root,owner.bound._run.admission)
        output_policy,_=publication._output_policy(owner,output_input,start['cells'])
        require(output_policy['schema_version']==1,'batched local producer requires explicit local output policy; external route unadmitted')
        own_source='tradingagents/research/onchain_replication/compact_mcm_batched.py'
        ad=owner.bound._run.admission
        require(ad.experiment['source_files'].get(own_source)==file_hash(ad.root/own_source),'batched adapter source not installed/registered')
        owner.boundary();target.check()
        root=producer.directory(target,graph_hash);durable_mkdir(root.parent);root.mkdir();root,fd=io._open(root);inode=io._signature(os.fstat(fd))[:2]
        start_sha=io._write(fd,'start.json',io._json(start))
        from . import stage_retention
        selection=stage_retention.mcm_selection(graph,target.dictionary) if 'restart_retention' in owner.policy else None
        stage=owner._begin('mcm-'+graph_hash,start['scope']['workflow'],start['cells'],None,retention_selection=selection)
        require(b['max_journal_bytes']+b['max_closure_token_bytes']+b['max_checkpoint_bytes']+4*io.META_LIMIT<=stage.reservation,'new batched retained bytes exceed genuine stage reservation')
        def boundary():
            held.check(owner);target.check();owner.boundary();stage.lease();target.final();io._root(root,fd)
            require(io._read(fd,'start.json',io.META_LIMIT)==io._json(start),'batched producer start changed')
        boundary();binding=_compute(target,stage,graph,policy,start,modules,boundary);boundary()
        binding.update(mcm_policy_input=input_name,mcm_policy_sha256=start['policy_sha256'])
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
        owner.poisoned=True;raise
    finally:
        if fd is not None:io._release(lambda:os.close(fd))
