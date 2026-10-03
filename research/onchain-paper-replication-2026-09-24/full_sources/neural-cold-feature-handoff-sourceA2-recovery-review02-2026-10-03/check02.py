"""Read-only recovered sourceA2 scope check; no numerical/admission/Owner imports."""
import hashlib,json,os,stat,subprocess,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;P=BASE/'neural-cold-feature-handoff-root-integration02-2026-10-03';R=P/'sourceA2-recovery02';C=R/'source';REMOTE='6778fedd54117aec7b09d210286ea2f69341d8de'
def sha(b):return hashlib.sha256(b).hexdigest()
def doc(p):return json.loads(p.read_bytes())
def git(root,*a,input=None):return subprocess.check_output(['git','-c','protocol.allow=never',*a],cwd=root,input=input,env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_OPTIONAL_LOCKS':'0','GIT_NO_REPLACE_OBJECTS':'1','GIT_TERMINAL_PROMPT':'0'},timeout=20)
receipt=doc(P/'REMOTE_SOURCE_A_RECOVERY02.json');assert receipt['remote_commit']==REMOTE and len(receipt['selected_blobs'])==13
assert git(R/'repository.git','rev-parse','FETCH_HEAD').decode().strip()==REMOTE
for row in receipt['selected_blobs']:
 b=git(R/'repository.git','show',REMOTE+':'+row['path']);assert len(b)==row['bytes'] and sha(b)==row['sha256'] and b==(R/Path(row['path']).name).read_bytes()
meta=doc(R/'SOURCE_A_RETENTION02.json');archive=R/'sourceA2-capsule02.tar.gz';assert sha(archive.read_bytes())==meta['archive_sha256']==receipt['archive_sha256'] and archive.stat().st_size==2313910
rows={r['path']:r for r in meta['members']};assert len(rows)==len(meta['members'])==733;seen=set()
with tarfile.open(archive,'r:gz') as tf:
 for m in tf:
  assert m.name=='source' or m.name.startswith('source/');name='.' if m.name=='source' else m.name[7:];assert name in rows and name not in seen;seen.add(name);r=rows[name];p=C/name;s=p.lstat();assert stat.S_IMODE(s.st_mode)==m.mode==r['mode']
  if r['kind']=='directory':assert stat.S_ISDIR(s.st_mode) and m.isdir()
  else:assert stat.S_ISREG(s.st_mode) and m.isfile() and s.st_size==m.size==r['bytes'] and sha(p.read_bytes())==sha(tf.extractfile(m).read())==r['sha256']
assert seen==set(rows);actual={'.'}
for parent,dirs,files in os.walk(C,followlinks=False):actual.update(str((Path(parent)/n).relative_to(C)) for n in dirs+files)
assert actual==seen;assert sum(r['kind']=='file' for r in rows.values())==507 and sum(r['kind']=='directory' for r in rows.values())==226 and sum(r['bytes'] for r in rows.values())==5106027
A='9742c6ec817dd0917f9f35a52e4b83965ca1cd29';T='095fd51e4d65318f4ee92de9873edf98cbee6c9b';S='fb9fad1d93836b4f92f2be8111da4adf22b7e069';assert git(C,'rev-parse','HEAD').decode().strip()==A
for c,parents in [(A,[T]),(T,[S]),(S,[])]:assert git(C,'rev-list','--parents','-n','1',c).decode().split()==[c]+parents
assert git(C,'rev-list','--all').decode().splitlines()==[A,T,S]
for n in ('.git/objects/info/alternates','.git/info/grafts','.git/shallow'):assert not(C/n).exists()
assert git(C,'for-each-ref','--format=%(refname)','refs/replace/').strip()==b''
regmeta=doc(R/'REGISTRATION_SOURCE_A02.json');snap=doc(R/'SOURCE_GIT_SNAPSHOT02.json');prep=doc(R/'INPUT_PREPARATION02.json');assert regmeta['source_A2']==A and regmeta['source_T2']==T and regmeta['source_S2']==S and snap['source_S2']==S
for parent,child,wanted in [(S,T,prep['actual_added_files']),(T,A,regmeta['added_files'])]:
 parts=git(C,'diff-tree','--no-commit-id','--name-status','-r','-z',parent,child).decode().split('\0');pairs=list(zip(parts[:-1:2],parts[1:-1:2]));assert all(k=='A' for k,n in pairs) and sorted(n for k,n in pairs)==sorted(wanted)
release=doc(R/'PROPOSED_MATERIALIZATION_RELEASE02.json');assert release['source']==A and release['status']=='draft' and release['remaining'] and release['prior_materialization'] is None
for k in ('registration','sources','phase_contract','runtime','native_environment'):
 r=release[k];b=(C/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256'] and git(C,'show',A+':'+r['path'])==b
sources=doc(C/release['sources']['path'])['files'];inv=doc(C/'cold_prep/source_inventory.json');assert len(sources)==195 and inv['package_count']==147 and sources=={r['target']:r['sha256'] for r in inv['source_inventory']}
def batch(commit,mapping):
 names=sorted(mapping);wire=git(C,'cat-file','--batch',input=''.join(commit+':'+n+'\n' for n in names).encode());off=0
 for n in names:
  end=wire.index(b'\n',off);oid,kind,size=wire[off:end].split();size=int(size);assert kind==b'blob' and len(oid)==40 and size<=4194304;b=wire[end+1:end+1+size];assert sha(b)==mapping[n] and b==(C/n).read_bytes() and wire[end+1+size:end+2+size]==b'\n';off=end+2+size
 assert off==len(wire)
batch(A,sources)
reg=doc(C/release['registration']['path']);identity='compact-cold-inputs-20261003-01';assert reg['program_id']=='compact-cold-engineering-20261003' and set(reg['experiments'])=={identity};e=reg['experiments'][identity];assert len(e['inputs'])==9 and e['source_files']==sources and e['parent'] is None
family=reg['families'][e['family']];assert family['attempt_budget']==2 and family['prior_attempts']==0 and reg['datasets']['synthetic-cold']['exposures']==[]
assert doc(C/release['phase_contract']['path'])=={'schema_version':1,'identity':identity,'experiment':e,'family':family,'expected_outputs':e['outputs']}
for r in e['inputs'].values():assert sha((C/r['path']).read_bytes())==r['sha256'] and git(C,'show',A+':'+r['path'])==(C/r['path']).read_bytes()
anchor=doc(C/e['inputs']['anchor']['path']);assert anchor['commit']==S and anchor['files']=={n:h for n,h in sources.items() if n.startswith('tradingagents/')} and len(anchor['files'])==147;batch(S,anchor['files'])
assert doc(R/'numerical-anchor02.json')==anchor
assert sha((C/e['charter']['path']).read_bytes())==e['charter']['sha256']
runtime=doc(C/release['runtime']['path']);assert len(runtime['distribution_records'])==len({r['name'] for r in runtime['distribution_records']})==251
native=doc(C/release['native_environment']['path']);software=doc(C/e['inputs']['environment']['path']);assert set(native).isdisjoint(software)
# Recovery retains original absolute mapping; never convert recovered path to authority.
original=Path(regmeta['root']);assert release['root']==str(original) and original!=C and doc(C/e['inputs']['future_resources']['path'])['storage_budget']['root']==str(original)
# Original withdrawal remains external reference; body presence is not fabricated.
oldA='6ab2bf29f0a31c5465e9b4abc8bfbf97d1dd341e';assert regmeta['old_A_withdrawn_unchanged']==oldA and snap['old_A_unchanged']==oldA
withdrawreview=BASE/'claim-source-git-batch-root-integration-review01-2026-10-03/REVIEW_INTEGRATION01.md';assert sha(withdrawreview.read_bytes())==snap['withdrawal_review']=='bd3bf8f02c856366e926ba51f36a07111cca3ebd3d9201594cded0cdd05881f6'
absent=[]
for ident in (identity,'compact-cold-comparison-20261003-01'):
 for base in ('research_runs','proof_outer','proof_supervise','research_artifacts/compact-cold-engineering-20261003','research_artifacts/onchain-paper-replication-2026-09-24/runs'):
  p=C/base/ident;assert not p.exists() and not p.is_symlink();absent.append(str(p))
# Compare original selected source/inputs only; no inferred live authority or runtime checks.
for n,h in sources.items():assert sha((original/n).read_bytes())==h
for r in e['inputs'].values():assert sha((original/r['path']).read_bytes())==r['sha256']
result={'status':'PASS-exact-recovered-A2-preparation-only','remote_commit':REMOTE,'selected_remote_blobs':13,'members':733,'files':507,'directories':226,'logical_bytes':5106027,'archive_sha256':receipt['archive_sha256'],'A2':A,'T2':T,'S2':S,'sources':195,'anchor':147,'inputs':9,'runtime_RECORD_pins_retained':251,'draft_status':release['status'],'absent_recovered_namespaces':absent,'external_withdrawal_review':snap['withdrawal_review'],'qualification':'Installed runtime/empirical stores/release/Owner/numerical/native capacity/live PID or global dedup authority not recovered or inferred.'}
(HERE/'readback02.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='absent_recovered_namespaces'},sort_keys=True))
