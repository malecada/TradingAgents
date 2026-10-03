"""Independent failed-outcome verification: no fetch, extraction or execution."""
import ast,hashlib,json,os,stat,subprocess,tarfile,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];P=HERE.parent/'original-import-native-successor-preparation04-2026-10-03';CAP=P/'capsule02'; REC=P/'failure-recovery01';REST=REC/'recovered-failed-capsule02'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0',GIT_OPTIONAL_LOCKS='0')
def git(root,*args):return subprocess.check_output(['git','-c','protocol.allow=never',*args],cwd=root,env=env,stderr=subprocess.PIPE)
x=load(P/'EXECUTION_PRIMARY01.json');m=load(P/'RETAINED_PRIMARY01.json');r=load(P/'REMOTE_FAILED_PRIMARY_RECOVERY01.json');rel=load(P/'release01.json')
assert sha((P/'EXECUTION_PRIMARY01.json').read_bytes())=='d7b7193703bff5ffcf09d6b003feabb639fd45ad1fca25349433d69605f2d3ae'
assert sha((P/'RETAINED_PRIMARY01.json').read_bytes())==x['retention_sha256']=='2d1972192c89d7db31308aa97edfa596690c9bcb44d9eabfdb6b26b1ff1cbd9a'
assert sha((P/'REMOTE_FAILED_PRIMARY_RECOVERY01.json').read_bytes())=='ae95acd6b1d39fa5d39978259d2a0e84dd023a6fe99cd0af8d8e35a8a88fdc34'
for archive in [P/'retained-primary01.tar.gz',REC/'retained-primary01.tar.gz']:
 assert sha(archive.read_bytes())==m['archive_sha256']==r['archive_sha256'] and archive.stat().st_size==m['archive_bytes']
rows={z['path']:z for z in m['members']};assert len(rows)==817
for root in (CAP,REST):
 actual={str(z.relative_to(root)) for z in [root,*root.rglob('*')]};assert actual==set(rows)
 for name,row in rows.items():
  q=root/name;s=q.lstat();assert stat.S_IMODE(s.st_mode)==row['mode']
  if row['kind']=='file':assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==row['bytes'] and sha(q.read_bytes())==row['sha256']
  else:assert stat.S_ISDIR(s.st_mode)
  if root==CAP:assert s.st_blocks*512==row['allocated_bytes']
seen=set()
with tarfile.open(REC/'retained-primary01.tar.gz','r|gz') as t:
 for member in t:
  name='.' if member.name=='capsule02' else member.name.removeprefix('capsule02/')
  assert name in rows and name not in seen;seen.add(name);row=rows[name];assert member.mode==row['mode']
  if row['kind']=='directory':assert member.isdir()
  else:
   assert member.isfile() and member.size==row['bytes'];f=t.extractfile(member)
   with f:b=f.read(member.size+1)
   assert len(b)==row['bytes'] and sha(b)==row['sha256']
assert seen==set(rows)
assert sum(z['bytes'] for z in rows.values())==5973237 and sum(z['allocated_bytes'] for z in rows.values())==8441856
assert sum(z['kind']=='file' for z in rows.values())==579
repo=REC/'repository.git';assert git(repo,'rev-parse','FETCH_HEAD').decode().strip()==r['remote_commit']
for z in r['selected_blobs']:
 b=git(repo,'show',r['remote_commit']+':'+z['path']);assert len(b)==z['bytes'] and sha(b)==z['sha256'] and b==(ROOT/z['path']).read_bytes()
assert len(r['selected_blobs'])==53
for root in [CAP,REST]:
 assert git(root,'rev-parse','HEAD').decode().strip()==x['source_commit']==rel['capsule_commit']
 for name,pin in rel['source_files'].items():
  b=(root/name).read_bytes();assert sha(b)==pin
  assert git(root,'show',rel['capsule_commit']+':'+name)==b and git(root,'show',rel['source_anchor']+':'+name)==b
 assert sha((root/rel['registration']).read_bytes())==rel['registration_sha256']
