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
    require(type(value) is dict and set(value)==INTENT_FIELDS and type(value['schema_version']) is int
        and value['schema_version']==2 and value['format']=='archived-compact-stage-v2',
        'anchored archived stage intent schema required')
    io._identity(value['owner']);reader.events._scope(value['scope'])
    for key in ('log_terminal_sha256','archive_complete_sha256'):io._identity(value[key])
    require((value['kind']=='mcm')==(value['stream_terminal_sha256'] is not None),
        'archived stream kind differs')
    if value['stream_terminal_sha256'] is not None:io._identity(value['stream_terminal_sha256'])
    capacity=compact_policy.validate(value['policy'],kind=value['kind'],pairs=value['pairs'])
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
    require(observed=={'schema_version':1,'archive_complete_sha256':archive_complete_sha256,
        'replay':record,'execution_admitted':False} and type(count) is int
        and 0<=count<=policy['schedule']['max_total_checkpoints']
        and record['completed_pairs']==record['started_pairs']==pairs and record['pending'] is None,
        'archived stage matching denominator differs')
    # No external callbacks during this final source/tree/score check.
    path,sfd = io._open(root/'matching')
    try:
        source = reader._Snapshot(path,sfd,archive_complete_sha256,owner,scope,archive_policy,transport)
        require(source.complete['terminal_sha256'] == log_terminal_sha256
            and source.start['limits'] == policy['log'] and source.complete['replay'] == record and scope['policy'] == cache_key({
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
    logical = _trees(root/'checkpoints',ref_fd,count,start_sha,policy)
    stream_start = None
    if kind == 'mcm':
        scores,stream_start = local.stream(root/'stream',owner=owner,scope=scope,
            terminal=stream_terminal_sha256,policy=policy,pairs=pairs)
        require(scores == record['matching_scores_sha256'],'archived matching and score stream differ')
    require(io._signature(info) == io._signature(os.fstat(ref_fd)) == io._signature(
        os.stat('checkpoint-references.bin',dir_fd=fd,follow_symlinks=False)), 'archived reference changed during join')
    require(io._read(fd,'intent.json',io.META_LIMIT) == intent,'archived stage intent changed')
    io._root(attempt,fd)
    return {'schema_version':2,'format':'archived-compact-stage-v2','kind':kind,'owner':owner,'scope':scope,
        'policy_sha256':capacity['policy_sha256'],'completed_pairs':pairs,'log_terminal_sha256':log_terminal_sha256,
        'stream_terminal_sha256':stream_terminal_sha256,'stream_start_sha256':stream_start,
        'archive_complete_sha256':archive_complete_sha256,'log_start_sha256':start_sha,
        'stage_read_intent_sha256':io._hash(intent),'event_read_intent_sha256':io._hash(read_intent_raw),
        'event_read_complete_sha256':io._hash(read_complete_raw),
        'matching_scores_sha256':record['matching_scores_sha256'],'checkpoints':count,
        'checkpoint_logical_bytes':logical,'checkpoints_sha256':digest.hexdigest(),'execution_admitted':False}



def verify(root, *, owner, scope, policy, kind, pairs, log_terminal_sha256,
           stream_terminal_sha256, archive_complete_sha256, archive_policy,
           attempt, transport, lease, max_read_metadata_bytes, max_stage_bytes,
           on_verified=None):
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
    lease()
    reader.archive._capacity(attempt.parent,archive_policy['local_free_floor_bytes'],1,max_stage_bytes)
    lease(); fd = reader.archive._claim(attempt); identity = io._signature(os.fstat(fd))[:2]
    ref_fd = None
    try:
        try:
            intent = io._json({'schema_version':2,'format':'archived-compact-stage-v2','owner':owner,
                'scope':scope,'policy':policy,'kind':kind,'pairs':pairs,
                'log_terminal_sha256':log_terminal_sha256,'stream_terminal_sha256':stream_terminal_sha256,
                'archive_complete_sha256':archive_complete_sha256,'archive_policy':archive_policy,
                'max_stage_bytes':max_stage_bytes,'max_read_metadata_bytes':max_read_metadata_bytes})
            io._write(fd,'intent.json',intent)
            ref_fd = os.open('checkpoint-references.bin',os.O_CREAT|os.O_EXCL|os.O_RDWR|os.O_NOFOLLOW,0o600,dir_fd=fd)
            ref_identity = io._signature(os.fstat(ref_fd))[:2]
            count = per_pair = 0

            def live():
                lease();io._root(attempt,fd)
                require(not any(os.path.lexists(attempt/name) for name in ('failed.json','cleanup-failed.json')),
                    'archived stage attempt failed')

            def visit(frame):
                nonlocal count,per_pair
                if frame[1] == 0:per_pair = 0
                elif frame[1] == 3:
                    count += 1;per_pair += 1
                    require(count <= maximum and per_pair <= policy['schedule']['max_checkpoints'],
                        'archived checkpoint schedule exceeded')
                    start,_ = local.read(root/'matching','start.json')
                    local.checkpoint(root/'checkpoints',frame,start_sha=io._hash(io._json(start)),
                        policy=policy,ordinal=count)
                    require(os.write(ref_fd,REF.pack(frame[0],frame[7])) == REF.size,
                        'archived checkpoint reference write incomplete')

            observed = reader.verify(root/'matching',expected_sha256=archive_complete_sha256,
                owner=owner,scope=scope,archive_policy=archive_policy,attempt=attempt/'events',
                transport=transport,lease=live,max_read_metadata_bytes=max_read_metadata_bytes,on_event=visit)
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
        path,fd=io._open(attempt);source,source_fd=io._open(root/'matching')
        raw=io._read(fd,'complete.json',io.META_LIMIT)
        require(io._hash(raw)==expected_sha256,'archived local completion hash differs')
        result=json.loads(raw)
        require(type(result) is dict and type(result.get('schema_version')) is int
            and result['schema_version']==2 and result.get('format')=='archived-compact-stage-v2',
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
            got=_inspect(root,attempt,fd,ref_fd,ref_identity,intent,read_intent_raw,read_complete_raw,transport)
            require(got==result,'archived local scientific result differs')
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
