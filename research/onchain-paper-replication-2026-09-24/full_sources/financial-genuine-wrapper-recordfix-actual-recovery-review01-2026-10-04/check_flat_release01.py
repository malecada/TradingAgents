import hashlib,importlib.util,json,os,shutil,sys
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;P=F/'financial-genuine-wrapper-root-recordfix-flat01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(x,m):
 assert x,m
 checks.append(m)
ck(sha((P/'restore01.py').read_bytes())=='b5c775a24e19c97cf0ef032a7598347689b8dfc27de5e273bccbe5710d9d519d','accepted exact flat source')
sys.path.insert(0,str(P));sp=importlib.util.spec_from_file_location('exact_flat_release',P/'restore01.py');C=importlib.util.module_from_spec(sp);sp.loader.exec_module(C);R=C.R
raw=R.read(P,'REQUEST_PROPOSAL01.json');ck(sha(raw)=='03e5b088ff1706c2caee65bab7639cc70aa2d4e1d6128bb3a36fc84fed4c8348','actual proposal exactpin');q=json.loads(raw);ck(q['release'] is None and R.encode(q)==raw,'canonical unexecuted flat request')
contract=R.digest(R.encode({k:v for k,v in q.items() if k!='release'}));ck(contract=='d8ca6aa59ca6bc6c5c1005cc02ed49b96d3df38b1bc93a7e08e0a1634557424e','exact actual flat request contract')
remote=Path(q['remote_root']);ck(remote==F/'financial-genuine-wrapper-root-recordfix-remote01-2026-10-04' and q['remote_receipt_sha256']=='0eec2d133f35af75fa6b5c17b16d7f0de24ec1756d957361ea425fd7ddf0d083','exact original actual remote')
review=C.ref(q['review']);rv=json.loads(review);ck(sha(review)=='d51dcd8a756fb70b7efc705ce9b59f7354589ed583e6eca0757247addbe291fe' and rv['flat_source_sha256']==sha(R.read(P,'restore01.py')) and rv['flat_verdict']=='ACCEPTED_SOURCE_ONLY_PENDING_ACTUAL_REMOTE_AND_RELEASE','actual flat-only review authority; historical remote01 remains withheld')
actual=json.loads(R.read(O,'REMOTE_READBACK01.json'));ck(actual['decision']=='ACCEPTED_ACTUAL_RECORDFIX_REMOTE_RECOVERY_PENDING_FRESH_FLAT' and actual['receipt_sha256']==q['remote_receipt_sha256'],'genuine independent actual remote acceptance')
bundle,bodies,receipt=C.remote_bodies(remote,q['remote_receipt_sha256']);m,a,t=C.joins(bodies);ck(len(bodies)==6 and len(m['members'])==986 and a['tracked']==325 and a['selected']==324 and len(a['role_hashes'])==8,'actual received sixbody pins/full986/325324/eightroles')
ck(all(not os.path.lexists(P/n) for n in ['INTENT01.json','flat-source01','RECOVERY01.json','FAILED01.json']),'all original flat namespace absent');free=shutil.disk_usage(P).free;ck(free>=R.FLOOR,'actual observed10GiB floor')
release={'decision':'accepted-exact-recordfix-flat-recovery','source':C.SOURCE,'helper_sha256':sha(R.read(P,'restore01.py')),'request_sha256':contract,'review_sha256':sha(review)}
R.put(O/'FLAT_RELEASE01.json',release);bound=dict(q,release={'path':str(O/'FLAT_RELEASE01.json'),'sha256':R.digest(R.encode(release))});ck(C.validate_request(bound)==remote,'genuine fivefield independent release accepted by actual validator')
ck(all(not os.path.lexists(P/n) for n in ['INTENT01.json','flat-source01','RECOVERY01.json','FAILED01.json']),'no actual flat executed');ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports')
out={'schema_version':1,'decision':'ACCEPTED_EXACT_ONE_USE_RECORDFIX_FLAT_REQUEST','checks':len(checks),'proposal_sha256':sha(raw),'contract_sha256':contract,'release_sha256':R.digest(R.encode(release)),'source':C.SOURCE,'flat_helper_sha256':release['helper_sha256'],'actual_remote_receipt_sha256':q['remote_receipt_sha256'],'actual_remote_review_sha256':sha(R.read(O,'REMOTE_READBACK01.json')),'original_flat_source_review_sha256':sha(review),'observed_disk_free_bytes':free,'actual_flat_executed':False,'native_or_numerical_authority':False}
R.put(O/'FLAT_RELEASE_READBACK01.json',out);print(json.dumps(out,indent=2))