original=load(HERE.parent/'original-import-fixture-native-preparation-2026-10-03/original_inputs01.json')
for row in original['inputs']:assert sha((REST/row['capsule_path']).read_bytes())==row['sha256']
for name,pin in original['original_source_files'].items():assert sha(git(REST,'show',original['original_source']+':'+name))==pin['claim_sha256']
i=x['identity'];run=CAP/'research_runs'/i;claim=load(run/'claim.json');term=load(run/'failed.json')
assert sha((run/'claim.json').read_bytes())==x['claim_sha256']==term['claim_sha256'] and sha((run/'failed.json').read_bytes())==x['terminal_sha256']
assert term['status']=='failed' and not (run/'complete.json').exists() and claim['effective_attempt_budget']==3
assert claim['source']==rel['capsule_commit'] and claim['registration_sha256']==rel['registration_sha256']
assert {f.name:sha(f.read_bytes()) for f in (run/'outputs').iterdir()}==term['output_sha256']==r['output_hashes']
assert load(run/'outputs/cell-ledger.json')==x['cells'] and [c['status'] for c in x['cells']]==['failed','unavailable']
old=CAP/'research_runs/original-import-native-success-20261003-01'
assert sha((old/'claim.json').read_bytes())=='f475dd6c04d7dfc5e9d94bba30b5d3e686d1b71b5f5394dfa1aa0b174797f61e'
assert sha((old/'failed.json').read_bytes())=='09206641f5ce569716bbf61246ecc85c20daa3ed40bf7f82427e4772198881c0'
base=CAP/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/i;g=load(base/'guard/final.json');ch=load(base/'guard/child_exit.json');ready=load(base/'guard/cpu_ready.json')
assert g['child_exit_code']==ch['exit_code']==1 and g['cleanup_verified'] is True
assert g['memory_events']==x['memory_events'] and all(v==0 for v in g['memory_events'].values())
assert g['kernel_controls']==x['kernel_controls'] and g['peak_sampled_memory_current_bytes']==393662464 and g['elapsed_seconds']==257.8945938109973
assert all(not Path('/proc',str(pid)).exists() for pid in x['recorded_pids_absent']) and len(x['recorded_pids_absent'])==6
assert not Path(x['original_cgroup_absent']).exists()
unit=subprocess.run(['systemctl','--user','show',g['unit'],'--property=ActiveState,SubState,ControlGroup,Result,ExecMainStatus'],capture_output=True,text=True,timeout=10);assert unit.returncode==0
props=dict(z.split('=',1) for z in unit.stdout.splitlines() if '=' in z);assert props['ActiveState'] in ['inactive','failed'] and props['ControlGroup']==''
journals=list((CAP/'research_artifacts/onchain_representations').glob('*/'+i));assert len(journals)==1;j=journals[0]
assert sha((j/'compact/dictionary-import/import-complete.json').read_bytes())==x['original_dictionary_import_complete_sha256']
stages=list(j.glob('compact/mcm-*'));assert len(stages)==1 and not (stages[0]/'stage-complete.json').exists()
assert not (CAP/'research_artifacts/onchain_compact_outputs').exists()
outer=CAP/'fixture_outer'/i;assert load(outer/'terminal.json')['proof'] is None and load(outer/'cleanup.json')['unresolved_pid_absence'] is True
pkg=CAP/'tradingagents/research/onchain_replication';tree=ast.parse((pkg/'compact_mcm.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_produce_locked');compute=next(n for n in ast.walk(fn) if isinstance(n,ast.FunctionDef) and n.name=='compute');imp=next(n for n in compute.body if isinstance(n,ast.ImportFrom) and any(a.name=='resource_refusal' for a in n.names));assert imp.lineno==282
assert not (pkg/'resource_refusal.py').exists() and not any('resource_refusal' in name for name in rel['source_files'])
log=(base/'guard/child.log').read_text();assert 'from . import resource_refusal' in log and 'ImportError' in log
assert not {'numpy','torch','scipy','tradingagents'}&set(sys.modules)
print(json.dumps({'raw_status':'failed','source':rel['capsule_commit'],'source_count':len(rel['source_files']),'member_count':len(rows),'files':579,'directories':238,'logical_bytes':5973237,'allocated_bytes':8441856,'archive_sha256':m['archive_sha256'],'remote_commit':r['remote_commit'],'remote_blobs_verified':53,'source_HEAD_and_anchor_joins':156,'original_Git_paths':26,'original_JSON':11,'closed_failed_claims':2,'effective_budget':3,'dictionary_import_completed':True,'MCM_stages':1,'MCM_completions':0,'scalar_references':0,'PIDs_absent':x['recorded_pids_absent'],'cgroup_absent':True,'current_unit':props,'native_peak_sampled_bytes':g['peak_sampled_memory_current_bytes'],'native_elapsed_seconds':g['elapsed_seconds'],'OOM':False,'outer_raw_authentication_refused':x['actual_selected_raw_authentication_error'],'outer_cleanup_unresolved_preserved':True,'numerical_imports':False},indent=2))
