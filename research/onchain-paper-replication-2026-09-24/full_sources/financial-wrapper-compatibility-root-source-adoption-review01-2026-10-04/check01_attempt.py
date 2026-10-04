from pathlib import Path
import json,hashlib,stat,os,ast,subprocess
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'financial-wrapper-compatibility-root-integration01-2026-10-04';A=F/'financial-wrapper-operational-provenance-compatibility-preparation02-2026-10-04';V=F/'financial-wrapper-operational-provenance-compatibility-review02-2026-10-04';O=F/'financial-wrapper-compatibility-root-source-adoption-review01-2026-10-04';O.mkdir(mode=0o700)
h=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(p.read_bytes());q=J(D/'SOURCE_ADOPTION_DRAFT01.json');assert h((D/'SOURCE_ADOPTION_DRAFT01.json').read_bytes())=='57c03b0dada661970bc34346695173acc607383cf69c7c2c09595eb2018d2783';S=Path(q['genuine_same_root'])
old=J(D/'OLD_IMPLEMENTATION194.json');new=J(D/'TARGET_IMPLEMENTATION195.json');assert len(old)==194 and len(new)==195 and sum(new.get(n)==v for n,v in old.items())==191;assert sum(n.startswith('tradingagents/') for n in old)==149 and sum(n.startswith('tradingagents/') for n in new)==150
vm=J(V/'MACHINE01.json');assert vm['decision']=='ACCEPTED_SOURCE_ONLY_OPERATIONAL_PROVENANCE_COMPATIBILITY02' and not vm['material_findings'];assert h((V/'MACHINE01.json').read_bytes()).startswith('c12bc775') and h((V/'MANIFEST01.json').read_bytes()).startswith('6d61d65f')
# Full independent reviewer seal plus full author seal are authenticated.
seals=[]
for base in (V,A):
 mf=base/'MANIFEST01.json';m=J(mf);names=[]
 for x in m['members']:
  p=base/x['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==x['mode'];names.append(x['path'])
  if x['kind']=='file':assert len(p.read_bytes())==x['bytes'] and h(p.read_bytes())==x['sha256']
  elif x['kind'] in ('dir','directory'):assert stat.S_ISDIR(s.st_mode)
  elif x['kind']=='symlink':assert os.readlink(p)==x.get('target',x.get('link_target'))
  else:raise AssertionError(x)
 assert sorted(names)==sorted(str(p.relative_to(base)) for p in base.rglob('*') if p!=mf)
 seals.append({'path':str(mf),'sha256':h(mf.read_bytes()),'members':len(names)})
full=F/'financial-wrapper-complete100-failed-full-recovery-review03-2026-10-04';assert h((full/'MACHINE01.json').read_bytes())==q['actual_failed_full_byte_recovery_machine'];assert h((full/'MANIFEST01.json').read_bytes())=='d24ff359f85f087ee2d36bd6010a4b04f43207ffae92603c31e5acd80f5b1726'
def git(args):return subprocess.run(['git','--no-replace-objects',*args],cwd=S,capture_output=True,check=True,timeout=20).stdout
assert git(['rev-parse','HEAD']).decode().strip()==q['current_source_design'];assert git(['diff','--name-only','HEAD'])==b'';assert len(git(['ls-tree','-r','--name-only','HEAD']).splitlines())==339
assert git(['merge-base','--is-ancestor',q['historical_parent_source'],q['current_source_design']])==b''
for n,pin in old.items():assert h((S/n).read_bytes())==pin and git(['show','HEAD:'+n])==(S/n).read_bytes()
changes=[]
for x in q['implementation_source_changes']:
 n=x['path'];basename=Path(n).name;target=D/('TARGET_'+basename);b=target.read_bytes();assert len(b)==x['new_bytes'] and h(b)==x['new_sha256']==new[n]==vm['sources'][basename] and b==(A/basename).read_bytes()
 p=S/n
 if x['new_regular_file']:assert not os.path.lexists(p) and n not in old;mode=stat.S_IMODE(target.stat().st_mode)
 else:
  assert p.read_bytes()==(D/('ORIGINAL_'+basename)).read_bytes() and len(p.read_bytes())==x['old_bytes'] and h(p.read_bytes())==x['old_sha256']==old[n];mode=stat.S_IMODE(p.stat().st_mode)
 changes.append({**x,'required_adopted_mode':mode,'target_copy_mode':stat.S_IMODE(target.stat().st_mode)})
assert {n for n in set(old)|set(new) if old.get(n)!=new.get(n)}=={x['path'] for x in changes}
# Scientific functions/loader/control defaults compared as AST, never imported.
for basename,allowed in [('training.py',{'_reserve'}),('financial_wrapper_fixture.py',{'authorize','_parent','_reference_state'})]:
 aa=ast.parse((D/('ORIGINAL_'+basename)).read_text());bb=ast.parse((D/('TARGET_'+basename)).read_text())
 for t in (aa,bb):t.body=[n for n in t.body if getattr(n,'name',None) not in allowed]
 assert ast.dump(aa)==ast.dump(bb)
# Whole current nonGit original is exactly recovered588 member snapshot.
C=F/'financial-wrapper-complete100-failed-outcome-capture02-2026-10-04';m=J(C/'CAPSULE_MASTER_MANIFEST01.json');paths=[];protected=[]
for x in m['members']:
 p=S/x['path'];st=p.lstat();assert stat.S_IMODE(st.st_mode)==x['mode']
 if x['kind']=='file':assert h(p.read_bytes())==x['sha256'] and st.st_size==x['bytes']
 if x['path'] not in {c['path'] for c in changes}:protected.append(x)
for root,ds,fs in os.walk(S):
 if Path(root)==S:ds.remove('.git')
 paths.extend(str((Path(root)/n).relative_to(S)) for n in ds+fs)
assert sorted(paths)==sorted(x['path'] for x in m['members']);assert len(protected)==585
(O/'BEFORE_ALL_NONGIT588.json').write_bytes((C/'CAPSULE_MASTER_MANIFEST01.json').read_bytes());(O/'PROTECTED_NON_TARGET585.json').write_text(json.dumps({'source':str(S),'members':protected},indent=2)+'\n')
# Old gate stays literal and will not admit changed implementation hashes.
gatepath=S/'fixture_inputs/financial_wrapper_claimedrun01/gates.json';assert h(gatepath.read_bytes())==q['expected_original_gate_sha256'];gate=J(gatepath);exp=gate['experiments']['financial-wrapper-classification-eager-complete100-20261003-01'];mismatch=[x['path'] for x in changes if x['path'] in exp['source_files'] and exp['source_files'][x['path']]!=x['new_sha256']];assert len(mismatch)==3
claims=[]
for p in sorted((S/'research_runs').glob('*/claim.json')):
 c=J(p);assert (p.parent/'failed.json').is_file() and not (p.parent/'complete.json').exists();claims.append({'identity':p.parent.name,'claim_sha256':h(p.read_bytes()),'failed_sha256':h((p.parent/'failed.json').read_bytes()),'budget':c.get('effective_attempt_budget',c['family']['attempt_budget'])})
assert len(claims)==3 and max(x['budget'] for x in claims)==19
P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-root-launch-20261004-01');terminal=J(P/'attempt/parent-terminal.json');assert not Path(terminal['cleanup']['cgroup']).exists()
for x in terminal['cleanup']['actual_control_operations'].values():assert not Path('/proc',str(x['pid'])).exists()
active=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
 try:argv=(proc/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if str(P/'parent01.py').encode() in argv or (b'tradingagents.research.onchain_replication.job' in argv and str(S).encode() in argv):active.append(proc.name)
assert not active
for n in ['SOURCE_ADOPTION_DRAFT01.json','OLD_IMPLEMENTATION194.json','TARGET_IMPLEMENTATION195.json']:(O/n).write_bytes((D/n).read_bytes())
(O/'check01.py').write_bytes(Path('/tmp/adoption_review01.py').read_bytes())
read={'schema_version':1,'proposal_sha256':h((D/'SOURCE_ADOPTION_DRAFT01.json').read_bytes()),'source_root':str(S),'current_source_design':q['current_source_design'],'historical_parent':q['historical_parent_source'],'old_map_sha256':h((D/'OLD_IMPLEMENTATION194.json').read_bytes()),'target_map_sha256':h((D/'TARGET_IMPLEMENTATION195.json').read_bytes()),'changes':changes,'old_paths':194,'new_paths':195,'unchanged_implementation':191,'old_package_paths':149,'new_package_paths':150,'protected_nongit_members':585,'source_and_review_seals':seals,'review_machine_sha256':h((V/'MACHINE01.json').read_bytes()),'failed_full_recovery_machine_sha256':q['actual_failed_full_byte_recovery_machine'],'claims':claims,'old_gate_sha256':h(gatepath.read_bytes()),'old_gate_new_body_mismatches':mismatch,'scientific_ast_unchanged':True,'current_matching_processes':active,'current_cgroup_absent':True,'future_source_design':None,'future_policy_gate_budget_native':None}
(O/'READBACK01.json').write_text(json.dumps(read,indent=2)+'\n');print('PASS',len(protected),changes[-1]['required_adopted_mode'])
