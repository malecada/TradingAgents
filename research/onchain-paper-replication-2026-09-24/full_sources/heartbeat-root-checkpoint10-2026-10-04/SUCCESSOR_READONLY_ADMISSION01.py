"""Genuine committed admission only; no launch, Owner, checkpoint decode or claim."""
import hashlib,json,os,sys,time
from pathlib import Path
from types import SimpleNamespace
root=Path.cwd();f=root/'research/onchain-paper-replication-2026-09-24/full_sources';c=f/'heartbeat-root-checkpoint10-2026-10-04';cap=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');parent=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-resource-successor-root-launch-20261005-01');q=json.loads((parent/'REQUEST_SOURCE_BOUND_DRAFT01.json').read_bytes());assert q['status']=='DRAFT_NOT_RELEASED' and q['final_review'] is None and q['proofs']['full_recovery'] is None
assert not any(n=='tradingagents' or n.startswith('tradingagents.') for n in sys.modules);begun=time.monotonic();sys.path.insert(0,str(cap))
from tradingagents.research.onchain_replication import job
from tradingagents.research.admission import Admission
args=SimpleNamespace(root=str(cap),registration=q['registration'],experiment=q['identity'],source=q['source']);ad,j=job._admitted(args)
assert type(ad)is Admission and ad.ready and ad.source==ad.design_source==q['source'] and ad.bindings is None and ad.bindings_sha256 is None
assert ad.experiment['source_files']==q['source_files'] and {k:v['sha256'] for k,v in ad.inputs.items()}==q['input_hashes'] and len(ad.inputs)==34 and ad.effective_attempt_budget==20
assert not any(n in sys.modules for n in ('numpy','torch','scipy','pandas'))
for p in (cap/'research_runs'/q['identity'],job._base(args),parent/'attempt'):assert not os.path.lexists(p)
record={'schema_version':1,'decision':'genuine-readonly-admission-passed-not-release','identity':q['identity'],'source':ad.source,'design_source':ad.design_source,'registration_sha256':ad.registration_sha256,'source_count':len(ad.experiment['source_files']),'input_count':len(ad.inputs),'effective_attempt_budget':ad.effective_attempt_budget,'actual_admission_type':str(type(ad)),'monitor_owner':None,'scientific_owner':None,'bindings':ad.bindings,'bindings_sha256':ad.bindings_sha256,'numerical_imports':[],'lifecycle_claim_created':False,'elapsed_seconds':time.monotonic()-begun,'namespace_absent':True,'qualification':'fresh genuine Admission, actual pinned runtime/source/input checks; full external preclaim and release remain separate'}
with (c/'SUCCESSOR_READONLY_ADMISSION01.json').open('x') as w:json.dump(record,w,sort_keys=True,indent=2);w.write('\n')
print(json.dumps(record,sort_keys=True))
