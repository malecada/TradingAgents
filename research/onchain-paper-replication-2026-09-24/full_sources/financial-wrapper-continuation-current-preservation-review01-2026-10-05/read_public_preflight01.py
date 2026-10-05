"""Read actual Root failures; no Parent/preclaim invocation or numerical import."""
from pathlib import Path
import sys, os, json
H=Path(__file__).resolve().parent;F=H.parent
sys.path.insert(0,str(F/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05'))
from verify_capture01 import Reader,R
rd=Reader();C=F/'heartbeat-root-checkpoint10-2026-10-04';P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-compatibility-root-launch-20261005-01')
refs={}
for n in ('CONTINUATION_PUBLIC_PREFLIGHT01_FAILED.json','CONTINUATION_PUBLIC_PREFLIGHT02_FAILED.json','CONTINUATION_PUBLIC_PREFLIGHT02.stderr.txt'):
 raw=rd.read(C/n);refs[n]={'path':str(C/n),'sha256':R.digest(raw)}
 with R.new_file(H/('ACTUAL_'+n)) as fd:
  offset=0
  while offset<len(raw):
   written=os.write(fd,raw[offset:]);rd.need(written>0,'literal actual evidence write');offset+=written
  os.fsync(fd)
one=json.loads(rd.read(C/'CONTINUATION_PUBLIC_PREFLIGHT01_FAILED.json'));two=json.loads(rd.read(C/'CONTINUATION_PUBLIC_PREFLIGHT02_FAILED.json'));stderr=rd.read(C/'CONTINUATION_PUBLIC_PREFLIGHT02.stderr.txt').decode()
rd.need(one['actual_root_exit']==two['actual_root_exit']==1 and one['before_PRECLAIM_validate'] is True,'two actual failed Root read-only entries')
rd.need(two['error']=='exact historical alias linkage differs' and two['reader_bytes'] is None and not two['numerical_claim_spent'],'actual unresolved predicate and unknown bytes')
rd.need('exact historical alias linkage differs' in stderr and '_historical' in stderr and '318' in stderr,'raw actual traceback joins recorded failure')
raw=rd.read(P/'REQUEST_FINAL01.json','c00ce9b4a9410d6045baf957030431f2ef3851ac84fb43436d0e2e013c9cfe63');rd.need(raw==rd.read(P/'REQUEST_RELEASED01.json'),'canonical filename is literal same bytes')
q=json.loads(raw);draft=json.loads(rd.read(P/'REQUEST_FINAL_REVIEW_DRAFT01.json','a794aa04070a43a0d738cff1ec9a0fe91ff0d18c095a7f93ff2576ede7ac71ba'))
review={'path':str(H/'FINAL_PARENT_RELEASE01.json'),'sha256':'d4b0238e30d5fd864dd9d27f753d8edc25b9c05ba4ec4cadb940d83100bb8149'}
rd.need(q==dict(draft,final_review=review),'actual canonical request only binds genuine accepted final review')
rd.read(Path(review['path']),review['sha256'])
rd.read(P/'parent01.py',q['caller_sha256']);preclaim=rd.read(P/'preclaim01.py',q['helper_hashes']['preclaim01.py']).decode()
rd.need("require(prior[descriptor]==hist[key],'exact historical alias linkage differs')" in preclaim,'actual pinned refusal predicate')
cap=Path(q['capsule_root']);identity=q['identity'];paths=[P/'attempt',cap/'research_runs'/identity,cap/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/identity]
rd.need(all(not os.path.lexists(p) for p in paths),'actual unspent namespaces remain absent')
rd.finish()
result={'schema_version':1,'status':'FAILED_PUBLIC_PREFLIGHT_NUMERICAL_ENTRY_WITHHELD','actual_attempts':[one,two],'actual_refs':refs,'canonical_request_sha256':R.digest(raw),'final_review':review,'actual_bound_release_unchanged':True,'actual_failure_location':'preclaim01.py:318 in _historical','unresolved_predicate':'prior[descriptor] == policy[historical][key] for exact historical aliases','actual_namespace_absence':[str(p) for p in paths],'reader_bytes':None,'preflight_rerun_by_reviewer':False,'numerical_entry_released':False,'source_or_policy_correction':None,'checks':rd.checks,'read_bytes':rd.total}
R.put(H/'PUBLIC_PREFLIGHT_READBACK01.json',result)
print(json.dumps({'status':result['status'],'sha256':R.digest(R.encode(result)),'checks':rd.checks}))
