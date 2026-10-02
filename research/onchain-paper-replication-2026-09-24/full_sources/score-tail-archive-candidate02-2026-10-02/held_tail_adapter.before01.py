"""Candidate genuine-held boundary for local tail-byte verification only.

Install beside score_tail_archive only after review; imported production Owner
itself pulls numerical modules, so this module is NOT imported by pure tests.
No surrogate authority, public lease-only transport activation or event-budget
reinterpretation is accepted. Resource Binding must supply its actual job input.
The separate shared tail-population dispatch extension is still unimplemented.
"""
from pathlib import Path
import os
import sys

from tradingagents.research.onchain_replication import compact_owner as owners
from tradingagents.research.onchain_replication import archive_dispatch as dispatch
from tradingagents.research.onchain_replication.provenance import canonical_bytes, digest, thaw
from . import score_tail_archive as tail

require=tail.require


def _joins(owner,stage,c):
    require(owner.identity==c['owner'] and owner._binding_sha256==c['binding_sha256']
        and stage.owner is owner and owner.active is stage and owner.stages.get(stage.name) is stage
        and stage.name==c['stage'] and stage.intent_sha256==c['stage_intent_sha256']
        and stage.kind=='mcm' and not stage.closed and stage.pairs==c['rows']*32
        and stage.scope['workflow']==c['scope']['workflow'],'original owner/stage/workload denominator differs')


class HeldSource:
    """A captured original Owner/stage/token; never acquires a substitute lock."""
    def __init__(self,owner,stage,held,value):
        require(type(owner) is owners.Owner and type(stage) is owners.Stage
            and type(held) is owners._HeldTransition,'genuine compact Owner, Stage and held token required')
        self.owner=owner;self.stage=stage;self.held=held;self.contract=tail.contract(value)
        self._pin=tail.encode(self.contract);self._original=(owner,stage,held,owner.bound,owner.bound._run)
        self.check()
    def check(self):
        owner,stage,held,bound,run=self._original
        require((self.owner,self.stage,self.held)==(owner,stage,held) and owner.bound is bound
            and bound._run is run and tail.encode(self.contract)==self._pin,'held source objects changed')
        held.check(owner);owner.lease();stage.integrity();owners.verify_current(owner)
        _joins(owner,stage,self.contract)
        require(bound.record.get('resource_only') is True
            and bound.record.get('job_input')==self.contract['job_input']
            and bound.record.get('job_sha256')==self.contract['job_sha256']
            and bound.record['source_commit']==self.contract['source_commit']
            and run.admission.source==self.contract['source_commit'],'actual resource job/source join required')
        key=self.contract['job_input'];require(run.admission.inputs[key]['sha256']==self.contract['job_sha256'],'job admission hash differs')
        raw=run.read_input(key);require(digest(raw)==self.contract['job_sha256'],'actual selected job bytes differ')
        held.check(owner);owners.verify_current(owner);stage.integrity();_joins(owner,stage,self.contract)
        require(owner.bound is bound and bound._run is run and tail.encode(self.contract)==self._pin,
            'held source replaced during job callback')
        require(tail.digest(stage.intent)==self.contract['stage_intent_sha256'],'original stage intent differs')
        path,fd=tail.open_root(stage.root)
        try:
            require((os.fstat(fd).st_dev,os.fstat(fd).st_ino)==stage.inode,'stage inode differs')
            require(tail.read_member(fd,'intent.json',tail.META)==stage.intent,'stage original source differs')
        finally:tail.cleanup((lambda:os.close(fd),),sys.exception())
        held.check(owner)
    def original_parts(self):
        self.check();c=self.contract;stream=self.stage.root/'stream';index=c['index']
        roots=(stream/'tails'/f'tail-{index:012d}',stream/'batches')
        require(str(roots[1])==c['batch_directory'],'original stage batch destination differs')
        result=[];pins=[]
        for root,names in ((roots[0],('start.json','terminal.json','records.bin')),
                           (roots[1],(f'chunk-{index:012d}.json',f'chunk-{index:012d}.bin'))):
            path,fd=tail.open_root(root)
            try:
                inode=(os.fstat(fd).st_dev,os.fstat(fd).st_ino)
                for name in names:
                    body=tail.read_member(fd,name,tail.MAX_BYTES if name.endswith('.bin') else tail.META)
                    result.append(body);pins.append((path,name,inode,tail.signature(os.stat(name,dir_fd=fd,follow_symlinks=False))))
                tail.root_check(path,fd)
            finally:tail.cleanup((lambda:os.close(fd),),sys.exception())
        batch_root,bfd=tail.open_root(roots[1])
        try:
            require(tail.digest(tail.read_member(bfd,'start.json',tail.META))==c['batch_start_sha256'],
                'original batch start differs')
            batch_start_pin=tail.signature(os.stat('start.json',dir_fd=bfd,follow_symlinks=False))
            tail.root_check(batch_root,bfd)
        finally:tail.cleanup((lambda:os.close(bfd),),sys.exception())
        tail.verify_bytes(c,*result);self.check()
        # The final authority callback precedes every original inode/body rejoin.
        for (root,name,inode,pin),body in zip(pins,result,strict=True):
            path,fd=tail.open_root(root)
            try:
                require((os.fstat(fd).st_dev,os.fstat(fd).st_ino)==inode
                    and tail.signature(os.stat(name,dir_fd=fd,follow_symlinks=False))==pin
                    and tail.read_member(fd,name,max(1,len(body)))==body,'original source changed during authority callback')
                tail.root_check(path,fd)
            finally:tail.cleanup((lambda:os.close(fd),),sys.exception())
        batch_root,bfd=tail.open_root(roots[1])
        try:
            require(tail.signature(os.stat('start.json',dir_fd=bfd,follow_symlinks=False))==batch_start_pin
                and tail.digest(tail.read_member(bfd,'start.json',tail.META))==c['batch_start_sha256'],
                'original batch start changed across callback')
            tail.root_check(batch_root,bfd)
        finally:tail.cleanup((lambda:os.close(bfd),),sys.exception())
        self.held.check(self.owner);return tuple(result)


def bind_transport(source,transport,ledger,claim):
    """Fail closed until shared Context and typed ledger support tail population.

    Even an actual event Operation/View must not authorize an 80-byte tail. The
    existing dispatch.binding and its 168-byte max_events accounting cannot be
    reused by merely swapping a callback or increasing that event population.
    """
    require(type(source) is HeldSource,'original held source required');source.check()
    require(type(transport) is dispatch.View,'actual shared transport View required')
    raise NotImplementedError('tail population is absent from archive_dispatch.preflight, '
        'Context capability record and archive_owner_operations.Ledger; no transfer admitted')
