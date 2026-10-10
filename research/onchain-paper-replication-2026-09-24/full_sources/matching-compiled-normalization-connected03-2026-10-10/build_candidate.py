from pathlib import Path
import hashlib,difflib,re
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'matching-compiled-normalization-connected02-2026-10-10'
NAMES=['matching_annealing.py','matching_checkpoint.py','matching_immutable_session.py','batched_pair_executor.py','batched_numeric_reuse.py','batched_numeric_execution.py','compiled_normalization_policy.py','compiled_small_lse.py']
source={name:(OLD/name).read_text() for name in NAMES}
def change(s,a,b,count=1):
    assert s.count(a)==count,(a,s.count(a),count)
    return s.replace(a,b)
# Add read-only currentness capability; accepted numerical/loader/close bodies
# are unchanged. No unloading function or global owner is introduced.
s=source['compiled_small_lse.py']
s=change(s,'    try:return SimpleNamespace(lse=lse,close=close)', '''    def loaded():
        return _ORIGINAL_FN is not None
    def current():
        return (_fn is _ORIGINAL_FN and (_fn is None or
            (_fn.argtypes==_ARGS and _fn.restype is ctypes.c_int and _live()))
            and _original.__code__ is _CODE
            and (np.geterr,np.isfinite,np.abs,np.all,np.empty,np.ndarray)==_NP_PINS)
    try:return SimpleNamespace(lse=lse,close=close,current=current,loaded=loaded)''')
source['compiled_small_lse.py']=s
# Reuse EXACT existing fresh source/runtime/helper checks on every lease.
s=source['compiled_normalization_policy.py']
s=change(s,'def read_reference(path,expected,limit,exact_size=None):','def read_reference(path,expected,limit,exact_size=None,*,owned=False):')
s=change(s,'        before=os.fstat(fd)','        before=os.fstat(fd)\n        if owned:require(before.st_uid==os.getuid(),\"library reference owner differs\")')
s=change(s,'def open_backend(owner):','def _backend_references(owner):')
needle="    return compiled_small_lse.open_backend(p['library_path'],p['library_sha256'])"
s=change(s,needle,"    return p,compiled_small_lse\n\ndef open_backend(owner):\n    references=_backend_references(owner)\n    if references is None:return None\n    p,helper=references\n    return helper.open_backend(p['library_path'],p['library_sha256'])")
s=re.sub(r"HELPER_SHA256 = '[^']+'","HELPER_SHA256 = '"+hashlib.sha256(source['compiled_small_lse.py'].encode()).hexdigest()+"'",s,count=1)
s+=(HERE/'backend_owner.fragment').read_text();source['compiled_normalization_policy.py']=s
# Direct standalone sessions retain02 ownership. Borrowing uses02's original
# independent terminal release closure and checks lease validity at boundaries.
s=source['matching_immutable_session.py']
s=change(s,'compiled_normalization_policy_value=None):','compiled_normalization_policy_value=None,_normalization_owner=None):')
s=change(s,'normalizer = compiled_normalization_policy.open_backend(self)','normalizer = compiled_normalization_policy.open_backend(self) if _normalization_owner is None else _normalization_owner.borrow(self)')
s=change(s,'for name in ("lse","close")) if normalizer is not None else ()','for name in (("lse","close") if _normalization_owner is None else ("lse","close","current"))) if normalizer is not None else ()')
needle='            require(getattr(self._normalizer,name) is function and function.__code__ is code, "normalization function changed")'
s=change(s,needle,needle+'\n        if len(self._normalizer_functions)==3:self._normalizer_functions[2][1]()',count=2)
source['matching_immutable_session.py']=s
# PairExecutor owns the pool, so one NumericReuse lifetime owns one backend.
s=source['batched_pair_executor.py']
needle="        if schedule['max_checkpoints']>policy['max_publications']:raise ValueError('checkpoint count exceeds policy')"
s=change(s,needle,needle+'''
        self.closed=False
        self._normalization_owner=(compiled_normalization_policy.BackendOwner(dict(self._compiled_normalization_policy))
            if self._compiled_normalization_policy is not None else None)
        self._normalization_owner_pin=self._normalization_owner
        self._normalization_cleanup=self._normalization_owner.close if self._normalization_owner is not None else lambda:None
    def close(self):
        self.closed=True
        self._normalization_cleanup()
''')
s=change(s,"        if self.poisoned:raise ValueError('executor poisoned')","        if self.poisoned or self.closed:raise ValueError('executor poisoned or closed')")
needle='            compiled_normalization_policy.current(self)'
s=change(s,needle,needle+'''
            if self._normalization_owner is not self._normalization_owner_pin:raise ValueError('normalization owner replaced')
            if self._normalization_owner is not None:self._normalization_owner.current()''')
