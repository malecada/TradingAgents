"""Read-only actual timeout closure; stream hashes, no numerical/package imports."""
import hashlib,json,os,stat,subprocess,tarfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];BASE=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources';P=BASE/'original-import-native-successor-preparation06-2026-10-03';CAP=P/'capsule04';IDENTITY='original-import-native-success-20261003-04'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(65536),b''):h.update(b)
 return h.hexdigest()
def doc(p):return json.loads(p.read_text())
def read_git(*args):return subprocess.check_output(['git',*args],cwd=CAP,env={**os.environ,'GIT_NO_LAZY_FETCH':'1'},timeout=20)
def run():
 receipt=doc(P/'EXECUTION_PRIMARY01.json');ret=doc(P/'RETAINED_PRIMARY01.json');release=doc(P/'release01.json')
 assert sha(P/'RETAINED_PRIMARY01.json')==receipt['retention_sha256'];archive=P/'retained-primary01.tar.gz';assert sha(archive)==ret['archive_sha256'] and archive.stat().st_size==ret['archive_bytes']
 expected={r['path']:r for r in ret['members']};assert len(expected)==1058
 names=set();count=0
 with tarfile.open(archive,'r:gz') as tar:
  for member in tar:
   name=member.name;assert name not in names and name in expected;names.add(name);row=expected[name];assert member.mode==row['mode']
   path=CAP/name;s=path.lstat();assert stat.S_IMODE(s.st_mode)==row['mode']
   if row['kind']=='directory':assert member.isdir() and stat.S_ISDIR(s.st_mode)
   else:
    assert member.isfile() and stat.S_ISREG(s.st_mode) and member.size==s.st_size==row['bytes'];assert sha(path)==row['sha256']
    stream=tar.extractfile(member);h=hashlib.sha256()
    for chunk in iter(lambda:stream.read(65536),b''):h.update(chunk)
    assert h.hexdigest()==row['sha256'];count+=1
 assert names==set(expected) and count==ret['files']==750 and ret['directories']==308
 assert sum(r['bytes'] for r in ret['members'])==ret['logical_bytes']==7301050
 root_names={'.'}
 for parent,dirs,files in os.walk(CAP,followlinks=False):
  for n in dirs+files:root_names.add(str((Path(parent)/n).relative_to(CAP)))
 assert root_names==names,'capsule membership changed after retention'
 claimp=CAP/'research_runs'/IDENTITY/'claim.json';terminalp=claimp.with_name('failed.json');claim=doc(claimp);terminal=doc(terminalp)
 assert sha(claimp)==receipt['claim_sha256']==terminal['claim_sha256'];assert sha(terminalp)==receipt['terminal_sha256'];assert claim['source']==claim['design_source']==receipt['source_commit']==release['capsule_commit'];assert terminal['status']=='failed' and claim['effective_attempt_budget']==5
 assert sha(P/'release01.json')==receipt['release_sha256'];assert read_git('rev-parse','HEAD').decode().strip()==claim['source']
 exp=claim['experiment'];assert len(exp['source_files'])==162
 for name,h in exp['source_files'].items():assert sha(CAP/name)==h and hashlib.sha256(read_git('show',claim['source']+':'+name)).hexdigest()==h
 for name,r in exp['inputs'].items():assert sha(CAP/r['path'])==r['sha256']
 assert sha(CAP/exp['charter']['path'])==exp['charter']['sha256'];assert sha(CAP/release['registration'])==release['registration_sha256']
 for name,h in terminal['output_sha256'].items():assert sha(claimp.parent/'outputs'/name)==h
 assert set(terminal['output_sha256'])=={'resource-binding.json'}
 assert all(not(claimp.parent/'outputs'/n).exists() for n in receipt['missing_registered_outputs'])
 guardbase=CAP/f'research_artifacts/onchain-paper-replication-2026-09-24/runs/{IDENTITY}/guard';guard=doc(guardbase/'final.json');outer=doc(CAP/f'fixture_outer/{IDENTITY}/terminal.json');cleanup=doc(CAP/f'fixture_outer/{IDENTITY}/cleanup.json')
 assert guard['elapsed_seconds']==receipt['native_elapsed_seconds']==1802.3540939379964;assert guard['cleanup_unit_properties']['Result']=='timeout' and guard['cleanup_unit_properties']['ExecMainStatus']=='125';assert guard['child_exit_code'] is None
 assert guard['memory_events']==receipt['memory_events'] and all(v==0 for v in guard['memory_events'].values());assert guard['kernel_controls']==receipt['kernel_controls'];assert outer['status']=='failed' and outer['proof'] is None
 pids={};metadata=[]
 def walk(v,where):
  if isinstance(v,dict):
   for k,value in v.items():
    loc=where+'/'+k
    if (k=='pid' or k.endswith('_pid')) and type(value) is int and value>1:pids.setdefault(value,[]).append(loc)
    if k=='cpu_thread_readback' and isinstance(value,dict):
     for pid in value:
      assert pid.isdigit();pids.setdefault(int(pid),[]).append(loc)
    walk(value,loc)
  elif isinstance(v,list):
   for i,x in enumerate(v):walk(x,where+'/'+str(i))
 for row in ret['members']:
  n=row['path']
  if row['kind']=='file' and IDENTITY in n and n.endswith('.json') and '/fixture_inputs/' not in '/'+n and row['bytes']<=1048576:
   walk(doc(CAP/n),n);metadata.append({'path':n,'sha256':row['sha256']})
 for pid in receipt['recorded_pids_absent']:pids.setdefault(pid,[]).append('root collector recorded_pids_absent')
 assert not any(Path('/proc',str(pid)).exists() for pid in pids),'original PID/TID remains'
 assert guard['cgroup']==receipt['original_cgroup_absent'] and not Path(guard['cgroup']).exists()
 extra=sorted(set(pids)-set(receipt['recorded_pids_absent']))
 imports=[r for r in ret['members'] if IDENTITY in r['path'] and r['path'].endswith('/dictionary-import/import-complete.json')];assert len(imports)==1 and imports[0]['sha256']==receipt['original_dictionary_import_complete_sha256']
 markers=[r['path'] for r in ret['members'] if IDENTITY in r['path'] and '/compact/mcm-' in r['path'] and r['path'].endswith('/complete.json')];assert not markers
 for cell in receipt['separate_root_observed_cells']:
  assert sha(CAP/cell['evidence']['path'])==cell['evidence']['sha256'];assert doc(CAP/cell['evidence']['path'])==cell['original_durable_record']
 assert [c['status'] for c in receipt['separate_root_observed_cells']]==['failed','unavailable']
 post=receipt['actual_selected_post_tail'];assert sha(CAP/post['path'])==post['sha256'] and post['disk_free_bytes']>=10737418240
 assert receipt['actual_selected_raw_authentication'] is None and receipt['actual_selected_raw_authentication_error']['message']=='child terminal snapshot failed/missing'
 claims=sorted((CAP/'research_runs').glob('original-import-native-success-*/claim.json'));assert len(claims)==4 and all(p.with_name('failed.json').exists() for p in claims)
 dependent=release['cases']['second_target_publication_failure']['identity'] if 'identity' in release['cases']['second_target_publication_failure'] else 'original-import-native-publication-failure-20261003-04'
 assert not(CAP/'research_runs'/dependent/'claim.json').exists()
 return {'observed_utc':datetime.now(timezone.utc).isoformat(),'status':'accepted-failed-outcome-local-closure','members':1058,'files':750,'directories':308,'logical_bytes':7301050,'archive_sha256':ret['archive_sha256'],'source_count':162,'input_count':len(exp['inputs']),'all_pids_absent':sorted(pids),'pid_provenance':{str(k):v for k,v in sorted(pids.items())},'extra_guard_or_journal_pids_not_in_collector':extra,'cgroup_absent':guard['cgroup'],'actual_guard_child_exit_code':None,'actual_native_ExecMainStatus':125,'qualification':'Collector native_child_exit_code125 is native unit status, not original guard child_exit_code which is null. Original outer unresolved PID absence retained; this later observation supplements it.','engineering_effective':5,'engineering_closed_failed':4,'dictionary_import_complete':True,'complete_mcm_markers':0,'genuine_scalar_comparison_proof':False,'outputs':['resource-binding.json'],'missing_outputs':receipt['missing_registered_outputs'],'dependent_identity_checked':dependent,'metadata_refs':metadata}
if __name__=='__main__':print(json.dumps(run(),indent=2,sort_keys=True))
