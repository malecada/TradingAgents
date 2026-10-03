"""One new closed financial source archival capture; no registration or execution."""
import hashlib,json,os,sys,time
from pathlib import Path
ROOT=Path.cwd().resolve()
HERE=Path(__file__).resolve().parent
BASE=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/held-consumer-final-recovery-preparation04-2026-10-03'
PINS={'recovery04.py': 'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a', 'owned_io.py': '09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb', 'bounded_git01.py': 'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}
for name,pin in PINS.items():
    if hashlib.sha256((BASE/name).read_bytes()).hexdigest()!=pin:
        raise ValueError('unchanged capture primitive pin')
sys.path.insert(0,str(BASE))
import recovery04 as R
from bounded_git01 import git
SOURCE=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source')
HEAD='868bfa6404a2c34d6e5b6e0932a2baf4b38eb370'

def main():
    R.require(not (HERE/'INTENT01.json').exists(),'one-use capture namespace')
    R.require(git(SOURCE,['rev-parse','HEAD'],cap=128).decode().strip()==HEAD,'fixed current financial source')
    R.require(not git(SOURCE,['status','--porcelain'],cap=65536),'closed clean source required')
    tree=git(SOURCE,['ls-tree','-r','-z',HEAD],cap=R.FILE)
    entries=tree.split(b'\0')[:-1]
    R.require(len(entries)==243,'exact tracked scope')
    manifest=R.scan(SOURCE)
    installed=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/financial-genuine-wrapper-installed-expectation-review01-2026-10-04'
    R.require(installed.is_dir(),'independent installed-scope review required')
    reviews={p.name:R.digest(R.read(installed,p.name)) for p in sorted(installed.iterdir()) if p.is_file()}
    R.require(reviews and 'MANIFEST01.json' in reviews,'closed independent review manifest')
    request={'schema_version':1,'source_root':str(SOURCE),'actual_HEAD':HEAD,'complete_tracked':243,'implementation_sources':194,'package_sources':149,'auxiliary_drafts_and_expectation':49,'complete_manifest_sha256':R.digest(R.encode(manifest)),'installed_scope_review':reviews,'capture_primitive_sha256':PINS,'mode':'complete closed financial source archival capture; no registration or release','shared_runtime_body_scope':False,'empirical_store_scope':False,'claimed_phases':0}
    R.put(HERE/'REQUEST01.json',request)
    R.put(HERE/'complete-manifest01.json',manifest)
    R.put(HERE/'INTENT01.json',{'schema_version':1,'status':'one-use archival capture only','pid':os.getpid(),'source':HEAD,'request_sha256':R.digest(R.encode(request))})
    begin=time.monotonic()
    archive=R.pack(SOURCE,manifest,HERE/'complete-source01.tar.gz')
    R.require(git(SOURCE,['rev-parse','HEAD'],cap=128).decode().strip()==HEAD,'final current source join')
    result={'schema_version':1,'source':HEAD,'source_root':str(SOURCE),'request_sha256':R.digest(R.encode(request)),'archive':archive,'logical_bytes':sum(v.get('bytes',0) for v in manifest['members']),'members':len(manifest['members']),'regular_bodies':sum(v['kind']=='file' for v in manifest['members']),'whole_current_git_and_source':True,'shared_runtime_bodies':False,'empirical_stores':False,'registration_or_native_authority':False,'elapsed_seconds':time.monotonic()-begin}
    R.put(HERE/'CAPTURE01.json',result)
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__':
    main()
