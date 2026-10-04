import datetime,hashlib,json,os,stat,subprocess
from pathlib import Path
M=Path.cwd();S=M/'research/onchain-paper-replication-2026-09-24';B=S/'full_sources';C=B/'heartbeat-root-checkpoint10-2026-10-04'
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()=='900bd0aeeb17cf17b11318b343cee6fc43bcfa09'
assert not subprocess.check_output(['git','diff','--cached','--name-only'])
def write(p,body):
 with p.open('xb') as f:f.write(body)
def enc(x):return (json.dumps(x,sort_keys=True,indent=2)+'\n').encode()
def pin(p):return hashlib.sha256(p.read_bytes()).hexdigest()
remote=B/'financial-genuine-wrapper-root-claimedrun-source339-remote01-2026-10-04';assert not remote.exists();remote.mkdir(mode=0o700)
old=B/'financial-genuine-wrapper-root-recordfix-failed-remote01-2026-10-04/recover01.py';assert pin(old)=='0b397ccd0a014f60a414ce79d67dfd53c58a0fb61ca616a6576cc43da4bbf0aa';write(remote/'recover01.py',old.read_bytes())
flat=B/'financial-genuine-wrapper-claimedrun-source339-flat-20261004-01';assert not flat.exists();flat.mkdir(mode=0o700)
prep=B/'financial-genuine-wrapper-claimedrun-source-recovery-preparation03-2026-10-04'
for n in ['restore01.py','git_objects01.py','recovery04.py','owned_io.py','bounded_git01.py','CAPTURE_PINS01.json']:write(flat/n,(prep/n).read_bytes())
assert pin(flat/'restore01.py')=='9e21e92ca69fad038dc77324b8fcc9f7600380293e55a90b7c0fd5b8ae95c1fc'
capture=B/'financial-genuine-wrapper-root-claimedrun-recovery-evidence-capture01-2026-10-04';raw=json.loads((capture/'CAPTURE01.json').read_bytes());pid=raw['observed_pid'];assert not Path('/proc',str(pid)).exists()
write(capture/'ACTUAL_TOOL_TERMINAL02.json',enc({'status':'ACTUAL_CAPTURE_TOOL_EXIT0_RECORDED_ADDITIVELY','session_id':47856,'start_tool_chunk':'1a7997','completion_tool_chunk':'951f63','actual_exit':0,'observed_pid':pid,'observed_start_ticks':raw['observed_start_ticks'],'observed_pid_absent_now':True,'original_group_history':None,'capture_sha256':pin(capture/'CAPTURE01.json'),'qualification':'Actual original capsule capture PID/start ticks were observed by the capture script. Original process group was not recorded. This additive tool completion does not rewrite the original capture receipt or independent review.'}))
stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
top=f'''# Current execution checkpoint — October 4, 2026

**TOP {stamp}: strict Source339 fresh flat recovery source03 and complete applicable archival evidence are independently accepted. The complete four-tree handoff witness and four recovery source/review scopes were actually captured and accepted. Exact external recovery proceeds now; no numerical job or paper fit is active.** Main and actual remote900bd0aeeb17cf17b11318b343cee6fc43bcfa09 were confirmed by push44473/exit0 and actual readback71973/exit0. Later evidence below is local pending this commit.

Actual Source current=design0a2e7639b42b9423b90743feadcda4078aa21816 retains339tracked338pins194implementation149package/eightroles/f4ea correction and193 unchanged bodies. Gate3a202938 retains all11 old4474 entries plus exactly one fresh claimedrun definition. Full Source1029typed747bodies9,692,681B captureb5b6aad2/fdf77348 is independently acceptedda7a1b69. Genuine original job._admitted97927/exit0 is independently accepted24e6451d/059232d0: actual metadata ceiling19, base18/prior0/spent1/highest ACTUAL18, no Run/Binding/Owner/new claim/numerical imports. Installed new Parent5d5cbdae/034d5977 remains DRAFTb1087b98 with fullSourceRecovery and final releaseNULL. Fresh fixed financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01 remains unclaimed/unattempted.

Source recovery01 remains permanently WITHHELD SR1–SR3. Narrow fixed-seven-commit02fc913e83/05af0c62 is acceptedee1e4aa2 with SR4 generic 1,025-commit qualification preserved. Separately named strict03restore9e21e92c/gitc364269b/manifest8ae5ecff is independently accepteddacd234b/4075db6d after2,840checks: actual1,025 witness refuses before extra insertion,1,024 boundary/cached/cycle/depth behavior and complete inverse unchanged. Source-only acceptance is not actual747-body restoration or release.

Root actual witness capture98488/eecc9d/86f75b exit0 produced archive31560b60/manifest1c40420c,222ordinary187bodies preserving234original typed186regular13literal links across all four handoff author/review roots without following or extracting links. Different-author6997c0d2/ead8eeb0 accepted4,053checks of whole canonical archive/current membership. Root actual recovery-evidence capture47856/1a7997/951f63 exit0 preserved all2,801typed2,263bodies in four complete archives6ea19512/2386d591/94bc3195/72d4928d with full original sealed02/03 source and reviews/generic witnesses. Independent4c913b91/1714f0bb accepted51,125checks; actualPID431674/ticks15745332 is absent, original group is unknown. These byte captures and reviews remain excluded from empirical credit.

Root installed exact accepted remote0b397ccd into a new source339-remote01 namespace and strict03 closure into new fixed source339-flat-20261004-01; neither has executed. Next: commit/push/readback all closed evidence, freeze sorted bounded complete Source339 selection and archive supplements, independently review selection, ONE actual external recovery, then exact different-author flat request/release and ONE actual747-body recovery. Actual full Source339 recovery and acceptance precede final Parent proof/request/release and whole final caller/review/witness external recovery. Fresh processes/namespaces/native/resource eligibility precede at most ONE fixed fresh engineering attempt. No release is supplied by file installation.

Parallel outcome_archive owns NEW claimedrun-outcome-binding-preparation01 only, adapting exact future genuine final request/proofs/release to a verifier; all current missing proof values remain genuineNULL and refuse. Root alone owns Main/capsule/caller/Git integration, registrations/accounting, STATE, actual preservation/recovery and ONE native launcher. Original source clone-mode failure, Root assembly typo, stage17 builder failure and all withheld candidates/witnesses remain immutable. No ordinary preparation failure consumed an additional numerical claim.

The original unexpected native58508/exit1/claim4c54/failed3515 remains permanently FAILED before fitting from duplicate fresh admission after ResearchRun.start. Full failed1049typed763-body scope is actually externally and freshly flat recovered/accepted09113794. Original Parent self exitNULL and Root memory aliasNULL stay immutable, separate authentic Root/child1 and325,218,304B sampled current qualification retained; no OOM/capacity/saving conclusion. Never replay/refund/transfer this identity. All18 original engineering phase contracts still remain required; prospective19 includes this spent failure without forgiving it.

All1,420paper fits525BTC895ETH/45initialincluded remain pending; paper36closed27COMPLETE9FAILED/highest64/no65/coverage77of109/resource7COMPLETE102UNAVAILABLE. Import5FAILED/highest6/no transfer, neural04FAILED3.75GiB/all9unavailable, tinyouterFAILED/threeactualcomponents3,823bitwise passed, coldtwo exhausted remain fixed. All13tasks/C01–C18/original32motifs512spent/full motif dictionary→MCM→GAT→attention LSTM/bothassets/history/comparisons/32Task8requirements27variants16classes/full eligible population/cold scientific ancestry/joint gradients/15asset-years5480dates/fund350 historical65-address-vintage remain required. ModelCONFIG20f451/trainingd527/protocol/tolerances fixed. Physical16GB/10GiBfloor;55,439,818,752B MCM needs authenticated tails AND batch/output streaming/offload and full recovery before deletion. No credentials/pay/contact/trading/deployment/VPS systemd SSH.

---

'''
write(C/'TOP22.md',top.encode())
for p in [S/'STATE.md',B/'parallel-execution-2026-10-02/COORDINATION.md']:p.write_bytes(top.encode()+p.read_bytes())
scopes=['financial-genuine-wrapper-claimedrun-recovery-evidence-capture-review01-2026-10-04','financial-genuine-wrapper-claimedrun-source-recovery-preparation02-2026-10-04','financial-genuine-wrapper-claimedrun-source-recovery-preparation03-2026-10-04','financial-genuine-wrapper-claimedrun-source-recovery-review02-2026-10-04','financial-genuine-wrapper-claimedrun-source-recovery-review03-2026-10-04','financial-genuine-wrapper-claimedrun-witness-actual-capture-review01-2026-10-04','financial-genuine-wrapper-claimedrun-witness-capture-review01-2026-10-04','financial-genuine-wrapper-root-claimedrun-witness-capture01-2026-10-04','financial-genuine-wrapper-root-claimedrun-recovery-evidence-capture01-2026-10-04']
paths=[S/'STATE.md',B/'parallel-execution-2026-10-02/COORDINATION.md']
for tree in [C,remote,flat,*[B/n for n in scopes]]:
 assert tree.is_dir()
 for root,dirs,files in os.walk(tree,followlinks=False):
  root=Path(root);links=[n for n in dirs if(root/n).is_symlink()];paths.extend(root/n for n in links);dirs[:]=[n for n in dirs if n not in links and n not in ('.git','selected','__pycache__','union-bytes01') and not n.endswith('.git')];paths.extend(root/n for n in files)
