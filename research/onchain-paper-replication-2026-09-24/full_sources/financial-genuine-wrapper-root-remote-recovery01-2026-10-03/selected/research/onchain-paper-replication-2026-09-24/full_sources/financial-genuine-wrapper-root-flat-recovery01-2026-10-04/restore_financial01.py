"""One fresh financial byte-only flat archive restore; no native authority."""
import argparse,hashlib,json,os,shutil,sys,time
from pathlib import Path
ROOT=Path.cwd().resolve()
HERE=Path(__file__).resolve().parent
BASE=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/held-consumer-final-recovery-preparation04-2026-10-03'
PINS={'recovery04.py': 'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a', 'owned_io.py': '09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb', 'bounded_git01.py': 'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}
for name,pin in PINS.items():
    if hashlib.sha256((BASE/name).read_bytes()).hexdigest()!=pin:
        raise ValueError('unchanged flat primitive pin')
sys.path.insert(0,str(BASE))
import recovery04 as R
REL='research/onchain-paper-replication-2026-09-24/full_sources/financial-genuine-wrapper-root-preservation02-2026-10-04'
REMOTE=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/financial-genuine-wrapper-root-remote-recovery01-2026-10-03'
EXPECTED={'CAPTURE01.json':'eae9b52e1bb03523977a29e26be557b5e1d90e4bbc29c5385c42e3e98c2f835e','REQUEST01.json':'581d14b87b8fd8fb3a686196f4978ede199589a73eef7f9879f0d28dc41efd2f','complete-manifest01.json':'850667c80ff2b1a66a0c65795178765d6e5ec3d873e52d809a5d7659593ac56f','complete-source01.tar.gz':'497a0ae3c0aba9b5f8bb41e933bed878ba49adf759a880d8a338637d732d1af4'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--remote-receipt-sha256',required=True);p.add_argument('--review-manifest-sha256',required=True);a=p.parse_args()
    R.require(not os.path.lexists(HERE/'flat01') and not os.path.lexists(HERE/'INTENT01.json'),'fresh flat identity')
    R.require(shutil.disk_usage(HERE).free>=R.FLOOR,'initial observed10GiB floor')
    review=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/financial-genuine-wrapper-flat-source-review01-2026-10-04'
    R.require(R.digest(R.read(review,'MANIFEST01.json'))==a.review_manifest_sha256,'exact independent flat-source review pin')
    remote_raw=R.read(REMOTE,'REMOTE_RECOVERY01.json')
    R.require(R.digest(remote_raw)==a.remote_receipt_sha256,'actual remote receipt pin')
    remote=json.loads(remote_raw)
    R.require(remote['genuine_run_or_native_started'] is False and remote['status']=='fresh-actual-remote-financial-source-archive-and-supporting-bodies-recovered','actual archive-only receipt')
    recovered={row['path']:row for row in remote['selected_blobs']}
    bodies={}
    bundle=REMOTE/'selected'/REL
    for name,pin in EXPECTED.items():
        row=recovered[REL+'/'+name]
        R.require(row['sha256']==pin and row['git_mode'] in ('100644','100755'),'actual remote selected pin')
        raw=R.read(bundle,name)
        R.require(len(raw)==row['bytes'] and R.digest(raw)==pin,'actual fetched archive body join')
        R.require(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_object'],'actual immutable Git OID join')
        bodies[name]=raw
    cap=json.loads(bodies['CAPTURE01.json']);manifest=json.loads(bodies['complete-manifest01.json']);request=json.loads(bodies['REQUEST01.json'])
    R.require(cap['source']==request['actual_HEAD']=='868bfa6404a2c34d6e5b6e0932a2baf4b38eb370','exact financial source')
    R.require(cap['request_sha256']==EXPECTED['REQUEST01.json'] and cap['archive']['manifest_sha256']==EXPECTED['complete-manifest01.json'],'actual complete source bindings')
    R.require(cap['members']==755 and cap['regular_bodies']==533 and request['complete_tracked']==243,'exact full scope')
    R.validate(manifest)
    R.put(HERE/'INTENT01.json',{'schema_version':1,'status':'one-use flat archive restore','pid':os.getpid(),'source':cap['source'],'remote_receipt_sha256':a.remote_receipt_sha256,'capture_sha256':EXPECTED['CAPTURE01.json']})
    begin=time.monotonic()
    (HERE/'flat01').mkdir(mode=0o700)
    actual=R.restore(bundle/'complete-source01.tar.gz',cap['archive'],manifest,HERE/'flat01')
    R.require(shutil.disk_usage(HERE).free>=R.FLOOR,'final observed10GiB floor')
    R.put(HERE/'RECOVERY01.json',{'schema_version':1,'status':'actual-financial-source-fresh-flat-archive-recovered','source':cap['source'],'remote_receipt_sha256':a.remote_receipt_sha256,'independent_source_review_manifest_sha256':a.review_manifest_sha256,'capture_sha256':EXPECTED['CAPTURE01.json'],'actual':actual,'elapsed_seconds':time.monotonic()-begin,'free_bytes':shutil.disk_usage(HERE).free,'full_runtime_or_empirical_store_recovered':False,'native_or_claim_started':False})
    print(json.dumps({'status':'actual-financial-source-fresh-flat-archive-recovered','regular_bodies':actual['regular_bodies'],'members':actual['members'],'elapsed_seconds':time.monotonic()-begin},sort_keys=True))
if __name__=='__main__':
    main()
