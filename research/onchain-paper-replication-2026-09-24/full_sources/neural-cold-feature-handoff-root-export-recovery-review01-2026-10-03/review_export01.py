"""Independent remote export and genuine Git snapshot verification, read only."""
import ast,hashlib,json,os,stat,subprocess,tarfile
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3];I=P.with_name('neural-cold-feature-handoff-root-integration01-2026-10-03');O=I/'export-recovery01';G=O/'repository.git';S=O/'source'
def h(b):return hashlib.sha256(b).hexdigest()
def j(p):return json.loads(p.read_bytes())
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0',GIT_OPTIONAL_LOCKS='0')
def git(root,*args):return subprocess.check_output(['git','-c','protocol.allow=never',*args],cwd=root,env=env,stderr=subprocess.PIPE)
r=j(I/'REMOTE_SOURCE_EXPORT_RECOVERY01.json');commit=r['remote_commit'];assert commit=='1cdc42223108e6a04defc69954a63fcec94abaa5' and git(G,'rev-parse','FETCH_HEAD').decode().strip()==commit
assert not(G/'objects/info/alternates').exists();assert len(r['selected_blobs'])==5
for row in r['selected_blobs']:
 b=git(G,'show',commit+':'+row['path']);assert len(b)==row['bytes'] and h(b)==row['sha256'] and b==(R/row['path']).read_bytes()==(O/Path(row['path']).name).read_bytes()
ret=j(O/'SOURCE_EXPORT_RETENTION01.json');a=O/'source-export01.tar.gz';assert h(a.read_bytes())==ret['archive_sha256']==r['archive_sha256'] and a.stat().st_size==ret['archive_bytes']
rows={x['path']:x for x in ret['members']};assert len(rows)==235 and {str(p.relative_to(S)) for p in [S,*S.rglob('*')]}==set(rows)
seen=set()
with tarfile.open(a,'r|gz') as t:
 for m in t:
  n='.' if m.name=='source' else m.name.removeprefix('source/');assert n in rows and n not in seen;seen.add(n);row=rows[n];p=S/n;s=p.lstat()
  assert p.resolve()==p and stat.S_IMODE(s.st_mode)==row['mode']==m.mode
  if row['kind']=='directory':assert m.isdir() and stat.S_ISDIR(s.st_mode)
  else:
   assert m.isfile() and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and m.size==s.st_size==row['bytes']
   with t.extractfile(m) as f:b=f.read(m.size+1)
   assert h(b)==row['sha256'] and b==p.read_bytes()
assert seen==set(rows) and sum(x['bytes'] for x in rows.values())==3403631
snap=j(I/'SOURCE_GIT_SNAPSHOT01.json');C=Path(snap['capsule']);anchor=j(I/'numerical-anchor01.json');cid=snap['source_commit']
assert cid==anchor['commit']=='c65287a2c70fdc38fd6335a994dfd29fe97e26b4' and h((I/'numerical-anchor01.json').read_bytes())==snap['numerical_anchor']['sha256']
assert git(C,'rev-parse','HEAD').decode().strip()==cid and not(C/'.git/objects/info/alternates').exists() and not(C/'.git/shallow').exists() and not(C/'.git/info/grafts').exists()
commit_body=git(C,'cat-file','commit',cid);assert not any(line.startswith(b'parent ') for line in commit_body.splitlines())
assert git(C,'for-each-ref','refs/replace')==b''
files={n for n,row in rows.items() if row['kind']=='file'};assert len(files)==200
assert set(git(C,'ls-tree','-r','--name-only',cid).decode().splitlines())==files
for n in files:
 b=(C/n).read_bytes();assert b==(S/n).read_bytes()==git(C,'show',cid+':'+n) and h(b)==rows[n]['sha256']
assert git(C,'diff','--no-ext-diff','--exit-code',cid,'--')==b''
inv=j(S/'cold_prep/source_inventory.json');sources=inv['source_inventory'];assert len(sources)==195
for row in sources:
 b=(C/row['target']).read_bytes();assert h(b)==row['sha256'] and len(b)==row['bytes'] and b==(R/row['origin']).read_bytes()
# Extract only the actual stdlib file-discovery function, not package imports.
job=C/'tradingagents/research/onchain_replication/job.py';tree=ast.parse(job.read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='required_sources');ns={'Path':Path,'__file__':str(job)}
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(job),'exec'),ns);required=ns['required_sources']()
assert set(anchor)=={'commit','files'} and set(anchor['files'])==required and len(required)==147
for n,pin in anchor['files'].items():assert h((C/n).read_bytes())==pin and h(git(C,'show',cid+':'+n))==pin
assert sum((C/n).stat().st_size for n in required)==1477313
for n in ['research_runs','research_artifacts','fixture_outer']:assert not(C/n).exists()
fail=j(I/'RECOVERY_SOURCE_PREFLIGHT_FAILURE01.json');assert h((I/'recover_export.baseline01.py').read_bytes())==fail['source_sha256'] and fail['actual_remote_fetches']==fail['actual_recovery_trees_created']==0
print(json.dumps({'remote_receipt_sha256':h((I/'REMOTE_SOURCE_EXPORT_RECOVERY01.json').read_bytes()),'remote_commit':commit,'selected_blobs':5,'archive_sha256':h(a.read_bytes()),'members':235,'files':200,'directories':35,'logical_bytes':3403631,'original_allocated_bytes':sum(x['allocated_bytes'] for x in rows.values()),'genuine_initial_commit':cid,'parent_count':0,'tracked_files':200,'current_source_origins':195,'required_package':147,'package_bytes':1477313,'snapshot_receipt_sha256':h((I/'SOURCE_GIT_SNAPSHOT01.json').read_bytes()),'numerical_anchor_sha256':h((I/'numerical-anchor01.json').read_bytes()),'no_claim_or_artifact_namespace':True,'no_network_extraction_numerics_jobs':True},indent=2))
