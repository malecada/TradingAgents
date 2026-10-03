"""Offline review of actual recovered SCI sourceA; no authority or numerical imports."""
import hashlib,json,os,stat,subprocess,tarfile
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4];P=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/neural-cold-feature-handoff-root-integration01-2026-10-03';R=P/'sourceA-recovery01';C=R/'source';REMOTE='6c5615481c52087ea648540061102afbc8c34331'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(65536),b''):h.update(b)
 return h.hexdigest()
def doc(p):return json.loads(p.read_text())
def git(root,*args):return subprocess.check_output(['git',*args],cwd=root,env={**os.environ,'GIT_NO_LAZY_FETCH':'1'},timeout=20)
def main():
 report=doc(P/'REMOTE_SOURCE_A_RECOVERY01.json');assert report['remote_commit']==REMOTE and len(report['selected_blobs'])==13
 assert git(R/'repository.git','rev-parse','FETCH_HEAD').decode().strip()==REMOTE
 for r in report['selected_blobs']:
  b=git(R/'repository.git','show',REMOTE+':'+r['path']);assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'];assert (R/Path(r['path']).name).read_bytes()==b
 metadata=doc(R/'SOURCE_A_RETENTION01.json');archive=R/'sourceA-capsule01.tar.gz';assert sha(archive)==metadata['archive_sha256']==report['archive_sha256'];rows={r['path']:r for r in metadata['members']};assert len(rows)==728;seen=set()
 with tarfile.open(archive,'r:gz') as tar:
  for member in tar:
   assert member.name=='source' or member.name.startswith('source/');name='.' if member.name=='source' else member.name[7:];assert name in rows and name not in seen;seen.add(name);r=rows[name];p=C/name;s=p.lstat();assert stat.S_IMODE(s.st_mode)==member.mode==r['mode']
   if r['kind']=='directory':assert member.isdir() and stat.S_ISDIR(s.st_mode)
   else:
    assert member.isfile() and stat.S_ISREG(s.st_mode) and member.size==s.st_size==r['bytes'];assert sha(p)==r['sha256'];h=hashlib.sha256();f=tar.extractfile(member)
    for b in iter(lambda:f.read(65536),b''):h.update(b)
    assert h.hexdigest()==r['sha256']
 assert seen==set(rows);actual={'.'}
 for parent,dirs,files in os.walk(C,followlinks=False):actual.update(str((Path(parent)/n).relative_to(C)) for n in dirs+files)
 assert actual==seen and sum(r['kind']=='file' for r in rows.values())==507 and sum(r['bytes'] for r in rows.values())==5094899
 A=metadata['source_A'];T=metadata['source_T'];S=metadata['anchor_S'];assert A=='6ab2bf29f0a31c5465e9b4abc8bfbf97d1dd341e';assert git(C,'rev-parse','HEAD').decode().strip()==A
 assert git(C,'rev-list','--parents','-n','1',A).decode().split()==[A,T];assert git(C,'rev-list','--parents','-n','1',T).decode().split()==[T,S];assert git(C,'rev-list','--parents','-n','1',S).decode().split()==[S];assert not(C/'.git/objects/info/alternates').exists()
 release=doc(R/'PROPOSED_MATERIALIZATION_RELEASE01.json');assert release['source']==A and release['status']=='draft' and release['remaining'];sources=doc(C/release['sources']['path'])['files'];assert len(sources)==195
 for n,h in sources.items():assert sha(C/n)==h and hashlib.sha256(git(C,'show',A+':'+n)).hexdigest()==h
 for key in ('registration','sources','runtime','native_environment','phase_contract'):
  ref=release[key];assert sha(C/ref['path'])==ref['sha256'] and (C/ref['path']).stat().st_size==ref['bytes'];assert git(C,'show',A+':'+ref['path'])==(C/ref['path']).read_bytes()
 registration=doc(C/release['registration']['path']);ID='compact-cold-inputs-20261003-01';assert set(registration['experiments'])=={ID};assert registration['program_id']=='compact-cold-engineering-20261003';e=registration['experiments'][ID];family=registration['families'][e['family']];assert family['attempt_budget']==2 and family['prior_attempts']==0 and registration['datasets']['synthetic-cold']['exposures']==[];assert len(e['inputs'])==9 and e['source_files']==sources
 for name,ref in e['inputs'].items():assert sha(C/ref['path'])==ref['sha256'] and git(C,'show',A+':'+ref['path'])==(C/ref['path']).read_bytes()
 assert sha(C/e['charter']['path'])==e['charter']['sha256'];contract=doc(C/release['phase_contract']['path']);assert contract['experiment']==e and contract['family']==family and contract['expected_outputs']==e['outputs']==['proof-materialize.json']
 anchor=doc(C/e['inputs']['anchor']['path']);assert anchor['commit']==S and len(anchor['files'])==147
 for n,h in anchor['files'].items():assert h==sources[n] and hashlib.sha256(git(C,'show',S+':'+n)).hexdigest()==h
 runtime=doc(C/release['runtime']['path']);assert len(runtime['distribution_records'])==len({r['name'] for r in runtime['distribution_records']})==251
 native=doc(C/release['native_environment']['path']);software=doc(C/e['inputs']['environment']['path']);assert set(native).isdisjoint(software);assert native['PYTHONPATH']==release['root'] and release['root']!=str(C)
 for ident in (ID,'compact-cold-comparison-20261003-01'):
  for namespace in ('research_runs','proof_outer','proof_supervise','research_artifacts/compact-cold-engineering-20261003','research_artifacts/onchain-paper-replication-2026-09-24/runs'):assert not(C/namespace/ident).exists()
 return {'observed_utc':datetime.now(timezone.utc).isoformat(),'status':'accepted-exact-sourceA-recovery','remote_commit':REMOTE,'selected_blobs':13,'members':728,'files':507,'directories':221,'logical_bytes':5094899,'source_A':A,'source_T':T,'anchor_S':S,'source_count':195,'anchor_count':147,'registered_inputs':9,'runtime_RECORD_pins_retained':251,'release_status':'draft','restored_paths_rebound':False,'installed_runtime_verified_by_recovery':False,'restored_authority_claimed':False}
if __name__=='__main__':print(json.dumps(main(),indent=2,sort_keys=True))
