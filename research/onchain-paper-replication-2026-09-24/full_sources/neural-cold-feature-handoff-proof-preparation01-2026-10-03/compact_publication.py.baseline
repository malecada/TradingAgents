"""Exclusive durable compact closure metadata under its still-active owner.

This records the complete binding without adding old-format journal events or
sealing an owner. Terminal handoff/native dispatch and whole-workflow physical
accounting remain separate. Output allowance covers four bounded metadata files.
"""
import json
import os
import sys

from . import compact_closure, compact_owner, score_batches as io
from .provenance import canonical_bytes, durable_mkdir, freeze, thaw

require = io._require


def _owner(closure):return closure._dictionary._proof.owner


def directory(closure):
    owner = _owner(closure);bound = owner.bound.record
    return owner.bound._run.admission.root/'research_artifacts/onchain_compact_publications'/bound['workflow_identity']/bound['experiment']


def _final(closure):
    closure._integrity()
    compact_closure._final(closure._dictionary,closure._denominator,closure._graphs)


class Published:
    __slots__ = ('_closure','_record','_directory','_inode','_bodies','_limit')
    def __init__(self,closure,record,root,inode,bodies,limit):
        for name,value in (('_closure',closure),('_record',freeze(record)),('_directory',root),
            ('_inode',inode),('_bodies',freeze(bodies)),('_limit',limit)):
            object.__setattr__(self,name,value)
    def __setattr__(self,name,value):raise AttributeError('compact publication is immutable')
    directory = property(lambda self:self._directory)
    record = property(lambda self:self._record)
    def lease(self):
        self._closure.lease()
        require(self.record['closure_sha256'] == io._hash(canonical_bytes(thaw(self._closure.record))),
            'compact publication closure changed')
    def _evidence(self):
        require(self.directory == directory(self._closure),'compact publication path differs')
        path,fd = io._open(self.directory)
        try:
            info = os.fstat(fd)
            require((info.st_dev,info.st_ino) == self._inode,'compact publication directory changed')
            compact_owner.entries(path,set(self._bodies),required=set(self._bodies))
            for name,body in self._bodies.items():
                require(io._read(fd,name,self._limit) == body,'compact publication saved metadata changed')
            io._root(path,fd)
        finally:io._cleanup((lambda:os.close(fd),))
    def _check(self):
        self._closure._check();self.lease();_final(self._closure);self._evidence()
    def check(self):
        owner = _owner(self._closure)
        require(owner._transition.acquire(blocking=False),'concurrent compact publication check')
        try:self._check()
        finally:owner._transition.release()


def _failed(owner,root,inode):
    owner.poisoned = True
    path,fd = io._open(root)
    try:
        info = os.fstat(fd)
        require((info.st_dev,info.st_ino) == inode,'failed compact publication directory changed')
        if not compact_owner.present(root/'failed.json'):
            io._write(fd,'failed.json',canonical_bytes({'schema_version':1,'status':'failed','owner':owner.identity}))
        io._root(path,fd)
    finally:io._cleanup((lambda:os.close(fd),))


def publish(closure,*,input_name):
    require(type(closure) is compact_closure.Receipt,'actual compact closure Receipt required')
    owner = _owner(closure)
    require(owner._transition.acquire(blocking=False),'concurrent compact closure publication')
    fd = None;claimed = False;inode = None
    try:
        closure._check();run = owner.bound._run;bound = owner.bound.record
        selected = json.loads(run.read_input('execution_job'))['payload']['representation_jobs'][bound['representation']]
        item = json.loads(run.read_input(selected['plan_input']))['producers'][bound['producer']]
        require(type(input_name) is str and input_name in run.admission.inputs
            and item.get('compact_publication_input') == selected.get('compact_publication_input') == input_name,
            'selected compact publication policy differs')
        policy = json.loads(run.read_input(input_name))
        require(type(policy) is dict and set(policy) == {'schema_version','max_metadata_bytes','max_attempt_bytes'}
            and type(policy['schema_version']) is int and policy['schema_version'] == 1
            and all(type(policy[k]) is int and 0 < policy[k] < 2**63 for k in ('max_metadata_bytes','max_attempt_bytes'))
            and policy['max_metadata_bytes'] <= 2*1024**2,'compact publication policy differs')
        cap = policy['max_metadata_bytes'];reserved = 4*cap
        require(reserved <= policy['max_attempt_bytes'],'compact publication output allowance exceeded')
        root = directory(closure)
        require(root.is_absolute() and root.resolve() == root and not compact_owner.present(root),
            'compact publication already claimed or redirected')
        start = {'schema_version':1,'owner':owner.identity,'policy_input':input_name,
            'policy_sha256':run.admission.inputs[input_name]['sha256'],
            'closure_sha256':io._hash(canonical_bytes(thaw(closure.record))),
            'reserved_encoded_bytes':reserved,'resumable':False}
        binding = canonical_bytes(thaw(closure.record['binding']))
        start_raw = canonical_bytes(start)
        record = start | {'status':'complete','start_sha256':io._hash(start_raw),'binding_sha256':io._hash(binding),
            'closure':thaw(closure.record),'representation_sealed':False,'run_outputs_published':False}
        bodies = {'start.json':start_raw,'binding.json':binding,'complete.json':canonical_bytes(record)}
        failed = canonical_bytes({'schema_version':1,'status':'failed','owner':owner.identity})
        require(max(len(b) for b in (*bodies.values(),failed)) <= cap,
            'compact publication metadata allowance exceeded before claim')
        closure.lease();_final(closure);durable_mkdir(root.parent)
        require(root.resolve() == root,'compact publication parent redirected')
        closure.lease();_final(closure)
        root.mkdir();claimed = True;info = root.lstat();inode = (info.st_dev,info.st_ino)
        parent,pfd = io._open(root.parent)
        try:os.fsync(pfd);io._root(parent,pfd)
        finally:io._cleanup((lambda:os.close(pfd),))
        root,fd = io._open(root)
        require(os.fstat(fd).st_dev == owner.root.stat().st_dev,'compact publication device differs')
        written = set()
        for name,body in bodies.items():
            closure.lease();_final(closure);io._root(root,fd)
            compact_owner.entries(root,written,required=written)
            for previous in written:
                require(io._read(fd,previous,cap) == bodies[previous],'compact publication predecessor changed')
            io._write(fd,name,body);written.add(name)
        result = Published(closure,record,root,inode,bodies,cap)
        result.lease();_final(closure);result._evidence()
        return result
    except BaseException as primary:
        if claimed:
            try:_failed(owner,root,inode)
            except BaseException as failure:
                primary.add_note('Compact publication failure marker: '+repr(failure))
                if isinstance(failure,io.CleanupFailure):raise failure from primary
        raise
    finally:
        primary = sys.exception()
        try:
            if fd is not None:
                try:io._cleanup((lambda:os.close(fd),))
                except BaseException as cleanup:
                    owner.poisoned = True
                    try:_failed(owner,root,inode)
                    except BaseException as error:cleanup.add_note('Compact publication failure marker: '+repr(error))
                    if primary is not None:raise cleanup from primary
                    raise
        finally:owner._transition.release()
