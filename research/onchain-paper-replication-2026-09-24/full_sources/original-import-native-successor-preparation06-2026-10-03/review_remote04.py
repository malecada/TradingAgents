"""Read already-fetched Git bodies and archive. No fetch/extraction/import/claim."""
from pathlib import Path
import hashlib,json,os,stat,subprocess,tarfile
P=Path(__file__).resolve().parent;R=P.parents[3];OUT=P/'preparation-recovery01';G=OUT/'repository.git';C=OUT/'recovered-capsule04'
def h(b):return hashlib.sha256(b).hexdigest()
def j(p):return json.loads(p.read_bytes())
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0',GIT_OPTIONAL_LOCKS='0')
def git(root,*args):return subprocess.check_output(['git','-c','protocol.allow=never',*args],cwd=root,env=env,stderr=subprocess.PIPE)
r=j(P/'REMOTE_PREPARATION_RECOVERY01.json');commit=r['remote_commit'];assert commit=='27508ce1c7689ae15cd2fdb10ea48f0cd70f25e3'
assert git(G,'rev-parse','FETCH_HEAD').decode().strip()==commit
assert not(G/'objects/info/alternates').exists() and not(C/'.git/objects/info/alternates').exists()
selected={};local_differences=[]
for row in r['selected_blobs']:
 b=git(G,'show',commit+':'+row['path']);assert len(b)==row['bytes'] and h(b)==row['sha256'];selected[Path(row['path']).name]=b
 if b!=(R/row['path']).read_bytes():local_differences.append({'name':Path(row['path']).name,'remote_sha256':h(b),'current_sha256':h((R/row['path']).read_bytes())})
assert len(selected)==30 and [x['name'] for x in local_differences]==['collect_primary05.py']
ret=json.loads(selected['CAPSULE_PREPARATION01.json']);d=json.loads(selected['release-draft01.json']);a=OUT/'capsule-source-input-gate01.tar.gz'
assert a.read_bytes()==selected[a.name] and h(a.read_bytes())==ret['archive_sha256']==r['archive_sha256']
rows={x['path']:x for x in ret['members']};assert len(rows)==990
assert {str(p.relative_to(C)) for p in [C,*C.rglob('*')]}==set(rows)
seen=set()
with tarfile.open(a,'r|gz') as t:
 for m in t:
  n='.' if m.name=='capsule04' else m.name.removeprefix('capsule04/');assert n in rows and n not in seen;seen.add(n);row=rows[n];p=C/n;s=p.lstat()
  assert p.resolve()==p and stat.S_IMODE(s.st_mode)==m.mode==row['mode']
  if row['kind']=='directory':assert m.isdir() and stat.S_ISDIR(s.st_mode)
  else:
   assert m.isfile() and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and m.size==s.st_size==row['bytes']
   with t.extractfile(m) as f:b=f.read(m.size+1)
   assert h(b)==row['sha256'] and b==p.read_bytes() and b==(P/'capsule04'/n).read_bytes()
assert seen==set(rows) and sum(x['bytes'] for x in rows.values())==6943394 and sum(x['allocated_bytes'] for x in rows.values())==9969664
assert sum(x['kind']=='file' for x in rows.values())==702 and sum(x['kind']=='directory' for x in rows.values())==288
assert git(C,'rev-parse','HEAD').decode().strip()==d['capsule_commit']==r['capsule_head']=='ce0e37f8eaaca258c46944a4cbdb9ae30e40fa26'
assert len(d['source_files'])==162
for n,pin in d['source_files'].items():
 b=(C/n).read_bytes();assert h(b)==pin and git(C,'show',d['capsule_commit']+':'+n)==b==git(C,'show',d['source_anchor']+':'+n)
g=(C/d['registration']).read_bytes();assert h(g)==d['registration_sha256'] and git(C,'show',d['capsule_commit']+':'+d['registration'])==g
orig=json.loads(selected['original_inputs01.json']);assert len(orig['inputs'])==11 and len(orig['original_source_files'])==26
for row in orig['inputs']:assert h((C/row['capsule_path']).read_bytes())==row['sha256']
for n,row in orig['original_source_files'].items():assert h(git(C,'show',orig['original_source']+':'+n))==row['claim_sha256']
hist=[]
for i,reported in enumerate(r['historical_claims'],1):
 identity=f'original-import-native-success-20261003-0{i}';run=C/'research_runs'/identity;c=j(run/'claim.json');t=j(run/'failed.json');assert not(run/'complete.json').exists()
 assert reported['identity']==identity and h((run/'claim.json').read_bytes())==reported['claim_sha256']==t['claim_sha256'] and h((run/'failed.json').read_bytes())==reported['terminal_sha256']
 assert c['effective_attempt_budget']==i+1 and t['status']=='failed'
 out={p.name:h(p.read_bytes()) for p in (run/'outputs').iterdir()};assert out==t['output_sha256']==reported['output_sha256'] and len(out)==(4 if i<3 else 2)
 oldgate=git(C,'show',c['source']+':'+c['registration']);assert h(oldgate)==c['registration_sha256'] and json.loads(oldgate)['experiments'][identity]==c['experiment']
 for n,pin in c['experiment']['source_files'].items():assert h(git(C,'show',c['source']+':'+n))==pin
 hist.append({'identity':identity,'source_count':len(c['experiment']['source_files']),'output_count':len(out)})
identity=hist[-1]['identity'];run=C/'research_runs'/identity
assert not any((run/'outputs'/x).exists() for x in ['cell-ledger.json','resource-summary.json'])
source=C/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/identity
assert [j(source/(x+'.json'))['status'] for x in ['import-target-01','import-target-02']]==['failed','unavailable']
outer=C/'fixture_outer'/identity;assert j(outer/'cleanup.json')['unresolved_pid_absence'] is True and j(outer/'terminal.json')['proof'] is None
for i in range(1,5):assert not(C/'research_runs'/f'original-import-native-publication-failure-20261003-0{i}').exists()
assert not(C/'research_runs/original-import-native-success-20261003-04').exists() and not(C/'fixture_outer/original-import-native-success-20261003-04').exists()
print(json.dumps({'receipt_sha256':h((P/'REMOTE_PREPARATION_RECOVERY01.json').read_bytes()),'FETCH_HEAD':commit,'remote_blobs':30,'members':990,'files':702,'directories':288,'logical_bytes':6943394,'original_allocated_bytes':9969664,'current_and_anchor_sources':162,'original_git_paths':26,'original_json':11,'histories':hist,'new_claims':0,'local_remote_differences':local_differences,'runtime_recovered':False,'network_extraction_execution':False},indent=2))
