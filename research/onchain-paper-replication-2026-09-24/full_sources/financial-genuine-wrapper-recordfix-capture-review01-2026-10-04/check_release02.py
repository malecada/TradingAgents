import importlib.util,json,os,stat,sys,hashlib
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;P=F/'financial-genuine-wrapper-recordfix-capture-preparation01-2026-10-04';Q=F/'financial-genuine-wrapper-root-recordfix-capture01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(x,m):
 assert x,m
 checks.append(m)
ck(sha((O/'MANIFEST01.json').read_bytes())=='53f3f1a4213bcf3cd1f3fac282d8dcea93e64d1501ba3dcfd651cd5e553b3d97','original source review manifest unchanged')
for r in json.loads((O/'MANIFEST01.json').read_bytes())['members']:
 p=O/r['path'];st=p.lstat();ck(stat.S_IMODE(st.st_mode)==r['mode'],'old reviewed mode unchanged')
 if r['kind']=='file':ck(st.st_size==r['bytes'] and sha(p.read_bytes())==r['sha256'],'old reviewed body unchanged')
 elif r['kind']=='symlink':ck(os.readlink(p)==r['target'],'old witness symlink text unchanged')
ck(sha((P/'capture01.py').read_bytes())=='c4710f2361e6f2e61b1da6e89988a6c1ff43f91f8e4e44c58b71a397feca1096','exact helper unchanged')
sys.path.insert(0,str(P));sp=importlib.util.spec_from_file_location('release_review_capture',P/'capture01.py');C=importlib.util.module_from_spec(sp);sp.loader.exec_module(C);R=C.R
raw=R.read(Q,'REQUEST_PROPOSAL01.json');ck(sha(raw)=='30996eb893ccdb6a089a9f73f3b91b35f9ae3005f1f0b3387fef70c040e25f16','actual proposal pin');q=json.loads(raw);ck(R.encode(q)==raw and q['release'] is None,'canonical unexecuted proposal')
ck(C.contract(q)=='5aaf7cda0a06d94164c39b27d49ae2a5c8694d1b7b80f6c39f39704e987c20ce','exact immutable contract except release')
manifest=R.scan(C.CAP);ck(manifest==q['manifest'] and R.digest(R.encode(manifest))==q['manifest_sha256']=='26c67e9c9b28dd4cd607ab3833fa14143d6e8e4c7c3617024275294940ffbc53','entire986 current writable tree')
ck(len(manifest['members'])==986 and sum(x['kind']=='file' for x in manifest['members'])==713,'exact current fulltree count')
auth=C.authenticate();ck(R.encode(auth)==R.read(Q,'ACTUAL_AUTHENTICATION01.json'),'actual325Git324pins8roles authentication exact')
out=Path(q['output_root']);ck(out==Path('/home/malecada/master_thesis/onchain-financial-isolation/financial-recordfix-source-capture-20261004-01') and out.parent==C.SCOPE and out.resolve()==out and not os.path.lexists(out) and not out.is_relative_to(C.CAP),'fresh fixed disjoint canonical output')
for n in ['research_runs','research_artifacts','fixture_outer']:ck(not os.path.lexists(C.CAP/n),'no current claim/job output '+n)
cwd_matches=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:cwd=os.readlink(p/'cwd')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if cwd==str(C.CAP):cwd_matches.append(int(p.name))
ck(not cwd_matches,'no process currently has corrected source cwd')
free=C.floor(C.CAP);ck(free>=R.FLOOR,'observed actual disk floor')
for key in ['source_review','review_manifest']:C.reference(q[key])
release={'schema_version':1,'decision':'accepted-exact-recordfix-source-capture','contract_sha256':C.contract(q),'source':C.SOURCE,'source_review_sha256':q['source_review']['sha256'],'review_manifest_sha256':q['review_manifest']['sha256'],'helper_sha256':sha((P/'capture01.py').read_bytes())}
# Publish a genuine independent exact contract release only after these real checks.
R.put(O/'EXACT_RELEASE02.json',release);released=dict(q,release={'path':str(O/'EXACT_RELEASE02.json'),'sha256':R.digest(R.encode(release))});ck(C.validate_request(released)==out,'actual unchanged validator accepts genuine independent exact release')
ck(not os.path.lexists(out) and R.scan(C.CAP)==manifest,'no capture and unchanged final source')
ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports')
readback={'schema_version':1,'decision':'ACCEPTED_EXACT_ONE_USE_LOCAL_SOURCE_CAPTURE_CONTRACT','checks':len(checks),'proposal_sha256':sha(raw),'contract_sha256':C.contract(q),'release_sha256':R.digest(R.encode(release)),'output_root':str(out),'source':C.SOURCE,'manifest_sha256':q['manifest_sha256'],'observed_disk_free_bytes':free,'current_corrected_source_cwd_processes':cwd_matches,'actual_capture_executed':False,'native_or_numerical_authority':False}
R.put(O/'RELEASE_READBACK02.json',readback);print(json.dumps(readback,indent=2))
