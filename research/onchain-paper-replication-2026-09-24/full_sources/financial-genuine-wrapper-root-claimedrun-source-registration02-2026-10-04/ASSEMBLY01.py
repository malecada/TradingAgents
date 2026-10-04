import copy,hashlib,json,os,stat,subprocess,sys
from pathlib import Path
M=Path.cwd();B=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=B/'financial-genuine-wrapper-root-claimedrun-source-registration02-2026-10-04'
NEW=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');OLD=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source')
ID='financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01';PREV='financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01';PREFIX='fixture_inputs/financial_wrapper_claimedrun01'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=NEW,text=True).strip()=='649fb8a11089524aaef7843dffeeb90a3a55ca17'
assert not os.path.lexists(D) and not os.path.lexists(NEW/PREFIX);D.mkdir(mode=0o700);(D/'ASSEMBLY01.py').write_bytes(Path(__file__).read_bytes())
sys.path.insert(0,str(B/'held-consumer-final-recovery-preparation04-2026-10-03'));import recovery04 as R
assert hashlib.sha256((B/'financial-genuine-wrapper-claimedrun-capsule-history-review01-2026-10-04/MANIFEST02.json').read_bytes()).hexdigest()=='6156ea777cd332c84ce6c7332f722bcf8cd9e52969b57f5fce95e5a39efb14f1'
G=B/'financial-genuine-wrapper-root-claimedrun-handoff-generation01-2026-10-04/generated01';V=B/'financial-genuine-wrapper-claimedrun-source-handoff-review02-2026-10-04';assert R.digest(R.read(V,'MANIFEST03.json'))=='235adb12a75006ff3c0af97fd0920dc3641a1dbbe38ba4193cb5578d2dab325f'
P=B/'financial-genuine-wrapper-root-claimedrun-budget19-preparation01-2026-10-04';BV=B/'financial-genuine-wrapper-claimedrun-budget19-review01-2026-10-04'
review=R.read(BV,'EXTENSION_REVIEW01.json');assert R.digest(review)=='3268b76971e4e721222707d16d25dfe84e94104779931e647fb4d7a2bf01202e'
allocation=R.read(P,'ALLOCATION19.PROPOSAL.json');extension=R.read(P,'EXTENSION19.PROPOSAL.json');assert R.digest(allocation)=='fe135553dc8ebebd84b8adf5cd8011008d53f5c8f6a72761ed3a5837662ac427' and R.digest(extension)=='dfed4dd70d7ed37f3b57f155e1f3acadde6ac673d5261be4a1510a96b0c615e4'
wrapper='tradingagents/research/onchain_replication/financial_wrapper_fixture.py';candidate=R.read(B/'financial-genuine-wrapper-root-claimedrun-handoff-generation01-2026-10-04','candidate.py');assert R.digest(candidate)=='f4ea651b4677c83f8e16c316d17f704d44d9ec86ff78a4bf7c4b895e92e1a16e'
assert R.digest(R.read(NEW,wrapper))=='e2d9208ac51fd5876b63b6a72f734fc4fedd28fa42ac9c7fa1014346feb8404c'
mode=stat.S_IMODE((NEW/wrapper).lstat().st_mode);temp=NEW/(wrapper+'.claimedrun-new');
with R.new_file(temp) as fd:
 off=0
 while off<len(candidate):n=os.write(fd,candidate[off:]);assert n>0;off+=n
 os.fsync(fd)
os.chmod(temp,mode);os.replace(temp,NEW/wrapper)
dest=NEW/PREFIX;dest.mkdir(mode=0o755);handoff=json.loads(R.read(G,'HANDOFF01.json'));assert handoff['proposed_root']==str(NEW)and handoff['identity']==ID and len(handoff['input_roles'])==8
def save(n,raw):
 with R.new_file(dest/n) as fd:
  off=0
  while off<len(raw):size=os.write(fd,raw[off:]);assert size>0;off+=size
  os.fsync(fd)
 assert R.read(dest,n)==raw
for role,ref in handoff['input_roles'].items():
 raw=R.read(G,role+'.json');assert R.digest(raw)==ref['sha256'];save(role+'.json',raw)
