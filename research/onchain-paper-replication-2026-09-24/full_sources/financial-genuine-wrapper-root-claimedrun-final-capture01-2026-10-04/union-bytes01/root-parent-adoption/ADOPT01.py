import copy,hashlib,json,os,sys
from pathlib import Path
M=Path.cwd();B=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=B/'financial-genuine-wrapper-root-claimedrun-parent-adoption01-2026-10-04'
A=B/'financial-genuine-wrapper-claimedrun-parent-preparation01-2026-10-04';V=B/'financial-genuine-wrapper-claimedrun-parent-review01-2026-10-04'
P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-root-launch-20261004-01')
sys.path.insert(0,str(B/'held-consumer-final-recovery-preparation04-2026-10-03'));import recovery04 as R
assert not os.path.lexists(D) and not os.path.lexists(P);assert R.digest(R.read(A,'MANIFEST01.json'))=='9c29f83031acde0e8c4794ca162756b481416d34711bd3770e7327ca4d2436cb'
assert R.digest(R.read(V,'MANIFEST01.json'))=='034d5977ba0327a425fb4d99ebf7deda3fec78ab55ff1fd7a971c2cf9ec34f71'
raw=R.read(A,'REQUEST_TEMPLATE01.json');q=json.loads(raw);assert q['caller_sha256']=='5d5cbdae455c62c3e66b53208b0f79e6e5bbc7ce05d3ded77126da5e0692deda'and q['proofs']['full_recovery'] is None and q['final_review'] is None
proof=B/'financial-genuine-wrapper-claimedrun-actual-admission-review01-2026-10-04';ad=R.read(proof,'INDEPENDENT_SOURCE_INPUT_RUNTIME01.json');assert R.digest(ad)=='059232d0f7fc8922cee526a1bd30fef2ecb51ee17103284bcaac18c77e77641c'
N=Path(q['capsule_root']);cumulative=R.read(N,'fixture_inputs/financial_wrapper_claimedrun01/extension-review19.json');assert R.digest(cumulative)=='3268b76971e4e721222707d16d25dfe84e94104779931e647fb4d7a2bf01202e'
D.mkdir(mode=0o700);P.mkdir(mode=0o700);(D/'ADOPT01.py').write_bytes(Path(__file__).read_bytes());(P/'proofs').mkdir(mode=0o700)
def save(p,body):
 with R.new_file(p) as fd:
  offset=0
  while offset<len(body):n=os.write(fd,body[offset:]);assert n>0;offset+=n
  os.fsync(fd)
 assert R.read(p.parent,p.name)==body
save(P/'parent01.py',R.read(A,'parent01.py'));assert R.digest(R.read(P,'parent01.py'))==q['caller_sha256']
for name,pin in q['helper_hashes'].items():
 body=R.read(A,name);assert R.digest(body)==pin;save(P/name,body)
for role,name,body in [('cumulative','CUMULATIVE19_REVIEW01.json',cumulative),('independent_source_input_runtime','INDEPENDENT_SOURCE_INPUT_RUNTIME01.json',ad)]:
 save(P/'proofs'/name,body);q['proofs'][role]={'path':str(P/'proofs'/name),'sha256':R.digest(body)}
save(P/'REQUEST_DRAFT01.json',R.encode(q))
assert q['proofs']['full_recovery'] is None and q['final_review'] is None and q['status']!='RELEASED_ONE_USE_FINANCIAL_PARENT'
assert not os.path.lexists(P/'attempt') and not os.path.lexists(N/'research_runs'/q['identity'])
R.put(D/'ADOPTION01.json',{'status':'ACTUAL_INSTALLED_NEW_PARENT_DRAFT_NOT_RELEASED','parent_root':str(P),'source':q['source'],'identity':q['identity'],'caller_sha256':q['caller_sha256'],'helpers':q['helper_hashes'],'request_sha256':R.digest(R.encode(q)),'actual_genuine_metadata_proof_sha256':R.digest(ad),'genuine_cumulative_review_sha256':R.digest(cumulative),'full_new_source_recovery':None,'exact_final_review':None,'whole_parent_manifest':R.scan(P),'new_admission_rerun':False,'new_claim':False,'numerical_launched':False,'scope':'Root actual immutable one-use parent/helper and two genuine accepted proof-body installation. Draft remains refused until actual full Source339 recovery and different-author exact request release, final complete caller/review preservation/recovery and fresh native eligibility.'})
print(json.dumps({'parent_installed':str(P),'request_sha256':R.digest(R.encode(q)),'actual_new_claim':False,'release':False}))
