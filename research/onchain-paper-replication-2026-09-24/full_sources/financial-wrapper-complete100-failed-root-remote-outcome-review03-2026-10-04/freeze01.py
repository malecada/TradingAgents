import datetime,hashlib,importlib.util,json,os,shutil,stat
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;D=B/'financial-wrapper-complete100-failed-root-remote03-2026-10-04';MAIN=B.parents[2]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(H/n).write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
r=json.loads((H/'READBACK01.json').read_text());o=json.loads((H/'ORIGINAL_REJOIN01.json').read_text());spec=importlib.util.spec_from_file_location('readonly_current_watch',D/'watch01.py');w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w);current=w.census(D);save('CURRENT_OWNED_TREE01.json',{'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':sha(D/'watch01.py'),'actual_read_only_census':current,'distinct_from_original1342samples':True})
for n in r['flat_absent']:assert not os.path.lexists(D/n)
for n,p in r['source_pins'].items():assert sha(D/n)==p['sha256']
assert sha(D/'REMOTE_RECOVERY01.json')==r['remote_receipt_sha256']
report='''# Actual forensic remote03 and prospective flat entry review

ACCEPTED for the actual35-body byte retrieval, and for ONE still-unattempted original restore01.py entry bound to receipt33c0a82e. This is ordinary forensic byte preservation; no numerical release follows.

The exact recovered35 paths total16,481,302 bytes and29 distinct Git blob OIDs from commitc23c9156. All35 current original bytes, mode/type/OID tree entries and computed Git blob identities agree. The fetched commit object and full selected tree were inspected locally with lazy fetching disabled. The first and final original ls-remote outputs join exactly. All109 original operations record exit0, actual reaped exit0, empty cleanup failures and actual child hard/soft4MiB limit readbacks. Original Root exit0 and raw stdout/empty stderr match their hashes. Current recorded PIDs and process groups are absent; this does not reconstruct unobserved historical descendants or prove continuous process-tree coverage.

All1,342 actual complete storage observations meet the fixed policy. Their maxima are35,199,442 logical bytes,35,631,104 allocated bytes and174 members, with43 regular extent changes. The initial14-member allocation is retained. These are sampled whole-namespace measurements, not atomic snapshots or a kernel quota. The separate final current census includes later receipt/output bodies and is not substituted into the original sample series. Root elapsed68.9247620489914 seconds and helper elapsed68.82393640300143 remain distinct recorded values.

All ten archives passed bounded PAX framing, every typed member/path/mode/hash, full termination checks and an independent canonical TAR/gzip reconstruction. The capsule master is588 typed members/475 files/23,015,911 bytes, disjointly covered by eight shards; repeated directory metadata is explicitly allowed. Parent has28/24 and support26/23; the ten physical shard manifests total762 entries/522 files. Every current original capsule member (excluding separately preserved .git), complete Parent and explicit support mapping still matches. The prior zero-capsule capture remains withheld with all nine selected original bodies unchanged; its reused Parent/support archives remain literal. Original remote02 is still failed. That remote02 terminal is locally pinned here, not falsely included in this earlier committed35-body retrieval.

Installed remote9ddc59dd, watchcd2200b0, flat8a4cb8e0 and all three unchanged primitive pins match the genuine source/release records. The status suffix02 and fresh bare namespace suffix02 are original literal strings inside remote03; they are not rewritten to manufacture provenance. The flat caller authenticates the exact actual receipt/selection and all10 manifests, creates private0700 destinations before the unchanged R4 restore, rejoins every retained flat body, enforces its180-second/10GiB-floor/file bounds, and retains failed disposition/first-fatal handling. All ten output namespaces plus FLAT_INTENT/RECOVERY/FAILED were absent at this review. The release is consumed by a single entry; any failure remains terminal in that namespace.

4,738 final readback/original-scope checks passed. The first harness erroneously queried bare HEAD, which this object-only recovery intentionally does not install. Its traceback and all partial evidence are retained. The corrected checker queries the pinned fetched commit object and its tree, without network; the original helper's actual FETCH_HEAD join remains in the109-operation receipt. No helper main, entry or restore was executed by this reviewer, no checkpoint was deserialized, and no numerical package was imported.

Actual fresh flat recovery and independent whole-outcome acceptance remain future. Baseline385 Git reconstruction is separate; this review grants no recovered POSIX topology, installed runtime body closure, checkpoint validity, complete100 success, financial result, budget refund or whole-fit capacity. All three failed research claims remain spent. Root must preserve these new review/release receipts subsequently; they postdate the remote commit.
'''
(H/'REPORT01.md').write_text(report)
machine={'schema_version':1,'decision':'ACCEPTED_ACTUAL_FORENSIC_REMOTE03_AND_ONE_FLAT_ENTRY','reviewer':'combined_worker_review','root':str(D),'remote_receipt_sha256':r['remote_receipt_sha256'],'root_exit_sha256':r['root_exit_sha256'],'remote_commit':r['selection']['commit'],'selection_sha256':r['selection']['sha256'],'selected_rows':35,'selected_logical_bytes':16481302,'unique_git_oids':29,'actual_git_operations':109,'helper_pins':r['source_pins'],'maximum_entries':1,'exact_command':[str(MAIN/'.venv/bin/python'),'-B',str(D/'restore01.py'),'--remote-receipt-sha256',r['remote_receipt_sha256']],'required_absent_paths':r['flat_absent'],'flat_scopes':[x['scope'] for x in r['archives']],'flat_deadline_seconds':180,'disk_floor_bytes':10737418240,'per_body_bytes':4194304,'flat_logical_bound_bytes':67108864,'actual_flat_recovery':None,'numerical_release':False,'claims_or_allowances_changed':False,'research_identity_permanently_failed':True,'baseline385_git_separate':True,'posix_runtime_capacity_authority':False,'readback_sha256':sha(H/'READBACK01.json'),'original_rejoin_sha256':sha(H/'ORIGINAL_REJOIN01.json'),'report_sha256':sha(H/'REPORT01.md'),'final_checks':r['checks']+o['checks'],'qualification':'Single original ordinary byte restoration only; fresh output and final boundary checks must still pass. All review receipts postdate the actual remote commit.'}
save('MACHINE01.json',machine)
rows=[]
for base,dirs,files in os.walk(H,followlinks=False):
 for n in sorted(dirs+files):
  p=Path(base)/n;st=p.lstat();row={'path':str(p.relative_to(H)),'mode':stat.S_IMODE(st.st_mode)}
  if stat.S_ISDIR(st.st_mode):row['kind']='directory'
  elif stat.S_ISREG(st.st_mode):assert st.st_size<=4194304;row.update(kind='file',bytes=st.st_size,sha256=sha(p))
  else:raise ValueError('unexpected owned type')
  rows.append(row)
rows.sort(key=lambda x:x['path']);save('MANIFEST01.json',{'schema_version':1,'scope':'whole review except self manifest','members':rows,'typed_members':len(rows),'files':sum(x['kind']=='file' for x in rows),'regular_bytes':sum(x.get('bytes',0) for x in rows)})
print(json.dumps({'manifest_sha256':sha(H/'MANIFEST01.json'),'machine_sha256':sha(H/'MACHINE01.json'),'report_sha256':sha(H/'REPORT01.md'),'typed_members':len(rows),'current_owned':current}))
