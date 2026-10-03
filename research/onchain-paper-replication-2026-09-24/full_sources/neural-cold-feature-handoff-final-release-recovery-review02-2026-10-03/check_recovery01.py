"""Independent saved-body + already fetched Git recovery check; no network."""
import hashlib,json,os,pathlib,stat,subprocess,sys
HERE=pathlib.Path(__file__).resolve().parent;BASE=HERE.parent
ROOT=BASE.parents[2];A=BASE/'neural-cold-feature-handoff-root-launch-request02-2026-10-03';REC=A/'final-release-recovery02';BARE=REC/'repository.git';SAVED=REC/'selected';COMMIT='860101739df43e9756d39db05cc07cbf2c9d1639'
assert ROOT.name=='TradingAgents-audit-fixes'
env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0','GIT_TERMINAL_PROMPT':'0'}
def git(*args):
 r=subprocess.run(['git','-c','protocol.allow=never','--git-dir',str(BARE),*args],env=env,capture_output=True,timeout=10)
 assert r.returncode==0,(args,r.stderr[:500]);assert len(r.stdout)<=4*1024**2
 return r.stdout
sha=lambda b:hashlib.sha256(b).hexdigest()
receiptpath=A/'REMOTE_FINAL_RELEASE_RECOVERY02.json';receipt=json.loads(receiptpath.read_bytes());manifestpath=A/'SELECTED_RELEASE_BODIES02.json';body=manifestpath.read_bytes();manifest=json.loads(body);name=str(manifestpath.relative_to(ROOT))
assert receipt['status']=='fresh-actual-remote-final-release-bodies-recovered' and receipt['remote_commit']==COMMIT
assert git('rev-parse','FETCH_HEAD').decode().strip()==COMMIT
assert receipt['manifest']=={'path':name,'sha256':sha(body),'bytes':len(body)}
assert receipt['selected_blobs']==manifest['rows'];assert len(manifest['rows'])==183 and receipt['blobs_including_manifest']==184
rows=manifest['rows']+[receipt['manifest']];assert len({r['path'] for r in rows})==184
assert [r['path'] for r in manifest['rows']]==sorted(r['path'] for r in manifest['rows'])
actual=[]
for root,dirs,files in os.walk(SAVED,followlinks=False):
 for d in dirs:
  s=(pathlib.Path(root)/d).lstat();assert stat.S_ISDIR(s.st_mode)
 for f in files:actual.append(str((pathlib.Path(root)/f).relative_to(SAVED)))
assert sorted(actual)==sorted(r['path'] for r in rows)
currentdifferent=[];total=0;pin={}
for row in rows:
 n=row['path'];rel=pathlib.PurePosixPath(n);assert not rel.is_absolute() and '..' not in rel.parts and str(rel)==n
 p=SAVED/n;s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
 b=p.read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256'];assert git('cat-file','-t',COMMIT+':'+n)==b'blob\n';assert git('show',COMMIT+':'+n)==b
 if (ROOT/n).read_bytes()!=b:currentdifferent.append(n)
 total+=len(b);pin[n]=row['sha256']
assert receipt['logical_bytes_without_manifest']==total-len(body) and total-len(body)<=64*1024**2
must={'MATERIALIZE_REQUEST02.json':'ef024344fba338a34208686ef55f64a784a68571d0194d0e5a14040daa067836','EXACT_COMMAND02.json':'3f20df217e73eb249140687d755ed984c41a0029e868cfcc3ffc544ec16814ac','parent_wait05.py':'33fb83b106e0c9c75162e6f60db4a2eab8cfb6d7248e9173ff7c49b1da0798a3','PARENT_COMMAND05.json':'e150426d3995128f9d37eac51a5d127d2bf9ba100ce62ca728b074f5fcd0cf6a','recover_release02.py':'77e5eac5bddf22e035cd2d4b8f78fe8a6992b82941a476052ecd03a0c09e09c2'}
for n,h in must.items():assert pin[str((A/n).relative_to(ROOT))]==h
q=json.loads((SAVED/A.relative_to(ROOT)/'MATERIALIZE_REQUEST02.json').read_bytes());c=json.loads((SAVED/A.relative_to(ROOT)/'EXACT_COMMAND02.json').read_bytes());p=json.loads((SAVED/A.relative_to(ROOT)/'PARENT_COMMAND05.json').read_bytes())
assert p['cwd']==c['cwd']==q['capsule'];assert p['argv'][2]==str(A/'parent_wait05.py');assert p['argv'][4]==str(A/'EXACT_COMMAND02.json');assert p['argv'][6]==must['EXACT_COMMAND02.json'];assert p['argv'][8]==str(A/'actual-parent-wait02')
assert pin[str(pathlib.Path(c['launcher']['path']).relative_to(ROOT))]==c['launcher']['sha256']=='3eb3c7f578c7b1308992cda0d8f3bea7ca98ed42ae97ad578590e7e993b4ad6a'
review=BASE/'neural-cold-feature-handoff-root-launch-request-review02-2026-10-03'
assert pin[str((review/'REVIEW_PARENT05.md').relative_to(ROOT))]=='4c3bb4a7dc58f98d2b7efc9fee281e71edea726fe54f9ea9a3b4a5d12ca0290b'
assert pin[str((review/'REVIEW_REQUEST02.md').relative_to(ROOT))]=='e79d3087cde4a359d9b2c3d4d8488d70e61c976d08eb473af68d94df0f5810d0'
assert not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules)
print(json.dumps({'receipt_sha256':sha(receiptpath.read_bytes()),'manifest_sha256':sha(body),'commit':COMMIT,'selected_files':184,'logical_without_manifest':total-len(body),'logical_including_manifest':total,'saved_membership_exact':True,'all_objects_present_with_lazy_fetch_disabled':True,'all_bodies_and_hashes_match':True,'current_originals_different':currentdifferent,'exact_request_command_parent_launcher_and_reviews_match':True,'network_or_numerical_or_original_invocation':False},indent=2))
