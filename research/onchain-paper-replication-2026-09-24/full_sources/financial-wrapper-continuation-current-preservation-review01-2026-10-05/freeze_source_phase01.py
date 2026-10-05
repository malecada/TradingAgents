"""Finite immutable source-phase snapshot, excluding later actual entry/outcomes."""
from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;F=H.parent;sys.path.insert(0,str(F/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05'));from verify_capture01 import Reader,R
rd=Reader();P=F/'financial-wrapper-continuation-current-preservation-preparation01-2026-10-05';N=F/'financial-wrapper-continuation-current-preservation-preparation02-2026-10-05';A=F/'financial-wrapper-continuation-current-admission-review01-2026-10-05';parent=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-compatibility-root-launch-20261005-01')
comp=json.loads(rd.read(P/'CURRENT_COMPOSITION02.json','65ee768ba3a6569b125920bbc61f01d64487a90a5ced608df31b505cd008f370'));source=json.loads(rd.read(A/'SOURCE_INPUT_RUNTIME_PROOF01.json','18e4dcd06596478b8d338bd2b0b53cd6adcaca3f565fd85211ec591c335bb0d3'));reuse=json.loads(rd.read(parent/'proof_reuse_contract01.json','d46aa04a41b530d0e497ca8c423beacab58d778a7241839084ac0751a38da033'))
refs={}
def add(role,ref):
 raw=rd.read(Path(ref['path']),ref['sha256']);old=refs.get(ref['path']);assert old is None or old['sha256']==ref['sha256'];refs.setdefault(ref['path'],dict(ref,bytes=len(raw),roles=[]))['roles'].append(role)
for i,r in enumerate(comp['basis_refs']):add('composition_basis_%d'%i,r)
for role,r in reuse['anchors'].items():add('accepted_reuse_'+role,r)
for role,r in source['compatibility_preclaim_external_refs'].items():add('accepted_policy_'+role,r)
for role in ('review','report'):add('current_source_'+role,source[role])
for name in ('CUMULATIVE_PROOF01.json','SOURCE_INPUT_RUNTIME_PROOF01.json','MACHINE01.json','MANIFEST01.json'):
 raw=rd.read(A/name);add('current_admission_'+name,{'path':str(A/name),'sha256':R.digest(raw)})
# These complete modest review trees preserve authentic basis evidence. No old body stores are reread.
scopes=[P,N,A,F/'financial-wrapper-compatibility-complete100-recovery-outcome-review03-2026-10-05',F/'financial-wrapper-compatibility-baseline-recovery-review02-2026-10-05']
closed=[]
for p in scopes:
 raw=rd.read(p/'MANIFEST01.json');closed.append({'path':str(p),'manifest_sha256':R.digest(raw)})
rd.finish();R.put(H/'TRANSPORT_DEPENDENCIES01.json',{'schema_version':1,'closed_scopes':closed,'additional_exact_metadata_refs':list(refs.values()),'current_source_snapshot':'SOURCE_PHASE_MANIFEST01.json plus exactly its declared members','scope':'Finite new payload plus actual trusted basis metadata; historical raw stores are reused under accepted proofs, not recursively retransferred or newly claimed current. One literal negative symlink is metadata only; never follow it.','future_entry_and_outcome_excluded':True,'new_numerical_authority':False})
report='''# Current preservation source phase

Accepted exact local composition65ee768b/selectionafa2f09d:27 new bodies842,160 bytes, comprising five CAP files,11 Parent files,two genuine source/accounting proofs and nine original Git objects. All copied and original new bodies/modes joined independently. The complete current CAP namespace is1,049 typed/823 regular; old818 body hashes are reused from accepted actual complete100 recovery32acf316 and the initial authenticated census, with fresh complete metadata/mode/extent/signature checks. The old818 bodies were not reread. The genuine407-object basis02900ae1 plus exact nine original object bodies reconstructs current416; current360 tracked/359 source pins/29 input roles and source664e remain exact. The source-bound drafteb5aa and callerb50d remain unreleased: full_recovery and final_review are null.

Original helper9161fc is withheld at bind02.py:50. It opens a child FD before allocating the hash/parts objects and before entering try/finally. A real owned-file descriptor plus injected MemoryError at digest allocation left that child FD open; the review closed it after observing the leak. Successor53f4a5fc changes exactly one statement order, allocating the digest/parts before acquiring the descriptor. Full byte/AST inverse, the exact original RED/new GREEN and ordinary real-body controls pass; immutable IO09d1 and boundedGitdb4a remain unchanged. No full collect or second old818 scan ran.

The first reviewer read/close test had an incorrect expected result: IO09d1 uses sys.exception() and already preserved the original read fatal. Its failed assertion, source and owned fixture are retained; the corrected control passes. That harness error is explicitly not a source finding.

SOURCE_PRESERVATION_RELEASEd092 grants only the exact corrected read-only source and authenticated local preservation bytes. It does not grant remote or flat entry, external recovery, complete-current proof, final Parent release, admission or numerical execution. Concrete future receiver/flat roots, actual pushed commit, canonical exact selection, generated helper/caller and release-bound contracts remain required. Sampled currentness is not writer exclusion; no runtime-package body, POSIX reconstruction or whole-capacity claim follows.

SOURCE_PHASE_MANIFEST01 is a precise immutable inventory of this phase, including original witnesses. Later actual entry/outcome files will be new files outside this snapshot in the same consolidated review directory. This is one review with a finite source snapshot, not a closed claim about all future directory contents. TRANSPORT_DEPENDENCIES01 lists the exact finite current/accepted metadata anchors; it does not recursively retransfer old raw stores or invent a future proof.
'''
with (H/'SOURCE_PHASE_REPORT01.md').open('x') as f:f.write(report)
ref=lambda p:{'path':str(p),'sha256':R.digest(R.read(p.parent,p.name))}
R.put(H/'SOURCE_PHASE_MACHINE01.json',{'schema_version':1,'decision':'ACCEPTED_EXACT_CURRENT_PRESERVATION_SOURCE_AND_LOCAL_BYTES_ONLY','source':'664e2ca5fa11d6640ab79f64c5aa222aeb3a9128','reviewer':'/root/storage_watch_review','release':ref(H/'SOURCE_PRESERVATION_RELEASE01.json'),'report':ref(H/'SOURCE_PHASE_REPORT01.md'),'composition_readback':ref(H/'COMPOSITION_READBACK01.json'),'source_readback':ref(H/'SUCCESSOR_READBACK01.json'),'transport_dependencies':ref(H/'TRANSPORT_DEPENDENCIES01.json'),'helper_sha256':'53f4a5fc154311e7dcbbb77dcdd37954a6f07f9ab83e5ad7ecc543932b98375b','original_helper_withheld':'9161fc3812687708f4365b3137b05f9d2b65bb8a8b9a314cdc966cf64b99ccec','actual_entry_release':None,'external_recovery':False,'numerical_authority':False})
m=R.scan(H);m['scope']='Exact source-phase snapshot; later review files intentionally outside this frozen inventory';m['self_excluded']='SOURCE_PHASE_MANIFEST01.json';R.put(H/'SOURCE_PHASE_MANIFEST01.json',m)
print(json.dumps({'manifest':ref(H/'SOURCE_PHASE_MANIFEST01.json'),'machine':ref(H/'SOURCE_PHASE_MACHINE01.json'),'dependencies':ref(H/'TRANSPORT_DEPENDENCIES01.json'),'source_snapshot_members':len(m['members']),'metadata_ref_count':len(refs)}))