paths.append(B/'financial-genuine-wrapper-root-claimedrun-witness-capture01-2026-10-04/union-bytes01/ORIGINAL_TREES01.json')
write(C/'STAGE18_BUILDER01.py',Path(__file__).read_bytes());paths.append(C/'STAGE18_BUILDER01.py')
rows=[]
for p in sorted(set(paths)):
 rel=p.relative_to(M).as_posix();assert not any(n.lower() in('keys','apis','.env','.ssh','hf_token.txt')or n.lower().endswith(('.pem','.key'))for n in p.parts);st=p.lstat()
 if stat.S_ISLNK(st.st_mode):body=os.readlink(p).encode();kind='lexical-link'
 else:assert stat.S_ISREG(st.st_mode)and st.st_size<=4*1024**2;body=p.read_bytes();kind='file'
 rows.append({'path':rel,'kind':kind,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()})
write(C/'STAGE18.json',enc({'rows':rows,'count':len(rows),'scope':'Closed actual complete handoff witness capture and recovery-source/review captures; full strict03 source/review/witnesses; Root exact remote/flat helper installations and checkpoint. Duplicate Git/selected/union bodies excluded; original complete opaque archives retained. No external/native execution.'}))
names=[r['path']for r in rows]+[(C/'STAGE18.json').relative_to(M).as_posix()]
for start in range(0,len(names),80):subprocess.run(['git','add','-f','--',*names[start:start+80]],check=True)
print(json.dumps({'staged_paths':len(names),'new_claim':False,'native_active':False,'effective_metadata':19,'highest_actual':18,'spent':1}))
