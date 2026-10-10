from pathlib import Path
import hashlib,difflib,resource,signal
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(10,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(10)
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'matching-compiled-normalization-connected03-2026-10-10'
NAMES=('compiled_normalization_policy.py','compiled_small_lse.py','matching_immutable_session.py','batched_pair_executor.py','batched_numeric_reuse.py','matching_annealing.py','matching_checkpoint.py','batched_numeric_execution.py')
source={n:(OLD/n).read_text() for n in NAMES}
s=source['batched_pair_executor.py']
a="                    if primary is not None:primary.add_note('executor cleanup failed: '+repr(cleanup))"
b="""                    if primary is not None:
                        try:BaseException.add_note(primary,'executor cleanup failed: '+repr(cleanup))
                        except BaseException:pass"""
assert s.count(a)==1;s=s.replace(a,b)
a="                    else:cleanup_error.add_note('additional executor cleanup failed: '+repr(cleanup))"
b="""                    else:
                        try:BaseException.add_note(cleanup_error,'additional executor cleanup failed: '+repr(cleanup))
                        except BaseException:pass"""
assert s.count(a)==1;s=s.replace(a,b);source['batched_pair_executor.py']=s
old=hashlib.sha256((OLD/'batched_pair_executor.py').read_bytes()).hexdigest();new=hashlib.sha256(s.encode()).hexdigest()
s=source['batched_numeric_reuse.py'];assert s.count(old)==1;source['batched_numeric_reuse.py']=s.replace(old,new)
for name,body in source.items():
 (HERE/name).write_text(body);old=(OLD/name).read_text()
 for suffix,left,right in (('.from03.patch',old,body),('.to03.inverse.patch',body,old)):
  (HERE/(name+suffix)).write_text(''.join(difflib.unified_diff(left.splitlines(True),right.splitlines(True),fromfile=name,tofile=name)))
