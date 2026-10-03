"""One closed source290 and unreleased external-parent byte archival capture."""
import argparse,hashlib,json,os,shutil,sys,time
from pathlib import Path
MAIN=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
BASE=MAIN/'research/onchain-paper-replication-2026-09-24/full_sources'
HERE=Path(__file__).resolve().parent
PRIMITIVES=BASE/'held-consumer-final-recovery-preparation04-2026-10-03'
PINS={'recovery04.py':'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}
for name,pin in PINS.items():
 if hashlib.sha256((PRIMITIVES/name).read_bytes()).hexdigest()!=pin:raise ValueError('unchanged capture primitive pin')
sys.path.insert(0,str(PRIMITIVES))
import recovery04 as R
from bounded_git01 import git
SOURCE=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source')
PARENT=SOURCE.parents[1]/'genuine-financial-wrapper-root-launch-20261004-01'
HEAD='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0'
COMPOSE=BASE/'financial-genuine-wrapper-root-parent-composition01-2026-10-04'
REVIEW=BASE/'financial-genuine-wrapper-root-composition-review01-2026-10-04'

def main():
 p=argparse.ArgumentParser();p.add_argument('--review-manifest-sha256',required=True);a=p.parse_args()
 observations=[]
 def floor():
  free=shutil.disk_usage(HERE).free;R.require(free>=R.FLOOR,'observed10GiB floor');observations.append({'monotonic':time.monotonic(),'free_bytes':free})
 floor();R.require(not os.path.lexists(HERE/'INTENT01.json'),'one-use capture namespace')
 R.require(git(SOURCE,['rev-parse','HEAD'],cap=128).decode().strip()==HEAD and not git(SOURCE,['status','--porcelain'],cap=65536),'exact closed source')
 R.require(len(git(SOURCE,['ls-tree','-r','-z',HEAD],cap=R.FILE).split(b'\0')[:-1])==290,'tracked290')
 source_manifest=json.loads(R.read(COMPOSE,'SOURCE_MANIFEST01.json'));parent_manifest=json.loads(R.read(COMPOSE,'PARENT_MANIFEST01.json'))
 R.same(SOURCE,source_manifest);R.same(PARENT,parent_manifest)
 R.require(R.digest(R.read(REVIEW,'MANIFEST01.json'))==a.review_manifest_sha256,'exact independent composition and capture review')
 reviews={f.name:R.digest(R.read(REVIEW,f.name)) for f in sorted(REVIEW.iterdir()) if f.is_file()}
 request={'schema_version':1,'source':HEAD,'source_root':str(SOURCE),'parent_root':str(PARENT),'tracked':290,'source_pins':289,'implementation':194,'package':149,'source_manifest_sha256':R.digest(R.encode(source_manifest)),'parent_manifest_sha256':R.digest(R.encode(parent_manifest)),'independent_review':reviews,'primitive_sha256':PINS,'status':'closed unreleased archival scope only','shared_runtime_bodies':False,'empirical_stores':False,'claim_started':False}
 floor();R.put(HERE/'REQUEST01.json',request);R.put(HERE/'SOURCE_MANIFEST01.json',source_manifest);R.put(HERE/'PARENT_MANIFEST01.json',parent_manifest)
 R.put(HERE/'INTENT01.json',{'pid':os.getpid(),'source':HEAD,'request_sha256':R.digest(R.encode(request)),'one_use':True,'numerical_authority':False})
 begin=time.monotonic();floor();archives={}
 for label,root,m in [('source',SOURCE,source_manifest),('parent',PARENT,parent_manifest)]:
  floor();archives[label]=R.pack(root,m,HERE/('complete-'+label+'01.tar.gz'));floor()
 floor();R.same(SOURCE,source_manifest);R.same(PARENT,parent_manifest)
 R.require(git(SOURCE,['rev-parse','HEAD'],cap=128).decode().strip()==HEAD,'final source')
 result={'source':HEAD,'archives':archives,'request_sha256':R.digest(R.encode(request)),'source_members':len(source_manifest['members']),'parent_members':len(parent_manifest['members']),'elapsed_seconds':time.monotonic()-begin,'disk_floor_observations':observations,'continuous_floor_watch_claim':False,'final_release_recovered':False,'native_authority':False,'shared_runtime_bodies':False,'empirical_stores':False,'claim_started':False}
 R.put(HERE/'CAPTURE01.json',result);print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
