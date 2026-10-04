import ast,hashlib,json,os,shutil,stat,time
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;OLD=B/'financial-genuine-wrapper-recordfix-final-union-recovery-preparation01-2026-10-04';CAPTURE=B/'financial-genuine-wrapper-claimedrun-final-capture-preparation01-2026-10-04/capture01.py'
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(v):return (json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
for n in ('recovery04.py','owned_io.py','bounded_git01.py'):shutil.copy2(OLD/n,H/n)
shutil.copy2(OLD/'restore_union01.py',H/'original-restore_union01.py')
shutil.copy2(CAPTURE,H/'CAPTURE_SCHEMA_SOURCE01.py')
ns={'Path':Path}
for n in ast.parse(CAPTURE.read_bytes()).body:
 if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('MAIN','BASE','PARENT','SCOPES'):exec(compile(ast.Module(body=[n],type_ignores=[]),'<static capture context>','exec'),ns)
import sys
sys.path.insert(0,str(H));import recovery04 as R
start=time.monotonic();logical=0;trees=[]
for label,root in sorted(ns['SCOPES'].items()):
 R.require(root.resolve()==root,'canonical original root');rows=[]
 def scan(p,rel):
  global logical
  R.require(time.monotonic()-start<120 and len(rows)<32768,'bounded snapshot');s=p.lstat();before=R.sig(s);r={'path':rel,'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISLNK(s.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
  elif stat.S_ISDIR(s.st_mode):
   r['kind']='directory';rows.append(r)
   for c in sorted(p.iterdir()):scan(c,c.name if rel=='.' else rel+'/'+c.name)
   R.require(R.sig(p.lstat())==before,'directory changed');return
  else:
   R.require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=R.FILE,'bounded original file');body=R.read(root,rel);logical+=len(body);R.require(logical<=64*1024**2,'whole original bound');r.update(kind='file',bytes=len(body),sha256=sha(body),union_path=label+'/'+rel)
  R.require(R.sig(p.lstat())==before,'original changed');rows.append(r)
 scan(root,'.');trees.append({'scope':label,'original_root':str(root),'members':sorted(rows,key=lambda r:r['path'])})
expected={'schema_version':1,'qualification':'Read-only exact complete original census for future capture authentication; not an archive, recovery or release','scope_trees':trees,'source_commit':'0a2e7639b42b9423b90743feadcda4078aa21816','original_regular_logical_bytes':logical};body=enc(expected);R.require(len(body)<=R.FILE,'bounded census');(H/'EXPECTED_ORIGINALS01.json').write_bytes(body)
s=(H/'original-restore_union01.py').read_text();edits=[]
def change(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b);edits.append({'old':a,'new':b})
change("out.name.startswith('financial-genuine-wrapper-recordfix-final-union-flat-')","out.name=='financial-genuine-wrapper-claimedrun-final-union-flat-20261004-01'")
change("mapping['source_commit']=='649fb8a11089524aaef7843dffeeb90a3a55ca17' and mapping['source_manifest_sha256']=='26c67e9c9b28dd4cd607ab3833fa14143d6e8e4c7c3617024275294940ffbc53' and mapping['source_archive_sha256']=='8d49d60b509bc9c95cd04274127b12387b8070295499dad3d24db63b9a376efb' and mapping['source_full_recovery_readback_sha256']=='f86497ee97d6b5d91066db1aa2520d1bed844165b4e08d7169a5917c5bfda4df'","mapping['source_commit']=='0a2e7639b42b9423b90743feadcda4078aa21816' and mapping['source_manifest_sha256']=='fdf77348b81a4d6df8b420b98530f5485900a0461636e1c201506106b036dfd8' and mapping['source_archive_sha256']=='b5b6aad2f515447dc6566cfb716a20ef90031313d48f1ac903ab756735431e24' and mapping['source_full_recovery_readback_sha256']=='468dac2c06e570a89a30771c3f7e1b8e064e6f27e610acf01edcccf91c9a2825'")
a=" scopes={'actual-parent','root-parent-adoption','final-parent-review','root-verifier-binding','actual-verifier-review','binder-preparation','binder-review','caller-preparation','caller-review','verifier-preparation','verifier-review'}\n trees=mapping['scope_trees'];R.require(type(trees)is list and len(trees)==11 and {t['scope'] for t in trees}==scopes,'complete eleven originals')"
change(a," trees=mapping['scope_trees'];validate_expected_trees(trees)")
change("'original_trees':11,'original_typed_members':typed", "'original_trees':len(trees),'original_typed_members':typed")
# Same phrase appears again in return after previous edit; retain exact declared occurrence.
change("return {'original_trees':11,", "return {'original_trees':len(trees),")
change("actual eleven-original mapping/body/mode/link-count joins; no link followed or POSIX tree instantiated","actual complete twenty-original mapping/body/mode/link-count joins; no link followed or POSIX tree instantiated")
new='''EXPECTED_ORIGINALS_SHA256=PIN

def validate_expected_trees(trees):
 raw=R.read(H,'EXPECTED_ORIGINALS01.json');R.require(R.digest(raw)==EXPECTED_ORIGINALS_SHA256,'exact complete original census pin');expected=json.loads(raw)
 R.require(type(trees)is list and len(trees)==20 and trees==expected['scope_trees'],'complete exact twenty original roots/membership/body/modes/literal links')
 # Explicit anchors independently prevent substitution of stale caller/source contexts.
 by={t['scope']:{r['path']:r for r in t['members']} for t in trees}
 anchors={
  ('actual-parent','parent01.py'):'5d5cbdae455c62c3e66b53208b0f79e6e5bbc7ce05d3ded77126da5e0692deda',
  ('actual-parent','REQUEST_FINAL03.json'):'529c9bf3c587e6160a217e8eb339882e59433b6fc0f759d0009d261f872b2bd8',
  ('actual-parent','proofs/FINAL_REVIEW01.json'):'95dadb68b74693212dece8b363156ddc5d98c4b4726a9c50577d2655bb8f3c38',
  ('actual-parent','proofs/CUMULATIVE19_REVIEW01.json'):'3268b76971e4e721222707d16d25dfe84e94104779931e647fb4d7a2bf01202e',
  ('actual-parent','proofs/INDEPENDENT_SOURCE_INPUT_RUNTIME01.json'):'059232d0f7fc8922cee526a1bd30fef2ecb51ee17103284bcaac18c77e77641c',
  ('actual-parent','proofs/FULL_SOURCE_RECOVERY01.json'):'468dac2c06e570a89a30771c3f7e1b8e064e6f27e610acf01edcccf91c9a2825',
  ('root-verifier-binding','generated-claimedrun01/verifier01.py'):'14089451a225aa541eb6faf30c78cb31c79b1380d7ef54d77e895575e3ce250c',
  ('root-verifier-binding','generated-claimedrun01/BINDING01.json'):'57e3b72754668f3be5d1611475b9c29be3fabd91ffe71c5cad60792fa4881989',
  ('actual-verifier-review','MANIFEST01.json'):'0c39988229162fd10b0d0df77f71163a4675a778251a8d75634283e40482bea2',
 }
 for (scope,path),pin in anchors.items():R.require(by[scope][path]['kind']=='file' and by[scope][path]['sha256']==pin,'genuine fixed actual caller/verifier proof '+scope+'/'+path)
 return expected

'''.replace('PIN',repr(sha(body)),1)
change('def authenticate_union(q,m,auth_raw,metadata_raw):',new+'def authenticate_union(q,m,auth_raw,metadata_raw):')
(H/'restore_union01.py').write_text(s);(H/'INVERSE01.json').write_bytes(enc({'original_sha256':sha((H/'original-restore_union01.py').read_bytes()),'candidate_sha256':sha(s.encode()),'edits':edits}));(H/'REQUEST_TEMPLATE01.json').write_bytes(enc({'schema_version':1,'remote_root':None,'remote_receipt_sha256':None,'remote_commit':None,'archive':None,'manifest':None,'union_auth':None,'expected_members':None,'expected_files':None,'expected_logical_bytes':None,'output_root':str(B/'financial-genuine-wrapper-claimedrun-final-union-flat-20261004-01'),'review':None,'release':None}));print(json.dumps({'trees':len(trees),'members':sum(len(t['members']) for t in trees),'regular':sum(r['kind']=='file' for t in trees for r in t['members']),'links':sum(r['kind']=='lexical-symlink' for t in trees for r in t['members']),'logical_bytes':logical,'census_bytes':len(body),'census_sha256':sha(body),'candidate_sha256':sha(s.encode())}))
