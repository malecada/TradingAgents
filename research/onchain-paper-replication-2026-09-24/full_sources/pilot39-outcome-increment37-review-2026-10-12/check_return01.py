from pathlib import Path
import hashlib,json,subprocess,os,tarfile,io
F=Path('research/onchain-paper-replication-2026-09-24/full_sources');D=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/full39outcome37';R=F/'pilot39-outcome-increment37-review-2026-10-12';sha=lambda b:hashlib.sha256(b).hexdigest();E={}
def read(p):
 b=p.read_bytes();E[str(p)]=sha(b);return b
def js(p):return json.loads(read(p))
f=js(D/'FRESH_GIT_RECOVERY37.json');ops=js(D/'GIT_OPERATIONS37.json');cap=js(D/'CAPTURE37.json');s=js(D/'SELECTION37.json');local=js(R/'LOCAL_CAPTURE_REVIEW01.json')
assert E[str(R/'LOCAL_CAPTURE_REVIEW01.json')]=='13644d89a3fbfd8e85b1ec7f43c09cbebefacc86fbed8c7a32903f58c43cef80'
assert ops==f['operations'] and len(ops)==13
names=['local_head','remote_get_url','remote_actual_branch_readback','local_archive_git_tree_join','fresh_bare_init','fresh_remote_add','set_promisor','set_tree_zero_filter','actual_external_commit_only_fetch','fetched_head_readback','actual_external_commit_body','actual_external_selected_blob_fetch','actual_external_archive_blob_return'];assert [x['operation'] for x in ops]==names
raw={}
for op in ops:
 assert op['exit_code']==0
 for stream in ['stdout','stderr']:
  b=read(D/(op['operation']+'.'+stream));assert len(b)==op[stream+'_bytes'] and sha(b)==op[stream+'_sha256'];raw[op['operation']+'.'+stream]=b
source='3e4fa8a605101dcde45397fcf34243fd422dd03a';assert source==f['source']==f['actual_remote_head']==f['actual_fetch_head']==raw['local_head.stdout'].decode().strip()==raw['fetched_head_readback.stdout'].decode().strip()
assert raw['remote_actual_branch_readback.stdout'].decode().strip()==source+'\trefs/heads/research/onchain-paper-replication-2026-09-24'
assert raw['remote_get_url.stdout'].decode().strip()==f['actual_external_source']
commit=raw['actual_external_commit_body.stdout'];assert sha(commit)==f['commit_body_sha256'] and hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest()==source
assert f['capture']['path']==str(D/'CAPTURE37.json') and f['capture']['sha256']==E[str(D/'CAPTURE37.json')]
returned=read(Path(f['returned_archive']['path']));original=read(Path(cap['archive']['path']));assert returned==original==raw['actual_external_archive_blob_return.stdout']
assert len(returned)==f['returned_archive']['bytes']==cap['archive']['bytes']==11663360 and sha(returned)==f['returned_archive']['sha256']==cap['archive']['sha256']=='9356d093879b3c2dc2565ec11994e92adb29b793f1d574d37ec080a1528a770e'
blob=hashlib.sha1(b'blob '+str(len(returned)).encode()+b'\0'+returned).hexdigest();assert blob==f['archive_git_blob_oid'];join='100644 blob '+blob+'\t'+cap['archive']['path'];assert join==f['local_commit_tree_join']==raw['local_archive_git_tree_join.stdout'].decode().strip()
# Read-only local object validation, explicitly prohibit lazy fetching.
env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0','GIT_OPTIONAL_LOCKS':'0'}
def git(args,cwd=Path.cwd()):return subprocess.check_output(['git',*args],cwd=cwd,env=env,timeout=20)
assert git(['cat-file','commit',source])==commit and git(['ls-tree',source,'--',cap['archive']['path']]).decode().strip()==join
bare=Path(f['fresh_bare']);assert bare==Path.cwd().parent/'onchain-pilot-recovery/real-pilot-outcome39-20261012-37.git' and f['no_alternates'] and not (bare/'objects/info/alternates').exists()
assert git(['rev-parse','--is-bare-repository'],bare)==b'true\n' and read(bare/'FETCH_HEAD').decode().split()[0]==source
assert git(['cat-file','commit',source],bare)==commit
expected=sorted(s['rows']+s['directories'],key=lambda r:r['path']);count=0
with tarfile.open(fileobj=io.BytesIO(returned),mode='r:') as archive:
 members=archive.getmembers();assert [m.name for m in members]==[r['path'] for r in expected]
 for m,r in zip(members,expected,strict=True):
  assert m.mode==int(r['mode'],8) and m.uid==m.gid==m.mtime==0
  if r['type']=='directory':assert m.isdir()
  else:assert m.isfile() and m.size==r['bytes'] and sha(archive.extractfile(m).read())==r['sha256'];count+=1
assert count==318
print(json.dumps({'status':'PASS','source':source,'actual_operations':13,'archive_bytes':len(returned),'archive_sha256':sha(returned),'archive_git_blob_oid':blob,'regular_files':318,'directories':56,'fresh_bare':str(bare),'no_alternates':True,'returned_typed_body_checks':True,'accepted_local_pax_reencoding_applies_by_exact_byte_identity':True,'evidence':E,'qualification':'Actual declared increment remote return only. No network/recovery executed by reviewer; only bounded local Git object reads with lazy fetching disabled.'},indent=2))
