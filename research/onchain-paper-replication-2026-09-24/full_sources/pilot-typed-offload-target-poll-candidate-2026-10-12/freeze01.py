from pathlib import Path
import hashlib,json,difflib,ast
P=Path(__file__).resolve().parent;R=P.parents[3];S=R/'tradingagents/research/onchain_replication'
names=('archive_owner_policy.py','archive_owner_operations.py','typed_payload_operations.py')
forward=[];inverse=[]
for n in names:
 old=(P/('BASELINE_'+n)).read_text();new=(P/n).read_text();assert old==(S/n).read_text();ast.parse(new)
 path='tradingagents/research/onchain_replication/'+n
 forward.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+path,tofile='b/'+path))
 inverse.extend(difflib.unified_diff(new.splitlines(True),old.splitlines(True),fromfile='a/'+path,tofile='b/'+path))
(P/'CANDIDATE01.diff').write_text(''.join(forward));(P/'INVERSE01.diff').write_text(''.join(inverse))
(P/'REPORT.md').write_text('''# Typed offload Target polling candidate

Status: UNINSTALLED; focused offline AST engineering only. Three isolated source copies; Main/live source, inputs, Gate, registration, source limits, network and research jobs unchanged.

Original constructor polls Target once, then Ledger._current(full=True) invokes Selection.check/_record; _record performs boundary + two read_input calls twice. writer_policy repeats the same six admission operations. Twelve simulated nine-second operations produce 108 seconds without a Target poll; original Interval refuses stale refresh at the next lease. CHECK02/03/04 retain this expected original RED and candidate GREEN using actual extracted _record/_inputs/Selection and unchanged Interval implementation. Fixtures are explicitly not genuine Owner/Run/Admission authority.

The selected target keyword flows through Ledger._current -> Selection.check -> _record -> _inputs. After each existing Owner.boundary/verify_current pair and each run.read_input, the new module function checks exact Target type and same Owner/execution chain, calls Target.lease, then rejoins Owner and exact execution identity. Every original admission, metadata/schema/runtime/content/capacity/transport comparison remains in its original relative order. No cache, generic callable, stale-window increase or validation deletion is introduced. None sends original empty kwargs, preserving old calls/results/order.

The constructor forwards its existing target through both six-operation blocks. New module-level pre-cap polls rejoin the pinned Target, original parent context capability and held transition before/after callbacks, without accessing self.cap. All newly added constructor polls precede installing context._cap. Recovery writer_policy also forwards the existing selected target. No added fallible poll follows capability installation while the context manager still has op=None. Existing reservations, publication ordering and slot restoration remain; failure still poisons Owner and ledger. Selected failure-note handling uses guarded BaseException.add_note so cleanup evidence failure cannot replace a primary callback fatal; the None note path remains literal old behavior.

Eleven focused controls are covered by CHECK04 (ten pass plus fixture setup error) and CLEANUP05 (the two affected cleanup/ledger controls pass after supplying the missing AST-only transition decorator stub). CHECK01's invalid synthetic capacity allowance was corrected in its fixture, not weakened in production checks; raw failure and draft retained. CHECK02/03 each record nine passes. Controls cover 12x9s flow, None order/result parity, exact Target/owner/execution replacement refusal, source/environment callback errors, 61s indivisible refusal, Selection and Ledger forwarding, no self.cap dependency, capability mutation, no polls after installation, poisoning, slot restoration and original-fatal retention even when cleanup and overridden add_note fail. No full repository matrix or actual research authority was run.

Recursion audit: Target.lease calls target_lease/Lease.check. Lease._live uses Owner/Stage.lease and compact_owner.verify_current; Lease._full uses execution.check and Target.final(full_graph=False). These paths do not call Selection.check/_record, so the added seam does not recurse. Existing scheduler callbacks and full/live/fingerprint policy are untouched. A single admission or a full callback that exceeds the registered freshness limit still refuses; this is scheduling repair, not a guarantee that all real durations fit.

New helpers are module functions, authenticated by existing _loaded scanning when their already-used modules are source-pinned. Existing AUTHORITY_CLASSES does not include Selection/Ledger/_Operation; no roster change is made. New precap helper was deliberately moved out of _Operation into module scope (iteration02 retains the draft). archive_dispatch imports archive_owner_policy before population and typed_payload_operations during setup; caller._prepare_lease_modules imports typed_payload_operations before activation. Future committed source pins must include all three exact changed bodies. Existing class-body hashes and capability checks remain; genuine source/runtime activation is unproved here.

CANDIDATE01.diff and INVERSE01.diff contain final changes. prepare_candidate01.py is retained initial draft generation evidence, not the final installer; final copies/diff are authoritative. No new authority framework or operational release is provided. Root owns review, integration, committed future source/registration, recovery and actual qualification.
''')
def pin(f):
 b=f.read_bytes();return dict(path=str(f.relative_to(R)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
source=list(names)+['imported_mcm_identity.py','imported_authority_lease.py','imported_authority_interval.py','compact_owner.py','real_pilot_import_caller.py','archive_dispatch.py']
manifest={'status':'UNINSTALLED_FOCUSED_SYNTHETIC_VERIFIED','source_pins':[pin(S/n) for n in source],'files':[pin(f) for f in sorted(P.rglob('*')) if f.is_file() and f.name!='SOURCE_MANIFEST01.json']}
(P/'SOURCE_MANIFEST01.json').write_text(json.dumps(manifest,indent=2)+'\n')
for n in (*names,'SOURCE_MANIFEST01.json'):print(n,pin(P/n)['sha256'])
