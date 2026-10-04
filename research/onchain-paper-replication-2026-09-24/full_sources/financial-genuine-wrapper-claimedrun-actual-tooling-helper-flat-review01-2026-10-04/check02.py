import hashlib,json,os,sys
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;ROOT=B/'financial-genuine-wrapper-root-claimedrun-tooling-helper-flat01-2026-10-04';OUT=ROOT/'flat-eight-scopes01';sys.path.insert(0,str(ROOT));import recovery04 as R
checks=[];refs=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v,n):assert v,n;checks.append(n)
def pin(p,h):b=p.read_bytes();ok(sha(b)==h,'context pin '+p.name);refs.append({'path':str(p),'sha256':h});return b
recovery=json.loads((OUT/'RECOVERY01.json').read_bytes());q=json.loads((ROOT/'REQUEST_BOUND02.json').read_bytes());ok(recovery['remote_commit']==q['remote_commit'] and recovery['remote_receipt_sha256']==q['remote_receipt_sha256'],'final actual remote binding')
for flag in ['genuine_numerical_started','posix_tree_instantiated','runtime_or_empirical_store_recovery']:ok(recovery[flag] is False,'recovery authority false '+flag)
for scope in recovery['scopes']:
 r=scope['result'];ok(r['status']=='fresh-flat-archival-recovery-not-origin-proof','original result qualification')
 for flag in ['instantiated_posix_tree','outside_stores_recovered','recovered_tree_git_join','research_authority','runtime_package_bodies_recovered']:ok(r[flag] is False,'actual scope authority false '+flag)
source=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');cap=B/'financial-genuine-wrapper-root-claimedrun-source339-capture01-2026-10-04';m=json.loads(pin(cap/'source-manifest.json','fdf77348b81a4d6df8b420b98530f5485900a0461636e1c201506106b036dfd8'));R.same(source,m);ok(len(m['members'])==1029,'whole actual Source339 unchanged');pin(cap/'source.tar.gz','b5b6aad2f515447dc6566cfb716a20ef90031313d48f1ac903ab756735431e24')
p=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-root-launch-20261004-01');pq=json.loads(pin(p/'REQUEST_FINAL03.json','529c9bf3c587e6160a217e8eb339882e59433b6fc0f759d0009d261f872b2bd8'));pin(p/'parent01.py',pq['caller_sha256'])
for name,h in pq['helper_hashes'].items():pin(p/name,h)
for ref in [*pq['proofs'].values(),pq['final_review']]:pin(Path(ref['path']),ref['sha256'])
pin(source/pq['registration'],pq['registration_sha256']);ok(pq['design_source']=='0a2e7639b42b9423b90743feadcda4078aa21816' and len(pq['input_hashes'])==8,'current Source339 context fields');ok(not os.path.lexists(p/'attempt'),'native Parent stillprelaunch')
with (H/'CONTEXT02.json').open('x') as f:json.dump({'checks':len(checks),'check_names':checks,'current_context_refs':refs,'full_terminal_sha256':sha((ROOT/'ACTUAL_TOOL_TERMINAL02.json').read_bytes()),'source_current_unchanged':True,'Root_native_still_unattempted_at_observation':True},f,sort_keys=True,indent=2);f.write('\n')
print(len(checks))
