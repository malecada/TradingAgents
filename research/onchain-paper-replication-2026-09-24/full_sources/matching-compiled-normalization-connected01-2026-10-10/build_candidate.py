from pathlib import Path
import hashlib,json,difflib
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
SRC=ROOT/'tradingagents/research/onchain_replication'
OLD=OUT.parent/'matching-compiled-small-pair-prototype04-2026-10-09'
names=['matching_annealing.py','matching_checkpoint.py','matching_immutable_session.py','batched_pair_executor.py','batched_numeric_reuse.py','batched_numeric_execution.py']
changes={}
def replace(s,a,b,count=1):
    assert s.count(a)==count,(a,s.count(a),count)
    return s.replace(a,b)
for name in names:
    s=(SRC/name).read_text();(OUT/('baseline_'+name)).write_text(s)
    if name=='matching_annealing.py':
        s=replace(s,'def _advance_checked(state,a,b,c,*,max_operations,edge_cache_policy=None):','def _advance_checked(state,a,b,c,*,max_operations,edge_cache_policy=None,normalizer=None):')
        for block,axis in [('block',1),('padded',0),('block',0)]:
            old=f'logsumexp({block},axis={axis},keepdims=True)'
            new=f'(logsumexp({block},axis={axis},keepdims=True) if normalizer is None else normalizer.lse({block},axis={axis},keepdims=True,fallback=logsumexp))'
            s=replace(s,old,new)
    elif name=='matching_checkpoint.py':
        s=replace(s,'def _advance_owned(s,a,b,c,*,max_operations,edge_cache_policy=None):','def _advance_owned(s,a,b,c,*,max_operations,edge_cache_policy=None,normalizer=None):')
        s=replace(s,"**({'edge_cache_policy':dict(selected)} if selected is not None else {}))","**({'edge_cache_policy':dict(selected)} if selected is not None else {}),**({'normalizer':normalizer} if normalizer is not None else {}))")
    else:
        s=replace(s,'from . import adaptive_edge_policy','from . import adaptive_edge_policy\nfrom . import compiled_normalization_policy')
        s=replace(s,'edge_cache_policy=None):','edge_cache_policy=None,compiled_normalization_policy_value=None):')
        # Selection metadata is validated at constructor entry without numeric backend loading.
        line='adaptive_edge_policy.attach(self,edge_cache_policy)'
        indent='            ' if name=='batched_numeric_execution.py' else '        '
        s=replace(s,line,line+'\n'+indent+'compiled_normalization_policy.attach(self,compiled_normalization_policy_value)')
        if name=='matching_immutable_session.py':
            s=replace(s,'        self.advances = 0','        self.advances = 0\n        self._normalizer = compiled_normalization_policy.open_backend(self)\n        self._normalizer_pin = self._normalizer\n        self._normalizer_functions = tuple((name,getattr(self._normalizer,name),getattr(self._normalizer,name).__code__) for name in (\"lse\",\"close\")) if self._normalizer is not None else ()')
            s=replace(s,'        adaptive_edge_policy.current(self)','        adaptive_edge_policy.current(self)\n        compiled_normalization_policy.current(self)\n        require(self._normalizer is self._normalizer_pin, "normalization backend changed")\n        for name,function,code in self._normalizer_functions:\n            require(getattr(self._normalizer,name) is function and function.__code__ is code, "normalization function changed")',2)
            s=replace(s,'max_operations=max_operations,**adaptive_edge_policy.options(self))','max_operations=max_operations,**adaptive_edge_policy.options(self),**({"normalizer":self._normalizer} if self._normalizer is not None else {}))')
            s += '' # Close remains terminal and drops graph ownership before backend cleanup.
            s=replace(s,'        self.a = self.b = self.config = self.pins = self.identity = None','        self.a = self.b = self.config = self.pins = self.identity = None\n        if self._normalizer is not None:self._normalizer.close()')
        else:
            s=replace(s,'**adaptive_edge_policy.options(self))','**adaptive_edge_policy.options(self),**compiled_normalization_policy.options(self))')
            if name=='batched_pair_executor.py':
                s=replace(s,'            adaptive_edge_policy.current(self)','            adaptive_edge_policy.current(self)\n            compiled_normalization_policy.current(self)')
                s=replace(s,'                    adaptive_edge_policy.join(self,session)','                    adaptive_edge_policy.join(self,session)\n                    compiled_normalization_policy.join(self,session)')
            elif name=='batched_numeric_reuse.py':
                s=replace(s,'        adaptive_edge_policy.join(self,self.executor)','        adaptive_edge_policy.join(self,self.executor)\n        compiled_normalization_policy.join(self,self.executor)')
            elif name=='batched_numeric_execution.py':
                lines=s.splitlines(True);s=''.join(line+(' '* (len(line)-len(line.lstrip()))+'compiled_normalization_policy.join(self,self.memo)\n' if 'adaptive_edge_policy.join(self,self.memo)' in line else '') for line in lines)
                s=replace(s,"        if self._edge_cache_policy is not None:summary['edge_cache_policy']=dict(self._edge_cache_policy)","        if self._edge_cache_policy is not None:summary['edge_cache_policy']=dict(self._edge_cache_policy)\n        if self._compiled_normalization_policy is not None:summary['compiled_normalization_policy']=dict(self._compiled_normalization_policy)")
                s=replace(s,"            if self._edge_cache_policy is not None:binding['edge_cache_policy']=dict(self._edge_cache_policy)","            if self._edge_cache_policy is not None:binding['edge_cache_policy']=dict(self._edge_cache_policy)\n            if self._compiled_normalization_policy is not None:binding['compiled_normalization_policy']=dict(self._compiled_normalization_policy)")
                s=replace(s,"        selected=adaptive_edge_policy.freeze(binding.get('edge_cache_policy'))","        selected=adaptive_edge_policy.freeze(binding.get('edge_cache_policy'))\n        normalization=compiled_normalization_policy.freeze(binding.get('compiled_normalization_policy'))")
                s=replace(s,"            require(adaptive_edge_policy.freeze(s.get('edge_cache_policy'))==selected,'numeric summary adaptive policy differs')","            require(adaptive_edge_policy.freeze(s.get('edge_cache_policy'))==selected,'numeric summary adaptive policy differs')\n            require(compiled_normalization_policy.freeze(s.get('compiled_normalization_policy'))==normalization,'numeric summary normalization policy differs')")
    changes[name]=s
