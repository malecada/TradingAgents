"""Explicit fresh archive-backed writer; the original local PairLog is unchanged.

Only newly owned sealed chunks and their verified temporary copies are disposed.
A completion includes full archived event replay. Actual scientific stage/owner
admission, checkpoint/score joins and whole-workflow budgets remain external.
"""
import hashlib
import json
import os
import re
import sys

from . import compact_pair_log as events, archive_chunks as archive
from . import archive_consume as consume, archived_pair_log as replay

io = events.io
require = io._require


def _policy(value, limits, transport):
    require(isinstance(value, dict) and set(value) == {'schema_version', 'remote_prefix',
        'transport_identity', 'max_chunks', 'max_metadata_bytes', 'local_free_floor_bytes'},
        'archive writer policy schema')
    result = json.loads(io._json(value))
    require(type(result['schema_version']) is int and result['schema_version'] == 1
        and isinstance(result['remote_prefix'], str)
        and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,99}', result['remote_prefix'])
        and result['transport_identity'] == archive._transport(transport), 'archive writer endpoint/prefix')
    count = (limits['max_events']+limits['chunk_events']-1)//limits['chunk_events']
    require(type(result['max_chunks']) is int and result['max_chunks'] == count
        and type(result['max_metadata_bytes']) is int
        and (7*count+8)*io.META_LIMIT <= result['max_metadata_bytes'] < 2**63
        and type(result['local_free_floor_bytes']) is int
        and 10*1024**3 <= result['local_free_floor_bytes'] < 2**63, 'archive writer allowance')
    return result


def _chunk(index): return f'chunk-{index:012d}'


def _scope(owner, start, index, begin, end, before, after, digest, size):
    return io._hash(io._json({'owner': owner, 'log_start_sha256': start, 'index': index,
        'event_start': begin, 'event_stop': end, 'head_before': before, 'head_after': after,
        'payload_sha256': digest, 'bytes': size}))


