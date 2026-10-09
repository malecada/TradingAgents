from pathlib import Path
import ast,difflib
P=Path(__file__).resolve().parent;ROOT=P.parents[3];source=ROOT/'tradingagents/research/onchain_replication/matching_owner.py';text=source.read_text()
observer='''
# Explicitly selected, four-phase nested wall timing; never authority evidence.
_LEASE_TIMING_CLOCK=time.monotonic_ns
_LEASE_TIMING_PHASES=('first_guard','journal','snapshots','second_guard')
_LEASE_TIMING_LIMIT=2**63-1

class BindingLeaseTiming:
    def __init__(self,binding):
        require(type(binding) is Binding,'actual Binding timing target required')
        self.binding=binding;self._binding_pin=binding
        self.clock=_LEASE_TIMING_CLOCK;self._last=None
        self._totals=(0,)*12;self.closed=False

    def _check(self,binding,*,allow_closed=False):
        require(type(self) is BindingLeaseTiming and self.binding is binding is self._binding_pin,
                'binding timing identity differs')
        require(self.clock is _LEASE_TIMING_CLOCK,'binding timing clock differs')
        require(type(self.closed) is bool and (allow_closed or not self.closed),'binding timing closed')
        require(type(self._totals) is tuple and len(self._totals)==12
                and all(type(v) is int and 0<=v<=_LEASE_TIMING_LIMIT for v in self._totals)
                and all(self._totals[i+2]<=self._totals[i] for i in range(0,12,3)),
                'binding timing counters differ')

    def _now(self):
        require(self.clock is _LEASE_TIMING_CLOCK,'binding timing clock differs')
        now=self.clock()
        require(self.clock is _LEASE_TIMING_CLOCK and type(now) is int and 0<=now<=_LEASE_TIMING_LIMIT
                and (self._last is None or now>=self._last),'binding timing clock invalid')
        self._last=now;return now

    @contextmanager
    def phase(self,name,binding):
        primary=None
        try:
            self._check(binding)
            require(type(name) is str and name in _LEASE_TIMING_PHASES,'binding timing phase differs')
            index=3*_LEASE_TIMING_PHASES.index(name)
            start=self._now()
        except BaseException:
            self.closed=True;raise
        try:
            yield
        except BaseException as error:
            primary=error;raise
        finally:
            try:
                finish=self._now();self._check(binding)
                values=list(self._totals)
                values[index]+=1;values[index+1]+=finish-start;values[index+2]+=int(primary is not None)
                require(all(v<=_LEASE_TIMING_LIMIT for v in values),'binding timing counter overflow')
                self._totals=tuple(values)
            except BaseException as timing_error:
                self.closed=True
                if primary is None:raise
                BaseException.add_note(primary,'binding phase timing failed: '+type(timing_error).__name__)

    def snapshot(self):
        self._check(self.binding,allow_closed=True)
        result={'binding_timing_closed':int(self.closed)}
        for i,name in enumerate(_LEASE_TIMING_PHASES):
            for j,suffix in enumerate(('calls','ns','failures')):
                result['binding_'+name+'_'+suffix]=self._totals[i*3+j]
        return result

'''
text=text.replace('import json\n','import json\nimport time\nfrom contextlib import contextmanager\n',1)
pos=text.index('\nclass Binding:');text=text[:pos]+'\n'+observer+text[pos:]
a=text.index('    def lease(self):',text.index('class Binding:'));b=text.index('\n    def check(self):',a);old=text[a:b]
lines=old.splitlines();body='\n'.join(lines[2:]);legacy='\n'.join('    '+x for x in body.splitlines())
# Same statements, only grouped with four fixed observer regions.
observed=body.replace('        self._guard()',"        with observer.phase('first_guard',self):\n            self._guard()",1)
start=observed.index('        if self._ancestry_arguments');end=observed.index('        reader=metadata',start)
observed=observed[:start]+"        with observer.phase('journal',self):\n"+'\n'.join('    '+x for x in observed[start:end].rstrip().splitlines())+'\n'+observed[end:]
start=observed.index('        reader=metadata');end=observed.rindex('        self._guard()')
observed=observed[:start]+"        with observer.phase('snapshots',self):\n"+'\n'.join('    '+x for x in observed[start:end].rstrip().splitlines())+'\n'+"        with observer.phase('second_guard',self):\n            self._guard()"
new='    def lease(self,*,observer=None):\n'+lines[1]+'\n        if observer is None:\n'+legacy+'\n            return\n        require(type(observer) is BindingLeaseTiming,\'exact binding timing observer required\')\n'+observed+'\n'
text=text[:a]+new+text[b:];ast.parse(text);(P/'matching_owner.py').write_text(text);(P/'inverse.patch').write_text(''.join(difflib.unified_diff(text.splitlines(True),source.read_text().splitlines(True),fromfile='candidate',tofile='baseline')))
