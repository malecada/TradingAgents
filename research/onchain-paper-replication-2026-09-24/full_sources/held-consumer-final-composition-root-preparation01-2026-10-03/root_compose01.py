from pathlib import Path
import hashlib,json,os,stat
from datetime import datetime,timezone
B=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes/research/onchain-paper-replication-2026-09-24/full_sources');D=B/'held-consumer-final-composition-root-preparation01-2026-10-03';P=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-root-launch-20261003-01');A=B/'held-consumer-one-use-parent-preparation03-2026-10-03';V=B/'held-consumer-one-use-parent-review03-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest()
assert H((A/'launch_success01.py').read_bytes())=='7a197e2f57db3fff44fce453356d187f62dce5f119125e6814831eb6008f38dc';assert H((V/'MANIFEST03.json').read_bytes())=='e139bb9addee67043b74d6d2970e58cf75f3c5c390706ec68571fff16f981dee';assert H((V/'REVIEW03.md').read_bytes())=='c176c462509e279a325c4557023f41e18710e95dc4f951908b7ce1faaa078b77';assert not os.path.lexists(P)
P.mkdir(mode=0o700);(P/'proofs').mkdir(mode=0o700);(P/'source-review').mkdir(mode=0o700)
selected={'launch_success01.py':A/'launch_success01.py','held_outcome02.py':A/'held_outcome02.py','release-unreleased01.json':A/'release-unreleased01.json','request-unreleased01.json':A/'REQUEST_TEMPLATE03.json','source-review/PARENT_PROTOCOL03.md':A/'PROTOCOL03.md','source-review/PARENT_MANIFEST03.json':A/'MANIFEST03.json','source-review/PARENT_REVIEW03.md':V/'REVIEW03.md','source-review/PARENT_REVIEW_MANIFEST03.json':V/'MANIFEST03.json','proofs/RELEASE_REVIEW_TEMPLATE01.json':A/'RELEASE_REVIEW_TEMPLATE01.json','proofs/RECOVERY_REVIEW_TEMPLATE01.json':A/'RECOVERY_REVIEW_TEMPLATE01.json'}
rows=[]
for name,origin in sorted(selected.items()):
 s=origin.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304;raw=origin.read_bytes();out=P/name;fd=os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,stat.S_IMODE(s.st_mode))
 try:
  offset=0
  while offset<len(raw):n=os.write(fd,raw[offset:]);assert n>0;offset+=n
  os.fsync(fd)
 finally:os.close(fd)
 assert out.read_bytes()==raw;rows.append({'path':name,'original_path':str(origin),'sha256':H(raw),'bytes':len(raw),'mode':stat.S_IMODE(out.lstat().st_mode)})
for path in (P/'proofs',P/'source-review',P,P.parent):
 fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:os.fsync(fd)
 finally:os.close(fd)
assert not os.path.lexists(P/'attempt')
receipt={'schema_version':1,'observed_utc':datetime.now(timezone.utc).isoformat(),'status':'actual-parent-source-composed-unreleased','actual_parent_root':str(P),'caller_sha256':H((P/'launch_success01.py').read_bytes()),'semantic_parser_sha256':H((P/'held_outcome02.py').read_bytes()),'parent_source_review_sha256':H((P/'source-review/PARENT_REVIEW03.md').read_bytes()),'copied_members':rows,'actual_member_body_equality':True,'source_review_scope':'exact source03 only; actual composite not independently accepted yet','release_status':'UNRELEASED-native-engineering','remaining':['independent exact actual composition/baseline scope review','freeze native contract and obtain genuine independent execution review','complete actual external baseline+laterproof recovery','separate fresh recovered Git objectstore/source/history proof','review exact final request/envelope and check fresh native eligibility before one success'],'actual_attempt_namespace_created':False,'genuine_admission_invoked':False,'native_started':False,'external_baseline_recovery':False,'research_authority':False}
(D/'ACTUAL_PARENT_COMPOSITION01.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n');print('Actual unreleased parent source copied',len(rows),'caller',receipt['caller_sha256'],'no attempt namespace')
