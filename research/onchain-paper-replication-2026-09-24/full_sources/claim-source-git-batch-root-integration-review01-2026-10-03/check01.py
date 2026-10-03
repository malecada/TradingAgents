import ast,hashlib,json,os,stat,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;REPO=HERE.parents[3]
I=BASE/'claim-source-git-batch-root-integration01-2026-10-03';P=BASE/'neural-cold-feature-handoff-root-integration01-2026-10-03'
refs={}
def raw(p):
 b=p.read_bytes();refs[str(p)]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};return b
def js(p):return json.loads(raw(p))
def h(b):return hashlib.sha256(b).hexdigest()
def git(root,*a):return subprocess.check_output(['git','-c','protocol.allow=never',*a],cwd=root,env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_OPTIONAL_LOCKS':'0','GIT_TERMINAL_PROMPT':'0'},timeout=20)
w=js(I/'WITHDRAWAL_SOURCE_A01.json');v=js(I/'INTEGRATION01.json');script=raw(I/'integrate_source01.py');old=Path(w['old_root']);new=Path(w['successor_root'])
assert w['status']=='withdrawn-unattempted-root-selection' and v['status']=='accepted-source-integrated-no-execution-release'
assert w['family_attempt_budget']==2 and w['family_prior_attempts']==0 and w['exposures']==[] and v['numeric_jobs_started']==0
candidate=BASE/'claim-source-git-batch-candidate01-2026-10-03';manifest=js(candidate/'MANIFEST01.json');assert h((candidate/'MANIFEST01.json').read_bytes())==v['candidate_manifest']
for r in manifest['files']:
 b=(candidate/r['path']).read_bytes();assert len(b)==r['bytes'] and h(b)==r['sha256']
assert raw(REPO/v['target'])==raw(candidate/'candidate01.py') and h((REPO/v['target']).read_bytes())==v['new_sha256']
assert h(raw(BASE/'claim-source-git-batch-review01-2026-10-03/REVIEW_BATCH01.md'))==v['independent_review']
assert h(raw(BASE/'claim-source-git-batch-selected-extents-investigation01-2026-10-03/REPORT01.md'))==v['selected_extent_report'] # declared pin only; no independent self-review
assert h(git(REPO,'show',v['main_previous_head']+':'+v['target']))==v['old_sha256']
assert h((old/v['target']).read_bytes())==v['old_sha256'] and git(old,'rev-parse','HEAD').decode().strip()==w['old_source']
# Compare all retained source-A members, including genuine Git, with unchanged recovery.
meta=js(P/'SOURCE_A_RETENTION01.json');recovered=P/'sourceA-recovery01/source';count=0
for r in meta['members']:
 a=old/r['path'];b=recovered/r['path'];sa=a.lstat();sb=b.lstat();assert stat.S_IMODE(sa.st_mode)==stat.S_IMODE(sb.st_mode)==r['mode'],r['path']
 if r['kind']=='directory':assert stat.S_ISDIR(sa.st_mode) and stat.S_ISDIR(sb.st_mode)
 else:assert stat.S_ISREG(sa.st_mode) and sa.st_size==sb.st_size==r['bytes'] and h(a.read_bytes())==h(b.read_bytes())==r['sha256'],r['path']
 count+=1
assert count==728
actual={'.'}
for parent,dirs,files in os.walk(old,followlinks=False):actual.update(str((Path(parent)/n).relative_to(old)) for n in dirs+files)
assert actual=={r['path'] for r in meta['members']}
assert git(old,'rev-list','--parents','-n','1',meta['source_A']).decode().split()==[meta['source_A'],meta['source_T']]
assert git(old,'rev-list','--parents','-n','1',meta['source_T']).decode().split()==[meta['source_T'],meta['anchor_S']]
inv=js(old/'cold_prep/source_inventory.json');assert len(inv['source_inventory'])==195 and inv['package_count']==147
sources={r['target']:r['sha256'] for r in inv['source_inventory']}
for r in inv['source_inventory']:assert len((old/r['target']).read_bytes())==r['bytes'] and h((old/r['target']).read_bytes())==r['sha256']
anchor=js(old/'cold_prep/anchor.json');assert anchor['commit']==meta['anchor_S'] and anchor['files']=={p:h for p,h in sources.items() if p.startswith('tradingagents/')} and len(anchor['files'])==147
reg=js(old/'cold-registration.json');assert git(old,'show',meta['source_A']+':cold-registration.json')==(old/'cold-registration.json').read_bytes()
assert len(reg['experiments'])==1;exp=reg['experiments']['compact-cold-inputs-20261003-01'];assert exp['source_files']==sources and len(exp['inputs'])==9
family=reg['families'][exp['family']];assert family['attempt_budget']==2 and family['prior_attempts']==0 and reg['datasets']['synthetic-cold']['exposures']==[]
for r in exp['inputs'].values():assert h((old/r['path']).read_bytes())==r['sha256'] and git(old,'show',meta['source_A']+':'+r['path'])==(old/r['path']).read_bytes()
assert len(w['unclaimed_paths_absent'])==10 and len(set(w['unclaimed_paths_absent']))==10
for s in w['unclaimed_paths_absent']:
 p=Path(s);assert p.is_relative_to(old) and not p.exists() and not p.is_symlink()
assert not new.exists() and not new.is_symlink()
# Also bound the live repository namespace; not a claim of all hosts/unlisted roots.
main_absent=[]
for s in w['unclaimed_paths_absent']:
 p=REPO/Path(s).relative_to(old);assert not p.exists() and not p.is_symlink();main_absent.append(str(p))
assert js(P/'PROPOSED_MATERIALIZATION_RELEASE01.json')['status']=='draft'
assert h(raw(BASE/'neural-cold-feature-handoff-sourceA-recovery-review01-2026-10-03/REVIEW_RECOVERY01.md'))==w['old_full_recovery_review']
for pid in v['old_pids_absent']:assert not Path('/proc',str(pid)).exists()
assert not Path(v['old_cgroup_absent']).exists()
# Root script performs a byte copy and writes metadata; no research imports or launch API.
t=ast.parse(script)
assert not any(isinstance(n,(ast.Import,ast.ImportFrom)) and ('tradingagents' in ast.unparse(n) or any(x in ast.unparse(n) for x in ('numpy','torch','pandas'))) for n in ast.walk(t))
assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in {'Popen','start','admit','verify_claim'} for n in ast.walk(t))
result={'status':'PASS-narrow-actual-integration-withdrawal','source_A':w['old_source'],'old_exact_members':count,'sources':195,'anchor_package':147,'inputs':9,'old_id_paths_absent':10,'main_id_paths_absent':main_absent,'new_root_absent':str(new),'old_pids_absent':v['old_pids_absent'],'live_candidate':v['new_sha256'],'runtime_or_empirical_recovery_claimed':False,'extent_report':'declared pin only; not independently re-reviewed','qualification':'Observed named namespaces only; no global all-host job absence, elapsed-time proof, gate, authority or numerical result inferred.'}
(HERE/'readback01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');(HERE/'refs01.json').write_text(json.dumps(refs,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
