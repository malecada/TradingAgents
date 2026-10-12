from pathlib import Path
import os,resource,runpy,types
os.sched_setaffinity(0,{2,3});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
from contextlib import contextmanager
C=Path('research/onchain-paper-replication-2026-09-24/full_sources/pilot-typed-offload-target-poll-candidate-2026-10-12');ns=runpy.run_path(str(C/'check01.py'));N=types.SimpleNamespace
class BrokenPublication(BaseException):
 def __repr__(self):raise SystemExit('repr interruption')
primary=KeyboardInterrupt('primary');context=N(_cap='parent',_failed=False);ledger=N(_poisoned=False);owner=N(poisoned=False,_archive_operations=ledger)
op=N(context=context,parent='parent',closed=False,sha='a',lease=lambda:(_ for _ in ()).throw(primary),_publish=lambda *a:(_ for _ in ()).throw(BrokenPublication()))
def construct(*a,**kw):context._cap='child';return op
env={'contextmanager':contextmanager,'require':ns['require'],'_Operation':construct};ns['load'](C/'typed_payload_operations.py',{'operation'},env)
try:
 with env['operation'](owner,object(),kind='x',binding={},payload_bytes=1,chunk_count=1,target=object()):raise AssertionError('yielded')
except KeyboardInterrupt as e:assert e is primary
else:raise AssertionError('lost primary')
assert owner.poisoned and ledger._poisoned and context._failed and context._cap=='parent' and op.closed
print('PASS: publication error repr failure preserves primary, poison and parent capability cleanup')
