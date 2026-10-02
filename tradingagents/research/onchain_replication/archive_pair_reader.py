"""Cold verification of a closed archive writer through a fresh read claim.

The source namespace is read-only. Trusted completion/owner/scope/policy are
mandatory; every event is fetched and replayed. This does not admit a scientific
stage, inspect checkpoint bodies or join score streams. Caller supplies actual
guard/transport budgets and bounds cumulative read claims and retained metadata.
"""
import json
import os
import re
import sys

from . import archive_pair_writer as writer, archive_consume as consume
from . import archived_pair_log as replay

archive = writer.archive
events = writer.events
io = writer.io
require = io._require


def _object(raw):
    value = json.loads(raw)
    require(isinstance(value, dict) and io._json(value) == raw, 'canonical archive object required')
    return value


def _inventory(path, fixed, pattern, count):
    root, fd = io._open(path)
    try:
        seen = 0
        with os.scandir(fd) as entries:
            for entry in entries:
                seen += 1
                match = re.fullmatch(pattern, entry.name)
                require(seen <= len(fixed)+count and (entry.name in fixed or
                    match is not None and int(match[1]) < count), 'cold archive inventory differs')
        require(seen == len(fixed)+count, 'cold archive inventory incomplete')
        io._root(root, fd)
    finally: io._cleanup((lambda: os.close(fd),))


def _contents(path, bodies):
    root, fd = io._open(path)
    try:
        archive._inventory(fd, set(bodies))
        for name, raw in bodies.items():
            require(io._read(fd, name, io.META_LIMIT) == raw, 'cold archive retained metadata differs')
        io._root(root, fd)
    finally: io._cleanup((lambda: os.close(fd),))


def _read_bodies(mapping):
    intent = io._json({'schema_version':1, 'format':'archive-consume-v1',
        'receipt_sha256':mapping['receipt_sha256'], 'receipt':mapping['receipt']})
    verified = io._json({'schema_version':1, 'intent_sha256':io._hash(intent),
        'bytes':mapping['bytes'], 'payload_sha256':mapping['payload_sha256']})
    return {'intent.json':intent, 'verified.json':verified, 'complete.json':io._json({
        'schema_version':1, 'verified_sha256':io._hash(verified), 'owned_cache_disposed':True})}


