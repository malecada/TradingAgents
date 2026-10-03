"""Offline actual selected-Git and complete byte recovery review; no array decoding."""
import hashlib,json,os,stat,subprocess,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;MAIN=BASE.parents[2];P=BASE/'neural-cold-feature-handoff-root-compare-request02-2026-10-03';R=P/'capsule-recovery02';T=P/'capsule-retention02';C=R/'source';CAP=Path('/home/malecada/master_thesis/onchain-fixture-isolation/neural-cold-proof-native-20261003-02/source')
def sha(b):return hashlib.sha256(b).hexdigest()
def doc(p):return json.loads(p.read_bytes())
def git(root,*a):return subprocess.check_output(['git','-c','protocol.allow=never',*a],cwd=root,env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_OPTIONAL_LOCKS':'0','GIT_NO_REPLACE_OBJECTS':'1','GIT_TERMINAL_PROMPT':'0'},timeout=20)
q=doc(P/'CAPSULE_RECOVERY_REQUEST02.json');receipt=doc(R/'recovery.json');remote='c2107c74a92891dc5574a15d812873300291b9be';assert q['remote_commit']==receipt['remote_commit']==remote;assert git(R/'repository.git','rev-parse','FETCH_HEAD').decode().strip()==remote
selected=[q['retention'],q['archive'],q['draft'],*q['code']];assert len(selected)==7 and receipt['selected']==selected
for i,row in enumerate(selected):
 b=git(R/'repository.git','show',remote+':'+row['path']);assert len(b)==row['bytes'] and sha(b)==row['sha256'] and b==(R/f'selected-{i:02d}').read_bytes()==(MAIN/row['path']).read_bytes()
meta=doc(T/'retention.json');assert sha((T/'retention.json').read_bytes())=='cac6d1a678e85d814b7f62fcc7185140c8e95b3b80ed96abcf86c81e2c2cbcf0';archive=T/'capsule.tar.gz';assert sha(archive.read_bytes())==meta['archive_sha256']==q['archive']['sha256'] and archive.stat().st_size==2464836;assert archive.read_bytes()==(R/'capsule.tar.gz').read_bytes()==(R/'source.canonical.tar.gz').read_bytes()
rows={r['path']:r for r in meta['members']};assert len(rows)==len(meta['members'])==974;seen=set()
with tarfile.open(archive,'r:gz') as tf:
 for m in tf:
  assert m.name=='source' or m.name.startswith('source/');name='.' if m.name=='source' else m.name[7:];assert name in rows and name not in seen;seen.add(name);r=rows[name]
  for tree in (CAP,T/'source',C):
   p=tree/name;s=p.lstat();assert stat.S_IMODE(s.st_mode)==m.mode==r['mode']
   if r['kind']=='directory':assert m.isdir() and stat.S_ISDIR(s.st_mode)
   else:assert m.isfile() and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==m.size==r['bytes'] and sha(p.read_bytes())==r['sha256']
  if m.isfile():assert sha(tf.extractfile(m).read())==r['sha256']
assert seen==set(rows)
for tree in (CAP,T/'source',C):
 actual={'.'}
 for parent,dirs,files in os.walk(tree,followlinks=False):actual.update(str((Path(parent)/n).relative_to(tree)) for n in dirs+files)
 assert actual==seen
assert (sum(r['kind']=='file' for r in rows.values()),sum(r['kind']=='directory' for r in rows.values()),sum(r.get('bytes',0) for r in rows.values()))==(706,268,5931010)
B='361339125a3f1cd57e7ba8611f5a994ae649fa0b';A='9742c6ec817dd0917f9f35a52e4b83965ca1cd29';S='fb9fad1d93836b4f92f2be8111da4adf22b7e069';assert git(C,'rev-parse','HEAD').decode().strip()==B and git(C,'rev-list','--parents','-n','1',B).decode().split()==[B,A]
assert not(C/'.git/objects/info/alternates').exists() and not(C/'.git/info/grafts').exists() and git(C,'for-each-ref','--format=%(refname)','refs/replace/').strip()==b''
draft=doc(T/'draft.json');adds={r['capsule_path'] for r in draft['exact_four_additions']};changes=git(C,'diff-tree','--no-commit-id','--name-status','-r',A,B).decode().splitlines();assert set(changes)=={'A\t'+p for p in adds}
for r in draft['exact_four_additions']:assert sha((C/r['capsule_path']).read_bytes())==r['sha256'] and len((C/r['capsule_path']).read_bytes())==r['bytes'] and git(C,'show',B+':'+r['capsule_path'])==(C/r['capsule_path']).read_bytes()
first='compact-cold-inputs-20261003-01';second='compact-cold-comparison-20261003-01';oldreg=doc(C/'cold-registration.json');reg=doc(C/'cold-comparison-registration02.json');assert {k:v for k,v in oldreg.items() if k!='experiments'}=={k:v for k,v in reg.items() if k!='experiments'} and reg['experiments'][first]==oldreg['experiments'][first]
e=reg['experiments'][first];new=reg['experiments'][second];assert len(e['source_files'])==195 and new['source_files']==e['source_files'] and new['parent']==first;fam=reg['families'][e['family']];assert(fam['attempt_budget'],fam['prior_attempts'])==(2,0)
for n,h in e['source_files'].items():assert sha((C/n).read_bytes())==h and git(C,'show',A+':'+n)==git(C,'show',B+':'+n)==(C/n).read_bytes()
assert len(e['inputs'])==9
for r in e['inputs'].values():assert sha((C/r['path']).read_bytes())==r['sha256'] and git(C,'show',A+':'+r['path'])==(C/r['path']).read_bytes()
anchor=doc(C/'cold_prep/anchor.json');assert anchor['commit']==S and len(anchor['files'])==147
for n,h in anchor['files'].items():assert sha(git(C,'show',S+':'+n))==h==e['source_files'][n]
run=C/'research_runs'/first;claim=doc(run/'claim.json');term=doc(run/'complete.json');assert claim['source']==term['source']==A and claim['experiment']==e and term['status']=='complete' and term['claim_sha256']==sha((run/'claim.json').read_bytes()) and not(run/'failed.json').exists()
proof=doc(run/'outputs/proof-materialize.json');assert len(proof['inputs'])==43 and proof['registration_pending'] and proof['environment_input_pending'];inputs={('execution_job' if n=='future_execution_job' else n):v for n,v in proof['inputs'].items()}|{'environment':e['inputs']['environment']};assert len(inputs)==44 and inputs==new['inputs'];components=0
for n,r in inputs.items():
 raw=(C/r['path']).read_bytes();assert sha(raw)==r['sha256']
 if n.startswith('graph-'):
  for x in json.loads(raw)['arrays'].values():
   b=(C/Path(r['path']).parent/x['path']).read_bytes();assert len(b)==x['bytes'] and sha(b)==x['sha256'];components+=1
assert components==76 and term['output_sha256']=={'proof-materialize.json':sha((run/'outputs/proof-materialize.json').read_bytes())}
assert len(doc(C/'cold_prep/runtime.json')['distribution_records'])==251
for ns in ('research_runs','proof_outer','proof_supervise','research_artifacts/compact-cold-engineering-20261003','research_artifacts/onchain-paper-replication-2026-09-24/runs'):assert not os.path.lexists(C/ns/second)
release=C/'cold_release/compare02/released-envelope02.json';assert sha(release.read_bytes())=='407642fc43b41b40dc918e40ce81d375fcc0067d2af7d99c44beb42548f64011';assert doc(release)['source']==B and doc(release)['root']==str(CAP)!=str(C)
OLD=BASE/'neural-cold-feature-handoff-materialization-outcome01-2026-10-03';oldmeta=doc(OLD/'OUTCOME_RETENTION01.json');assert len(oldmeta['members'])==1023
oldcaps=OLD/'outcome-recovery01/collection/data/capsule';oldnames={'.'};non_git_files=0;git_changes=[]
for parent,dirs,files in os.walk(oldcaps,followlinks=False):oldnames.update(str((Path(parent)/n).relative_to(oldcaps)) for n in dirs+files)
assert len(oldnames)==959
for name in oldnames:
 p=oldcaps/name;dest=C/name;assert dest.exists()
 if name=='.' or name=='.git' or name.startswith('.git/'):
  if p.is_file() and p.read_bytes()!=dest.read_bytes():git_changes.append(name)
  continue
 assert stat.S_IMODE(p.lstat().st_mode)==stat.S_IMODE(dest.lstat().st_mode)
 if p.is_file():assert p.read_bytes()==dest.read_bytes();non_git_files+=1
newnames=seen-oldnames;allowed=adds|{'cold_release/compare02','cold_release/compare02/released-envelope02.json'};assert all(n in allowed or n.startswith('.git/') for n in newnames)
# Authenticate the whole prior collection remains immutable against its original archive inventory.
for row in oldmeta['members']:
 p=OLD/'outcome-recovery01/collection'/row['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==row['mode']
 if row['kind']=='file':assert s.st_size==row['bytes'] and sha(p.read_bytes())==row['sha256']
process=doc(BASE/'neural-cold-feature-handoff-materialization-closure-review01-2026-10-03/PROCESS_NATIVE_READBACK01.json');assert len(process['all_observed_pids'])==11 and all(not Path('/proc',str(n)).exists() for n in process['all_observed_pids']) and not Path(process['cgroup']).exists()
logs=R/'git-logs';assert (logs/'0000.out').read_text().split()==[remote,'refs/heads/research/onchain-paper-replication-2026-09-24'];outlogs=sorted(logs.glob('*.out'));assert outlogs[-1].read_text().split()==[remote,'refs/heads/research/onchain-paper-replication-2026-09-24']
out={'status':'ACCEPTED-exact-actual-B2-capsule-recovery','remote':remote,'selected_blobs':7,'members':974,'files':706,'directories':268,'logical_bytes':5931010,'archive_sha256':sha(archive.read_bytes()),'B2':B,'source':195,'anchor':147,'runtime_metadata_RECORD':251,'original_inputs':9,'emitted_refs':43,'comparison_refs':44,'opaque_component_hashes':76,'prior_collection_members':1023,'prior_capsule_members':959,'unchanged_prior_non_git_files':non_git_files,'changed_prior_git_files':sorted(git_changes),'added_members':sorted(newnames),'original_materialization':'CLOSED_COMPLETE_SCIENCE_PENDING','comparison':'UNCLAIMED','all11original_pids_and_cgroup_absent':True,'limits':'Seven selected Git bodies and whole capsule bytes; no external reviews/final request, installed runtime or financial stores recovered; no authority rebasing/replay.'}
(HERE/'readback01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
