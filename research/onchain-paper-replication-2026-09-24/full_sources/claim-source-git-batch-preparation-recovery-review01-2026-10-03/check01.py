import hashlib,json,os,stat,subprocess,tarfile
from pathlib import Path,PurePosixPath
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;ROOT=HERE.parents[3]
P=BASE/'claim-source-git-batch-root-integration01-2026-10-03';R=P/'source-preparation-recovery01';C=R/'selected';REMOTE='950a55e2e430a22e1e9f350a20b46c6856f10f77'
def sha(b):return hashlib.sha256(b).hexdigest()
def doc(p):return json.loads(p.read_bytes())
def git(root,*args):return subprocess.check_output(['git','-c','protocol.allow=never',*args],cwd=root,env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_OPTIONAL_LOCKS':'0','GIT_TERMINAL_PROMPT':'0'},timeout=20)
receipt=doc(P/'REMOTE_PREPARATION_RECOVERY01.json');assert receipt['remote_commit']==REMOTE and len(receipt['selected_blobs'])==3
assert git(R/'repository.git','rev-parse','FETCH_HEAD').decode().strip()==REMOTE
for row in receipt['selected_blobs']:
 b=git(R/'repository.git','show',REMOTE+':'+row['path']);assert len(b)==row['bytes'] and sha(b)==row['sha256'] and b==(R/Path(row['path']).name).read_bytes()
meta=doc(R/'SOURCE_PREPARATION_RETENTION01.json');archive=R/'source-preparation-bundle01.tar.gz';assert sha(archive.read_bytes())==receipt['archive_sha256']==meta['archive_sha256'] and archive.stat().st_size==meta['archive_bytes']==1426072
rows={r['path']:r for r in meta['members']};assert len(rows)==meta['files']==299 and sum(r['bytes'] for r in rows.values())==5253487
seen=set()
with tarfile.open(archive,'r:gz') as tf:
 for m in tf:
  assert m.name.startswith('selected/');name=m.name[len('selected/'):];rel=PurePosixPath(name);assert name==str(rel) and not rel.is_absolute() and '..' not in rel.parts
  assert name in rows and name not in seen and m.isfile();seen.add(name);r=rows[name];p=C/name;s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and m.mode==r['mode']==stat.S_IMODE(s.st_mode) and m.size==r['bytes']==s.st_size
  b=tf.extractfile(m).read();assert sha(b)==sha(p.read_bytes())==r['sha256']
assert seen==set(rows)
actual=set();dirs=0
for root,ds,fs in os.walk(C,followlinks=False):
 for name in ds:assert stat.S_ISDIR((Path(root)/name).lstat().st_mode);dirs+=1
 for name in fs:actual.add(str((Path(root)/name).relative_to(C)))
assert actual==seen
prefix='research/onchain-paper-replication-2026-09-24/full_sources/'
T=C/(prefix+'claim-source-git-batch-review01-2026-10-03');tiny=doc(T/'TINY_GIT_RETENTION01.json');a=T/tiny['archive'];assert sha(a.read_bytes())==tiny['archive_sha256'] and a.stat().st_size==tiny['archive_bytes'];expected={r['path']:r for r in tiny['members']};tinyseen=set()
with tarfile.open(a,'r:gz',encoding='utf-8',errors='surrogateescape') as tf:
 for m in tf:
  assert m.name=='tiny-git01' or m.name.startswith('tiny-git01/');name='.' if m.name=='tiny-git01' else m.name[len('tiny-git01/'):];assert name in expected and name not in tinyseen;tinyseen.add(name);r=expected[name];assert m.mode==r['mode']
  if r['kind']=='directory':assert m.isdir()
  else:assert m.isfile() and m.size==r['bytes'] and sha(tf.extractfile(m).read())==r['sha256']
assert tinyseen==set(expected) and len(tinyseen)==64 and sum(r['kind']=='file' for r in expected.values())==39 and sum(r['bytes'] for r in expected.values())==26025
# Recovered actual references; own extent reasoning is not reviewed.
I=C/(prefix+'claim-source-git-batch-root-integration01-2026-10-03');v=doc(I/'INTEGRATION01.json');w=doc(I/'WITHDRAWAL_SOURCE_A01.json')
assert sha((C/v['target']).read_bytes())==v['new_sha256']==sha((C/(prefix+'claim-source-git-batch-candidate01-2026-10-03/candidate01.py')).read_bytes())
for name,h in [('claim-source-git-batch-candidate01-2026-10-03/MANIFEST01.json',v['candidate_manifest']),('claim-source-git-batch-review01-2026-10-03/REVIEW_BATCH01.md',v['independent_review']),('claim-source-git-batch-selected-extents-investigation01-2026-10-03/REPORT01.md',v['selected_extent_report'])]:assert sha((C/(prefix+name)).read_bytes())==h
assert w['status']=='withdrawn-unattempted-root-selection' and w['old_source']=='6ab2bf29f0a31c5465e9b4abc8bfbf97d1dd341e' and w['family_attempt_budget']==2 and w['family_prior_attempts']==0
assert receipt['source_snapshot']==meta['source_commit']=='429236e0f713d4442e392d745be5fe026ce0ac42'
# Authenticity at original MAIN snapshot is local provenance, not recovery of those Git objects.
assert git(ROOT,'rev-parse',meta['source_commit']+'^{commit}').decode().strip()==meta['source_commit']
for name,r in rows.items():assert sha(git(ROOT,'show',meta['source_commit']+':'+name))==r['sha256']
result={'status':'PASS-exact-selected-preparation-recovery','remote_commit':REMOTE,'actual_remote_blobs':3,'source_snapshot':meta['source_commit'],'files':299,'logical_bytes':5253487,'archive_sha256':meta['archive_sha256'],'owned_extraction_directories_observed':dirs,'tiny_archive_members':64,'tiny_archive_files':39,'tiny_archive_directories':25,'tiny_archive_logical_bytes':26025,'original_main_snapshot_provenance_checked_locally':299,'qualification':'299 file bodies recovered through archive; not299 original main Git objects. Original directory modes/runtime/capsules/empirical stores excluded. Own extent reasoning not independently reviewed.'}
(HERE/'readback01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
