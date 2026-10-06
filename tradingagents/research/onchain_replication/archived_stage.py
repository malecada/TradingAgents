"""Explicit archived-event/current-local-checkpoint-and-score content join.

Fresh read evidence is retained outside the source stage. This is not owner or
empirical admission. Checkpoints and score tails/batches still remain local.
No historical local stage contract is weakened or selected implicitly.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import sys

from . import archive_pair_reader as reader, compact_stage as local, compact_policy
from .cache import cache_key
from .provenance import freeze

io = reader.io
require = io._require
REF = struct.Struct('<Q32s')


def _close(fd, primary):
    action = lambda: io._cleanup((lambda:os.close(fd),))
    if primary is None: action()
    else: io._close_after_failure(action,primary)


def _trees(root, ref_fd, count, start_sha, policy):
    """Index each local tree against its verified event reference by ordinal."""
    path, fd = io._open(root)
    try:
        seen = logical = 0
        with os.scandir(fd) as entries:
            for entry in entries:
                seen += 1
                require(seen <= count and re.fullmatch(r'event-[0-9]{12}',entry.name),
                    'archived checkpoint inventory differs')
                event = int(entry.name[6:]); directory = path/entry.name
                meta, ref = local.read(directory,'manifest.json')
                intent,_ = local.read(directory,'intent.json',meta['intent_sha256'])
                ordinal = intent['cumulative_checkpoints']
                require(type(ordinal) is int and 1 <= ordinal <= count and
                    os.pread(ref_fd,REF.size,(ordinal-1)*REF.size) == REF.pack(event,bytes.fromhex(ref)),
                    'archived checkpoint reference/ordinal differs')
                pending = intent['pair']
                frame = (event,3,pending['ordinal'],0.,0,bytes.fromhex(pending['purpose_sha256']),
                    bytes.fromhex(pending['identity_sha256']),bytes.fromhex(ref))
                _,size = local.checkpoint(path,frame,start_sha=start_sha,policy=policy,ordinal=ordinal)
                logical += size
                require(logical <= policy['schedule']['max_total_checkpoint_bytes'],
                    'archived checkpoint logical bound exceeded')
        require(seen == count,'archived checkpoint inventory incomplete');io._root(path,fd)
        return logical
    finally:_close(fd,sys.exc_info()[1])


INTENT_FIELDS = {'schema_version','format','owner','scope','policy','kind','pairs',
    'log_terminal_sha256','stream_terminal_sha256','archive_complete_sha256',
    'archive_policy','max_stage_bytes','max_read_metadata_bytes'}


def _validate_intent(value):
    retained=type(value) is dict and value.get('schema_version')==3
    require(type(value) is dict and set(value)==INTENT_FIELDS|({'retention'} if retained else set()) and type(value['schema_version']) is int
        and value['schema_version']==(3 if retained else 2) and value['format']==('archived-retained-stage-v3' if retained else 'archived-compact-stage-v2'),
        'anchored archived stage intent schema required')
    io._identity(value['owner']);reader.events._scope(value['scope'])
    for key in ('log_terminal_sha256','archive_complete_sha256'):io._identity(value[key])
    require((value['kind']=='mcm')==(value['stream_terminal_sha256'] is not None),
        'archived stream kind differs')
    if value['stream_terminal_sha256'] is not None:io._identity(value['stream_terminal_sha256'])
    capacity=compact_policy.validate(value['policy'],kind=value['kind'],pairs=value['pairs'])
    require(('restart_retention' in value['policy'])==retained,'retention requires explicit new stage format')
    if retained:
        require(set(value['retention'])=={'selection','seal_sha256'},'retention original reader pins')
        io._identity(value['retention']['seal_sha256'])
        require(value['retention']['selection']['kind']==value['kind'],'retention selector kind differs')
    limit=value['max_read_metadata_bytes'];maximum=value['policy']['schedule']['max_total_checkpoints']
    require(type(limit) is int and 0<limit<2**63 and type(value['max_stage_bytes']) is int
        and limit+REF.size*maximum+8*io.META_LIMIT<=value['max_stage_bytes']<2**63,
        'archived stage reference/metadata allowance')
    return capacity


def _inspect(root,attempt,fd,ref_fd,ref_identity,intent,read_intent_raw,read_complete_raw,transport):
    c=json.loads(intent);capacity=_validate_intent(c)
    owner=c['owner'];scope=c['scope'];policy=c['policy'];kind=c['kind'];pairs=c['pairs']
    archive_complete_sha256=c['archive_complete_sha256'];archive_policy=c['archive_policy']
    log_terminal_sha256=c['log_terminal_sha256'];stream_terminal_sha256=c['stream_terminal_sha256']
    observed=json.loads(read_complete_raw);record=observed['replay'];count=record['progress_events']
    require(read_intent_raw==io._json({'schema_version':1,'format':'archive-pair-read-v1',
        'archive_complete_sha256':archive_complete_sha256,'owner':owner,'scope':scope,
        'archive_policy':archive_policy,'max_read_metadata_bytes':c['max_read_metadata_bytes']}),
        'archived event read intent binding differs')
    require(read_complete_raw==io._json({'schema_version':1,'archive_complete_sha256':archive_complete_sha256,
        'replay':record,'execution_admitted':False}) and type(count) is int
        and 0<=count<=policy['schedule']['max_total_checkpoints']
        and record['completed_pairs']==record['started_pairs']==pairs and record['pending'] is None,
        'archived stage matching denominator differs')
    # No external callbacks during this final source/tree/score check.
    path,sfd = io._open(root/'matching')
    try:
        source = reader._Snapshot(path,sfd,archive_complete_sha256,owner,scope,archive_policy,transport)
        require((3*source.policy['max_chunks']+8)*io.META_LIMIT <= c['max_read_metadata_bytes'],
            'archived event read metadata allowance insufficient')
        require(source.complete['terminal_sha256'] == log_terminal_sha256
            and source.start['limits'] == policy['log']
            and io._json(source.complete['replay']) == io._json(record) and scope['policy'] == cache_key({
                'pair':policy['pair'],'schedule':policy['schedule']}), 'archived scientific policy/terminal differs')
        reader._inventory(attempt/'events',{'intent.json','complete.json'},r'chunk-([0-9]{12})',source.count)
        rpath,rfd = io._open(attempt/'events')
        try:
            require(io._read(rfd,'intent.json',io.META_LIMIT) == read_intent_raw
                and io._read(rfd,'complete.json',io.META_LIMIT) == read_complete_raw,'archived read receipt changed')
            io._root(rpath,rfd)
        finally:_close(rfd,sys.exc_info()[1])
        for index in range(source.count):
            mapping,_ = source.mapping(index)
            reader._contents(attempt/'events'/reader.writer._chunk(index),reader._read_bodies(mapping))
        start_sha = source.start_sha
    finally:_close(sfd,sys.exc_info()[1])
    info = os.fstat(ref_fd)
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == REF.size*count
        and io._signature(info)[:2] == ref_identity,'archived reference identity/extent differs')
    digest = hashlib.sha256();offset = 0
    while offset < info.st_size:
        block = os.pread(ref_fd,min(65536,info.st_size-offset),offset)
        require(bool(block),'archived references truncated');digest.update(block);offset += len(block)
    require(digest.hexdigest() == record['checkpoint_references_sha256'], 'archived reference content differs')
    retention_result=None
    if 'retention' in c:
        from . import stage_retention_reader
        retention_result=stage_retention_reader.check(root/'checkpoints',policy=policy['restart_retention'],
            selection=c['retention']['selection'],expected_sha256=c['retention']['seal_sha256'],start_sha256=start_sha)
        require(retention_result['events']==record['events'] and retention_result['progress_events']==count
            and retention_result['completed_pairs']==pairs,'retention actual stage population differs')
        logical=retention_result['spent']['control_bytes']+retention_result['spent']['replay_bytes']+retention_result['spent']['input_bytes']
        # Each fixed reference must still match the original pre-event bridge.
        from . import stage_retention as retention_module
        paths=sorted((root/'checkpoints/bridges').glob('progress-*.json'))
        require(len(paths)==count,'retention progress reference population')
        for index,path in enumerate(paths):
            bridge=retention_module._read(path)
            require(os.pread(ref_fd,REF.size,index*REF.size)==REF.pack(bridge['event'],bytes.fromhex(io._hash(retention_module.store._read(path,retention_module.store.CONTROL)))),
                'retention original progress reference differs')
    else:logical = _trees(root/'checkpoints',ref_fd,count,start_sha,policy)
    stream_start = None
    if kind == 'mcm':
        scores,stream_start = local.stream(root/'stream',owner=owner,scope=scope,
            terminal=stream_terminal_sha256,policy=policy,pairs=pairs)
        require(scores == record['matching_scores_sha256'],'archived matching and score stream differ')
    require(io._signature(info) == io._signature(os.fstat(ref_fd)) == io._signature(
        os.stat('checkpoint-references.bin',dir_fd=fd,follow_symlinks=False)), 'archived reference changed during join')
    require(io._read(fd,'intent.json',io.META_LIMIT) == intent,'archived stage intent changed')
    io._root(attempt,fd)
    result={'schema_version':c['schema_version'],'format':c['format'],'kind':kind,'owner':owner,'scope':scope,
        'policy_sha256':capacity['policy_sha256'],'completed_pairs':pairs,'log_terminal_sha256':log_terminal_sha256,
        'stream_terminal_sha256':stream_terminal_sha256,'stream_start_sha256':stream_start,
        'archive_complete_sha256':archive_complete_sha256,'log_start_sha256':start_sha,
        'stage_read_intent_sha256':io._hash(intent),'event_read_intent_sha256':io._hash(read_intent_raw),
        'event_read_complete_sha256':io._hash(read_complete_raw),
        'matching_scores_sha256':record['matching_scores_sha256'],'checkpoints':count,
        'checkpoints_sha256':digest.hexdigest(),'execution_admitted':False}
    if kind=='mcm':
        complete,_=local.read(root/'stream','complete.json',stream_terminal_sha256)
        if complete.get('schema_version')==2:
            result['typed_score_recovery_sha256']=complete['typed_proof_sha256']
    result['checkpoint_reserved_logical_bytes' if retention_result is not None else 'checkpoint_logical_bytes']=logical
    if retention_result is not None:result['retention']=c['retention']|{'claim_sha256':retention_result['claim_sha256'],'spent':retention_result['spent']}
    return result



def verify(root, *, owner, scope, policy, kind, pairs, log_terminal_sha256,
           stream_terminal_sha256, archive_complete_sha256, archive_policy,
           attempt, transport, lease, max_read_metadata_bytes, max_stage_bytes,
           on_verified=None,retention=None):
    """Verify all archived events and join actual local scientific payloads."""
    root = reader.archive._path(root); attempt = reader.archive._fresh(attempt)
    policy = json.loads(io._json(policy));archive_policy = json.loads(io._json(archive_policy))
    require(not attempt.is_relative_to(root) and not root.is_relative_to(attempt),
        'archived stage attempt must be separate from source')
    io._identity(owner); scope = reader.events._scope(scope)
    for ref in (log_terminal_sha256,archive_complete_sha256):io._identity(ref)
    require(callable(lease),'archived stage live lease required')
    require(on_verified is None or callable(on_verified),'archived stage finalizer must be callable')
    capacity = compact_policy.validate(policy,kind=kind,pairs=pairs)
    require((kind == 'mcm') == (stream_terminal_sha256 is not None),'archived stream kind differs')
    if stream_terminal_sha256 is not None:io._identity(stream_terminal_sha256)
    maximum = policy['schedule']['max_total_checkpoints']
    require(type(max_read_metadata_bytes) is int and 0 < max_read_metadata_bytes < 2**63
        and type(max_stage_bytes) is int and max_read_metadata_bytes+REF.size*maximum+8*io.META_LIMIT
            <= max_stage_bytes < 2**63,'archived stage reference/metadata allowance')
    require(('restart_retention' in policy)==(retention is not None),'explicit archived retention reader selection required')
    if retention is not None:retention=json.loads(io._json(retention))
    lease()
    reader.archive._capacity(attempt.parent,archive_policy['local_free_floor_bytes'],1,max_stage_bytes)
    lease(); fd = reader.archive._claim(attempt); identity = io._signature(os.fstat(fd))[:2]
    ref_fd = None
    try:
        try:
            intent_value={'schema_version':3 if retention is not None else 2,'format':'archived-retained-stage-v3' if retention is not None else 'archived-compact-stage-v2','owner':owner,
                'scope':scope,'policy':policy,'kind':kind,'pairs':pairs,
                'log_terminal_sha256':log_terminal_sha256,'stream_terminal_sha256':stream_terminal_sha256,
                'archive_complete_sha256':archive_complete_sha256,'archive_policy':archive_policy,
                'max_stage_bytes':max_stage_bytes,'max_read_metadata_bytes':max_read_metadata_bytes}
            if retention is not None:intent_value['retention']=retention
            _validate_intent(intent_value);intent=io._json(intent_value)
            io._write(fd,'intent.json',intent)
            ref_fd = os.open('checkpoint-references.bin',os.O_CREAT|os.O_EXCL|os.O_RDWR|os.O_NOFOLLOW,0o600,dir_fd=fd)
            ref_identity = io._signature(os.fstat(ref_fd))[:2]
            count = per_pair = 0
            retention_visitor=None
            if retention is not None:
                from . import stage_retention_reader
                start,start_sha=local.read(root/'matching','start.json')
                retention_visitor=stage_retention_reader.Visitor(root/'checkpoints',policy=policy['restart_retention'],
                    selection=retention['selection'],expected_sha256=retention['seal_sha256'],start_sha256=start_sha)

            def live():
                lease();io._root(attempt,fd)
                require(not any(os.path.lexists(attempt/name) for name in ('failed.json','cleanup-failed.json')),
                    'archived stage attempt failed')

            def visit(frame):
                nonlocal count,per_pair
                if retention_visitor is not None:retention_visitor.visit(frame)
                if frame[1] == 0:per_pair = 0
                elif frame[1] == 3:
                    count += 1;per_pair += 1
                    require(count <= maximum and per_pair <= policy['schedule']['max_checkpoints'],
                        'archived checkpoint schedule exceeded')
                    start,_ = local.read(root/'matching','start.json')
                    if retention_visitor is None:
                        local.checkpoint(root/'checkpoints',frame,start_sha=io._hash(io._json(start)),
                            policy=policy,ordinal=count)
                    require(os.write(ref_fd,REF.pack(frame[0],frame[7])) == REF.size,
                        'archived checkpoint reference write incomplete')

            observed = reader.verify(root/'matching',expected_sha256=archive_complete_sha256,
                owner=owner,scope=scope,archive_policy=archive_policy,attempt=attempt/'events',
                transport=transport,lease=live,max_read_metadata_bytes=max_read_metadata_bytes,on_event=visit)
            if retention_visitor is not None:retention_visitor.finish()
            record = observed['replay'];os.fsync(ref_fd);os.fsync(fd)
            require(record['completed_pairs'] == record['started_pairs'] == pairs
                and record['progress_events'] == count and record['pending'] is None,
                'archived stage matching denominator differs')
            read_intent,_ = local.read(attempt/'events','intent.json')
            read_intent_raw = io._json(read_intent);read_complete_raw = io._json(observed)

            def inspect():
                return _inspect(root,attempt,fd,ref_fd,ref_identity,intent,
                    read_intent_raw,read_complete_raw,transport)

            live();result = inspect()
            raw = io._json(result);io._write(fd,'complete.json',raw)
            live()
            # The finalizer may close a reserved read lease. Its publication is
            # provisional until the callback-free join and cleanup below pass.
            if on_verified is not None:on_verified(freeze(result))
            require(inspect() == result,'archived stage changed after publication')
            reader.archive._inventory(fd,{'intent.json','checkpoint-references.bin','events','complete.json'})
            require(io._read(fd,'complete.json',io.META_LIMIT) == raw,'archived stage completion changed')
            return result
        finally:
            if ref_fd is not None:_close(ref_fd,sys.exc_info()[1])
    except BaseException as error:
        try:
            io._root(attempt,fd)
            if not os.path.lexists(attempt/'failed.json'):reader.archive._failed(fd,error)
        except BaseException as evidence:error.add_note('archived stage failure evidence unavailable: '+repr(evidence))
        raise
    finally:reader.consume._close_attempt(attempt,fd,identity,sys.exc_info()[1])


def check(root, *, attempt, expected_sha256, transport, lease):
    """Read-only local revalidation of a trusted earlier v2 remote observation.

    No current remote availability, owner admission, or new read allowance is
    implied. Caller supplies the trusted proof hash and current live authority.
    Legacy v1 receipts lack the required anchors and are never upgraded here.
    """
    root=reader.archive._path(root);attempt=reader.archive._path(attempt)
    require(not attempt.is_relative_to(root) and not root.is_relative_to(attempt),
        'archived stage attempt must be separate from source')
    io._identity(expected_sha256);require(callable(lease),'archived local check live lease required')
    lease();fd=ref_fd=source_fd=None
    try:
        path,fd=io._open(attempt)
        reader.archive._inventory(fd,{'intent.json','checkpoint-references.bin','events','complete.json'})
        source,source_fd=io._open(root/'matching')
        raw=io._read(fd,'complete.json',io.META_LIMIT)
        require(io._hash(raw)==expected_sha256,'archived local completion hash differs')
        result=json.loads(raw)
        require(type(result) is dict and type(result.get('schema_version')) is int
            and (result['schema_version'],result.get('format')) in ((2,'archived-compact-stage-v2'),(3,'archived-retained-stage-v3')),
            'anchored archived stage receipt required')
        intent=io._read(fd,'intent.json',io.META_LIMIT)
        require(io._hash(intent)==result.get('stage_read_intent_sha256'),'archived stage intent anchor differs')
        _validate_intent(json.loads(intent))
        event_path,event_fd=io._open(attempt/'events')
        try:
            read_intent_raw=io._read(event_fd,'intent.json',io.META_LIMIT)
            read_complete_raw=io._read(event_fd,'complete.json',io.META_LIMIT)
            io._root(event_path,event_fd)
        finally:_close(event_fd,sys.exc_info()[1])
        require(io._hash(read_intent_raw)==result.get('event_read_intent_sha256')
            and io._hash(read_complete_raw)==result.get('event_read_complete_sha256'),
            'archived event read anchors differ')
        ref_fd=os.open('checkpoint-references.bin',os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
        ref_identity=io._signature(os.fstat(ref_fd))[:2]
        def inspect():
            reader.archive._inventory(fd,{'intent.json','checkpoint-references.bin','events','complete.json'})
            got=_inspect(root,attempt,fd,ref_fd,ref_identity,intent,read_intent_raw,read_complete_raw,transport)
            require(io._json(got)==raw,'archived local scientific result differs')
            reader.archive._inventory(fd,{'intent.json','checkpoint-references.bin','events','complete.json'})
            require(io._read(fd,'complete.json',io.META_LIMIT)==raw,'archived local completion changed')
            io._root(path,fd);io._root(source,source_fd)
        inspect();lease();inspect()
        return result
    finally:
        # All independently owned handles get one close even if another fails.
        try:
            if ref_fd is not None:_close(ref_fd,sys.exc_info()[1])
        finally:
            try:
                if source_fd is not None:_close(source_fd,sys.exc_info()[1])
            finally:
                if fd is not None:_close(fd,sys.exc_info()[1])
