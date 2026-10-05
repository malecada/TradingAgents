"""Finite sampled-validation scheduler and metadata fingerprints, not authority."""
import math,os,stat,time
from pathlib import Path
from types import MappingProxyType
KIND='imported-authority-sampled-stage-interval'
ASSUMPTION='Source/input/runtime mutation detection is sampled within registered intervals; full validation precedes successful boundaries. No atomic writer exclusion.'
def require(ok,why):
    if not ok:raise ValueError('import lease: '+why)
def policy(value):
    fields={'schema_version','kind','live_interval_ms','fingerprint_interval_ms','full_interval_ms','max_stale_ms','max_calls_between_full','assumption'}
    require(type(value) is dict and set(value)==fields and type(value['schema_version']) is int and value['schema_version']==1 and value['kind']==KIND and value['assumption']==ASSUMPTION,'explicit sampled contract required')
    require(all(type(value[k]) is int and 0<value[k]<2**31 for k in fields-{'schema_version','kind','assumption'}),'finite positive interval/call bounds required')
    require(value['live_interval_ms']<=value['fingerprint_interval_ms']<=value['full_interval_ms']<value['max_stale_ms'],'ordered finite intervals required')
    return dict(value)
def fingerprint(path):
    p=Path(path);s=p.lstat()
    require(stat.S_ISREG(s.st_mode) and s.st_nlink>=1 and p.resolve(strict=True)==p,'regular canonical evidence required')
    return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
class Interval:
    """Callback-neutral scheduler; callers must supply genuine authority checks."""
    def __init__(self,selected,clock=time.monotonic):
        self.policy=MappingProxyType(policy(selected));self.clock=clock;self._clock_pin=clock;self.closed=False;self.last=None;self.full=None;self.finger=None;self.live=None;self.calls=0
    def now(self):
        require(self.clock is self._clock_pin,'monotonic clock replaced')
        t=self.clock();require(type(t) in (int,float) and math.isfinite(t) and t>=0,'invalid monotonic clock')
        require(self.last is None or t>=self.last,'backward clock')
        self.last=t;return t
    def validate(self,full_check,fingerprint_check,live_check,*,boundary=False):
        require(not self.closed,'poisoned/closed interval')
        try:
            now=self.now()
            if self.full is not None:require((now-self.full)*1000<=self.policy['max_stale_ms'],'stale interval cannot refresh')
            full=boundary or self.full is None or self.calls>=self.policy['max_calls_between_full'] or (now-self.full)*1000>=self.policy['full_interval_ms']
            live=full or self.live is None or (now-self.live)*1000>=self.policy['live_interval_ms']
            if live:
                live_check();now=self.now()
                if self.full is not None:require((now-self.full)*1000<=self.policy['max_stale_ms'],'stale during live check')
                full=full or self.full is None or (now-self.full)*1000>=self.policy['full_interval_ms']
            if full:
                full_check();fingerprint_check();done=self.now()
                require((done-now)*1000<=self.policy['max_stale_ms'],'full validation exceeded freshness bound')
                self.full=self.finger=done;self.calls=0
            elif (now-self.finger)*1000>=self.policy['fingerprint_interval_ms']:
                fingerprint_check();done=self.now();require((done-self.full)*1000<=self.policy['max_stale_ms'],'validation exceeded freshness bound');self.finger=done
            if live:self.live=self.now()
            require((self.last-self.full)*1000<=self.policy['max_stale_ms'],'stale after live check')
            self.calls+=1
        except BaseException:self.closed=True;raise
