"""Opt-in byte-exact control shards and finite closed-history audit scheduling.

No Run/Owner/native authority is granted here. Fingerprints are observations,
not writer exclusion. Closed-history mutation detection is deliberately sampled;
all authority-consuming stage and final boundaries require a full audit.
"""
import hashlib
import math
import os
from pathlib import Path
import stat
import struct
import time

FORMAT = 'bounded-archive-control-history-v1'
ASSUMPTION = 'closed-history sampled; no writer exclusion; mandatory boundary full-byte audits'
META = 131072
MAX_SHARD = 4 * 1024**2
OVERHEAD = 296  # 8-byte lengths, <=256 UTF-8 name bytes, 32-byte chain


def need(value, message):
    if not value: raise ValueError(message)


def validate(p):
    fields = {'schema_version','format','assumption','success_control_bytes',
              'success_diagnostic_bytes','shard_bytes','full_interval_ms',
              'max_stale_ms','max_callbacks_between_full'}
    need(type(p) is dict and set(p) == fields and p['schema_version'] == 1
         and type(p['schema_version']) is int and p['format'] == FORMAT
         and p['assumption'] == ASSUMPTION, 'explicit control-history contract required')
    for k in fields - {'schema_version','format','assumption'}:
        need(type(p[k]) is int and 0 < p[k] < 2**63, 'finite control-history limit')
    need(max(p['success_control_bytes'],p['success_diagnostic_bytes']) <= META
         and max(p['success_control_bytes'],p['success_diagnostic_bytes']) + OVERHEAD <= p['shard_bytes'] <= MAX_SHARD,
         'bounded complete record must fit shard')
    need(p['full_interval_ms'] < p['max_stale_ms'], 'finite audit freshness required')
    return dict(p)


def capacity(p, commands):
    p = validate(p); need(type(commands) is int and 0 < commands < 2**63, 'finite commands')
    control = 4 * commands * (p['success_control_bytes'] + OVERHEAD)
    diagnostic = commands * (p['success_diagnostic_bytes'] + OVERHEAD)
    need(control+8*META<2**63 and diagnostic+META+8*1024**2<2**63,'control capacity overflow')
    # A shard is closed only when the next bounded record cannot fit. Thus
    # all but the last shard contain > shard_bytes-max_frame bytes.
    def shards(total, frame):
        return 1 + total // max(1,p['shard_bytes']-frame)
    return {'control_bytes':control+8*META,
            'diagnostic_bytes':diagnostic+META+8*1024**2,
            'control_files':shards(control,p['success_control_bytes']+OVERHEAD)+8,
            'diagnostic_files':shards(diagnostic,p['success_diagnostic_bytes']+OVERHEAD)+2,
            'max_file_bytes':max(p['shard_bytes'],META,8*1024**2),
            'payload_budget_semantics':'cumulative rounded IO remains separate; diagnostic bound is retained local bytes'}


class Interval:
    """Failures/backward/stale clocks poison; expensive work cannot refresh old age."""
    def __init__(self, p, clock=time.monotonic):
        self.p=validate(p);self.clock=clock;self.last=None;self.observed=None
        self.calls=0;self.failed=False;self._policy_pin=tuple(sorted(self.p.items()));self._clock_pin=clock
    def check(self, audit, *, force=False):
        need(not self.failed,'history audit poisoned')
        try:
            need(tuple(sorted(self.p.items()))==self._policy_pin and self.clock is self._clock_pin,'history policy/clock replaced')
            now=self.clock();need(type(now) in (int,float) and math.isfinite(now),'finite clock')
            need(self.observed is None or now>=self.observed,'history clock moved backward')
            if self.last is not None:need((now-self.last)*1000 < self.p['max_stale_ms'],'history audit stale')
            self.observed=now;self.calls+=1
            if force or self.last is None or (now-self.last)*1000>=self.p['full_interval_ms'] or self.calls>=self.p['max_callbacks_between_full']:
                previous=self.last; audit();end=self.clock()
                need(math.isfinite(end) and end>=now,'history audit clock moved backward')
                need((end-(now if previous is None else previous))*1000 < self.p['max_stale_ms'],'history audit expired during check')
                self.last=end;self.observed=end;self.calls=0
        except BaseException:
            self.failed=True;raise


def signature(s):
    return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)