class _Snapshot:
    """Fixed-size source context; manifest inventories are streamed, never listed."""
    def __init__(self, root, fd, expected, owner, scope, policy, transport):
        self.root = root; self.fd = fd
        self.raw = {name:io._read(fd,name,io.META_LIMIT) for name in
            ('start.json','archive-start.json','terminal.json','archive-complete.json')}
        self.start, self.astart, self.terminal, self.complete = (
            _object(self.raw[name]) for name in
            ('start.json','archive-start.json','terminal.json','archive-complete.json'))
        require(io._hash(self.raw['archive-complete.json']) == expected, 'cold archive completion hash differs')
        self.start_sha = io._hash(self.raw['start.json'])
        self.archive_sha = io._hash(self.raw['archive-start.json'])
        self.limits = events._limits(self.start.get('limits'))
        self.policy = writer._policy(policy, self.limits, transport)
        require(self.start.get('owner') == owner and self.start.get('scope') == scope,
            'cold archive owner/scope differs')
        require(self.astart == {'schema_version':1,'format':'archived-pair-writer-v1',
            'log_start_sha256':self.start_sha,'owner':owner,'policy':self.policy}, 'cold archive policy differs')
        require(set(self.complete) == {'schema_version','archive_start_sha256','terminal_sha256',
            'manifest_head_sha256','chunks','replay'} and type(self.complete['schema_version']) is int
            and self.complete['schema_version'] == 1 and self.complete['archive_start_sha256'] == self.archive_sha
            and self.complete['terminal_sha256'] == io._hash(self.raw['terminal.json']), 'cold archive completion schema/binding')
        io._identity(self.complete['manifest_head_sha256'])
        self.count = self.complete['chunks']
        require(type(self.count) is int and 0 <= self.count <= self.policy['max_chunks']
            and self.terminal.get('chunks') == self.count and self.terminal.get('status') == 'complete'
            and self.terminal.get('start_sha256') == self.start_sha, 'cold archive chunk denominator/status')
        state = self.terminal.get('state')
        require(isinstance(state,dict) and type(state.get('events')) is int
            and 0 <= state['events'] <= self.limits['max_events'], 'cold archive event denominator')
        self.events = state['events']
        require(self.count == (self.events+self.limits['chunk_events']-1)//self.limits['chunk_events'],
            'cold archive event/chunk denominator differs')
        self.check()

    def mapping(self, index):
        raw = io._read(self.fd,writer._chunk(index)+'.json',io.META_LIMIT); value = _object(raw)
        require(set(value) == {'schema_version','archive_start_sha256','log_start_sha256',
            'previous_manifest_sha256','index','event_start','event_stop','head_before','head_after',
            'payload_sha256','bytes','scope','receipt','receipt_sha256'}
            and type(value['schema_version']) is int and value['schema_version'] == 1,
            'cold archive mapping schema')
        for key in ('head_before','head_after','payload_sha256','previous_manifest_sha256'): io._identity(value[key])
        begin = index*self.limits['chunk_events']; end = min(self.events,begin+self.limits['chunk_events'])
        size = (end-begin)*events.RECORD_BYTES
        scope = writer._scope(self.start['owner'],self.start_sha,index,begin,end,
            value['head_before'],value['head_after'],value['payload_sha256'],size)
        remote = self.policy['remote_prefix']+f'-{index:012d}'
        receipt = {'schema_version':1,'format':'archive-chunk-v1','transport_identity':self.policy['transport_identity'],
            'remote':remote,'member':remote+'/payload.bin','scope':scope,'source_sha256':value['payload_sha256'],'bytes':size}
        require(value['archive_start_sha256'] == self.archive_sha and value['log_start_sha256'] == self.start_sha
            and all(type(value[k]) is int for k in ('index','event_start','event_stop','bytes'))
            and value['index'] == index and value['event_start'] == begin and value['event_stop'] == end
            and value['bytes'] == size and value['scope'] == scope and value['receipt'] == receipt
            and value['receipt_sha256'] == io._hash(io._json(receipt)), 'cold archive mapping binding differs')
        return value,io._hash(raw)

    def check(self):
        io._root(self.root,self.fd)
        for name,raw in self.raw.items():
            require(io._read(self.fd,name,io.META_LIMIT) == raw,'cold archive source changed')
        # Two numbered root members per chunk; validate each series separately.
        seen = 0
        with os.scandir(self.fd) as entries:
            for entry in entries:
                seen += 1; match = re.fullmatch(r'(?:chunk|disposed)-([0-9]{12})\.json',entry.name)
                require(seen <= 6+2*self.count and (entry.name in set(self.raw)|{'copies','reads'} or
                    match is not None and int(match[1]) < self.count),'cold archive root inventory differs')
        require(seen == 6+2*self.count,'cold archive root inventory incomplete')
        previous = self.archive_sha; head = self.start_sha
        for index in range(self.count):
            value,reference = self.mapping(index)
            require(value['previous_manifest_sha256'] == previous and value['head_before'] == head,
                'cold archive manifest chain differs')
            previous = reference; head = value['head_after']
            require(io._read(self.fd,f'disposed-{index:012d}.json',io.META_LIMIT) == io._json({
                'schema_version':1,'mapping_sha256':reference,'owned_payloads_disposed':True}),'cold archive disposition differs')
            _contents(self.root/'copies'/writer._chunk(index),
                {name:io._json(value['receipt']) for name in ('intent.json','complete.json')})
            _contents(self.root/'reads'/writer._chunk(index),_read_bodies(value))
        require(previous == self.complete['manifest_head_sha256'] and head == self.terminal.get('head'),
            'cold archive manifest terminal differs')
        for name in ('copies','reads'): _inventory(self.root/name,set(),r'chunk-([0-9]{12})',self.count)
        io._root(self.root,self.fd)