class ArchivePairLog(events.PairLog):
    def __init__(self, root, *, owner, scope, limits, max_iterations, lease, transport, archive_policy):
        limits = events._limits(limits)
        policy = _policy(archive_policy, limits, transport)
        archive._capacity(archive._path(root).parent, policy['local_free_floor_bytes'],
            3, limits['chunk_events']*events.RECORD_BYTES)
        super().__init__(root, owner=owner, scope=scope, limits=limits,
            max_iterations=max_iterations, lease=lease)
        self.root_identity = io._signature(os.fstat(self.fd))[:2]
        self.policy = policy; self.transport = transport
        self.archived = 0; self.archive_state = events._empty(); self.archive_head = self.start_sha
        self.payload_digest = hashlib.sha256(); self.archived_bytes = 0
        self.archive_start = {'schema_version': 1, 'format': 'archived-pair-writer-v1',
            'log_start_sha256': self.start_sha, 'owner': owner, 'policy': policy}
        self.children = {}
        try:
            self.archive_start_sha = self.manifest_head = io._write(self.fd, 'archive-start.json', io._json(self.archive_start))
            for name in ('copies', 'reads'):
                (self.root/name).mkdir()
                self.children[name] = io._signature((self.root/name).lstat())[:2]
            os.fsync(self.fd); self._archive_check()
        except BaseException as error:
            self._abort(error); raise

    def _archive_check(self):
        self._check()
        require(io._hash(io._json(self.start)) == self.start_sha
            and io._hash(io._read(self.fd, 'start.json', io.META_LIMIT)) == self.start_sha,
            'archive log start changed')
        require(io._hash(io._json(self.archive_start)) == self.archive_start_sha
            and self.archive_start['policy'] == self.policy
            and io._hash(io._read(self.fd, 'archive-start.json', io.META_LIMIT)) == self.archive_start_sha,
            'archive writer policy changed')
        require(archive._transport(self.transport) == self.policy['transport_identity'], 'archive endpoint changed')
        for name, identity in self.children.items():
            path, fd = io._open(self.root/name)
            try: require(io._signature(os.fstat(fd))[:2] == identity, 'archive child namespace changed')
            finally: os.close(fd)

    def _failure(self, error):
        fresh = None
        try:
            if self.closed:
                path, fd = io._open(self.root); fresh = fd
                require(io._signature(os.fstat(fd))[:2] == self.root_identity, 'failure namespace changed')
            else: fd = self.fd; io._root(self.root, fd)
            if not os.path.lexists(self.root/'failed.json'):
                io._write(fd, 'failed.json', io._json({'schema_version': 1, 'status': 'failed',
                    'error_type': type(error).__name__, 'events': self.events, 'archived_chunks': self.archived}))
        except BaseException as evidence:
            error.add_note('archive writer failure evidence unavailable: '+repr(evidence))
        finally:
            if fresh is not None: io._cleanup((lambda: os.close(fresh),))

    def _abort(self, error):
        self.poisoned = True; self._failure(error)
        io._close_after_failure(self.close, error)

    def _append(self, *args, **kwargs):
        try:
            self._archive_check()
            if self.events and self.events % self.start['limits']['chunk_events'] == 0:
                self._seal_chunk()
            super()._append(*args, **kwargs)
            self._archive_check()
        except BaseException as error:
            if not self.closed: self._abort(error)
            raise

    def _seal_chunk(self):
        self._archive_check()
        if self.chunk_fd is None: return
        index = self.archived; extent = (self.events-index*self.start['limits']['chunk_events'])*events.RECORD_BYTES
        require(index < self.policy['max_chunks'] and 0 < extent <= io.MAX_CHUNK_BYTES,
            'sealed chunk extent/ordinal')
        descriptor = self.chunk_fd; self.chunk_fd = None
        io._cleanup((lambda: os.close(descriptor),))
        raw = io._read(self.fd, events._name(index), extent)
        require(len(raw) == extent, 'sealed chunk size differs')
        state = dict(self.archive_state); head = self.archive_head
        for offset in range(0, extent, events.RECORD_BYTES):
            record = raw[offset:offset+events.RECORD_BYTES]; body = record[:-32]
            head = io._hash(bytes.fromhex(head)+body)
            require(record[-32:] == bytes.fromhex(head), 'sealed chunk chain changed')
            state = events._advance(state, body, self.start['limits'], self.start['max_iterations'])
        require(state == self.state and head == self.head, 'sealed chunk acknowledged state differs')
        digest = io._hash(raw); begin = index*self.start['limits']['chunk_events']; end = self.events
        scope = _scope(self.start['owner'], self.start_sha, index, begin, end,
            self.archive_head, head, digest, extent)
        remote = self.policy['remote_prefix']+f'-{index:012d}'
        copy_root = self.root/'copies'/_chunk(index)
        receipt_sha = archive.preserve(source=self.root/events._name(index), attempt=copy_root,
            expected_sha256=digest, expected_bytes=extent, scope=scope, remote=remote,
            transport=self.transport, lease=self._archive_check,
            free_floor_bytes=self.policy['local_free_floor_bytes'])
        copy_path, cfd = io._open(copy_root)
        try:
            receipt_raw = io._read(cfd, 'complete.json', io.META_LIMIT)
            receipt = {'schema_version': 1, 'format': 'archive-chunk-v1',
                'transport_identity': self.policy['transport_identity'], 'remote': remote,
                'member': remote+'/payload.bin', 'scope': scope, 'source_sha256': digest, 'bytes': extent}
            require(receipt_raw == io._json(receipt) and io._hash(receipt_raw) == receipt_sha,
                'sealed copy receipt binding differs')
            mapping = {'schema_version': 1, 'archive_start_sha256': self.archive_start_sha,
                'log_start_sha256': self.start_sha, 'previous_manifest_sha256': self.manifest_head,
                'index': index, 'event_start': begin, 'event_stop': end, 'head_before': self.archive_head,
                'head_after': head, 'payload_sha256': digest, 'bytes': extent,
                'scope': scope, 'receipt': receipt, 'receipt_sha256': receipt_sha}
            mapping_raw = io._json(mapping)
            mapping_sha = io._write(self.fd, _chunk(index)+'.json', mapping_raw)
            self._archive_check()
            require(io._read(self.fd, _chunk(index)+'.json', io.META_LIMIT) == mapping_raw,
                'sealed mapping changed')
            io._root(copy_path, cfd)
            archive._inventory(cfd, {'intent.json', 'complete.json', 'snapshot.bin', 'readback.bin'})
            for name in ('intent.json', 'complete.json'):
                require(io._read(cfd, name, io.META_LIMIT) == receipt_raw, 'copy metadata changed')
            for name in ('snapshot.bin', 'readback.bin'):
                require(io._read(cfd, name, extent) == raw, 'owned copy bytes changed')
            require(io._read(self.fd, events._name(index), extent) == raw, 'sealed local chunk changed')
            # Only these new owned payload entries; all immutable receipts remain.
            os.unlink(events._name(index), dir_fd=self.fd)
            for name in ('snapshot.bin', 'readback.bin'): os.unlink(name, dir_fd=cfd)
            os.fsync(cfd); os.fsync(self.fd)
            disposed = io._json({'schema_version': 1, 'mapping_sha256': mapping_sha, 'owned_payloads_disposed': True})
            io._write(self.fd, f'disposed-{index:012d}.json', disposed)
            self._archive_check()
            archive._inventory(cfd, {'intent.json', 'complete.json'}); io._root(copy_path, cfd)
            for name in ('intent.json', 'complete.json'):
                require(io._read(cfd, name, io.META_LIMIT) == receipt_raw, 'disposed copy metadata changed')
            require(not os.path.lexists(self.root/events._name(index))
                and io._read(self.fd, _chunk(index)+'.json', io.META_LIMIT) == mapping_raw
                and io._read(self.fd, f'disposed-{index:012d}.json', io.META_LIMIT) == disposed,
                'sealed disposition changed')
            self.payload_digest.update(raw); self.archived_bytes += extent
            self.archive_state = state; self.archive_head = head
            self.manifest_head = mapping_sha; self.archived += 1
        finally: io._cleanup((lambda: os.close(cfd),))

    def _mapping(self, index):
        raw = io._read(self.fd, _chunk(index)+'.json', io.META_LIMIT); value = json.loads(raw)
        require(isinstance(value, dict) and set(value) == {'schema_version', 'archive_start_sha256',
            'log_start_sha256', 'previous_manifest_sha256', 'index', 'event_start', 'event_stop',
            'head_before', 'head_after', 'payload_sha256', 'bytes', 'scope', 'receipt', 'receipt_sha256'}
            and type(value['schema_version']) is int and value['schema_version'] == 1
            and io._json(value) == raw, 'archived mapping schema')
        begin = index*self.start['limits']['chunk_events']; end = min(self.events, begin+self.start['limits']['chunk_events'])
        for key in ('head_before','head_after','payload_sha256','previous_manifest_sha256'): io._identity(value[key])
        scope = _scope(self.start['owner'], self.start_sha, index, begin, end,
            value['head_before'], value['head_after'], value['payload_sha256'], (end-begin)*events.RECORD_BYTES)
        remote = self.policy['remote_prefix']+f'-{index:012d}'
        receipt = {'schema_version': 1, 'format': 'archive-chunk-v1',
            'transport_identity': self.policy['transport_identity'], 'remote': remote,
            'member': remote+'/payload.bin', 'scope': scope, 'source_sha256': value['payload_sha256'],
            'bytes': (end-begin)*events.RECORD_BYTES}
        require(value['archive_start_sha256'] == self.archive_start_sha and value['log_start_sha256'] == self.start_sha
            and all(type(value[k]) is int for k in ('index','event_start','event_stop','bytes'))
            and value['index'] == index and value['event_start'] == begin and value['event_stop'] == end
            and value['bytes'] == receipt['bytes'] and value['scope'] == scope and value['receipt'] == receipt
            and value['receipt_sha256'] == io._hash(io._json(receipt)), 'archived mapping binding differs')
        return value, io._hash(raw)

    def _fetch(self, index, extent):
        self._archive_check(); mapping, _ = self._mapping(index)
        require(extent == mapping['bytes'], 'archive replay extent differs')
        return consume.consume(receipt_bytes=io._json(mapping['receipt']), receipt_sha256=mapping['receipt_sha256'],
            expected_scope=mapping['scope'], attempt=self.root/'reads'/_chunk(index), transport=self.transport,
            lease=self._archive_check, free_floor_bytes=self.policy['local_free_floor_bytes'])

    def _metadata(self, complete=None, *, reads):
        self._archive_check()
        names = {'start.json', 'archive-start.json', 'copies', 'reads', 'terminal.json'}
        if complete is not None: names.add('archive-complete.json')
        # Streaming inventory validation; no population-sized filename set.
        count = 0
        with os.scandir(self.fd) as entries:
            for entry in entries:
                count += 1
                match = re.fullmatch(r'(?:chunk|disposed)-([0-9]{12})\.json', entry.name)
                require(count <= len(names)+2*self.archived and (entry.name in names
                    or match is not None and int(match[1]) < self.archived), 'archive root inventory differs')
        require(count == len(names)+2*self.archived, 'archive root inventory incomplete')
        previous = self.archive_start_sha; head = self.start_sha
        for index in range(self.archived):
            mapping, reference = self._mapping(index)
            require(mapping['previous_manifest_sha256'] == previous and mapping['head_before'] == head,
                'archive mapping chain differs')
            previous = reference; head = mapping['head_after']
            require(io._read(self.fd, f'disposed-{index:012d}.json', io.META_LIMIT) == io._json({
                'schema_version': 1, 'mapping_sha256': reference, 'owned_payloads_disposed': True}), 'archive disposition differs')
            for category in ('copies', 'reads') if reads else ('copies',):
                path, fd = io._open(self.root/category/_chunk(index))
                try:
                    if category == 'copies':
                        bodies = {name:io._json(mapping['receipt']) for name in ('intent.json','complete.json')}
                    else:
                        intent = io._json({'schema_version':1,'format':'archive-consume-v1',
                            'receipt_sha256':mapping['receipt_sha256'],'receipt':mapping['receipt']})
                        verified = io._json({'schema_version':1,'intent_sha256':io._hash(intent),
                            'bytes':mapping['bytes'],'payload_sha256':mapping['payload_sha256']})
                        bodies = {'intent.json':intent,'verified.json':verified,'complete.json':io._json({
                            'schema_version':1,'verified_sha256':io._hash(verified),'owned_cache_disposed':True})}
                    archive._inventory(fd, set(bodies))
                    for name, body in bodies.items(): require(io._read(fd,name,io.META_LIMIT)==body,'archive member metadata changed')
                    io._root(path,fd)
                finally: io._cleanup((lambda:os.close(fd),))
        require(previous == self.manifest_head and head == self.head, 'archive manifest terminal differs')
        for category in ('copies', 'reads'):
            path, fd = io._open(self.root/category)
            try:
                count = 0; total = self.archived if category == 'copies' or reads else 0
                with os.scandir(fd) as entries:
                    for entry in entries:
                        count += 1; match = re.fullmatch(r'chunk-([0-9]{12})',entry.name)
                        require(count<=total and match is not None and int(match[1])<total,'archive member inventory differs')
                require(count==total,'archive member inventory incomplete');io._root(path,fd)
            finally:io._cleanup((lambda:os.close(fd),))
        require(io._hash(io._read(self.fd,'terminal.json',io.META_LIMIT))==self.terminal_sha,'archive terminal changed')
        if complete is not None: require(io._read(self.fd,'archive-complete.json',io.META_LIMIT)==complete,'archive completion changed')
        io._root(self.root,self.fd)

    def _terminal(self, status, reason):
        if status == 'failed':
            self._abort(RuntimeError(reason)); return None
        try:
            self._archive_check(); require(self.state['pending'] is None,'pending pair prevents archive completion')
            self._seal_chunk()
            terminal = {'schema_version':1,'start_sha256':self.start_sha,'status':'complete','reason':'',
                'state':self.state,'head':self.head,'chunks':self.archived,'record_bytes':self.archived_bytes,
                'payload_sha256':self.payload_digest.hexdigest()}
            terminal_raw=io._json(terminal);self.terminal_sha=io._write(self.fd,'terminal.json',terminal_raw)
            self._metadata(reads=False)
            result=replay.verify(start_bytes=io._read(self.fd,'start.json',io.META_LIMIT),terminal_bytes=terminal_raw,
                terminal_sha256=self.terminal_sha,owner=self.start['owner'],scope=self.start['scope'],
                read_chunk=self._fetch,lease=self._archive_check)
            complete=io._json({'schema_version':1,'archive_start_sha256':self.archive_start_sha,
                'terminal_sha256':self.terminal_sha,'manifest_head_sha256':self.manifest_head,
                'chunks':self.archived,'replay':result})
            self._metadata(reads=True)
            self.archive_complete_sha=io._write(self.fd,'archive-complete.json',complete)
            self._metadata(complete,reads=True)
            self.close();return self.terminal_sha
        except BaseException as error:
            self._abort(error);raise

    def close(self):
        if self.closed:return
        self.closed=True;descriptor=self.chunk_fd;self.chunk_fd=None
        primary=None
        try:
            if descriptor is not None:io._cleanup((lambda:os.close(descriptor),))
        except BaseException as error:
            primary=error;self._failure(error);raise
        finally:consume._close_attempt(self.root,self.fd,self.root_identity,primary)
