from pathlib import Path
import json,hashlib,stat,os
H=Path(__file__).resolve().parent;B=H.parent;D=B/'financial-wrapper-compatibility-operational-delta-root-remote03-2026-10-04';C=B/'heartbeat-root-checkpoint10-2026-10-04/root_operational_flat04.py';sha=lambda b:hashlib.sha256(b).hexdigest();draft=json.loads((D/'ROOT_FLAT04_INSTALLATION_DRAFT01.json').read_bytes())
for root,n,dest in [(C.parent,C.name,'root_operational_flat04.py'),(D,'ROOT_FLAT04_INSTALLATION_DRAFT01.json','ROOT_FLAT04_INSTALLATION_DRAFT01.json'),*[(D,n,'installed/'+n) for n in draft['helpers_and_metadata']]]:
 p=H/'evidence'/dest;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((root/n).read_bytes())
report='''# Exact flat entry04 review — withheld

**WITHHELD_EF1_EF2. No entry release is granted.** Caller815d2a88 and installed draft770f509c remain unexecuted and unchanged. The genuine installed source17f4/profiled238/review262160-231ae/current remote64c745/exit0f0/selectiond2f64 and source acceptancec1f124-c1ed84 authenticate. Its pure read-only component verifies15 records. Fixed flat namespaces are absent; current whole-owned census and10GiB floor pass. These successful preconditions do not discharge caller cleanup failures.

1. EF1 — caller `put`, line26, transfers a newly opened descriptor to `os.fdopen` without fallback cleanup if that call raises. Exact AST-extracted put with a real owned output descriptor and injected MemoryError at fdopen propagates that error while `os.fstat` proves the descriptor still open and the retained partial file has0 bytes. The reviewer then closes only that exact verified inode/descriptor and confirms closure. The same raw-fd transfer pattern exists at line64 for stdout/stderr; it needs an owned context which retains and closes each descriptor even before stream construction succeeds. Line63 bare close can itself replace the opening error. Use the already pinned owned IO ownership/cleanup contract rather than changing helper or scientific scope.

2. EF2 — outer finally line88 invokes final receipt construction/readback/publication without protecting the selected primary. Exact AST-extracted finalbody around a real original KeyboardInterrupt and genuine tiny-root watcher census encounters SystemExit during final receipt fdopen. SystemExit escapes instead of the original KeyboardInterrupt; the earlier object is only in context. The real newly opened terminal descriptor also requires reviewer cleanup. Protect diagnostic construction and terminal publication, preserve the original primary/fatal precedence, attempt remaining cleanup, and retain secondary exception objects. Lines81/83 currently retain only cleanup type names, so original exception evidence is also not durable in memory. A separate source successor should address these narrow ownership/diagnostic paths.

The witness READBACK01 incorrectly labels the second source line95 (reviewer location typo); its captured clause is exact actual line88, as preserved source confirms. No source/failure bytes are edited to hide the typo. Both real opaque partial files and all script/stdout/stderr are retained.

Thirty-six assertions passed, including exact draft-before-parse hash, installed eight dependency/helper mode/byte pins, genuine source review joins, actual installed selected component, fixed absent namespaces, sampled resources, previously recorded transfer PIDs absent, and owned wrong-pin/absent/symlink read refusals. No fabricated release, Admission, Run, Owner, child receipt or scientific outcome was constructed. The extracted finalbody used child=None and actual tiny owned census solely to reproduce final diagnostic failure; it is not a launched helper or process receipt.

Remaining review scope: full independent selected-job process census, actual child launch/kill/reap behavior, successful public outer execution, actual flat outcome and sidecar authentication are not tested or granted. Existing source04 finite sampling/private-output checks remain accepted separately. No network, flat entry, numerical imports, original Root output/mode mutation, research claim or budget change occurred. Source/caller05 must be separately frozen and independently reviewed before any one-use release.
'''
(H/'REPORT01.md').write_text(report)
r=json.loads((H/'READBACK01.json').read_bytes());m={'schema_version':1,'decision':'WITHHELD_EF1_EF2_CALLER_CLEANUP','owned_root':str(D),'root_outer_caller_sha256':sha(C.read_bytes()),'installation_draft_sha256':sha((D/'ROOT_FLAT04_INSTALLATION_DRAFT01.json').read_bytes()),'flat_helper_sha256':draft['source_sha256'],'remote_receipt_sha256':draft['remote_receipt_sha256'],'selection_sha256':draft['selection_sha256'],'flat_execution_released':False,'remote_execution_released':False,'numerical_authority':False,'actual_entry_started':False,'actual_flat_result':None,'checks':r['assertions'],'findings':['EF1 raw descriptor ownership lost at fdopen failure','EF2 final diagnostic publication masks original fatal and discards secondary objects'],'witness_sha256':sha((H/'READBACK01.json').read_bytes()),'report_sha256':sha((H/'REPORT01.md').read_bytes()),'line_correction':'READBACK EF2 line95 is reviewer typo; actual captured source clause line88'}
(H/'MACHINE01.json').write_text(json.dumps(m,indent=2,sort_keys=True)+'\n');rows=[]
for p in sorted(H.rglob('*')):
 if p==H/'MANIFEST01.json':continue
 s=p.lstat();z={'path':p.relative_to(H).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):z['kind']='directory'
 elif stat.S_ISREG(s.st_mode):z.update(kind='file',bytes=s.st_size,sha256=sha(p.read_bytes()))
 elif stat.S_ISLNK(s.st_mode):z.update(kind='symlink',target=os.readlink(p))
 else:raise AssertionError(p)
 rows.append(z)
(H/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'members':rows,'exclusion':'self only; actual negative link and both partial failed tiny writes preserved'},indent=2,sort_keys=True)+'\n');print(json.dumps({'manifest':sha((H/'MANIFEST01.json').read_bytes()),'machine':sha((H/'MACHINE01.json').read_bytes()),'witness':m['witness_sha256'],'report':m['report_sha256'],'members':len(rows)}))
