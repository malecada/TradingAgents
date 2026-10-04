import datetime,hashlib,json,os,stat,subprocess
from pathlib import Path

M=Path.cwd();S=M/'research/onchain-paper-replication-2026-09-24';B=S/'full_sources';C=B/'heartbeat-root-checkpoint10-2026-10-04'
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()=='712fee46e11dece8138ab08778a1f9819a10cad3'
assert not subprocess.check_output(['git','diff','--cached','--name-only'])
D=B/'financial-genuine-wrapper-root-recordfix-failed-remote01-2026-10-04';D.mkdir(mode=0o700)
original=B/'financial-genuine-wrapper-root-recordfix-final-remote01-2026-10-04/recover01.py'
body=original.read_bytes();assert hashlib.sha256(body).hexdigest()=='0b397ccd0a014f60a414ce79d67dfd53c58a0fb61ca616a6576cc43da4bbf0aa'
(D/'recover01.py').write_bytes(body)
def put(p,v):
 assert not p.exists();p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
put(D/'SOURCE_COPY01.json',{'helper_sha256':hashlib.sha256(body).hexdigest(),'byte_identical_source':str(original.relative_to(M)),'scope':'New namespace for complete actual failed Source/Parent/Root and full independent failed-case/capture/correction source witnesses. Exact old required six pre-case source-capture pins will also be selected without replacing postfailure evidence. No remote, native, claim or retry has run.','selection':None,'actual_remote':False})
stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
top=f'''# Current execution checkpoint — October 4, 2026

**TOP {stamp}: the actual failed financial engineering case and its complete postfailure Source/Parent/Root capture are independently accepted. The narrow claimed-run authorization correction is independently source accepted. Complete failed-scope external and fresh flat recovery is in preparation; no numerical job is active.** Actual last confirmed Main/remote712fee46e11dece8138ab08778a1f9819a10cad3; later receipts below are local pending this commit.

Financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01 remains permanently UNEXPECTED FAILED and genuinely spent. Actual native58508/b185ed/ea4290 exited1; genuine claim4c543d71/failed35158c0e, Source649fb8a325tracked324pins194implementation149package/eightroles and Parent82d79e1a/Q28f2 are immutable. Different-author failed-case MANIFEST02 62b7a4cf/246dd2f2 accepted1,449 checks: all ten observed PIDs/native cgroup absent, original declared cell unavailable and all three outputs/checkpoint absent, actual Root/child1 separately from original Parent self NULL. Native sampled memory.current maximum325,218,304B in4.233806s/no OOM is not kernel peak/capacity/saving; original Root null alias is preserved with additive qualification. Cause is the original wrapper's fresh job._admitted call after genuine ResearchRun.start claimed the identity. No fit completed and no planned first checkpoint was satisfied. Never relaunch this identity/capsule/Parent or refund the spent claim.

Root actual failed-scope capture75520/119d83/e28242 exited0, CAPTURE01 37c3f6b0: source1011typed730bodies archive3c67dff0/manifestc00c9722, parent33typed28bodies archivea1b7f9b9/manifestfbd106b9, outer5typed5bodies archivef4bf2cae/manifestd674aef4. Total1049typed763bodies independently accepted a3aa7bd1/37acf87b after19,007 checks, including all original986Source members unchanged plus25 postfailure members, original Git325/324, current raw claim/native/controllers/stop/Root streams/cleanup and original dispositions. Current captures are complete local bytes, not external/flat recovery. Earlier accepted pre-case Source/caller11-tree recovery791bc394/6f0d70c7 after33,223 checks remains immutable and cannot stand in for this failed-scope recovery.

Claimed-run correction candidatef4ea651b/authorb49a17d0 is independently SOURCE accepted33b0a19c/bc60374a after518 checks,61 author controls, full one-seam byte/AST inverse and194closure1changed193unchanged. It uses genuine existing run.admission/run.read_input, retaining active/source/input/args/current=design/noBindings/job/dependency/native/Owner/runtime/science checks. Shared admission/lifecycle/job repeat protection is unchanged. No successful active authorization, new Admission/Run/Owner, new source installation, gate, caller or numerical release is claimed. All future bindings remain unavailable; the failed identity cannot be used as a checkpoint parent.

Next safe Root work: commit/push/read back actual completed receipts, freeze bounded complete failed-scope selected union, independently review and perform ONE fresh remote recovery; then genuine exact new three-role R4 flat release, ONE complete763-body recovery and independent outcome acceptance. Root alone owns integration/registration/accounting/STATE/Git/external preservation and ONE launcher. outcome_archive owns NEW three-role failed-scope flat adapter; full_helper_review owns independent complete actual selection/recovery; combined_worker_review investigates exact same-program amendment accounting. This is ordinary parallel source/preservation work, no empirical replay. Financial engineering base18/prior0 now1FAILED/highest18/17 unused, all original18 phases still required. No19 amendment exists; any necessary cumulative amendment and fresh identity/source/caller must be prepared and independently reviewed before further empirical execution. No refund/transfer or phase substitution.

All1,420paper fits525BTC895ETH/45initialincluded remain pending. Paper36closed27COMPLETE9FAILED/highest64/no65/77of109/resource7COMPLETE102UNAVAILABLE unchanged. All13tasks/C01–C18/full original motif dictionary→MCM→GAT→attention LSTM/bothassets/history/comparisons/32Task8requirements27variants16classes/full eligible populations/cold ancestry/joint gradients/15asset-years5480dates/fund350 historical65-address-vintage remain required. Original32motifs512spent samples/config20f451/trainingd527/protocol/tolerances fixed. Import5FAILED/highest6, neural04FAILED3.75GiB/all9unavailable, tinyouterFAILED/3actualcomponents3823bitwise passed, coldtwo exhausted remain preserved. Physical16GB/10GiBfloor; fullMCM55,439,818,752B requires authenticated tails AND batch/output streaming/offload/full recovery before any deletion. No credentials/pay/contact/trading/deployment/VPS systemd SSH.
'''
for p in (S/'STATE.md',B/'parallel-execution-2026-10-02/COORDINATION.md'):p.write_text(top+'\n---\n\n'+p.read_text())
put(C/'TOP19.json',{'time_utc':stamp,'main_parent_commit':'712fee46e11dece8138ab08778a1f9819a10cad3','top_sha256':hashlib.sha256(top.encode()).hexdigest(),'actual_spent_claims':1,'actual_highest_engineering_budget':18,'actual_failed_case_review':'62b7a4cf44b5520d07949fc34570763449ce2d5447c031f75fe3e65860459a3c','actual_failed_capture_review':'a3aa7bd14e2e5afc6aa731980f9bcebedbbd160b61d1de1e01a2fb21e6aa277e','source_only_correction_review':'33b0a19c0fd5cb9583444b92846f0e1d40c135275df2964e37bd31d144143a5a','failed_external_recovery':False,'failed_flat_recovery':False,'native_active':False,'paper_fits_complete':0,'next':'Complete committed bounded failed-scope union external and fresh flat recovery with independent acceptance; no replay'})
scopes=['financial-genuine-wrapper-claimed-run-correction-preparation01-2026-10-04','financial-genuine-wrapper-claimed-run-correction-review01-2026-10-04','financial-genuine-wrapper-recordfix-final-union-actual-recovery-review01-2026-10-04','financial-genuine-wrapper-recordfix-first-failure-capture-review01-2026-10-04','financial-genuine-wrapper-recordfix-first-failure-review01-2026-10-04','financial-genuine-wrapper-recordfix-launch-command-investigation01-2026-10-04','financial-genuine-wrapper-recordfix-native-eligibility-observation01-2026-10-04','financial-genuine-wrapper-root-recordfix-failed-scope-capture01-2026-10-04','financial-genuine-wrapper-root-recordfix-final-flat01-2026-10-04','financial-genuine-wrapper-root-recordfix-final-remote01-2026-10-04','financial-genuine-wrapper-root-recordfix-first-native01-2026-10-04',D.name]
paths=[S/'STATE.md',B/'parallel-execution-2026-10-02/COORDINATION.md']
for tree in [C,*[B/n for n in scopes]]:
 for root,dirs,files in os.walk(tree,followlinks=False):
  dirs[:]=[n for n in dirs if not n.endswith('.git') and n not in ('selected','__pycache__')]
  assert not any((Path(root)/n).is_symlink() for n in dirs)
  paths.extend(Path(root)/n for n in files)
F=B/'financial-genuine-wrapper-recordfix-final-union-flat-20261004-01'
paths.extend(F/n for n in ('intent.json','request.json','RECOVERY01.json','flat/body-metadata.json'))
copy=C/'STAGE16_BUILDER01.py';assert not copy.exists();copy.write_bytes(Path(__file__).read_bytes());paths.append(copy)
rows=[]
for p in sorted(set(paths)):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<=4*1024**2
 rows.append({'path':p.relative_to(M).as_posix(),'bytes':s.st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
put(C/'STAGE16.json',{'rows':rows,'scope':'Explicit closed native FAILED attempt/complete failed-scope capture/independent reviews/accepted correction source and closed actual pre-case final recovery. Actual bare Git/selected/flat duplicate stores stay immutable locally; original complete archives preserve bytes.','count':len(rows),'native_or_network_started':False})
names=[r['path'] for r in rows]+[(C/'STAGE16.json').relative_to(M).as_posix()]
for start in range(0,len(names),80):subprocess.run(['git','add','-f','--',*names[start:start+80]],check=True)
print(json.dumps({'staged_count':len(names),'closed_attempt_spent':1,'numerical_active':False,'remote_started':False}))
