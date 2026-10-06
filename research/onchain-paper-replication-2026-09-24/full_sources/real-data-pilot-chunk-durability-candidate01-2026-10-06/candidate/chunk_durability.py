"""Selected sampled durability only; no scientific or run authority.

Acknowledged bytes remain read back. These volatile watermarks are not restart
receipts. Without the original terminal, a crash suffix is unknown/uncredited.
Time is checked at writer/lease activity; blocked syscalls/idle time have no
background flusher guarantee. Native bounds remain independent.
"""
import math
import os
import time
from types import MappingProxyType


def policy(value):
    if type(value) is not dict or set(value)!={'schema_version','scope','pair_records','tail_records','max_interval_ms'}:
        raise ValueError('explicit chunk durability policy required')
    if type(value['schema_version']) is not int or value['schema_version']!=1 or value['scope']!='resource-pilot-only':
        raise ValueError('resource-only durability version required')
    for key,maximum in (('pair_records',1000000),('tail_records',1000000),('max_interval_ms',60000)):
        if type(value[key]) is not int or not 0<value[key]<=maximum:raise ValueError('finite durability bound required')
    return dict(value)


class BatchSync:
    def __init__(self, selected, kind):
        p=policy(selected)
        if kind not in ('pair','tail'):raise ValueError('durability record kind')
        self.policy=MappingProxyType(p);self._policy=self.policy
        self.limit=p[kind+'_records'];self.interval=p['max_interval_ms']/1000
        self._limits=(self.limit,self.interval);self._clock=time.monotonic
        self.acknowledged=self.durable=0;self.head=self.durable_head=None
        self.poisoned=False;self.last=self._now();self.observed=self.last

    def _now(self):
        value=self._clock()
        if type(value) not in (int,float) or not math.isfinite(value):raise ValueError('finite durability clock required')
        return value

    def _check(self):
        if self.poisoned or self.policy is not self._policy or (self.limit,self.interval)!=self._limits:
            raise ValueError('durability state poisoned/changed')
        now=self._now()
        if now<self.observed:raise ValueError('durability clock reversed')
        self.observed=now
        return now

    def before(self,fd):
        try:
            now=self._check()
            if self.acknowledged>self.durable and now-self.last>=self.interval:self.barrier(fd)
        except BaseException:
            self.poisoned=True;raise

    def acknowledge(self,fd,count,head):
        try:
            now=self._check()
            if count!=self.acknowledged+1:raise ValueError('durability acknowledgement order')
            self.acknowledged=count;self.head=head
            if count-self.durable>=self.limit or now-self.last>=self.interval:self.barrier(fd)
        except BaseException:
            self.poisoned=True;raise

    def barrier(self,fd):
        try:
            self._check()
            if self.acknowledged>self.durable:
                if fd is None:raise ValueError('unflushed writer descriptor missing')
                os.fsync(fd)
                done=self._check()
                self.durable=self.acknowledged;self.durable_head=self.head;self.last=done
        except BaseException:
            self.poisoned=True;raise

    def snapshot(self):
        return {'acknowledged_records':self.acknowledged,'durable_records':self.durable,
            'durable_head':self.durable_head,'unflushed_records':self.acknowledged-self.durable,
            'volatile_not_restart_authority':True,'poisoned':self.poisoned}
