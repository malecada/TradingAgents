"""Read-only actual outcome recovery; bytes/metadata only, no decoded arrays."""
import hashlib,json,os,stat,subprocess,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;P=BASE/'neural-cold-feature-handoff-materialization-outcome01-2026-10-03';R=P/'outcome-recovery01';C=R/'collection';ORIGINAL=P/'collection01';REMOTE='0a6c751630dd3d086a3ada3675c937462592f633'
def sha(b):return hashlib.sha256(b).hexdigest()
def doc(p):return json.loads(p.read_bytes())
def git(root,*a,input=None):return subprocess.check_output(['git','-c','protocol.allow=never',*a],cwd=root,input=input,env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_OPTIONAL_LOCKS':'0','GIT_NO_REPLACE_OBJECTS':'1','GIT_TERMINAL_PROMPT':'0'},timeout=20)
receipt=doc(P/'REMOTE_OUTCOME_RECOVERY01.json');assert receipt['remote_commit']==REMOTE and len(receipt['selected_blobs'])==52 and git(R/'repository.git','rev-parse','FETCH_HEAD').decode().strip()==REMOTE
for row in receipt['selected_blobs']:
 b=git(R/'repository.git','show',REMOTE+':'+row['path']);assert len(b)==row['bytes'] and sha(b)==row['sha256'] and b==(R/'selected'/row['path']).read_bytes()
meta=doc(P/'OUTCOME_RETENTION01.json');archive=P/'materialization-outcome01.tar.gz';assert sha(archive.read_bytes())==receipt['archive_sha256']==meta['archive_sha256'] and archive.stat().st_size==2563986
rows={r['path']:r for r in meta['members']};assert len(rows)==1023 and len(meta['members'])==1023;seen=set()
with tarfile.open(archive,'r:gz') as tf:
 for m in tf:
  assert m.name=='collection' or m.name.startswith('collection/');name='.' if m.name=='collection' else m.name[len('collection/'):];assert name in rows and name not in seen;seen.add(name);r=rows[name]
  for tree in (C,ORIGINAL):
   p=tree/name;s=p.lstat();assert stat.S_IMODE(s.st_mode)==m.mode==r['mode']
   if r['kind']=='directory':assert m.isdir() and stat.S_ISDIR(s.st_mode)
   else:assert m.isfile() and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==m.size==r['bytes'] and sha(p.read_bytes())==r['sha256']
  if m.isfile():assert sha(tf.extractfile(m).read())==r['sha256']
assert seen==set(rows)
for tree in (C,ORIGINAL):
 actual={'.'}
 for parent,dirs,files in os.walk(tree,followlinks=False):actual.update(str((Path(parent)/n).relative_to(tree)) for n in dirs+files)
 assert actual==seen
assert sum(r['kind']=='file' for r in rows.values())==746 and sum(r['kind']=='directory' for r in rows.values())==277 and sum(r['bytes'] for r in rows.values())==6291908
report=doc(C/'collection.json');assert sha((C/'collection.json').read_bytes())==receipt['collection_sha256']==meta['collection_sha256'];assert report['outcomes']['materialize']['strict_scientific_disposition']=='MATERIALIZATION_COMPLETE_SCIENCE_PENDING' and report['outcomes']['compare']['strict_scientific_disposition']=='NOT_ATTEMPTED_OBSERVED' and report['paper_financial_completion'] is False
for name,pages in report['member_pages'].items():
 merged=[]
 for r in pages:
  p=C/'members'/name/r['path'];b=p.read_bytes();assert len(b)==r['bytes']<=8192 and sha(b)==r['sha256'];merged.extend(json.loads(b))
 assert len({r['path'] for r in merged})==len(merged)
 actual=set()
 for parent,ds,fs in os.walk(C/'data'/name,followlinks=False):actual.update(str((Path(parent)/n).relative_to(C/'data'/name)) for n in ds+fs)
 assert actual=={r['path'] for r in merged}
cap=C/'data/capsule';A='9742c6ec817dd0917f9f35a52e4b83965ca1cd29';T='095fd51e4d65318f4ee92de9873edf98cbee6c9b';S='fb9fad1d93836b4f92f2be8111da4adf22b7e069';assert git(cap,'rev-parse','HEAD').decode().strip()==A
for c,parents in [(A,[T]),(T,[S]),(S,[])]:assert git(cap,'rev-list','--parents','-n','1',c).decode().split()==[c]+parents
assert not(cap/'.git/objects/info/alternates').exists() and not(cap/'.git/info/grafts').exists() and git(cap,'for-each-ref','--format=%(refname)','refs/replace/').strip()==b''
inv=doc(cap/'cold_prep/source_inventory.json');sources={r['target']:r['sha256'] for r in inv['source_inventory']};assert len(sources)==195 and inv['package_count']==147
for name,h in sources.items():assert sha((cap/name).read_bytes())==h and sha(git(cap,'show',A+':'+name))==h
identity='compact-cold-inputs-20261003-01';run=cap/'research_runs'/identity;claim=doc(run/'claim.json');term=doc(run/'complete.json');assert not(run/'failed.json').exists() and term['status']=='complete' and term['claim_sha256']==sha((run/'claim.json').read_bytes()) and claim['source']==A
assert len(claim['inputs'])==9 and claim['family']['attempt_budget']==2 and claim['family']['prior_attempts']==0
for r in claim['inputs'].values():assert sha((cap/r['path']).read_bytes())==r['sha256'] and git(cap,'show',A+':'+r['path'])==(cap/r['path']).read_bytes()
anchor=doc(cap/claim['inputs']['anchor']['path']);assert anchor['commit']==S and len(anchor['files'])==147
for name,h in anchor['files'].items():assert sha(git(cap,'show',S+':'+name))==h==sources[name]
summary=doc(run/'outputs/proof-materialize.json');assert len(summary['inputs'])==43 and summary['registration_pending'] and summary['environment_input_pending'] and summary['historical_jobs_reopened'] is False
components=0
for name,r in summary['inputs'].items():
 b=(cap/r['path']).read_bytes();assert sha(b)==r['sha256']
 if name.startswith('graph-'):
  value=json.loads(b)
  for item in value['arrays'].values():
   binary=cap/Path(r['path']).parent/item['path'];assert binary.stat().st_size==item['bytes'] and sha(binary.read_bytes())==item['sha256'];components+=1
assert components==76
assert term['output_sha256']=={'proof-materialize.json':sha((run/'outputs/proof-materialize.json').read_bytes())}
compare='compact-cold-comparison-20261003-01';assert not(cap/'research_runs'/compare).exists()
assert doc(C/'data/parent-materialize/wait.json')['wrapper_exit_code']==0 and doc(C/'data/wrapper-materialize/tail-complete.json')['requires_actual_wrapper_exit0'] is True
runtime=doc(cap/'cold_prep/runtime.json');assert len(runtime['distribution_records'])==251
release=doc(cap/'cold_release/materialize02/released-envelope02.json');assert release['root']==report['root'] and release['root']!=str(cap)
process=doc(BASE/'neural-cold-feature-handoff-materialization-closure-review01-2026-10-03/PROCESS_NATIVE_READBACK01.json');assert len(process['all_observed_pids'])==11 and all(not Path('/proc',str(n)).exists() for n in process['all_observed_pids']) and not Path(process['cgroup']).exists()
out={'status':'ACCEPTED-exact-actual-outcome-recovery','remote_commit':REMOTE,'selected_remote_blobs':52,'members':1023,'files':746,'directories':277,'logical_bytes':6291908,'archive_sha256':receipt['archive_sha256'],'collection_sha256':receipt['collection_sha256'],'A2':A,'source_count':195,'anchor':147,'registered_inputs':9,'emitted_input_refs':43,'opaque_component_hashes':76,'materialization_disposition':report['outcomes']['materialize']['strict_scientific_disposition'],'comparison_disposition':report['outcomes']['compare']['strict_scientific_disposition'],'all11observed_original_pids_absent':process['all_observed_pids'],'runtime_RECORD_pins':251,'qualification':'Full outcome byte recovery only. No array decoding/rebased authority/runtime or financial-store recovery/job/admission/replay. B2 preparation remains separately reviewed.'}
(HERE/'readback01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
