"""One fresh two-target financial byte-only restore; no native authority."""
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
REL='research/onchain-paper-replication-2026-09-24/full_sources/financial-genuine-wrapper-root-preservation03-2026-10-04'
REMOTE=BASE/'financial-genuine-wrapper-root-remote-recovery02-2026-10-04'
REVIEW=BASE/'financial-genuine-wrapper-flat-source-review02-2026-10-04'
SOURCE='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0'
EXPECTED={'CAPTURE01.json': '3401a6d84e8e00439e921eaafa690e155f16022d742d9f77045742db15d42660', 'PARENT_MANIFEST01.json': '7f608e9877086f961f4f8a998ba5faa50d42b8fd65808e2cf3ba2756eb28b77e', 'REQUEST01.json': '17d92c05d58c3e4308097a945b3de3180e33629f92df1bfb83abcbaa6f67390f', 'SOURCE_MANIFEST01.json': 'ebe3ade50a6bd106105001a615144a2e4ef1d649755989bc63937063ed9c258c', 'complete-parent01.tar.gz': 'd620cea8113f365fb1c9a458f245031b1f04c063c861f0b08a9f1ba71f1e2c7f', 'complete-source01.tar.gz': '4a483c2d9d1ed1c5f652e73bb818ca8bd11dbe79fa7acaae34b11248655a4e76'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--remote-receipt-sha256',required=True);p.add_argument('--review-manifest-sha256',required=True);a=p.parse_args()
 R.require(all(not os.path.lexists(HERE/n) for n in ('flat-source01','flat-parent01','INTENT01.json')),'one-use two-target namespace')
 floors=[]
 def floor():
  free=shutil.disk_usage(HERE).free;R.require(free>=R.FLOOR,'observed10GiB floor');floors.append({'monotonic':time.monotonic(),'free_bytes':free})
 floor();R.require(R.digest(R.read(REVIEW,'MANIFEST01.json'))==a.review_manifest_sha256,'exact independent flat-source review')
 remote_raw=R.read(REMOTE,'REMOTE_RECOVERY01.json');R.require(R.digest(remote_raw)==a.remote_receipt_sha256,'actual remote receipt')
 remote=json.loads(remote_raw);R.require(remote['genuine_run_or_native_started'] is False and remote['status']=='fresh-actual-remote-financial-source290-and-parent-baseline-recovered','actual byte-only receipt')
 rows=remote['selected_blobs'];R.require(type(rows)is list and 1<=len(rows)<=506 and len({r['path'] for r in rows})==len(rows),'finite unique actual remote selection')
 recovered={r['path']:r for r in rows};bundle=REMOTE/'selected'/REL;bodies={}
 for name,pin in EXPECTED.items():
  row=recovered[REL+'/'+name];R.require(row['sha256']==pin and row['git_mode'] in ('100644','100755'),'actual selected pin')
  raw=R.read(bundle,name);R.require(len(raw)==row['bytes'] and R.digest(raw)==pin,'fetched complete archive body')
  R.require(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_object'],'actual Git OID');bodies[name]=raw
 cap=json.loads(bodies['CAPTURE01.json']);request=json.loads(bodies['REQUEST01.json'])
 R.require(cap['source']==request['source']==SOURCE and request['tracked']==290 and request['source_pins']==289 and request['implementation']==194 and request['package']==149,'exact source290')
 R.require(cap['request_sha256']==EXPECTED['REQUEST01.json'] and cap['claim_started'] is False and cap['final_release_recovered'] is False,'exact intermediate capture')
 manifests={label:json.loads(bodies[label.upper()+'_MANIFEST01.json']) for label in ('source','parent')}
 for label,m in manifests.items():
  R.validate(m);pin=EXPECTED[label.upper()+'_MANIFEST01.json'];R.require(cap['archives'][label]['manifest_sha256']==pin==request[label+'_manifest_sha256'] and cap['archives'][label]['sha256']==EXPECTED['complete-'+label+'01.tar.gz'],'archive manifest lineage')
  R.require(len(m['members'])==cap[label+'_members']==({'source':878,'parent':15}[label]),'entire target cardinality')
 R.put(HERE/'INTENT01.json',{'pid':os.getpid(),'source':SOURCE,'one_use':True,'remote_receipt_sha256':a.remote_receipt_sha256,'capture_sha256':EXPECTED['CAPTURE01.json'],'targets':['source','parent'],'claim_started':False})
 begin=time.monotonic();actual={}
 for label,m in manifests.items():
  floor();destination=HERE/('flat-'+label+'01');destination.mkdir(mode=0o700)
  actual[label]=R.restore(bundle/('complete-'+label+'01.tar.gz'),cap['archives'][label],m,destination);floor()
 result={'status':'actual-financial-source290-and-parent-baseline-fresh-flat-recovered','source':SOURCE,'remote_receipt_sha256':a.remote_receipt_sha256,'independent_flat_source_review_manifest_sha256':a.review_manifest_sha256,'capture_sha256':EXPECTED['CAPTURE01.json'],'actual':actual,'elapsed_seconds':time.monotonic()-begin,'disk_floor_observations':floors,'continuous_floor_watch_claim':False,'shared_runtime_bodies':False,'empirical_stores':False,'final_release_recovered':False,'native_or_claim_started':False}
 R.put(HERE/'RECOVERY01.json',result);print(json.dumps({k:result[k] for k in ('status','source','elapsed_seconds')},sort_keys=True))
if __name__=='__main__':main()
