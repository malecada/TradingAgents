from pathlib import Path
import json,hashlib,os,stat,subprocess,datetime
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'financial-wrapper-compatibility-root-integration01-2026-10-04';V=F/'financial-wrapper-compatibility-root-source-adoption-review01-2026-10-04'
def h(b):return hashlib.sha256(b).hexdigest()
def J(p):return json.loads(p.read_bytes())
def out(n,o):
 with (D/n).open('x') as f:json.dump(o,f,indent=2,sort_keys=True);f.write('\n')
q=J(D/'SOURCE_ADOPTION_DRAFT01.json');v=J(V/'MACHINE01.json');S=Path(q['genuine_same_root'])
assert h((D/'SOURCE_ADOPTION_DRAFT01.json').read_bytes())==v['proposal_sha256']
assert h((V/'MACHINE01.json').read_bytes())=='d9656bb44e7b88c1f38822235c783cae428d6b00e1af56f31b7a3b5c4d2c4b06'
assert v['decision']=='ACCEPTED_EXACT_FOUR_BODY_SOURCE_ADOPTION_ONLY'
def git(*args):return subprocess.run(['git','--no-replace-objects',*args],cwd=S,capture_output=True,check=True,timeout=20).stdout
assert git('rev-parse','HEAD').decode().strip()==q['current_source_design'];assert not git('diff','--name-only','HEAD');assert not (S/'.git/index.lock').exists()
base=J(V/'BEFORE_ALL_NONGIT588.json');protected=J(V/'PROTECTED_NON_TARGET585.json'); targets={x['path']:x for x in v['changes']}
def census():
 members=[]
 def visit(p):
  for item in sorted(os.scandir(p),key=lambda x:x.name):
   if p==S and item.name=='.git':continue
   a=Path(item.path);s=a.lstat();row={'path':a.relative_to(S).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
   if stat.S_ISDIR(s.st_mode):row['kind']='directory';members.append(row);visit(a)
   else:
    assert stat.S_ISREG(s.st_mode) and s.st_nlink==1;assert s.st_size<4*1024**2
    raw=a.read_bytes();assert len(raw)==s.st_size;row.update(kind='file',bytes=len(raw),sha256=h(raw));members.append(row)
 visit(S);return sorted(members,key=lambda x:x['path'])
before=census();assert before==base['members'];assert [x for x in before if x['path'] not in targets]==protected['members']
active=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
 try:argv=(proc/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if b'tradingagents.research.onchain_replication.job' in argv or any(x.endswith(b'/parent01.py') and b'onchain-financial-isolation' in x for x in argv):active.append({'pid':int(proc.name),'argv':[x.decode(errors='replace') for x in argv if x]})
assert not active
P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-root-launch-20261004-01');terminal=J(P/'attempt/parent-terminal.json');assert not Path(terminal['cleanup']['cgroup']).exists()
for x in terminal['cleanup']['actual_control_operations'].values():assert not Path('/proc',str(x['pid'])).exists()
assert not (S/'research_runs'/q['fixed_future_adopter']).exists()
mem={k:int(v.split()[0])*1024 for line in Path('/proc/meminfo').read_text().splitlines() for k,v in [line.split(':',1)]};sv=os.statvfs(S);disk=sv.f_bavail*sv.f_frsize;assert disk>10*1024**3
out('SOURCE_ADOPTION_PREFLIGHT01.json',{'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':q['current_source_design'],'review_sha256':h((V/'MACHINE01.json').read_bytes()),'before_members':len(before),'protected_members':len(protected['members']),'selected_processes':active,'prior_cgroup_absent':True,'new_adopter_absent':True,'mem_available':mem['MemAvailable'],'disk_free':disk,'numerical_release':None})
# A one-use source-only marker outside the protected genuine capsule.
out('SOURCE_ADOPTION_ATTEMPT01.json',{'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_only':True,'changes':v['changes'],'native_release':None})
for rel,row in targets.items():
 dest=S/rel;body=(D/('TARGET_'+dest.name)).read_bytes();assert h(body)==row['new_sha256'] and len(body)==row['new_bytes']
 if row['new_regular_file']:assert not dest.exists()
 else:assert h(dest.read_bytes())==row['old_sha256']
 # Deliberate source replacement; original literal/Git/body recovery is accepted.
 fd=os.open(dest,os.O_WRONLY|os.O_CREAT|(os.O_EXCL if row['new_regular_file'] else os.O_TRUNC),row['required_adopted_mode'])
 with os.fdopen(fd,'wb') as f:f.write(body);f.flush();os.fsync(f.fileno())
 os.chmod(dest,row['required_adopted_mode'])
after=census();assert len(after)==589;assert [x for x in after if x['path'] not in targets]==protected['members']
assert set(git('diff','--name-only','HEAD').decode().splitlines())=={p for p,x in targets.items() if not x['new_regular_file']}
git('add','--',*targets);staged=git('diff','--cached','--name-only').decode().splitlines();assert set(staged)==set(targets)
commit_result=git('commit','-m','fix: preserve publication races and explicit checkpoint provenance')
new=git('rev-parse','HEAD').decode().strip();assert git('merge-base','--is-ancestor',q['current_source_design'],new)==b'';assert not git('diff','--name-only','HEAD')
assert len(git('ls-tree','-r','--name-only','HEAD').splitlines())==340
assert h((S/'fixture_inputs/financial_wrapper_claimedrun01/gates.json').read_bytes())==q['expected_original_gate_sha256']
out('SOURCE_ADOPTION_AFTER589.json',{'schema_version':1,'root_mode':base['root_mode'],'members':after})
out('SOURCE_ADOPTION_RESULT01.json',{'schema_version':1,'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'ADOPTED_EXACT_FOUR_SOURCE_BODIES_ONLY','source_design':new,'previous_source':q['current_source_design'],'historical_source':q['historical_parent_source'],'git_commit_output':commit_result.decode(),'tracked':340,'nongit_members':589,'implementation':195,'package':150,'unchanged_original_implementation':191,'protected_non_target585_unchanged':True,'old_gate_unchanged_and_unfit_for_new_hashes':True,'policy':None,'budget20_adoption':None,'Run_or_NUM_release':None,'after_manifest_sha256':h((D/'SOURCE_ADOPTION_AFTER589.json').read_bytes())})
print(new)
