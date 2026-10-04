"""One complete actual pre-dispatch failed financial scope byte capture; never replay."""
import argparse,hashlib,json,os,shutil,sys,time
from pathlib import Path
MAIN=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
BASE=MAIN/'research/onchain-paper-replication-2026-09-24/full_sources'
HERE=Path(__file__).resolve().parent
PRIMITIVES=BASE/'held-consumer-final-recovery-preparation04-2026-10-03'
PINS={'recovery04.py': 'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a', 'owned_io.py': '09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb', 'bounded_git01.py': 'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}
for name,pin in PINS.items():
 if hashlib.sha256((PRIMITIVES/name).read_bytes()).hexdigest()!=pin:raise ValueError('unchanged capture primitive pin')
sys.path.insert(0,str(PRIMITIVES))
import recovery04 as R
from bounded_git01 import git
SOURCE=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source')
PARENT=SOURCE.parents[1]/'genuine-financial-wrapper-root-launch-20261004-01'
OUTER=BASE/'financial-genuine-wrapper-root-first-launch01-2026-10-04'
HEAD='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0'
REVIEW=BASE/'financial-genuine-wrapper-first-attempt-capture-review01-2026-10-04'
IDENTITY='financial-wrapper-classification-eager-interrupt1-20261003-01'

def main():
 p=argparse.ArgumentParser();p.add_argument('--review-manifest-sha256',required=True);a=p.parse_args()
 observations=[]
 def floor():
  free=shutil.disk_usage(HERE).free;R.require(free>=R.FLOOR,'observed10GiB floor');observations.append({'monotonic':time.monotonic(),'free_bytes':free})
 floor();R.require(all(not os.path.lexists(HERE/n) for n in ('INTENT01.json','CAPTURE01.json','REQUEST01.json')),'one-use failed capture namespace')
 R.require(git(SOURCE,['rev-parse','HEAD'],cap=128).decode().strip()==HEAD and not git(SOURCE,['status','--porcelain'],cap=65536),'exact original closed source')
 R.require(len(git(SOURCE,['ls-tree','-r','-z',HEAD],cap=R.FILE).split(b'\0')[:-1])==290,'tracked290')
 targets=[('source',SOURCE,878),('parent',PARENT,30),('outer',OUTER,8)]
 manifests={label:json.loads(R.read(HERE,label.upper()+'_MANIFEST01.json')) for label,_,_ in targets}
 for label,root,count in targets:R.same(root,manifests[label]);R.require(len(manifests[label]['members'])==count,'entire actual failed target count')
 R.require(R.digest(R.read(REVIEW,'MANIFEST01.json'))==a.review_manifest_sha256,'exact independent failed scope and capture-source review')
 R.require(not os.path.lexists(SOURCE/'research_runs'/IDENTITY) and not os.path.lexists(SOURCE/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/IDENTITY),'no actual numerical claim or dispatch')
 terminal=json.loads(R.read(PARENT/'attempt','parent-terminal.json'));actual=json.loads(R.read(OUTER,'ACTUAL_TERMINAL01.json'))
 R.require(terminal['actual_child_exit']==1 and terminal['actual_parent_exit'] is None and terminal['cleanup']['source_bound_no_dispatch'] is True and actual['actual_parent_exit']==1,'original pre-dispatch failed exit semantics')
 request={'schema_version':1,'source':HEAD,'identity':IDENTITY,'roots':{label:str(root) for label,root,_ in targets},'tracked':290,'source_pins':289,'implementation':194,'package':149,'manifests':{label:R.digest(R.encode(m)) for label,m in manifests.items()},'independent_review_manifest_sha256':a.review_manifest_sha256,'primitive_sha256':PINS,'status':'complete original unexpected failed outer scope; no claim/native/checkpoint','numerical_claims':0,'numerical_components_completed':0,'native_started':False,'shared_runtime_bodies':False,'empirical_stores':False}
 floor();R.put(HERE/'REQUEST01.json',request);R.put(HERE/'INTENT01.json',{'pid':os.getpid(),'source':HEAD,'identity':IDENTITY,'request_sha256':R.digest(R.encode(request)),'one_use':True,'numerical_authority':False})
 begin=time.monotonic();archives={}
 for label,root,_ in targets:floor();archives[label]=R.pack(root,manifests[label],HERE/('complete-'+label+'01.tar.gz'));floor()
 for label,root,_ in targets:R.same(root,manifests[label])
 floor();R.require(git(SOURCE,['rev-parse','HEAD'],cap=128).decode().strip()==HEAD,'final original source')
 result={'source':HEAD,'identity':IDENTITY,'archives':archives,'request_sha256':R.digest(R.encode(request)),'members':{label:len(m['members']) for label,m in manifests.items()},'elapsed_seconds':time.monotonic()-begin,'disk_floor_observations':observations,'continuous_floor_watch_claim':False,'actual_outer_exit':1,'original_parent_terminal_exit':None,'numerical_claims':0,'numerical_components_completed':0,'native_started':False,'shared_runtime_bodies':False,'empirical_stores':False,'failed_identity_permanently_reserved':True}
 R.put(HERE/'CAPTURE01.json',result);print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
