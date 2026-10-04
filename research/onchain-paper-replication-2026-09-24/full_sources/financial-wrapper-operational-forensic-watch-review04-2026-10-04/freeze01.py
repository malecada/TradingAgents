from pathlib import Path
import hashlib,json,os,stat,shutil
P=Path(__file__).absolute().parent;A=P.parent/'financial-wrapper-operational-forensic-watch-correction04-2026-10-04'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,v):(P/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
(P/'historical').mkdir(mode=0o700)
for n in ['FAILED01.json','ROOT_REMOTE02_EXIT01.json','READBACK01.json','ROOT_REMOTE02.stderr']:shutil.copyfile(A/'historical-failed-remote02'/n,P/'historical'/n)
a=json.loads((P/'READBACK01.json').read_bytes());b=json.loads((P/'READBACK02.json').read_bytes());author=json.loads((A/'MANIFEST01.json').read_bytes())
put('MACHINE01.json',{'schema_version':1,'decision':'ACCEPTED_NARROW_SOURCE_ONLY_FIXED_PUBLICATION_RETRY_SCHEDULE','watch_sha256':sha((P/'watch01.py').read_bytes()),'original_watch_sha256':sha((P/'watch.original03.py').read_bytes()),'author_manifest_sha256':sha((A/'MANIFEST01.json').read_bytes()),'author_typed_members':len(author['members']),'independent_checks':a['checks']+b['checks'],'exact_one_method_literal_inverse':True,'all_other_AST_and_POLICY_unchanged':True,'two_actual_publisher_pairs_old_RED_new_GREEN':True,'original_failed_receipt_sha256':'7491cc3c1940b68cab9b218e972a13c925f5ce1ff21d9f0a2f32ee416246268a','historical_init_observed_exit':None,'separate_init_actual_reaped_exit':0,'historical_changed_path':None,'historical_changed_signature_component':None,'timing_deviation':{'maximum_waits':2,'wait_seconds':0.1,'complete_attempts':3,'whole_sample_deadline':5,'returned_seconds_is_last_successful_sample_not_total_retry_elapsed':True},'actual_external_recovery':None,'actual_flat_recovery':None,'native_release':None,'numerical_execution':False,'live_source_or_claim_changes':False,'independent_git_child_execution':False,'reason_no_new_git_child':'Only census scheduling changes; copied receiver/process manager exact byte identity authenticated, author actual local child controls retained. Independent real publisher/iterator/metadata controls exercise the changed seam.'})
(P/'REPORT01.md').write_text('''# Independent forensic watcher04 source review

ACCEPTED_NARROW_SOURCE_ONLY for watcher bdeacaadc053e615245b3e2175089842708719448ec7da970d981e5dc077ca18. Full frozen author membership/type/mode/body checks and the exact one-method literal inverse to cd2200 passed. Every other AST node, POLICY value, owned-IO09d1 and receiver9ddc source remains unchanged. No source installation, remote/flat outcome, scientific claim or numerical release is granted.

The change adds only a fixed100ms pause before each of the remaining two complete attempts after ChangingTree/FileNotFoundError. The three-attempt and five-second limits remain; a pre-wait deadline check requires sufficient room and a post-wait check refuses overshoot before another attempt. No retry occurs for ordinary nonretriable errors, MemoryError, KeyboardInterrupt or SystemExit. Sleep itself may overrun under OS scheduling, which is detected; this is not a hard real-time preemption guarantee. The accepted result's seconds remains the final successful sample duration, not total retry-plus-pause time.

Independent real publisher threads and real lstat endpoints produced two oldRED/newGREEN pairs: old03 exhausted all attempts during finite publication; new04 included the newly published directory and body on complete attempt two after the pause. Further independent controls used actual pending-name rename/disappearance, persistent leaf inode and mode replacement, real extent growth, full namespace/pending-name counting, scaled lower cap/floor refusals, real hardlink and lexical redirect refusals, exact two-wait ceiling, deadline insufficient room/overshoot, first-fatal refusal, and actual iterator closure before a secondary exception. Existing receiver child/process handling was not rewritten or reexecuted independently; its byte identity and author's retained real local child evidence were authenticated. No network or empirical execution occurred.

The raw failed Root02 receipt retains observed init exitNULL separately from actual cleanup reap0, outer exit1, and no remote-success or flat receipt. Its exact changed path/signature component and discarded retry exceptions were not historically recorded and remain unknown. The new publication controls demonstrate a plausible reproducible timing mechanism; they do not reconstruct those missing historical values or reclassify that permanent failed namespace.

The source retains original sampled whole-tree64MiB logical/96MiB allocated,4MiB per regular file,32768 members, depth32,10GiB floor, five-second census and8192 sample limits. Both regular extent endpoints count via their maximum; complete directory identity/signature and namespace checks remain. Pauses improve the demonstrated finite publication case only. Persistent churn still refuses, and sampled metadata is neither continuous quota nor immutable-byte/ABA exclusion. Existing IO diagnostics are unchanged; the verified contract is first-fatal preservation and attempted actual descriptor cleanup, not a new universal secondary-exception serialization guarantee. Actual forensic success, process closure, resource scope and external/fresh recovery remain Root operations requiring independent outcome review. Financial return/fee/funding/exposure conventions, numerical methods and capacity were not exercised.
''')
rows=[]
def visit(p,rel=''):
 for q in sorted(p.iterdir(),key=lambda x:x.name):
  n=q.name if not rel else rel+'/'+q.name
  if n=='MANIFEST01.json':continue
  s=q.lstat();r={'path':n,'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(q));rows.append(r)
  elif stat.S_ISDIR(s.st_mode):r.update(kind='directory');rows.append(r);visit(q,n)
  elif stat.S_ISREG(s.st_mode):r.update(kind='file',bytes=s.st_size,sha256=sha(q.read_bytes()),nlink=s.st_nlink);rows.append(r)
  else:raise ValueError(n)
visit(P);rows.sort(key=lambda r:r['path']);put('MANIFEST01.json',{'schema_version':1,'scope':'complete independent review excluding self seal; lexical/hardlink controls retained literally','members':rows,'typed_members':len(rows),'regular_files':sum(r['kind']=='file' for r in rows),'regular_bytes':sum(r.get('bytes',0) for r in rows)})
print(json.dumps({n:sha((P/n).read_bytes()) for n in ['MANIFEST01.json','MACHINE01.json','REPORT01.md','READBACK01.json','READBACK02.json']}));print('checks',a['checks']+b['checks'],'typed',len(rows))
