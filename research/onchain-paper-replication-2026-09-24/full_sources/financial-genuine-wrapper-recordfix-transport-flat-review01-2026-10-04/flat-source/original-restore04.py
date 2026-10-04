"""One fresh three-target financial original-failed byte-only restore; no native authority."""
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
REL='research/onchain-paper-replication-2026-09-24/full_sources/financial-genuine-wrapper-root-preservation06-2026-10-04'
REMOTE=BASE/'financial-genuine-wrapper-root-remote-recovery04-2026-10-04'
REVIEW=BASE/'financial-genuine-wrapper-first-attempt-flat-source-review01-2026-10-04'
SOURCE='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0'
EXPECTED={'CAPTURE01.json': '645387e5bede68f778ad4a94c5e3b30c4e9f64bd10aa4cfb1108508939a8b899', 'REQUEST01.json': 'fb1f603733d24a5ca7e0eff41242651620b7561de17afc07668e1db102dbeca9', 'SOURCE_MANIFEST01.json': 'ebe3ade50a6bd106105001a615144a2e4ef1d649755989bc63937063ed9c258c', 'PARENT_MANIFEST01.json': '956da6e25ecd2cd61ce3eb28a15da1addd5e3db2079d5de094548f8269871eaa', 'OUTER_MANIFEST01.json': '3dae5c56e601d16a0a0b8d753abf70f426b810c27d8a614df2332217849d988c', 'complete-source01.tar.gz': '4a483c2d9d1ed1c5f652e73bb818ca8bd11dbe79fa7acaae34b11248655a4e76', 'complete-parent01.tar.gz': '832bc3dcfd215223dda75540fe19b4fddc1d05d862f1a3d7ff174da0151306fb', 'complete-outer01.tar.gz': 'ad4b4ce1f41c99d470653a8049add40d57e7959915b83b9cb592e82f4d07c784'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--remote-receipt-sha256',required=True);p.add_argument('--review-manifest-sha256',required=True);a=p.parse_args()
 R.require(all(not os.path.lexists(HERE/n) for n in ('flat-source01','flat-parent01','flat-outer01','INTENT01.json')),'one-use three-target namespace')
 floors=[]
 def floor():
  free=shutil.disk_usage(HERE).free;R.require(free>=R.FLOOR,'observed10GiB floor');floors.append({'monotonic':time.monotonic(),'free_bytes':free})
 floor();R.require(R.digest(R.read(REVIEW,'MANIFEST01.json'))==a.review_manifest_sha256,'exact independent flat-source review')
 remote_raw=R.read(REMOTE,'REMOTE_RECOVERY01.json');R.require(R.digest(remote_raw)==a.remote_receipt_sha256,'actual remote receipt')
 remote=json.loads(remote_raw);R.require(remote['genuine_run_or_native_started'] is False and remote['status']=='fresh-actual-remote-financial-source290-failed-parent-outer-recovered','actual byte-only receipt')
 rows=remote['selected_blobs'];R.require(type(rows)is list and 1<=len(rows)<=506 and len({r['path'] for r in rows})==len(rows),'finite unique actual remote selection')
 recovered={r['path']:r for r in rows};bundle=REMOTE/'selected'/REL;bodies={}
 for name,pin in EXPECTED.items():
  row=recovered[REL+'/'+name];R.require(row['sha256']==pin and row['git_mode'] in ('100644','100755'),'actual selected pin')
  raw=R.read(bundle,name);R.require(len(raw)==row['bytes'] and R.digest(raw)==pin,'fetched complete archive body')
  R.require(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_object'],'actual Git OID');bodies[name]=raw
 cap=json.loads(bodies['CAPTURE01.json']);request=json.loads(bodies['REQUEST01.json'])
 R.require(cap['source']==request['source']==SOURCE and request['tracked']==290 and request['source_pins']==289 and request['implementation']==194 and request['package']==149,'exact source290')
 R.require(cap['request_sha256']==EXPECTED['REQUEST01.json'] and cap['numerical_claims']==request['numerical_claims']==0 and cap['native_started'] is request['native_started'] is False and cap['failed_identity_permanently_reserved'] is True,'exact original failed byte capture')
 R.require(cap['identity']==request['identity']=='financial-wrapper-classification-eager-interrupt1-20261003-01' and cap['actual_outer_exit']==1 and cap['original_parent_terminal_exit'] is None,'original failed identity and actual versus NULL exits')
 manifests={label:json.loads(bodies[label.upper()+'_MANIFEST01.json']) for label in ('source','parent','outer')}
 for label,m in manifests.items():
  R.validate(m);pin=EXPECTED[label.upper()+'_MANIFEST01.json'];R.require(cap['archives'][label]['manifest_sha256']==pin==request['manifests'][label] and cap['archives'][label]['sha256']==EXPECTED['complete-'+label+'01.tar.gz'],'archive manifest lineage')
  R.require(len(m['members'])==cap['members'][label]==({'source':878,'parent':30,'outer':8}[label]),'entire target cardinality')
 R.put(HERE/'INTENT01.json',{'pid':os.getpid(),'source':SOURCE,'one_use':True,'remote_receipt_sha256':a.remote_receipt_sha256,'capture_sha256':EXPECTED['CAPTURE01.json'],'targets':['source','parent','outer'],'claim_started':False})
 begin=time.monotonic();actual={}
 for label,m in manifests.items():
  floor();destination=HERE/('flat-'+label+'01');destination.mkdir(mode=0o700)
  actual[label]=R.restore(bundle/('complete-'+label+'01.tar.gz'),cap['archives'][label],m,destination);floor()
 parent_metadata=json.loads(R.read(HERE/'flat-parent01',actual['parent']['metadata_file']))
 R.require(R.digest(R.encode(parent_metadata))==actual['parent']['metadata_sha256'],'actual parent flat mapping')
 parent_leaf=parent_metadata['flat_members']['REQUEST_FINAL03.json']
 R.require(R.digest(R.read(HERE/'flat-parent01',parent_leaf))=='dc80a4dff93fbf3261bdf151076c1420630ed38926ab7094d60eb1902bde25bc','preserved original failed final request')
 parent_terminal=json.loads(R.read(HERE/'flat-parent01',parent_metadata['flat_members']['attempt/parent-terminal.json']))
 outer_metadata=json.loads(R.read(HERE/'flat-outer01',actual['outer']['metadata_file']));R.require(R.digest(R.encode(outer_metadata))==actual['outer']['metadata_sha256'],'actual outer flat mapping')
 outer_terminal=json.loads(R.read(HERE/'flat-outer01',outer_metadata['flat_members']['ACTUAL_TERMINAL01.json']))
 R.require(parent_terminal['actual_parent_exit'] is None and parent_terminal['actual_child_exit']==1 and parent_terminal['cleanup']['source_bound_no_dispatch'] is True and outer_terminal['actual_parent_exit']==1,'actual original failed terminal semantics')
 result={'status':'actual-financial-source290-failed-parent-outer-fresh-flat-recovered','source':SOURCE,'remote_receipt_sha256':a.remote_receipt_sha256,'independent_flat_source_review_manifest_sha256':a.review_manifest_sha256,'capture_sha256':EXPECTED['CAPTURE01.json'],'actual':actual,'elapsed_seconds':time.monotonic()-begin,'disk_floor_observations':floors,'continuous_floor_watch_claim':False,'shared_runtime_bodies':False,'empirical_stores':False,'original_failed_final_request_sha256':'dc80a4dff93fbf3261bdf151076c1420630ed38926ab7094d60eb1902bde25bc','complete_original_failed_scope_bytes_recovered':True,'independent_failed_scope_acceptance':False,'original_identity_permanently_reserved':True,'numerical_claims':0,'native_or_claim_started':False}
 R.put(HERE/'RECOVERY01.json',result);print(json.dumps({k:result[k] for k in ('status','source','elapsed_seconds')},sort_keys=True))
if __name__=='__main__':main()
