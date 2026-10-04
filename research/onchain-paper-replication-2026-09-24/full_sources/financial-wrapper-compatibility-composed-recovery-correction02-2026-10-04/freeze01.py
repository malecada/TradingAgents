from pathlib import Path
import ast,hashlib,json,os,stat
D=Path(__file__).resolve().parent;h=lambda b:hashlib.sha256(b).hexdigest()
def put(n,o):(D/n).write_text(json.dumps(o,sort_keys=True,indent=2,allow_nan=False)+'\n')
src=(D/'verify02.py').read_bytes();ast.parse(src);new=json.loads((D/'CONTROLS02.json').read_bytes());old=json.loads((D/'CONTROLS01.json').read_bytes());actual=json.loads((D/'ACTUAL_READBACK01.json').read_bytes());inverse=json.loads((D/'INVERSE01.json').read_bytes());prior=json.loads((D/'PRIOR_AUTHENTICATION01.json').read_bytes())
assert h(src)=='421cc50f32b1bf1d6a483991deea0fa6700aeb4d165ddc1cecf64dacc08dc4a2' and len(new['rows'])==118 and len(old['rows'])==37
assert all((D/n).read_bytes()==b'' for n in ['CONTROLS02.err','CONTROLS_REPLAY01.err','ACTUAL_READBACK01.err','PRIOR_AUTHENTICATION01.err'])
report='''# Composed checker cleanup successor02

OBSERVATION_REQUIRES_INDEPENDENT_REVIEW. Successor02 corrects only owned cleanup and refusal-diagnostic handling in the withheld14145 checker. No accepted recovery proof, authority body, registration, claim or release is created. All complete byte/Git/source/policy composition predicates and bounds remain unchanged. Original checker01, Root measurement, gate-preview01 refusal and reviewer CR1/CR2/CR3 evidence remain immutable.

Exactly five literal substitutions reverse byte-for-byte and AST-for-AST to original14145: add stdlib types; add the pinned owned-IO delegation/retention wrapper; delegate Reader.read's one owned FD close; explicitly close the owned scandir iterator under the same rules; protect the public refusal diagnostic. The entire run(), flat_scope(), git_graph(), hashes, maps, all589/585/194/195/191/150/340/385+9 denominators, and Reader initialization/tick/anchor/json/final-global-currentness remain exact original AST. INPUTS01 is exactly f992329f.4MiB individual read/256MiB cumulative unique byte/32768 member+anchor/180second read-only bounds are unchanged; no numerical/runtime/preclaim limit is amended.

The copied owned_io.py is the literal09d1fbcc dependency. The identical bytes are embedded in the successor and SHA256-checked before compilation into a private stdlib module. This avoids adding a new mutable filesystem dependency bootstrap or import-path race; no dependency function is edited. The actual _cleanup semantics select the first actual fatal exception over ordinary body/close uncertainty, never retry an uncertain descriptor integer, and run each owned close action once. A narrow wrapper additionally retains primary and secondary actual objects using the BaseException dictionary descriptor. Optional evidence attachment cannot displace the selected exception. The pinned dependency's existing cause-attachment behavior remains unchanged.

CR1: ordinary ValueError followed by real FD-close MemoryError or SystemExit now escapes as the first actual fatal close object; original ordinary error remains reachable. CR2: original KeyboardInterrupt or MemoryError followed by iterator-close SystemExit or ValueError now preserves the earlier fatal identity, while closing the actual iterator once and retaining secondary evidence. No failed read enters the cache; no failed scan is published as an accepted tree. CR3: hostile str(), JSON encoding or print failures are processed as owned diagnostic actions. Earlier original fatal identity survives; an actual later fatal outranks an ordinary primary; all ordinary unresolved cleanup remains a stop through CleanupFailure. A bare raise preserves the original traceback when the selected primary survives.

118 new control rows passed: six exact original RED→corrected GREEN witnesses;25 actual-FD and25 actual-scandir primary/secondary matrices;60 exact-public-handler str/json/print matrices; nested real two-FD first-fatal/object-reachability checks; hostile exception attribute/cause hooks. Every owned FD closes once, no integer is retried, and every owned iterator closes once. All37 original opaque controls replayed with only the target filename and renamed retained-secondary attribute expectation changed; the replay inverse is retained. These are155 engineering rows, not scientific experiments, financial samples or actual authority outcomes.

The complete unchanged read-only actual composition passed again:1,727distinct files/84,824,406 bytes,589 current typed/585 protected/194 historical/195 target/191 equal/150 package/340 tracked paths, and385 original plus9 new logical Git objects forming the exact394 reachable set. The actual64 new opaque flat bodies/66physical files/83typed descendants, canonical archives, exact original modes and failed43 scope, genuine narrow outcomea0c192/1f3e, actual flat e702/sidecar72c910/Root d395, and original threeFAILED/spent/highest19 join. Checkpoint state is hashed only. The output decision remains COMPLETE_COMPOSED_BYTES_OBSERVED_REQUIRES_INDEPENDENT_REVIEW and recovery_proof remains null. The genuine different-author actual composition review and proof are still required.

Both original source and independent-withheld-review complete typed seals were reauthenticated, including every regular body and explicit metadata-only handling of FIFO/symlink adversarial fixtures. No blind FIFO read occurred. Original schema-error source versions/raw failures remain in the authenticated original preparation; original independent CR1/CR2/CR3 witnesses and stderr are copied literally into prior-review01. This correction's build, new matrix, inherited replay, prior authentication and actual readback had empty stderr; no unsuccessful local correction attempt was discarded.

Limits remain explicit: finite sampled currentness, not atomicity, writer exclusion, same-signature ABA protection, kernel aggregate quota, POSIX reconstruction, installed dependency-body recovery or whole fit capacity. Source policy/financial method, science AST, tolerances, old/new checkpoint provenance, spent identities and budgets are not changed. No network, public restoration, numerical package/array import, Owner/Run/Admission, proof, liveCAP/Root/gate/STATE edit or claim occurred. Final caller/gate/contract recovery and preclaim8MiB union eligibility remain separate. Invoke verify02.py only as the pinned-runtime read-only composition checker; output is observations only. Historical build/freeze scripts must not be replayed over this frozen directory.
'''
(D/'REPORT01.md').write_text(report)
put('MACHINE01.json',{'schema_version':1,'decision':'OBSERVATION_REQUIRES_INDEPENDENT_REVIEW','source_sha256':h(src),'original_source_sha256':inverse['original_sha256'],'owned_io_sha256':inverse['owned_dependency_sha256'],'inputs_sha256':inverse['inputs_sha256'],'full_literal_inverse':True,'full_AST_inverse':True,'literal_substitutions':5,'unchanged_definitions':inverse['unchanged_original_definitions'],'new_control_rows':118,'inherited_control_rows':37,'new_controls_sha256':h((D/'CONTROLS02.json').read_bytes()),'inherited_controls_sha256':h((D/'CONTROLS01.json').read_bytes()),'readback_sha256':h((D/'ACTUAL_READBACK01.json').read_bytes()),'report_sha256':h((D/'REPORT01.md').read_bytes()),'prior_authenticated_typed_members':sum(x['typed_members'] for x in prior['roots']),'actual_composition_status':actual['status'],'actual_files_read':actual['files_read'],'actual_bytes_read':actual['bytes_read'],'policy_sha256':actual['policy_sha256'],'checker_sha256':actual['checker_sha256'],'historical_map_sha256':actual['historical_map_sha256'],'target_map_sha256':actual['target_map_sha256'],'actual_current_typed':589,'actual_protected_typed':585,'actual_git_objects':394,'actual_tracked':340,'actual_failed':3,'highest_actual_allowance':19,'actual_recovery_proof':None,'actual_independent_composition_acceptance':None,'numerical_authority':False,'actual_restoration_invoked':False,'live_source_changed':False})
rows=[]
for base,ds,fs in os.walk(D,followlinks=False):
 for name in ds+fs:
  p=Path(base)/name
  if p==D/'MANIFEST01.json':continue
  st=p.lstat();x={'path':p.relative_to(D).as_posix(),'mode':stat.S_IMODE(st.st_mode),'nlink':st.st_nlink}
  if stat.S_ISDIR(st.st_mode):x['kind']='directory'
  elif stat.S_ISLNK(st.st_mode):x.update(kind='symlink',target=os.readlink(p))
  elif stat.S_ISFIFO(st.st_mode):x['kind']='fifo'
  elif stat.S_ISREG(st.st_mode):
   digest=hashlib.sha256()
   with p.open('rb') as f:
    for b in iter(lambda:f.read(65536),b''):digest.update(b)
   x.update(kind='file',bytes=st.st_size,sha256=digest.hexdigest())
  else:raise ValueError('unexpected fixture kind')
  rows.append(x)
put('MANIFEST01.json',{'schema_version':1,'manifest_self_excluded':True,'qualification':'Complete correction evidence including explicit FIFO/symlink/hardlink/sparse negative fixtures; not a restore manifest.','members':sorted(rows,key=lambda x:x['path'])})
print(json.dumps({n:h((D/n).read_bytes()) for n in ['verify02.py','MACHINE01.json','MANIFEST01.json','REPORT01.md','ACTUAL_READBACK01.json','INVERSE01.json']},sort_keys=True))