# Wrap accepted backend in a closure; imports and loader are lazy only through open_backend.
s=(OLD/'compiled_small_lse.py').read_text()
s=replace(s,"_PATH=Path(__file__).with_name('reduction.so')","_PATH=Path(library_path)")
s=replace(s,"_EXPECTED='9fd95c85ae9c5572adad1f0c8824d6f52f09762cc06fcb7ad03b17a6cc03e3f2'","_EXPECTED=library_sha256")
s=replace(s,'    global _fn,_fd,_close_error','    nonlocal _fn,_fd,_close_error')
# Entire original body becomes factory-local, including original imported numerical pins.
s='"""Session-owned adaptation of immutable prototype04; no import-time load."""\nfrom types import SimpleNamespace\n\ndef open_backend(library_path,library_sha256):\n'+''.join('    '+line if line.strip() else line for line in s.splitlines(True))+'\n    try:return SimpleNamespace(lse=lse,close=close)\n    except BaseException as primary:\n        try:close()\n        except BaseException as cleanup:primary.add_note("backend construction cleanup: "+repr(cleanup))\n        raise\n'
(OUT/'compiled_small_lse.py').write_text(s)
policy_path=OUT/'compiled_normalization_policy.py'
import re
policy_path.write_text(re.sub(r"HELPER_SHA256 = '[^']+'", "HELPER_SHA256 = '"+hashlib.sha256(s.encode()).hexdigest()+"'", policy_path.read_text(),count=1))
# Source pins must describe executable candidate bytes, never suppress existing guards.
reuse=changes['batched_numeric_reuse.py']
for name,module in [('batched_pair_executor.py','accepted'),('matching_checkpoint.py','engine'),('matching_annealing.py','engine.ann'),('matching_immutable_session.py','immutable_session')]:
    old=hashlib.sha256((SRC/name).read_bytes()).hexdigest();new=hashlib.sha256(changes[name].encode()).hexdigest()
    reuse=replace(reuse,f"({module}, '{old}')",f"({module}, '{new}')")
# Include policy in the existing roster and source guards. Backend is hashed lazily by policy.
reuse=replace(reuse,'immutable_session,adaptive_edge_policy)','immutable_session,adaptive_edge_policy,compiled_normalization_policy)')
policy_sha=hashlib.sha256((OUT/'compiled_normalization_policy.py').read_bytes()).hexdigest()
reuse=replace(reuse,'SOURCE_PINS=(','SOURCE_PINS=(\n    (compiled_normalization_policy, '+repr(policy_sha)+'),')
changes['batched_numeric_reuse.py']=reuse
for name,s in changes.items():
    (OUT/name).write_text(s)
    base=(SRC/name).read_text()
    (OUT/(name+'.patch')).write_text(''.join(difflib.unified_diff(base.splitlines(True),s.splitlines(True),fromfile='baseline_'+name,tofile=name)))
    (OUT/(name+'.inverse.patch')).write_text(''.join(difflib.unified_diff(s.splitlines(True),base.splitlines(True),fromfile=name,tofile='baseline_'+name)))
print('built',len(changes),'candidate module copies and closure helper')
