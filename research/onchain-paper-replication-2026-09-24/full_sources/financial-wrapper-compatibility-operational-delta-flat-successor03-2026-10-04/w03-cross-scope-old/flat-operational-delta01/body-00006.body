from pathlib import Path
import json,hashlib,stat,os,subprocess
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'financial-wrapper-compatibility-root-integration01-2026-10-04';V=F/'financial-wrapper-compatibility-root-source-adoption-review01-2026-10-04';O=F/'financial-wrapper-compatibility-actual-source-adoption-review01-2026-10-04';O.mkdir(mode=0o700);h=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(p.read_bytes());release=J(V/'MACHINE01.json');q=J(D/'SOURCE_ADOPTION_DRAFT01.json');result=J(D/'SOURCE_ADOPTION_RESULT01.json');S=Path(q['genuine_same_root']);current='7b056a574e3e7b3c7ba209a39ee6a615e649d60c';prior=release['original_source_design']
def git(args,body=None):return subprocess.run(['git','--no-replace-objects',*args],cwd=S,input=body,capture_output=True,check=True,timeout=20).stdout
assert h((V/'MACHINE01.json').read_bytes())=='d9656bb44e7b88c1f38822235c783cae428d6b00e1af56f31b7a3b5c4d2c4b06';assert h((V/'MANIFEST01.json').read_bytes())=='f05d24ddc2fc1f6673294b74d82eda10a4aeca4bbb7f4fcd6043b42796b8d205'
assert result['source_design']==current==git(['rev-parse','HEAD']).decode().strip();assert git(['rev-parse',current+'^']).decode().strip()==prior;assert git(['merge-base','--is-ancestor',q['historical_parent_source'],current])==b'';assert git(['diff','--name-only','HEAD'])==b''
expected_changes={x['path'] for x in release['changes']};assert set(git(['diff-tree','--no-commit-id','--name-only','-r',current]).decode().splitlines())==expected_changes
old=J(D/'OLD_IMPLEMENTATION194.json');target=J(D/'TARGET_IMPLEMENTATION195.json');assert len(old)==194 and len(target)==195 and sum(target.get(n)==v for n,v in old.items())==191 and sum(n.startswith('tradingagents/') for n in target)==150
for n,pin in target.items():assert h((S/n).read_bytes())==pin
for x in release['changes']:
 p=S/x['path'];s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==x['required_adopted_mode'] and s.st_size==x['new_bytes'] and h(p.read_bytes())==x['new_sha256'];assert p.read_bytes()==(D/('TARGET_'+p.name)).read_bytes()
 if not x['new_regular_file']:assert git(['show',prior+':'+x['path']])==(D/('ORIGINAL_'+p.name)).read_bytes()
# Full adopted working tree and current committed blobs.
after=J(D/'SOURCE_ADOPTION_AFTER589.json');assert h((D/'SOURCE_ADOPTION_AFTER589.json').read_bytes())==result['after_manifest_sha256'];rows=after['members'];assert len(rows)==589;by={x['path']:x for x in rows};actual=[]
for root,ds,fs in os.walk(S,followlinks=False):
 if Path(root)==S:ds.remove('.git')
 actual.extend(str((Path(root)/n).relative_to(S)) for n in ds+fs)
assert sorted(actual)==sorted(by)
for n,x in by.items():
 p=S/n;s=p.lstat();assert stat.S_IMODE(s.st_mode)==x['mode']
 if x['kind']=='file':assert stat.S_ISREG(s.st_mode) and s.st_size==x['bytes'] and h(p.read_bytes())==x['sha256']
 else:assert stat.S_ISDIR(s.st_mode)
protected=J(V/'PROTECTED_NON_TARGET585.json')['members'];assert len(protected)==585
for x in protected:assert by[x['path']]==x
tracked=git(['ls-tree','-rz','HEAD']).split(b'\0');assert tracked[-1]==b'' and len(tracked)-1==340;trackedjoins=[]
for line in tracked[:-1]:
 meta,n=line.split(b'\t');mode,kind,oid=meta.split();n=n.decode();assert kind==b'blob' and n in by;b=git(['cat-file','blob',oid.decode()]);assert b==(S/n).read_bytes();trackedjoins.append({'path':n,'git_mode':mode.decode(),'oid':oid.decode(),'sha256':h(b)})
