"""Explicit batched MCM closure; genuine owner boundaries, never old pair seals.

Selected local/typed-offload route. No registration or empirical admission.
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

FORMAT = 'ordered-mcm-batch-closure-v2'
PACKAGE = 'tradingagents.research.onchain_replication'
MODULES = {'driver':'batched_driver','journal':'batched_journal','executor':'batched_pair_executor'}
require = io._require


def selected(policy):
    return type(policy) is dict and type(policy.get('schema_version')) is int and policy['schema_version'] == 4


def validate(policy, pairs):
    require(selected(policy) and set(policy) == {'schema_version','max_entries','max_workflow_metadata_bytes','numeric','batched'}, 'batched MCM policy schema')
    b = policy['batched']
    require(type(b) is dict and set(b) == {'format','authority_boundaries','batch_cells','max_journal_bytes','max_body_bytes','max_closure_token_bytes','max_checkpoint_bytes','retention','max_spool_bytes','max_offload_metadata_bytes','max_offload_entries','max_offload_anchor_bytes'}, 'batched bounds schema')
    require(b['format'] == FORMAT and b['authority_boundaries'] == 'entry-batch-checkpoint-final', 'explicit operational deviation required')
    require(b['retention'] in ('local-v2','typed-recover-before-retire-v2'),'explicit batched retention route required')
    require(type(b['max_spool_bytes']) is int and 4*pairs <= b['max_spool_bytes'] < 2**63 and type(b['max_offload_metadata_bytes']) is int and 0 < b['max_offload_metadata_bytes'] < 2**63 and type(b['max_offload_entries']) is int and 0 < b['max_offload_entries'] <= 4000000,'explicit spool/metadata bounds required')
    for k in ('batch_cells','max_journal_bytes','max_body_bytes','max_closure_token_bytes','max_checkpoint_bytes'):
        require(type(b[k]) is int and 0 < b[k] < 2**63, 'positive batched allowance required')
    require(b['batch_cells'] <= 4096 and 1024 <= b['max_body_bytes'] <= 1024**2 and b['max_closure_token_bytes'] <= 64*1024**2, 'batch bounds differ')
    count = (pairs+b['batch_cells']-1)//b['batch_cells']
    require(type(b['max_offload_anchor_bytes']) is int and 0 <= b['max_offload_anchor_bytes'] <= 16*1024**2 and (b['retention']=='local-v2' or count*32<=b['max_offload_anchor_bytes']),'offload anchor memory allowance exceeded')
    require(count*168 <= b['max_closure_token_bytes'] and count*(2*b['max_body_bytes']+92)+pairs*53 <= b['max_journal_bytes'], 'full batch denominator not reserved')
    return b


def _modules(root, admission=None):
    import importlib
    result={name:importlib.import_module(PACKAGE+'.'+module) for name,module in MODULES.items()}
    # ONE packaged journal class is shared with the exact typed semantics helper.
    if admission is not None:
        names=tuple(MODULES.values())+('compact_mcm_batched','registered_offload','batched_offload_semantics','typed_payload_policy','typed_payload_operations')
        for name in names:
            module=importlib.import_module(PACKAGE+'.'+name)
            relative='tradingagents/research/onchain_replication/'+name+'.py'
            require(Path(module.__file__).resolve()==root/relative and admission.experiment['source_files'].get(relative)==file_hash(root/relative),'batched installed source not registered/current')
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


def _checkpoint_inventory(root, *, max_entries=65536):
    """Typed complete tree, including empty dirs; bounded opaque-body hashing."""
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


def _children(root, expected):
    require(root.resolve()==root and root.is_dir(),'child inventory root redirected')
    expected=set(expected);found=set()
    with os.scandir(root) as scan:
        for entry in scan:
            require(entry.name in expected and entry.name not in found,'unexpected batched child')
            st=entry.stat(follow_symlinks=False)
            require(stat.S_ISREG(st.st_mode) and st.st_nlink==1,'batched child type differs')
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
        _children(root/'stream',{'closure-tokens.bin','scores.f32'})
        if binding['retention']=='local-v2':
            _children(root/'matching',(f'{i:08d}'+suffix for i in range(binding['batches']) for suffix in modules['driver'].SUFFIXES))
            for _ in _tokens(root,binding,modules):pass
        else:
            require(binding['retention']=='typed-recover-before-retire-v2','retention schema differs')
            _children(root/'matching',())
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
        for _ in _spool(root,binding):pass
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
    binding=args['contract']['batched']
    yield from _spool(Path(args['stage_root']),binding,chunks=True)


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
    journal=None; fd=None; spool_fd=None; primary=None
    try:
        journal=modules['journal'].BatchJournal(stage.root/'matching',batch_cells=b['batch_cells'],max_cells=start['cells'],max_bytes=b['max_journal_bytes'],max_body_bytes=b['max_body_bytes'],boundary=boundary)
        original=(str(journal.root),tuple(journal.pin));fd=os.open(stream/'closure-tokens.bin',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        token_pin=io._signature(os.fstat(fd))[:2];token_hash=hashlib.sha256();seen=0
        spool_fd=os.open(stream/'scores.f32',os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        spool_pin=io._signature(os.fstat(spool_fd))[:2];spool_hash=hashlib.sha256()
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
        def sink(ordinal,center,motif,payload):
            nonlocal seen
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
        result=modules['driver'].drive(graph,target.dictionary,descriptor=descriptor,policy={k:policy['numeric'][k] for k in ('max_buffer_bytes','edge_chunk','extraction_limit')},journal=journal,executor=execute,consumer=sink,max_chunk_bytes=128,max_closure_token_bytes=b['max_closure_token_bytes'],post_batch=post_batch,final_batches=final_batches)
        require(seen==result['completed_cells']==start['cells'],'batched sink coverage differs')
        os.fsync(spool_fd)
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
        cleanup_error=None
        for action in actions:
            try:action()
            except BaseException as failure:
                if primary is not None:primary.add_note('Batched resource cleanup failed: '+repr(failure))
                elif cleanup_error is None:cleanup_error=failure
                else:cleanup_error.add_note('Batched resource cleanup failed: '+repr(failure))
        if primary is None and cleanup_error is not None:raise cleanup_error
    return {'child_directories':{name:list(io._signature((stage.root/name).lstat())) for name in ('matching','stream')},'retention':b['retention'],'external':external,'spool_inode':list(spool_pin),'spool_sha256':spool_hash.hexdigest(),'format':FORMAT,'rows':start['rows'],'cells':start['cells'],'batch_cells':b['batch_cells'],'batches':journal.batch,'max_body_bytes':b['max_body_bytes'],'journal_inode':list(original[1]),'token_inode':list(token_pin),'tokens_sha256':token_hash.hexdigest(),'stage_inode':list(stage.inode),'scientific_scope':start['scope'],'checkpoint_inventory':checkpoint_inventory,'checkpoint_count':checkpoint_count,'checkpoint_reserved_bytes':checkpoint_bytes,'restart_permitted':False,'authority_boundaries':'entry-batch-checkpoint-final'}


def produce(target, *, graph_hash,input_name,output_input,held):
    from .imported_mcm_identity import Target
    require(type(target) is Target,'genuine imported Target required')
    owner=target.owner;held.check(owner);root=None;fd=None;stage=None;mapped=None;matrix=None
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
        require(b['max_journal_bytes']+b['max_closure_token_bytes']+b['max_checkpoint_bytes']+b['max_spool_bytes']+b['max_offload_metadata_bytes']+4*io.META_LIMIT<=stage.reservation,'new batched retained bytes exceed genuine stage reservation')
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
        owner.poisoned=True
        matrix=None
        if mapped is not None:
            try:mapped.close()
            except BaseException as later:error.add_note('Batched mmap cleanup: '+repr(later))
        raise
    finally:
        if fd is not None:io._release(lambda:os.close(fd))