class Journal:
    """Original name/raw-byte records; no re-encoding, truncation or replacement.

    Each append is synced and read back before acknowledgement. The dedicated
    namespace is exclusive and never deletes or rewrites a prior shard. Closed
    shards are re-read at full audits, current shard identity on every append.
    """
    def __init__(self, root, *, record_bytes, total_bytes, records, shard_bytes):
        for v in (record_bytes,total_bytes,records,shard_bytes):need(type(v) is int and v>0,'finite journal bounds')
        need(record_bytes<=META and record_bytes+OVERHEAD<=shard_bytes<=MAX_SHARD,'journal record/shard bounds')
        self.root=Path(root);self.root.mkdir();self.inode=signature(self.root.lstat())[:2]
        self.record_bytes=record_bytes;self.total_bytes=total_bytes;self.records=records;self.shard_bytes=shard_bytes
        self.head=bytes(32);self.count=0;self.bytes=0;self.names=set();self.pins=[];self.failed=False
    def _root(self):
        s=self.root.lstat();need(stat.S_ISDIR(s.st_mode) and self.root.resolve()==self.root and signature(s)[:2]==self.inode,'journal root changed')
    def _path(self,index):return self.root/('control-%08d.bin'%index)
    def append(self,name,raw):
        need(not self.failed,'journal poisoned')
        try:
            self._root(); n=name.encode('utf-8')
            need(type(raw) is bytes and 0<len(n)<=256 and Path(name).name==name and name not in ('','.','..') and name not in self.names,'original unique control name required')
            need(len(raw)<=self.record_bytes and self.count<self.records,'success control bound exceeded')
            frame=struct.pack('<II',len(n),len(raw))+n+raw
            head=hashlib.sha256(self.head+frame).digest();frame+=head
            need(self.bytes+len(frame)<=self.total_bytes,'journal byte allowance exhausted')
            fresh=not self.pins or self.pins[-1][4]+len(frame)>self.shard_bytes
            index=len(self.pins) if fresh else len(self.pins)-1;path=self._path(index)
            flags=os.O_RDWR|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC
            fd=os.open(path,flags|(os.O_CREAT|os.O_EXCL if fresh else 0),0o600)
            try:
                before=os.fstat(fd);expected=0 if fresh else self.pins[-1][4]
                need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size==expected
                     and signature(before)==signature(path.lstat()) and (fresh or signature(before)==self.pins[-1]),'journal current shard changed')
                need(os.lseek(fd,0,os.SEEK_END)==expected,'journal append extent')
                sent=0
                while sent<len(frame):
                    nwrite=os.write(fd,frame[sent:]);need(nwrite>0,'journal zero write');sent+=nwrite
                os.fsync(fd);after=os.fstat(fd)
                need(after.st_size==expected+len(frame) and os.pread(fd,len(frame),expected)==frame
                     and signature(after)==signature(path.lstat()),'journal append readback differs')
                if fresh:self.pins.append(signature(after))
                else:self.pins[-1]=signature(after)
            finally:os.close(fd)
            if fresh:
                d=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
                try:os.fsync(d)
                finally:os.close(d)
            self.head=head;self.count+=1;self.bytes+=len(frame);self.names.add(name);self._root()
        except BaseException:
            self.failed=True;raise
    def audit(self):
        self._root();need(set(os.listdir(self.root))=={self._path(i).name for i in range(len(self.pins))},'journal membership differs')
        head=bytes(32);count=total=0;names=set()
        for i,pin in enumerate(self.pins):
            path=self._path(i);fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
            try:
                need(signature(os.fstat(fd))==pin and signature(path.lstat())==pin,'closed journal shard changed')
                offset=0
                while offset<pin[4]:
                    prefix=os.read(fd,8);need(len(prefix)==8,'partial control header')
                    nl,rl=struct.unpack('<II',prefix);need(0<nl<=256 and rl<=self.record_bytes,'control framing bound')
                    body=os.read(fd,nl+rl+32);need(len(body)==nl+rl+32,'partial control body')
                    name=body[:nl].decode('utf-8');need(name not in names,'duplicate archived name');names.add(name)
                    frame=prefix+body[:-32];head=hashlib.sha256(head+frame).digest();need(head==body[-32:],'control chain changed')
                    offset+=len(prefix)+len(body);count+=1
                need(offset==pin[4] and not os.read(fd,1) and signature(os.fstat(fd))==pin and signature(path.lstat())==pin,'journal EOF/stat changed')
                total+=offset
            finally:os.close(fd)
        need((head,count,total,names)==(self.head,self.count,self.bytes,self.names),'journal history differs')
        self._root()