needle='**compiled_normalization_policy.options(self))'
s=change(s,needle,'**compiled_normalization_policy.options(self),**({"_normalization_owner":self._normalization_owner} if self._normalization_owner is not None else {}))')
needle='            if primary is None and cleanup_error is not None:raise cleanup_error'
s=change(s,needle,'''            if self.poisoned:
                self.closed=True
                try:self._normalization_cleanup()
                except BaseException as cleanup:
                    if primary is not None:
                        try:BaseException.add_note(primary,'executor backend cleanup failed: '+repr(cleanup))
                        except BaseException:pass
                    elif cleanup_error is None:cleanup_error=cleanup
                    else:
                        try:BaseException.add_note(cleanup_error,'additional backend cleanup failed: '+repr(cleanup))
                        except BaseException:pass
            if primary is None and cleanup_error is not None:raise cleanup_error''')
source['batched_pair_executor.py']=s
# Capture the originally created executor close before numeric cache allocation;
# no backend can be acquired during this constructor. Connect both poison and
# normal close independently of cache clearing/end_batch failures.
s=source['batched_numeric_reuse.py']
needle='        self.checkpoint_adapter=self.executor.checkpoint'
s=change(s,needle,'        self._executor_pin=self.executor;self._executor_cleanup=self.executor.close\n'+needle)
needle='        adaptive_edge_policy.join(self,self.executor)'
s=change(s,needle,"        require(self.executor is self._executor_pin,'numeric executor replaced')\n"+needle)
needle='''        if self._geometry is not None:self._geometry.poison();self.last_geometry_summary=None
        self.poisoned=True;self.executor.poisoned=True;self.active=False;self._clear();self.last_receipt=None'''
s=change(s,needle,'''        primary=sys.exception()
        try:
            if self._geometry is not None:self._geometry.poison();self.last_geometry_summary=None
            self.poisoned=True;self._executor_pin.poisoned=True;self.active=False;self._clear();self.last_receipt=None
        except BaseException as error:
            if primary is None:primary=error
            elif error is not primary:
                try:BaseException.add_note(primary,'numeric poison cleanup failed: '+repr(error))
                except BaseException:pass
            raise primary
        finally:
            try:self._executor_cleanup()
            except BaseException as cleanup:
                if primary is None:raise
                try:BaseException.add_note(primary,'numeric backend cleanup failed: '+repr(cleanup))
                except BaseException:pass''')
needle='''        try:
            if self.active and not self.poisoned:self.end_batch()
        finally:self._clear();self.last_receipt=None;self.closed=True'''
s=change(s,needle,'''        primary=None
        try:
            if self.active and not self.poisoned:self.end_batch()
        except BaseException as error:
            primary=error;raise
        finally:
            cleanup_error=None
            try:self._clear()
            except BaseException as cleanup:cleanup_error=cleanup
            self.last_receipt=None;self.closed=True
            try:self._executor_cleanup()
            except BaseException as cleanup:
                if cleanup_error is None:cleanup_error=cleanup
                else:
                    try:BaseException.add_note(cleanup_error,'additional backend cleanup failed: '+repr(cleanup))
                    except BaseException:pass
            if cleanup_error is not None:
                if primary is None:raise cleanup_error
                try:BaseException.add_note(primary,'numeric close cleanup failed: '+repr(cleanup_error))
                except BaseException:pass''')
for name in ('compiled_normalization_policy.py','batched_pair_executor.py','matching_immutable_session.py'):
    old=hashlib.sha256((OLD/name).read_bytes()).hexdigest();new=hashlib.sha256(source[name].encode()).hexdigest()
    s=change(s,old,new)
source['batched_numeric_reuse.py']=s
for name,body in source.items():
    (HERE/name).write_text(body)
    old=(OLD/name).read_text()
    (HERE/(name+'.from02.patch')).write_text(''.join(difflib.unified_diff(old.splitlines(True),body.splitlines(True),fromfile=name+'-02',tofile=name+'-03')))
    (HERE/(name+'.to02.inverse.patch')).write_text(''.join(difflib.unified_diff(body.splitlines(True),old.splitlines(True),fromfile=name+'-03',tofile=name+'-02')))
print('candidate03 generated')
