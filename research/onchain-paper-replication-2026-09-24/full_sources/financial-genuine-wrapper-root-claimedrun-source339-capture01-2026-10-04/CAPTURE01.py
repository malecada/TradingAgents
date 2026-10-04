import hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
M=Path.cwd();B=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=B/'financial-genuine-wrapper-root-claimedrun-source339-capture01-2026-10-04'
N=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');H='0a2e7639b42b9423b90743feadcda4078aa21816'
sys.path.insert(0,str(B/'held-consumer-final-recovery-preparation04-2026-10-03'));import recovery04 as R
assert hashlib.sha256((B/'held-consumer-final-recovery-preparation04-2026-10-03/recovery04.py').read_bytes()).hexdigest()=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a'
assert not os.path.lexists(D);assert shutil.disk_usage(B).free>=R.FLOOR
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=N,text=True).strip()==H
D.mkdir(mode=0o700);(D/'CAPTURE01.py').write_bytes(Path(__file__).read_bytes());start=time.monotonic()
m=R.scan(N);R.validate(m);records=R.pack(N,m,D/'source.tar.gz');R.put(D/'source-manifest.json',m)
assert shutil.disk_usage(D).free>=R.FLOOR
R.put(D/'CAPTURE01.json',{'status':'ACTUAL_COMPLETE_SOURCE339_BYTE_CAPTURE_NOT_EXTERNAL_OR_RELEASE','source_root':str(N),'current_equals_design':H,'archive':records,'members':len(m['members']),'regular_bodies':sum(r['kind']=='file'for r in m['members']),'tracked':339,'registered_pins':338,'input_roles':8,'original_spent_claims':1,'new_claim_started':False,'parent_or_final_review_captured':False,'elapsed_seconds':time.monotonic()-start,'disk_free_after_bytes':shutil.disk_usage(D).free,'scope':'Complete actual writable Source02 tree including .git/current339, all unchanged original Git/history bodies and copied original failed claim. Canonical exact byte/mode/path archival preservation only. No external recovery, installed-runtime-body recovery, POSIX reinstantiation, budget adoption or numerical release.'})
print(json.dumps({'archive':records,'typed_members':len(m['members']),'regular_bodies':sum(r['kind']=='file'for r in m['members']),'new_claim':False}))
