import hashlib,json,os,shutil,stat
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
sources={'complete-root-generation01':'financial-genuine-wrapper-root-claimedrun-outcome-binding-generation01-2026-10-04','complete-binder-source-review02':'financial-genuine-wrapper-claimedrun-outcome-binding-review02-2026-10-04','complete-final-release-review01':'financial-genuine-wrapper-claimedrun-parent-final-release-review01-2026-10-04'}
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,o):
 with (H/n).open('x') as f:f.write(json.dumps(o,sort_keys=True,indent=2)+'\n')
for dest,source in sources.items():shutil.copytree(B/source,H/dest,symlinks=True)
q=json.loads((H/'complete-root-generation01/generated-claimedrun01/REQUEST_FINAL03.json').read_bytes());snap=H/'actual-parent-selected-body-snapshot';snap.mkdir();parent=Path(q['parent_root']);selected=['REQUEST_FINAL03.json','parent01.py',*q['helper_hashes']]
selected += [str(Path(ref['path']).relative_to(parent)) for ref in [*q['proofs'].values(),q['final_review']]]
for n in selected:
 p=snap/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(parent/n,p,follow_symlinks=False)
put('SNAPSHOT_SCOPE01.json',{'kind':'finite selected actual Parent snapshot, not a complete Parent capture','original_root':str(parent),'paths':sorted(selected),'complete_original_trees':sources})
put('HARNESS_FAILURE01.json',{'status':'preserved independent check01 failure','cause':'Original full-recovery proof is named READBACK01.json in its independent review directory, not FULL_SOURCE_RECOVERY01.json. Installed Parent uses the latter local name. check01 stopped at this incorrect original filename; check02 joins the actual original body/hash.','original_error':'FileNotFoundError','changed_original_or_actual_outcome':False,'additional_check_correction':'Actual inverse contains six effective edits because REQUEST_FINAL03 is unchanged; seven was the earlier test-only REQUEST_FINAL77 count. No candidate defect.'})
report='''Actual generated binding accepted for source and metadata scope. Independent check02 passed 2,146 checks. No material defect was found in this exact emission. The initial check01 harness failure is preserved: an incorrect assumed original recovery-proof filename was corrected to the actual independent READBACK01.json. This did not change any original or rerun any generation.

Complete Root generation MANIFEST_ACTUAL04 cd53521c5abe8d90ae7511e1f7c2d7fe574c5e59e8fa7a983d7b09392cbe4f5e matches all141 declared members, body types, modes and hashes, with only that manifest excluded from its census. Every adopted author02 member is unchanged. The complete generation tree, complete independent source review including all original window witnesses, and complete final release review are retained beneath this review. A separate explicitly selected Parent snapshot preserves the twelve referenced request/caller/helper/proof bodies; it is not represented as a whole Parent capture.

The installed request529c9bf3c587e6160a217e8eb339882e59433b6fc0f759d0009d261f872b2bd8 equals the emitted request byte-for-byte. Actual caller5d5 and all six helpers match the accepted bodies. Actual independent originals match cumulative3268, source-input-runtime0592, full-recovery468d and seven-field final release95dadb. The genuine original pure validate_release function accepted this actual request; no preflight, admit, Run, Owner, binder generation or outcome verifier was invoked. Source HEAD0a2 equals design/current, gate3a20, all338 source bodies and eight input hashes, runtime251 metadata and absence of a new claim were observed read-only.

Actual emitted verifier14089451a225aa541eb6faf30c78cb31c79b1380d7ef54d77e895575e3ce250c and BINDING57e3b72754668f3be5d1611475b9c29be3fabd91ffe71c5cad60792fa4881989 match independently reconstructed transformation and binding fields. The complete byte/AST inverse returns original f662. Six effective edits are present: request hash, source commit, three accounting edits and full ordered window/prior-exposure expansion. The request filename remains REQUEST_FINAL03, so the accepted helper skips that no-op; seven edits belonged to the earlier different test basename. Exact inverse to the already independently accepted source preserves native failure/CPU/cleanup semantics and schema guards, without repeating the prior351 scalar checks. Historical failed claim4c54/3515 remains pinned, two-identity denominator/effective19 applies only to a future genuine claim, and no exposure is declared fresh by this binding.

Root generation receipt07fefc records one original ea1d79 successful emission, exact stdout and empty stderr. OS PID/ticks/group/session history remains null; source inspection cannot reconstruct it. Later Root census03 failure06f232 occurred before its scan and remains separately preserved. Actual census04 sealed the existing output without regeneration. Neither census nor the reviewer harness failure is a scientific attempt.

This acceptance is not an outcome classification, numerical-capacity result or permission to execute. Root still requires complete final caller/proof/review/witness union capture, actual external recovery and fresh native eligibility/release. The original full Source recovery proof explicitly excludes final Parent/caller/review recovery, POSIX reinstantiation, installed runtime bodies and empirical stores; those limits are retained. Tensor/checkpoint arithmetic, financial results, fees/funding, PnL conventions, real native behavior and all1,420 paper fits were not tested. Original failed identity remains terminal, spent1, highest actual budget18; no new claim or numerical run was created.
'''
with (H/'REPORT01.md').open('x') as f:f.write(report)
readback=json.loads((H/'READBACK01.json').read_bytes());put('VERDICT01.json',{'schema_version':1,'reviewer':'combined_worker_review','decision':'ACCEPTED_ACTUAL_BINDING_SOURCE_ONLY','checks':readback['checks'],'readback_sha256':sha((H/'READBACK01.json').read_bytes()),'actual_request_sha256':readback['actual_request_sha256'],'actual_verifier_sha256':readback['actual_verifier_sha256'],'actual_binding_sha256':readback['actual_binding_sha256'],'actual_generation_manifest_sha256':readback['actual_generation_manifest_sha256'],'actual_outcome':None,'numerical_release':False,'complete_final_caller_recovery':None,'original_process_history':None,'material_findings':[],'effective_inverse_edits':6,'unchanged_request_basename':'REQUEST_FINAL03.json','remaining_requirements':['complete final caller/proof/review/witness capture and actual external recovery','fresh native eligibility and Root release']})
rows=[]
def scan(root):
 for p in sorted(root.iterdir()):
  s=p.lstat();r={'path':p.relative_to(H).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISREG(s.st_mode):b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b))
  elif stat.S_ISDIR(s.st_mode):r['kind']='directory'
  elif stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(p))
  else:raise ValueError('unexpected kind')
  rows.append(r)
  if r['kind']=='directory':scan(p)
scan(H);rows.sort(key=lambda r:r['path']);put('MANIFEST01.json',{'schema_version':1,'scope':'complete review excluding only this manifest','members':rows,'member_count':len(rows),'counts':{k:sum(r['kind']==k for r in rows) for k in ('file','directory','symlink')}})
for n in ('MANIFEST01.json','VERDICT01.json','READBACK01.json','REPORT01.md'):print(n,sha((H/n).read_bytes()))
print('members',len(rows))
