"""Read-only independent remote preparation verification; fetch prohibited."""
from pathlib import Path
import ast,hashlib,json,os,stat,subprocess,tarfile,sys
P=Path(__file__).resolve().parent;R=P.parents[3];C=P/'capsule03';Q=P/'preparation-recovery01';T=Q/'recovered-capsule03';repo=Q/'repository.git'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0',GIT_OPTIONAL_LOCKS='0')
def git(root,*args):return subprocess.check_output(['git','-c','protocol.allow=never',*args],cwd=root,env=env,stderr=subprocess.PIPE)
r=read(P/'REMOTE_PREPARATION_RECOVERY01.json');m=read(P/'CAPSULE_PREPARATION01.json');d=read(P/'release-draft01.json')
assert r['remote_commit']=='49654293c572953047855d3d04f382f6942460a9' and git(repo,'rev-parse','FETCH_HEAD').decode().strip()==r['remote_commit']
assert len(r['selected_blobs'])==43
for row in r['selected_blobs']:
 b=git(repo,'show',r['remote_commit']+':'+row['path']);assert sha(b)==row['sha256'] and len(b)==row['bytes'] and b==(R/row['path']).read_bytes()
rows={z['path']:z for z in m['members']};assert len(rows)==870
for base in (C,T):
 assert {str(z.relative_to(base)) for z in [base,*base.rglob('*')]}==set(rows)
 for name,row in rows.items():
  p=base/name;s=p.lstat();assert stat.S_IMODE(s.st_mode)==row['mode']
  if row['kind']=='directory':assert stat.S_ISDIR(s.st_mode)
  else:assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==row['bytes'] and sha(p.read_bytes())==row['sha256']
  if base==C:assert s.st_blocks*512==row['allocated_bytes']
for archive in [P/'capsule-source-input-gate01.tar.gz',Q/'capsule-source-input-gate01.tar.gz']:
 assert sha(archive.read_bytes())==r['archive_sha256']==m['archive_sha256'] and archive.stat().st_size==m['archive_bytes']
seen=set()
with tarfile.open(Q/'capsule-source-input-gate01.tar.gz','r|gz') as stream:
 for x in stream:
  name='.' if x.name=='capsule03' else x.name.removeprefix('capsule03/');assert name in rows and name not in seen;seen.add(name);row=rows[name];assert x.mode==row['mode']
  if row['kind']=='directory':assert x.isdir()
  else:
   assert x.isfile() and x.size==row['bytes'];f=stream.extractfile(x)
   with f:b=f.read(x.size+1)
   assert len(b)==row['bytes'] and sha(b)==row['sha256']
assert seen==set(rows)
assert sum(z['bytes'] for z in rows.values())==6254560 and sum(z['allocated_bytes'] for z in rows.values())==8892416
assert sum(z['kind']=='file' for z in rows.values())==616
for base in (C,T):
 assert git(base,'rev-parse','HEAD').decode().strip()==d['capsule_commit']==r['capsule_head']
 for name,pin in d['source_files'].items():
  b=(base/name).read_bytes();assert sha(b)==pin and git(base,'show',d['capsule_commit']+':'+name)==b and git(base,'show',d['source_anchor']+':'+name)==b
 assert sha((base/d['registration']).read_bytes())==d['registration_sha256']
 for entry in d['cases'].values():
  for prefix in ['research_runs','fixture_outer','research_artifacts/onchain-paper-replication-2026-09-24/runs']:assert not(base/prefix/entry['identity']).exists()
 for identity in ['original-import-native-publication-failure-20261003-01','original-import-native-publication-failure-20261003-02']:assert not(base/'research_runs'/identity).exists()
original=read(P.parent/'original-import-fixture-native-preparation-2026-10-03/original_inputs01.json')
for row in original['inputs']:assert sha((T/row['capsule_path']).read_bytes())==row['sha256']
for name,pin in original['original_source_files'].items():assert sha(git(T,'show',original['original_source']+':'+name))==pin['claim_sha256']
for row in r['historical_claims']:
 root=T/'research_runs'/row['identity'];claim=read(root/'claim.json');terminal=read(root/'failed.json')
 assert sha((root/'claim.json').read_bytes())==row['claim_sha256']==terminal['claim_sha256'] and sha((root/'failed.json').read_bytes())==row['terminal_sha256']
 assert not(root/'complete.json').exists() and terminal['status']=='failed'
 assert {p.name:sha(p.read_bytes()) for p in (root/'outputs').iterdir()}==terminal['output_sha256']==row['output_sha256']
 assert claim['source']==row['source'] and claim['effective_attempt_budget']==row['effective_attempt_budget']
 reg=git(T,'show',claim['source']+':'+claim['registration']);assert sha(reg)==claim['registration_sha256'] and json.loads(reg)['experiments'][row['identity']]==claim['experiment']
 for name,pin in claim['experiment']['source_files'].items():assert sha(git(T,'show',claim['source']+':'+name))==pin
# New wrappers retain exact previous semantics after named identity/path substitutions.
prior=P.parent/'original-import-native-successor-preparation04-2026-10-03'
a=(prior/'launch_primary01.py').read_text().replace('original-import-native-success-20261003-02','original-import-native-success-20261003-03').replace('REVIEW_PRIMARY_SUCCESSOR_RELEASE01.md','REVIEW_PRIMARY_SUCCESSOR_RELEASE03.md')
assert ast.dump(ast.parse(a))==ast.dump(ast.parse((P/'launch_primary03.py').read_text()))
a=(prior/'collect_primary01.py').read_text().replace('original-import-native-success-20261003-02','original-import-native-success-20261003-03').replace('capsule02','capsule03')
assert ast.dump(ast.parse(a))==ast.dump(ast.parse((P/'collect_primary03.py').read_text()))
assert not(P/'LAUNCH_INTENT_PRIMARY01.json').exists() and not(P/'OUTER_EXIT_PRIMARY01.json').exists()
assert not {'numpy','torch','scipy','tradingagents'}&set(sys.modules)
print(json.dumps({'receipt_sha256':sha((P/'REMOTE_PREPARATION_RECOVERY01.json').read_bytes()),'remote_commit':r['remote_commit'],'verified_remote_blobs':43,'complete_members':870,'files':616,'directories':254,'logical_bytes':6254560,'original_allocated_bytes':8892416,'archive_sha256':r['archive_sha256'],'archive_bytes':m['archive_bytes'],'HEAD':d['capsule_commit'],'source_anchor':d['source_anchor'],'source_and_anchor_joins':159,'original_source_paths':26,'original_inputs':11,'historical_claims':len(r['historical_claims']),'historical_source_bodies':[h['source_bodies'] for h in r['historical_claims']],'new_namespaces_absent':True,'launch_wrapper_AST_parity':True,'collector_AST_parity':True,'launch_sha256':sha((P/'launch_primary03.py').read_bytes()),'collector_sha256':sha((P/'collect_primary03.py').read_bytes()),'numerical_imports':False},indent=2))
