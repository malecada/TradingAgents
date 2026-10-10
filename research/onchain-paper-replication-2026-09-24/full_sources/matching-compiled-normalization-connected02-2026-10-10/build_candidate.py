from pathlib import Path
import hashlib,difflib
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'matching-compiled-normalization-connected01-2026-10-10'
names=['matching_annealing.py','matching_checkpoint.py','matching_immutable_session.py','batched_pair_executor.py','batched_numeric_reuse.py','batched_numeric_execution.py']
for name in names+['compiled_normalization_policy.py','compiled_small_lse.py']:
    (HERE/name).write_bytes((OLD/name).read_bytes())
for name in names:
    (HERE/('baseline_'+name)).write_bytes((OLD/('baseline_'+name)).read_bytes())
original=(OLD/'matching_immutable_session.py').read_text()
needle='''        self._normalizer = compiled_normalization_policy.open_backend(self)
        self._normalizer_pin = self._normalizer
        self._normalizer_functions = tuple((name,getattr(self._normalizer,name),getattr(self._normalizer,name).__code__) for name in ("lse","close")) if self._normalizer is not None else ()'''
replacement='''        # Allocate the terminal cleanup closure before acquiring any backend.
        # Its original capability is independent of the checked mutable attrs.
        owned_close = None
        close_attempted = False
        close_error = None
        def owned_cleanup():
            nonlocal close_attempted, close_error
            if close_error is not None:raise close_error
            if close_attempted:return
            close_attempted = True
            if owned_close is not None:
                try:owned_close()
                except BaseException as error:
                    close_error = error
                    raise
        self._normalizer_cleanup = owned_cleanup
        normalizer = None
        try:
            normalizer = compiled_normalization_policy.open_backend(self)
            owned_close = normalizer.close if normalizer is not None else None
            self._normalizer = normalizer
            self._normalizer_pin = normalizer
            self._normalizer_functions = tuple((name,getattr(normalizer,name),getattr(normalizer,name).__code__) for name in ("lse","close")) if normalizer is not None else ()
        except BaseException as primary:
            # Until this constructor returns, the executor has no session to
            # close. Attempt acquired cleanup here, retaining the primary error.
            try:
                if normalizer is not None and owned_close is None:owned_close = normalizer.close
                owned_cleanup()
            except BaseException as cleanup:
                try:BaseException.add_note(primary, 'session construction cleanup failed: '+repr(cleanup))
                except BaseException:pass
            raise'''
assert original.count(needle)==1
s=original.replace(needle,replacement)
needle='''        self.closed = True
        self.a = self.b = self.config = self.pins = self.identity = None
        if self._normalizer is not None:self._normalizer.close()'''
replacement='''        cleanup = self._normalizer_cleanup
        try:
            self.closed = True
            self.a = self.b = self.config = self.pins = self.identity = None
        except BaseException as primary:
            try:cleanup()
            except BaseException as error:
                try:BaseException.add_note(primary, 'session close cleanup failed: '+repr(error))
                except BaseException:pass
            raise
        else:cleanup()'''
assert s.count(needle)==1
s=s.replace(needle,replacement)
(HERE/'matching_immutable_session.py').write_text(s)
# Mandatory source-guard maintenance only; all reuse execution remains identical.
a=hashlib.sha256(original.encode()).hexdigest();b=hashlib.sha256(s.encode()).hexdigest()
p=HERE/'batched_numeric_reuse.py';reuse=p.read_text();assert reuse.count(a)==1;p.write_text(reuse.replace(a,b))
for name in names:
    body=(HERE/name).read_text();base=(HERE/('baseline_'+name)).read_text();prior=(OLD/name).read_text()
    for label,before,after in [('patch',base,body),('inverse.patch',body,base),('from01.patch',prior,body),('to01.inverse.patch',body,prior)]:
        (HERE/(name+'.'+label)).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=name+'-before',tofile=name+'-after')))
print('only session constructor/close and dependent source hash changed')
