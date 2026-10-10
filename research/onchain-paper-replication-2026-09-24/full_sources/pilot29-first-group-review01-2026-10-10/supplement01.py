import resource
resource.setrlimit(resource.RLIMIT_AS,(384*1024**2,384*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent;F=P.parent;R=P.parents[3];a=json.loads((P/'REVIEW01.json').read_bytes());inv=a['inventory']; checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def ck(v,n):
 assert v,n
 checks.append(n)
def body(suffix):
 matches=[v for k,v in inv.items() if k.endswith(suffix)];assert len(matches)==1,suffix
 return (P/matches[0]['copy']).read_bytes()
owner=body('/owner.json');ck(sha(owner)==a['owner'],'actual original owner canonical body hash')
prior=body('pilot29-first-batch-metadata-review01-2026-10-10/REVIEW01.json');ck(sha(prior)=='bc9e5a1b8f3768d7d9e315fe99bdccdde89647104c04abb97fba5f83a279e838','external accepted first batch review hash')
manifest=json.loads(body('pilot29-first-batch-metadata-review01-2026-10-10/MANIFEST01.json'));ck(manifest['files']['REVIEW01.json']['sha256']==sha(prior),'prior manifest exact review join')
ck(sha(body('real-data-pilot-full29-entry01-2026-10-09/gate04.json'))=='f6be8198d971451eea91647bf853de036b82405ffcb70e18db61ef204e76c898','external original gate hash')
claimpath=R/'research_runs/eth-paper-real-data-end-to-end-resource-20261009-29/claim.json';claim=claimpath.read_bytes();ck(len(claim)<256*1024 and sha(claim)=='5b81c3cb892f75a0b1505bb08049c5cc985b4dd43f01e38899c8f7abf54c2504','actual claim retained unchanged')
(P/'claim-snapshot.json').write_bytes(claim)
r=json.loads(body('/offload.json'))['receipt'];p=json.loads(prior)
for i,suffix in enumerate(('.pending.json','.records.bin','.complete.json')):
 ck(json.loads(body('/manifest.json'))['members'][i]['expected_sha256']==p['evidence'][next(k for k in p['evidence'] if k.endswith('00000000'+suffix))]['sha256'],'first original bytes prior evidence '+suffix)
res={'checks':checks,'additional_original_read_bytes':len(claim),'claim_sha256':sha(claim),'future_recovery_exact_receipt':r,'future_recovery_requirement':'Root must select the reviewed recovery route with the actual authenticated endpoint/transport identity and exactly this remote/member, receipt scope, original operation and manifest anchors; retain and authenticate 3532800 archive bytes, all 48 ordered member bytes/hashes, then pinned journal framing/purpose/closure before making a fresh recovery claim. No present remote listing or availability inferred; no fabricated Owner.'}
(P/'SUPPLEMENT01.json').write_text(json.dumps(res,sort_keys=True,indent=2)+'\n');print(json.dumps({'checks':len(checks),'sha256':sha((P/'SUPPLEMENT01.json').read_bytes())}))
