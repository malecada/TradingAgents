from pathlib import Path
import hashlib,json,os,stat
H=Path(__file__).resolve().parent;B=H.parent;A=B/'financial-wrapper-compatibility-coalesced-evidence-preparation03-2026-10-04';V=B/'financial-wrapper-compatibility-coalesced-evidence-source-review03-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest()
def save(n,x):(H/n).write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
(H/'prior-review03').mkdir(mode=0o700);pins={}
for n,pin in [('MANIFEST01.json','d3b22887453c96585db36a41a50e0121ce5dd37f9da2245bdd1913758a50a244'),('MACHINE01.json','285276d9c75a77463333935bdba60fcf275a1843066dbf216ae4adac8246797f'),('CENSUS_DEADLINE_WITNESS01.json','85822989f74d6fd3b900771e415ecc95673ca16a6fe12394ad08e2e5894f8076'),('census_deadline_witness01.py','3641d333723a0aab2e1ac33c5a77409297fd90b92d3454d0b9846a6b1bcfaaa4'),('REPORT01.md',None)]:
 b=(V/n).read_bytes();assert pin is None or sha(b)==pin;(H/'prior-review03'/n).write_bytes(b);pins[n]=sha(b)
for n in ['INPUTS01.json','preclaim01.py','owned_io.py']:assert (H/n).read_bytes()==(A/n).read_bytes()
dead=json.loads((H/'DEADLINE04.json').read_bytes());full=json.loads((H/'FULL_CONTROLS03.json').read_bytes());controls=json.loads((H/'CONTROLS02.json').read_bytes());inverse=json.loads((H/'SOURCE_INVERSE01.json').read_bytes())
report='''SOURCE-ONLY successor04 fixes the independently witnessed census deadline gap in original068147. Original03, all controls, independent withheld review285276/d3b228, raw5.10029852s witness and actual Root output remain unchanged. Root output is still lexically absent.

Only namespace() changes. Four literal edits place its existing5s start before root canonical/type IO, check elapsed immediately after every actual iterator cleanup, and check elapsed after final resource/fingerprint joins immediately before returning. Full literal and AST inverse restores068147 exactly; every other function, embedded557b Reader/09d1 owned_io body, fixed5c4c INPUTS and all byte/mode/policy/finality clauses are unchanged. No exception-handler finally check replaces an active body/cleanup fatal: elapsed checks run only after successful cleanup propagation.

The original actual-source empty-directory iterator-close delay was independently reproduced in the author-owned control: old03 returned success after5.100603457s, new04 refused after5.100376888s, both closing the real iterator exactly once. A separately labelled deterministic monotonic offset after real statvfs establishes old acceptance/new refusal at the final resource boundary; this is not represented as real5s wall work. Five real iterator/body fatal pairs retain the selected first fatal even when the diagnostic clock is overdue. A real completed writer close followed by an injected expired genuine Reader deadline refuses and preserves the partial opaque file. These20 new assertions pass.

The unchanged217-control suite passes again, including25 real write/close error pairs, private/fresh output, exact input/body/mode/hash/member/currentness/redirect/hardlink/late mutation/floor refusals. A separate complete local opaque metadata-copy control repeats all57 fixed bodies:51 provenance origins,38 receipts,13 source-evidence bodies, original c5cf proof and unchanged concrete policy names/modes. The actual local Reader charges7,981,596B including final rereads; the88B difference from preparation03 is solely shorter owned-control output paths in its draft body. Actual full fixed Root output/entry is never invoked. The57 original bodies total1,384,187B; the complete local output has59 files including its draft and origin map. The original policy manifest accepts its three unchanged proof/machine/report members through actual metadata-only Reader/_sealed components.

Complete-copy timing remains bound by the exact Reader's120s deadline from construction, including its INPUTS read, all copies and final rereads. Each actual put returns through owned descriptor cleanup before the next Reader read/tick. After output directory cleanup, Reader.finish and final all-input/output fingerprint joins precede the existing final reader.tick. Thus an overdue writer or cleanup cannot lead to a successful complete-copy return. The timing bounds are checks at defined boundaries and cannot preempt an indefinitely blocked syscall or terminal pipe; Root must supply the actual supervised one-use outer process and retain its real stdout/stderr/exit. No constant pause, retry, cap increase or terminal success is manufactured.

File4MiB, totalReader8MiB, census5s, whole-copy120s, output64MiB logical/96MiB allocated/256members and10GiB free floor remain unchanged. Sampled metadata/currentness does not provide writer exclusion, atomicity, ABA immunity or kernel quota. Failed partial paths are retained and never reused. All old evidence/source/ROOT/CAP/Git/Parent/claim artifacts remain unchanged. No scientific imports, arrays/checkpoint decoding, network, registration, Admission, Owner, Run or numerical execution occurred.

The fixed helper emits only a draft candidate layout and original literal proof copies. A different-author source release must precede Root's one actual invocation; a further genuine independent actual-copy review must author the accepted machine/report/typed seal. Complete final Parent8MiB preclaim budget is separate and still requires actual measurement; this copier's local read cost does not establish it. No new accepted proof or numerical release is present.
'''
(H/'REPORT01.md').write_text(report)
save('MACHINE01.json',{'schema_version':1,'status':'SOURCE_ONLY_DEADLINE_SUCCESSOR_READY_FOR_INDEPENDENT_REVIEW','source_sha256':sha((H/'copy_layout01.py').read_bytes()),'original_sha256':sha((H/'ORIGINAL03_copy_layout01.py').read_bytes()),'prior_review_pins':pins,'changed_function_only':'namespace','literal_edits':4,'full_literal_AST_inverse':True,'unchanged_inputs_sha256':sha((H/'INPUTS01.json').read_bytes()),'inherited_assertions':controls['assertions'],'new_deadline_assertions':dead['assertions'],'actual_old_new_delay':dead['witnesses'][:2],'local_full_copy_actual_reader_bytes':full['actual_bytes_read_including_full_finish'],'actual_root_output_absent':not os.path.lexists(json.loads((H/'INPUTS01.json').read_bytes())['output_root']),'actual_root_entry_invoked':False,'new_accepted_machine':None,'new_recovery_proof':None,'full_parent_preclaim_fit':None,'numerical_authority':False,'report_sha256':sha((H/'REPORT01.md').read_bytes())})
rows=[];todo=[H]
while todo:
 p=todo.pop()
 with os.scandir(p) as it:
  for e in it:
   n=Path(e.path).relative_to(H).as_posix()
   if n=='MANIFEST01.json':continue
   s=e.stat(follow_symlinks=False);r={'path':n,'mode':stat.S_IMODE(s.st_mode)}
   if stat.S_ISDIR(s.st_mode):r['kind']='directory';todo.append(Path(e.path))
   elif stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(e.path))
   else:assert stat.S_ISREG(s.st_mode) and s.st_size<=4194304;r.update(kind='file',bytes=s.st_size,sha256=sha(Path(e.path).read_bytes()),nlink=s.st_nlink)
   rows.append(r)
rows.sort(key=lambda r:r['path']);save('MANIFEST01.json',{'schema_version':1,'manifest_self_excluded':True,'members':rows,'typed_members':len(rows),'regular_files':sum(r['kind']=='file' for r in rows),'literal_links':sum(r['kind']=='symlink' for r in rows),'logical_bytes':sum(r.get('bytes',0) for r in rows),'original_negative_hardlink_pairs_retained':True})
print(json.dumps({n:sha((H/n).read_bytes()) for n in ['copy_layout01.py','MACHINE01.json','MANIFEST01.json','REPORT01.md','SOURCE_INVERSE01.json']}))
