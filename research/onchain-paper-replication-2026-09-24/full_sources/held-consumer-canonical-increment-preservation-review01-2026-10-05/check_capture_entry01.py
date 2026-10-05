from pathlib import Path
import hashlib,json,ast,subprocess,os,shutil,datetime
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'held-consumer-canonical-increment-preservation-review01-2026-10-05';A=F/'held-consumer-canonical-root-binding01-2026-10-05';S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-native-20261005-01/source');P=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-root-launch-20261005-01');OUT=F/'held-consumer-canonical-current-capture01-2026-10-05';H=F/'held-consumer-final-recovery-preparation04-2026-10-03';ID='original-import-canonical-held-success-20261005-01'
def h(b):return hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p),'sha256':h(p.read_bytes())}
def load(p):return json.loads(p.read_bytes())
def put(n,v):
 p=D/n;b=(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
 with p.open('xb') as f:f.write(b)
 p.chmod(0o444);print(n,h(b))
source=A/'capture_increment01.py';new=source.read_text();old=(A/'capture_increment01.unexecuted-withheld.py').read_text();assert h(old.encode())==load(D/'FINDING01.json')['source']['sha256']==load(A/'CAPTURE_SOURCE_WITHHELD01.json')['source_sha256']
start=new.index('    assert HELPERS.resolve()');end=new.index('    resource.setrlimit',start)
oldstart=old.index("    assert sha((HELPERS / 'recovery04.py')");oldend=old.index('    resource.setrlimit',oldstart)
inverse=new[:start]+old[oldstart:oldend]+new[end:];inverse=inverse.replace('import types\n','').replace('import hashlib\n','import hashlib\nimport importlib.util\n',1);assert inverse==old
ast.parse(new)
helpers={'owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f','recovery04.py':'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a'}
for n,pin in helpers.items():assert h((H/n).read_bytes())==pin and repr(pin) in new and (H/n).resolve()==H/n
parentpins={'launch_success01.py':'c90812faff70c431807900a118447d30711ac3eca239a4ee1ec11ec5f6139ea9','held_outcome02.py':'34f7945642eac91babe1f180b70c2d42f3b04daaf3e4c556f24eecab8ede4b95','request-unreleased01.json':'8660b2813b751dad5f5120f2486bc9ce7bc79e70fa03e61533b672db9620da6a','release-unreleased01.json':'f1d3dcc65ff8e290732f4c9fe9dd4268ba1388d25ebe4c509d809f9edf11caa4'}
for n,pin in parentpins.items():assert h((P/n).read_bytes())==pin and repr(pin) in new
q=load(P/'request-unreleased01.json');rel=load(P/'release-unreleased01.json');assert all(x is None for x in q['evidence'].values()) and all(rel[n] is None for n in ('release_review_sha256','external_capsule_recovery_sha256','external_recovery_review_sha256'))
assert q['status'].startswith('UNRELEASED') and rel['status'].startswith('UNRELEASED')
bp=F/'held-consumer-post-outcome-root-flat-recovery01-2026-10-03/flat01/capsule-metadata.json';base=load(bp);assert h(bp.read_bytes())=='d8b81554205b9eeb5523fbed41ba616ffc79a0b7fb78c6779b2bcee7f4844fdb'
assert h((json.dumps(base['manifest'],sort_keys=True,indent=2,allow_nan=False)+'\n').encode())=='52d650e256c6e11d9362a215d8af50197cac6be27c951175a5837508570f20d3'
assert len(base['manifest']['members'])==1012 and sum(r['kind']=='file' for r in base['manifest']['members'])==716
accepted=F/'held-consumer-post-outcome-actual-preservation-review01-2026-10-03'
for name,pin in [('ACTUAL_RECOVERY_REVIEW03.json','31640c18b341c4fd7bed39178863e578296b6b241b634f0fe929c9fb658e08b3'),('ACTUAL_FLAT_RECEIPT03.json','4018c09c3fc4a27d9cdd88e7cd1d7e38df0b0f0a97f542deecb6433e77d655f4')]:assert h((accepted/name).read_bytes())==pin
put('SOURCE_CHECK01.json',{'schema_version':1,'decision':'accepted-fixed-increment-capture-source','source':ref(source),'withheld_original':ref(A/'capture_increment01.unexecuted-withheld.py'),'resolved_finding':ref(D/'FINDING01.json'),'helpers':helpers,'parent_pins':parentpins,'accepted_old_regular_bodies':716,'accepted_old_typed_members':1012,'scope':['Capsule-including-physical-Git','Parent','Rootbinding','closed-gate-review','closed-parent-review'],'scan_file_cap':4194304,'scan_baseline_cap':134217728,'unique_increment_cap':16777216,'disk_floor':10737418240,'qualification':'Dependency bytes are pinned then those exact bytes executed in explicit-origin modules; R4 imported function identities joined. Exact Parent draft pins/nulls checked before scan. Only new unique content snapshotted; complete current manifests retain original typed names/modes and authenticated old hash inheritance. Original R4 repeated full rejoin/pack unchanged. No historical outcome copy, numerical import, runtime body recovery, POSIX instantiation, writer exclusion or execution authority.'})
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S).decode().strip()=='468d756c16b3825e83a931c082ab4072764a873d'
assert not subprocess.check_output(['git','status','--short','--untracked-files=no'],cwd=S).strip()
absent=[OUT,P/'attempt',S/'research_runs'/ID,S/'fixture_outer'/ID,S/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/ID];assert all(not os.path.lexists(p) for p in absent)
active=[]
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:
   if 'python' not in (p/'comm').read_text():continue
   args=[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0')]
   if any(x.endswith(('/launch_success01.py','/capture_increment01.py','/recover01.py')) for x in args):active.append(int(p.name))
  except (FileNotFoundError,ProcessLookupError,PermissionError):pass
assert not active;free=shutil.disk_usage(F).free;assert free>=10737418240
put('CAPTURE_ENTRY_RELEASE01.json',{'schema_version':1,'decision':'accepted-exact-once-canonical-increment-capture','source':ref(source),'source_check':ref(D/'SOURCE_CHECK01.json'),'cwd':str(M),'argv':[str(M/'.venv/bin/python'),'-B',str(source)],'one_use':True,'fresh_output':str(OUT),'absent_namespaces':[str(p) for p in absent],'active_selected_processes':active,'free_bytes':free,'metadata_eligibility_tool':'0f2faf','observed_scope_logical_bytes':[7276085,228686,1185368,20630,13255],'observed_scope_regular_files':[744,4,63,7,6],'scope_files_with_bad_type_link_or_over4MiB':0,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'execution_authority':False,'qualification':'Root alone may execute this preservation capture once. Keep all capture output streams and exit records outside scanned Rootbinding until final R.same. Retain every original failed/unknown disposition. Full actual capture, remote retrieval and fresh flat byte acceptance remain pending; no empirical or native launch.'})
