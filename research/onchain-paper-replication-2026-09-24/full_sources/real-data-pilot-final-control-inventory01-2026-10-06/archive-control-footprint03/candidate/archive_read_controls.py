"""Opt-in exact archive read receipts in the existing bounded Journal format.

Only reader controls change physical layout. Numerical payload, original receipt
bytes/hashes, event replay, fixed top controls and legacy defaults are unchanged.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import sys
from . import archive_control_history as history, archive_chunks as archive
from . import archive_consume as legacy
io=archive.io
require=io._require
from .archive_read_control_capacity import POLICY, ROLE_BYTES, FRAME_OVERHEAD, policy, capacity

def selected(writer_policy):
    value=writer_policy.get('read_controls')
    return None if value is None else policy(value)


def bodies(receipt,receipt_sha):
    # Caller first validates canonical original receipt / endpoint / extent.
    intent=io._json({'schema_version':1,'format':'archive-consume-v1','receipt_sha256':receipt_sha,'receipt':receipt})
    verified=io._json({'schema_version':1,'intent_sha256':io._hash(intent),'bytes':receipt['bytes'],'payload_sha256':receipt['source_sha256']})
    result={'intent.json':intent,'verified.json':verified,'complete.json':io._json({'schema_version':1,'verified_sha256':io._hash(verified),'owned_cache_disposed':True})}
    for name,raw in result.items():require(len(raw)<=ROLE_BYTES[name],'archive read encoded role exceeds schema bound')
    return result

def record_name(index,leaf):
    require(type(index) is int and 0<=index<10**12,'archive read ordinal width')
    return f'chunk-{index:012d}-'+leaf

class Writer:
    def __init__(self,root,chunks,selection):
        self.root=Path(root);self.policy=policy(selection);self.chunks=chunks;self.next=0;self.failed=False
        bound=capacity(chunks,self.policy)
        self.journal=history.Journal(self.root/'controls',record_bytes=8192,total_bytes=bound['journal_bytes'],records=3*chunks+4,shard_bytes=self.policy['shard_bytes'])
        self._pin=(self.root,self.chunks,id(self.journal),self.journal.root,self.journal.record_bytes,self.journal.total_bytes,self.journal.records,self.journal.shard_bytes)
    def _check(self):
        require(self._pin==(self.root,self.chunks,id(self.journal),self.journal.root,self.journal.record_bytes,self.journal.total_bytes,self.journal.records,self.journal.shard_bytes) and self.policy==POLICY,'packed archive writer binding changed')
        self.journal._root()
        for index,pin in enumerate(self.journal.pins):
            require(history.signature(self.journal._path(index).lstat())==pin,'packed archive acknowledged shard changed')
    def consume(self,index,*,receipt_bytes,receipt_sha256,expected_scope,transport,lease,free_floor_bytes):
        self._check()
        require(not self.failed and index==self.next and index<self.chunks,'packed archive read order/terminal differs')
        fd=None;identity_fd=None
        try:
            io._identity(receipt_sha256);io._identity(expected_scope)
            require(type(receipt_bytes) is bytes and len(receipt_bytes)<=io.META_LIMIT and io._hash(receipt_bytes)==receipt_sha256,'trusted bounded receipt bytes required')
            receipt=json.loads(receipt_bytes)
            require(type(receipt) is dict and set(receipt)=={'schema_version','format','transport_identity','remote','member','scope','source_sha256','bytes'} and type(receipt['schema_version']) is int and receipt['schema_version']==1 and receipt['format']=='archive-chunk-v1' and io._json(receipt)==receipt_bytes,'canonical archive receipt schema required')
            identity=archive._transport(transport)
            require(receipt['scope']==expected_scope and receipt['transport_identity']==identity and receipt['member']==archive._remote(receipt['remote']),'archive scope/endpoint/member differs')
            archive._extent(receipt['bytes'],receipt['source_sha256']);encoded=bodies(receipt,receipt_sha256)
            require(callable(lease),'mandatory archive consumption lease');lease();archive._capacity(self.root,free_floor_bytes,1,receipt['bytes'])
            root,fd=io._open(self.root);identity_fd=io._signature(os.fstat(fd))[:2]
            payload=self.root/('payload-%012d.bin'%index)
            def live():
                lease();io._root(root,fd);require(archive._transport(transport)==identity,'archive transport identity changed')
                self._check();require(not self.failed and self.next==index,'packed read writer changed')
            self.journal.append(record_name(index,'intent.json'),encoded['intent.json']);live()
            transport.get(receipt['member'],payload,expected_bytes=receipt['bytes']);live()
            archive._read(payload,receipt['bytes'],receipt['source_sha256'])
            self.journal.append(record_name(index,'verified.json'),encoded['verified.json']);live()
            before=payload.lstat();result=archive._read(payload,receipt['bytes'],receipt['source_sha256'])
            require(io._signature(before)==io._signature(payload.lstat()),'cache identity changed before disposal')
            # Every exact receipt is durably acknowledged before disposal. This
            # disposes only the existing verified temporary payload, never controls.
            payload.unlink();os.fsync(fd)
            self.journal.append(record_name(index,'complete.json'),encoded['complete.json']);live()
            require(type(result) is bytes and len(result)==receipt['bytes'] and io._hash(result)==receipt['source_sha256'],'returned archive bytes differ')
            self.next+=1
            return result
        except BaseException as error:
            self.failed=True
            try:self.journal.append(record_name(index,'failed.json'),io._json({'schema_version':1,'error_type':type(error).__name__}))
            except BaseException as evidence:error.add_note('packed failure receipt unavailable: '+repr(evidence))
            raise
        finally:
            if fd is not None:legacy._close_attempt(self.root,fd,identity_fd,sys.exc_info()[1])

def audit(root,expected,selection,*,max_chunks):
    """Cold exact inverse: expected iterable comes from trusted source mappings.

    Keeps one record only; validates names/raw bytes/order/chaining/EOF/inodes.
    No per-read manifest anchor can substitute for source-derived equality.
    """
    p=policy(selection);root=Path(root)/'controls';path,dfd=io._open(root)
    head=bytes(32);count=0;items=iter(expected)
    try:
        names=[];bound=capacity(max_chunks,p)
        with os.scandir(dfd) as entries:
            for entry in entries:
                require(len(names)<bound['files']-8,'packed archive shard count exceeded');names.append(entry.name)
        names.sort();require(names==['control-%08d.bin'%i for i in range(len(names))],'packed archive shard membership differs')
        for name in names:
            fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=dfd)
            try:
                before=os.fstat(fd);require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<before.st_size<=p['shard_bytes'],'packed archive shard extent/type')
                offset=0
                while offset<before.st_size:
                    prefix=os.read(fd,8);require(len(prefix)==8,'partial packed archive header')
                    nl,rl=struct.unpack('<II',prefix);require(0<nl<=32 and rl<=8192,'packed archive frame bounds')
                    body=os.read(fd,nl+rl+32);require(len(body)==nl+rl+32,'partial packed archive record')
                    expected_item=next(items,None);require(expected_item is not None,'extra packed archive record')
                    expected_name,expected_raw=expected_item
                    require(body[:nl]==expected_name.encode() and body[nl:nl+rl]==expected_raw,'packed archive exact original receipt differs')
                    head=hashlib.sha256(head+prefix+body[:-32]).digest();require(head==body[-32:],'packed archive record hash chain differs')
                    offset+=8+len(body);count+=1
                require(offset==before.st_size and not os.read(fd,1) and io._signature(before)==io._signature(os.fstat(fd))==io._signature(os.stat(name,dir_fd=dfd,follow_symlinks=False)),'packed archive shard changed')
            finally:io._cleanup((lambda:os.close(fd),),primary=sys.exc_info()[1])
        require(next(items,None) is None,'missing packed archive receipt');io._root(path,dfd)
        return {'records':count,'head_sha256':head.hex()}
    finally:io._cleanup((lambda:os.close(dfd),),primary=sys.exc_info()[1])