def verify(root, *, expected_sha256, owner, scope, archive_policy, attempt, transport, lease,
           max_read_metadata_bytes, on_event=None):
    """Return a fully replayed observation; never reopen or mutate source evidence."""
    io._identity(expected_sha256); io._identity(owner); scope = events._scope(scope)
    attempt = archive._fresh(attempt)
    require(callable(lease),'cold archive live lease required')
    require(on_event is None or callable(on_event),'optional event visitor must be callable')
    lease(); root, source_fd = io._open(root)
    fd = None; identity = None
    try:
        try:
            source = _Snapshot(root,source_fd,expected_sha256,owner,scope,archive_policy,transport)
            require(type(max_read_metadata_bytes) is int and
                (3*source.policy['max_chunks']+8)*io.META_LIMIT <= max_read_metadata_bytes < 2**63,
                'cold archive cumulative metadata allowance')
            require(not attempt.is_relative_to(root) and not root.is_relative_to(attempt),
                'cold read attempt must be separate from source')
            archive._capacity(attempt.parent,source.policy['local_free_floor_bytes'],1,
                source.limits['chunk_events']*events.RECORD_BYTES)
            lease(); source.check()
            fd = archive._claim(attempt); identity = io._signature(os.fstat(fd))[:2]
            intent = io._json({'schema_version':1,'format':'archive-pair-read-v1',
                'archive_complete_sha256':expected_sha256,'owner':owner,'scope':scope,
                'archive_policy':source.policy,'max_read_metadata_bytes':max_read_metadata_bytes})
            io._write(fd,'intent.json',intent)

            def live():
                lease(); io._root(root,source_fd); io._root(attempt,fd)
                require(not any(os.path.lexists(path/name) for path in (root,attempt)
                    for name in ('failed.json','cleanup-failed.json')),
                    'cold archive read failure marker')
                require(archive._transport(transport) == source.policy['transport_identity'],'cold archive endpoint changed')

            def fetch(index,extent):
                live(); mapping,_ = source.mapping(index)
                require(mapping['bytes'] == extent,'cold archive requested extent differs')
                return consume.consume(receipt_bytes=io._json(mapping['receipt']),receipt_sha256=mapping['receipt_sha256'],
                    expected_scope=mapping['scope'],attempt=attempt/writer._chunk(index),transport=transport,
                    lease=live,free_floor_bytes=source.policy['local_free_floor_bytes'])

            record = replay.verify(start_bytes=source.raw['start.json'],terminal_bytes=source.raw['terminal.json'],
                terminal_sha256=source.complete['terminal_sha256'],owner=owner,scope=scope,read_chunk=fetch,
                lease=live,on_event=on_event)
            require(record == source.complete['replay'],'cold archive replay/completion differs')
            result = {'schema_version':1,'archive_complete_sha256':expected_sha256,
                'replay':record,'execution_admitted':False}
            raw = io._json(result)

            def check(complete):
                source.check()
                _inventory(attempt,{'intent.json'}|({'complete.json'} if complete else set()),r'chunk-([0-9]{12})',source.count)
                require(io._read(fd,'intent.json',io.META_LIMIT) == intent,'cold read intent changed')
                for index in range(source.count):
                    mapping,_ = source.mapping(index)
                    _contents(attempt/writer._chunk(index),_read_bodies(mapping))
                if complete: require(io._read(fd,'complete.json',io.META_LIMIT) == raw,'cold read completion changed')
                io._root(attempt,fd)

            live(); check(False)
            io._write(fd,'complete.json',raw)
            live(); check(True)
            return result
        finally:
            primary = sys.exc_info()[1]
            close = lambda: io._cleanup((lambda:os.close(source_fd),))
            if primary is None: close()
            else: io._close_after_failure(close,primary)
    except BaseException as error:
        if fd is not None:
            try:
                io._root(attempt,fd)
                if not os.path.lexists(attempt/'failed.json'): archive._failed(fd,error)
            except BaseException as evidence: error.add_note('cold read failure evidence unavailable: '+repr(evidence))
        raise
    finally:
        if fd is not None: consume._close_attempt(attempt,fd,identity,sys.exc_info()[1])
