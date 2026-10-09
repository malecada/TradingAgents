from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;F=H.parent;R=Path.cwd();A=F/'mcm-immutable-pair-executor01-2026-10-09';old=F/'mcm-batched-execution03-2026-10-09/pair_executor.py';candidate=A/'pair_executor.py'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=candidate.read_text()
s=s.replace('from tradingagents.research.onchain_replication import matching_annealing as annealing\nfrom tradingagents.research.onchain_replication.matching_immutable_session import ImmutablePairSession\n\nEXECUTION_ROUTE = "immutable-input-session-v1"\n','')
s=s.replace('state=None;session=None;primary=None','state=None;primary=None')
s=s.replace('            session=ImmutablePairSession(a,b,self.config,engine=engine,annealing=annealing)\n','')
s=s.replace("session.advance(state,max_operations=self.schedule['operations_per_call'])","engine.advance(state,a,b,self.config,max_operations=self.schedule['operations_per_call'])")
s=s.replace('            if session is not None:session.close()\n','')
assert s==old.read_text()
files=[candidate,A/'MANIFEST01.json',A/'RESULT01.json',old,F/'matching-immutable-session-review02-2026-10-09/SOURCE_REVIEW01.json',R/'tradingagents/research/onchain_replication/matching_immutable_session.py',R/'tradingagents/research/onchain_replication/matching_annealing.py',R/'tradingagents/research/onchain_replication/matching_checkpoint.py',H/'reproduce.py',H/'TEST01.log',H/'RESULT01.json']
result={'decision':'withheld','scope':'source-only changed executor seam','literal_inverse':True,'finding':'unguarded session.close masks primary exception and skips engine.close(state)','failure_injection_scope':'A real checkpoint callback installs a throwing session.close. This proves exception robustness failure; it does not assert ordinary frozen close naturally raises.','required_fix':'Attempt session and engine cleanup independently; preserve existing primary and append cleanup notes; if no primary, poison and raise cleanup failure after attempting state cleanup.','inherited_numeric_and_session_proof':True,'actual_author_validation_counts':[12,0],'genuine_authority_or_empirical_execution':False,'evidence':{str(p.relative_to(R)):sha(p) for p in files}}
(H/'WITHHELD01.json').write_text(json.dumps(result,indent=2)+'\n');print(sha(H/'WITHHELD01.json'))