save('allocation19.json',allocation);save('extension19.json',extension);save('extension-review19.json',review)
mapping=R.read(B/'financial-genuine-wrapper-root-claimedrun-capsule-history-preparation02-2026-10-04','RELOCATION01.json');save('closed-history-relocation.json',mapping)
original_gate=R.read(OLD/'fixture_inputs/financial_wrapper_recordfix01','gates.json');assert R.digest(original_gate)=='4474df26460aab41281bfdcc311129b613a90d76963e853858841200d9faa69a';gate=json.loads(original_gate);old_entries=copy.deepcopy(gate['experiments']);parent=gate['experiments'][PREV]
charter=json.loads(R.read(OLD,parent['charter']['path']));charter['prior_operational_source_correction']=charter['operational_source_correction'];charter['operational_source_correction']={'fresh_fixed_initial_identity':ID,'new_source_root':str(NEW),'source_body_change':{'path':wrapper,'sha256':R.digest(candidate)},'closed_spent_parent':PREV,'closed_parent_role':'Correction ancestry only; no checkpoint/reference/Owner/runtime authority is supplied by the unexpected failed parent.','parent_claim_sha256':'4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128','parent_failed_sha256':'35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450','genuine_numerical_claims_before':1,'base_family_budget_unchanged':18,'prospective_reviewed_cumulative_ceiling':19,'remaining_original_phase_contracts':18,'operational_identity_definitions':20,'original_old_gate_entries_retained':11,'no_spent_claim_refund_or_transfer':True,'original_source_and_failed_partial_source01_immutable':True,'full_failed_scope_byte_recovery_review':'09113794673e1e4ff3016bf545482a9c2d40a23a3945dd2e55590944aeb24f40','source_correction_review':'33b0a19c0fd5cb9583444b92846f0e1d40c135275df2964e37bd31d144143a5a','actual_history_copy_review':'6156ea777cd332c84ce6c7332f722bcf8cd9e52969b57f5fce95e5a39efb14f1','actual_handoff_review':'235adb12a75006ff3c0af97fd0920dc3641a1dbbe38ba4193cb5578d2dab325f','extension_review_sha256':R.digest(review),'new_source_design_review':None,'new_caller_release':None,'new_full_source_caller_recovery':None,'paper_fit_credit':0}
charter['actual_claims_started']=1;charter['history_reference']='The immutable original base-family18/prior0 records its original admission history. One actual unexpected same-program FAILED claim4c54/3515 is now preserved, globally spent once, copied exactly into this reviewed destination. Prospective cumulative19 retains that claim plus all18 still-required original phases; other paper/import/cold/tiny budgets and exposures are not transferred. No fresh synthetic sample or checkpoint authority is claimed.'
for row in charter['phases']:
 if row['proposed_identity']=='financial-wrapper-classification-eager-interrupt1-20261003-01':row['proposed_identity']=ID
 row['proposed_dependencies']=[ID if n=='financial-wrapper-classification-eager-interrupt1-20261003-01'else n for n in row['proposed_dependencies']]
charter['required_before_any_claim']=[n.replace('finite reviewed18budget','finite independently reviewed cumulative19 amendment retaining base18/spent1')for n in charter['required_before_any_claim']]
charter['status']='CONCRETE_NEW_SOURCE_REGISTRATION_REQUIRES_EXACT_INDEPENDENT_REVIEW_AND_RELEASE';save('charter.json',R.encode(charter))
closure=json.loads(R.read(dest,'source_closure.json'));assert len(closure['installed'])==194 and sum(n.startswith('tradingagents/')for n in closure['installed'])==149
for n,h in closure['installed'].items():assert R.digest(R.read(NEW,n))==h
tracked=[n.decode()for n in subprocess.check_output(['git','ls-tree','-r','--name-only','-z','HEAD'],cwd=NEW).split(b'\0')if n];tracked+=sorted(p.relative_to(NEW).as_posix()for p in dest.iterdir());assert len(tracked)==338 and len(set(tracked))==338
e=copy.deepcopy(parent);e['parent']=PREV;e['charter']={'path':PREFIX+'/charter.json','sha256':R.digest(R.read(dest,'charter.json'))};e['inputs']={role:dict(ref,dataset='synthetic')for role,ref in handoff['input_roles'].items()};e['source_files']={n:R.digest(R.read(NEW,n))for n in sorted(tracked)};e['cumulative_budget_extension']={'extension':{'path':PREFIX+'/extension19.json','sha256':R.digest(extension)},'review':{'path':PREFIX+'/extension-review19.json','sha256':R.digest(review)}}
assert gate['families']['synthetic-financial-wrapper']==json.loads(extension)['base_family'];gate['experiments'][ID]=e;assert len(gate['experiments'])==12 and all(gate['experiments'][n]==v for n,v in old_entries.items());save('gates.json',R.encode(gate))
assert R.read(NEW/'fixture_inputs/financial_wrapper_recordfix01','gates.json')==original_gate
R.put(D/'ASSEMBLY_READBACK01.json',{'status':'ACTUAL_CORRECTED_SOURCE_INPUTS_AND_GATE_ASSEMBLED_NOT_COMMITTED_OR_RELEASED','root':str(NEW),'fresh_identity':ID,'base_family_unchanged':18,'actual_spent_before':1,'current_highest_actual_claim_budget':18,'prospective_reviewed_ceiling':19,'old_gate_entries_unchanged':11,'new_gate_entries':12,'source_file_pins':338,'eventual_tracked_files':339,'implementation_count':194,'package_count':149,'scientific_other_bodies_unchanged':193,'new_wrapper_sha256':R.digest(candidate),'new_gate_sha256':R.digest(R.read(dest,'gates.json')),'input_roles':handoff['input_roles'],'charter':e['charter'],'source_design_commit':None,'genuine_new_admission':None,'new_caller_release':None,'full_new_source_recovery':None,'new_claim_or_numerical':False,'scope':'Root ordinary reversible integration of actual accepted sources/metadata. Source/design commit and exact independent gate/source/cumulative review precede actual metadata admission and final caller/recovery/native release.'})
print(json.dumps({'new_gate_sha256':R.digest(R.read(dest,'gates.json')),'pins':338,'eventual_tracked':339,'old_entries_retained':11,'gate_entries':12,'new_claim_or_numeric':False,'source_design_commit':None}))