# Every former object remains byte-identical and locally available, not merely
# ancestry labels; no original object or source claim is rewritten.
objects=J(V/'ORIGINAL_GIT385.json')['objects'];raw=git(['cat-file','--batch'],('\n'.join(x['oid'] for x in objects)+'\n').encode());offset=0
for x in objects:
 end=raw.index(b'\n',offset);head=raw[offset:end].split();assert head==[x['oid'].encode(),x['type'].encode(),str(x['bytes']).encode()];b=raw[end+1:end+1+x['bytes']];assert h(b)==x['sha256'] and raw[end+1+x['bytes']:end+2+x['bytes']]==b'\n';offset=end+2+x['bytes']
assert offset==len(raw)
gate=S/'fixture_inputs/financial_wrapper_claimedrun01/gates.json';assert h(gate.read_bytes())==q['expected_original_gate_sha256'];claims=[]
for p in sorted((S/'research_runs').glob('*/claim.json')):
 c=J(p);assert (p.parent/'failed.json').is_file() and not (p.parent/'complete.json').exists();claims.append({'identity':p.parent.name,'claim_sha256':h(p.read_bytes()),'failed_sha256':h((p.parent/'failed.json').read_bytes()),'budget':c.get('effective_attempt_budget',c['family']['attempt_budget'])})
assert claims==J(V/'READBACK01.json')['claims'];assert len(claims)==3 and max(x['budget'] for x in claims)==19
assert not (S/'research_runs'/q['fixed_future_adopter']).exists()
P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-root-launch-20261004-01');terminal=J(P/'attempt/parent-terminal.json');assert terminal['actual_parent_exit'] is None and not Path(terminal['cleanup']['cgroup']).exists()
active=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
 try:argv=(proc/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if str(P/'parent01.py').encode() in argv or (b'tradingagents.research.onchain_replication.job' in argv and str(S).encode() in argv):active.append(proc.name)
assert not active
for x in protected:
 p=S/x['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==x['mode']
 if x['kind']=='file':assert h(p.read_bytes())==x['sha256']
for n in ['SOURCE_ADOPTION_RESULT01.json','SOURCE_ADOPTION_ATTEMPT01.json','SOURCE_ADOPTION_PREFLIGHT01.json','SOURCE_ADOPTION_AFTER589.json','SOURCE_ADOPTION_DRAFT01.json']:(O/n).write_bytes((D/n).read_bytes())
(O/'check01.py').write_bytes(Path('/tmp/actual_adoption01.py').read_bytes());(O/'INSPECT01_FAILURE.txt').write_text('Actual read-only discovery toole21ae1 guessed ADOPTION01.json and received FileNotFound. Actual receipt SOURCE_ADOPTION_RESULT01.json was then read. No source or result was modified.\n')
read={'schema_version':1,'current_source_design':current,'direct_parent':prior,'historical_source':q['historical_parent_source'],'same_root':str(S),'literal_changes':release['changes'],'all_589_nongit_verified':True,'protected_non_target585_unchanged':True,'old_git_objects_verified':385,'implementation_paths':195,'package_paths':150,'old_implementation_byte_equal':191,'tracked':340,'tracked_joins':trackedjoins,'after_manifest_sha256':result['after_manifest_sha256'],'old_gate_sha256':h(gate.read_bytes()),'claims':claims,'current_matching_processes':active,'current_cgroup_absent':True,'future_identity_unclaimed':True,'actual_root_receipt_sha256':h((D/'SOURCE_ADOPTION_RESULT01.json').read_bytes()),'authority':'actual source adoption only'}
(O/'READBACK01.json').write_text(json.dumps(read,indent=2)+'\n');print('PASS actual195/340/589/585/385')
