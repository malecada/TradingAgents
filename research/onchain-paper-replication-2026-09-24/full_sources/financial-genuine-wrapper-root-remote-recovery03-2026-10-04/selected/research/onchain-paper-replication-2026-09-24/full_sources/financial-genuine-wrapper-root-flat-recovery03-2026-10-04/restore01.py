"""One fresh three-target financial final-union byte-only restore; no native authority."""
import argparse,hashlib,json,os,shutil,sys,time
from pathlib import Path
ROOT=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
HERE=Path(__file__).resolve().parent
BASE=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
PRIMITIVE=BASE/'held-consumer-final-recovery-preparation04-2026-10-03'
PINS={'recovery04.py':'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}
for name,pin in PINS.items():
 if hashlib.sha256((PRIMITIVE/name).read_bytes()).hexdigest()!=pin:raise ValueError('unchanged flat primitive pin')
sys.path.insert(0,str(PRIMITIVE))
import recovery04 as R
REL='research/onchain-paper-replication-2026-09-24/full_sources/financial-genuine-wrapper-root-preservation05-2026-10-04'
REMOTE=BASE/'financial-genuine-wrapper-root-remote-recovery03-2026-10-04'
REVIEW=BASE/'financial-genuine-wrapper-final-flat-source-review01-2026-10-04'
SOURCE='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0'
EXPECTED={'CAPTURE01.json': '8ac4415b12753cf985688359efe7210122321ce21130c4bc472df65f04da4823', 'REQUEST01.json': 'ada07624b7954c85ed5f158785343496a4af9c5b7ee96372a6403146d88fceaf', 'SOURCE_MANIFEST01.json': 'ebe3ade50a6bd106105001a615144a2e4ef1d649755989bc63937063ed9c258c', 'PARENT_MANIFEST01.json': '950037968a4276b55023af89a4f6a999c3dac5efafd8b8b6898b9244688671cb', 'REVIEW_MANIFEST01.json': '22c51796c5327e7f68722c4069bb7451217f3e1d79b7ef72817f7a74f34dc1cf', 'complete-source01.tar.gz': '4a483c2d9d1ed1c5f652e73bb818ca8bd11dbe79fa7acaae34b11248655a4e76', 'complete-parent01.tar.gz': '839c8ae42993f85604879de67f31ac6c22958ced457e74d1e26a7355b0e41aab', 'complete-review01.tar.gz': '4d33b80083de2514dff756e81bb7ece83f3633864526ed267771660425b97ea3'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--remote-receipt-sha256',required=True);p.add_argument('--review-manifest-sha256',required=True);a=p.parse_args()
 R.require(all(not os.path.lexists(HERE/n) for n in ('flat-source01','flat-parent01','flat-review01','INTENT01.json')),'one-use three-target namespace')
 floors=[]
 def floor():
  free=shutil.disk_usage(HERE).free;R.require(free>=R.FLOOR,'observed10GiB floor');floors.append({'monotonic':time.monotonic(),'free_bytes':free})
 floor();R.require(R.digest(R.read(REVIEW,'MANIFEST01.json'))==a.review_manifest_sha256,'exact independent flat-source review')
 remote_raw=R.read(REMOTE,'REMOTE_RECOVERY01.json');R.require(R.digest(remote_raw)==a.remote_receipt_sha256,'actual remote receipt')
 remote=json.loads(remote_raw);R.require(remote['genuine_run_or_native_started'] is False and remote['status']=='fresh-actual-remote-financial-source290-final-parent-review-recovered','actual byte-only receipt')
 rows=remote['selected_blobs'];R.require(type(rows)is list and 1<=len(rows)<=506 and len({r['path'] for r in rows})==len(rows),'finite unique actual remote selection')
 recovered={r['path']:r for r in rows};bundle=REMOTE/'selected'/REL;bodies={}
 for name,pin in EXPECTED.items():
  row=recovered[REL+'/'+name];R.require(row['sha256']==pin and row['git_mode'] in ('100644','100755'),'actual selected pin')
  raw=R.read(bundle,name);R.require(len(raw)==row['bytes'] and R.digest(raw)==pin,'fetched complete archive body')
  R.require(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_object'],'actual Git OID');bodies[name]=raw
 cap=json.loads(bodies['CAPTURE01.json']);request=json.loads(bodies['REQUEST01.json'])
 R.require(cap['source']==request['source']==SOURCE and request['tracked']==290 and request['source_pins']==289 and request['implementation']==194 and request['package']==149,'exact source290')
 R.require(cap['request_sha256']==EXPECTED['REQUEST01.json'] and cap['claim_started'] is False and cap['final_release_recovered'] is False,'exact final-union byte capture')
 R.require(cap['final_request_sha256']=='dc80a4dff93fbf3261bdf151076c1420630ed38926ab7094d60eb1902bde25bc' and cap['native_authority'] is False,'actual fixed final request; no native authority')
 manifests={label:json.loads(bodies[label.upper()+'_MANIFEST01.json']) for label in ('source','parent','review')}
 for label,m in manifests.items():
  R.validate(m);pin=EXPECTED[label.upper()+'_MANIFEST01.json'];R.require(cap['archives'][label]['manifest_sha256']==pin==request[label+'_manifest_sha256'] and cap['archives'][label]['sha256']==EXPECTED['complete-'+label+'01.tar.gz'],'archive manifest lineage')
  R.require(len(m['members'])==cap[label+'_members']==({'source':878,'parent':23,'review':10}[label]),'entire target cardinality')
 R.put(HERE/'INTENT01.json',{'pid':os.getpid(),'source':SOURCE,'one_use':True,'remote_receipt_sha256':a.remote_receipt_sha256,'capture_sha256':EXPECTED['CAPTURE01.json'],'targets':['source','parent','review'],'claim_started':False})
 begin=time.monotonic();actual={}
 for label,m in manifests.items():
  floor();destination=HERE/('flat-'+label+'01');destination.mkdir(mode=0o700)
  actual[label]=R.restore(bundle/('complete-'+label+'01.tar.gz'),cap['archives'][label],m,destination);floor()
 parent_metadata=json.loads(R.read(HERE/'flat-parent01',actual['parent']['metadata_file']))
 R.require(R.digest(R.encode(parent_metadata))==actual['parent']['metadata_sha256'],'actual parent flat mapping')
 parent_leaf=parent_metadata['flat_members']['REQUEST_FINAL03.json']
 R.require(R.digest(R.read(HERE/'flat-parent01',parent_leaf))==cap['final_request_sha256'],'restored complete final request')
 result={'status':'actual-financial-source290-final-parent-review-fresh-flat-recovered','source':SOURCE,'remote_receipt_sha256':a.remote_receipt_sha256,'independent_flat_source_review_manifest_sha256':a.review_manifest_sha256,'capture_sha256':EXPECTED['CAPTURE01.json'],'actual':actual,'elapsed_seconds':time.monotonic()-begin,'disk_floor_observations':floors,'continuous_floor_watch_claim':False,'shared_runtime_bodies':False,'empirical_stores':False,'final_request_sha256':cap['final_request_sha256'],'complete_final_release_bytes_recovered':True,'independent_final_union_acceptance':False,'native_or_claim_started':False}
 R.put(HERE/'RECOVERY01.json',result);print(json.dumps({k:result[k] for k in ('status','source','elapsed_seconds')},sort_keys=True))
if __name__=='__main__':main()
