import hashlib,json,stat
from pathlib import Path
O=Path(__file__).resolve().parent;x=json.loads((O/'READBACK01.json').read_text())
(O/'REPORT01.md').write_text('''# WITHHELD: Source339 selection01 omits actual admission review

The exact176-row selection3b2d2525 at committed c29b1580 is withheld. It omits the complete original financial-genuine-wrapper-claimedrun-actual-admission-review01-2026-10-04 tree, including genuine independent metadata admission proof059232d0f7fc8922cee526a1bd30fef2ecb51ee17103284bcaac18c77e77641c and its manifest24e6451d2a9c5ec516b99ca95bb477567e5f9ef5d13adef3bb41c0633b93e5c7. Both original bodies exist and were authenticated. Neither hash appears in any selected direct body or any body in any selected archive. The selected actual-source-admission-review01 is a different tree and cannot substitute for this evidence. Root's raw actual admission record is also not the independent outcome review.

All176 selected original bodies match their immutable committed Git blobs, OIDs and modes. Selection is sorted/unique,17,783,124 bytes and363 expected operations under existing bounds. Every selected archive was bounded-raw parsed and canonically recompressed exactly. Current Source339/338 pins/eight roles/copied actual failed claim and current source Git bodies match; all four handoff original trees/186 bodies/13 literal links and all four recovery preparation/review archive scopes match their complete current originals. All selected self-owned review-manifest regular members are included. The missing actual-admission tree remains the concrete blocker despite those successful checks.

The safe inherited transport helper is unchanged0b397; its Source325 labels are historical qualifications, not Source339 evidence. Its fresh repo/selected/receipt/failure/intent namespaces were absent. No network, restore, admission, ResearchRun claim or numerical import was performed. Local selected body verification cannot establish external origin.

Preserve this original selection and all withheld evidence. A separately named successor selection must include the complete original actual-admission-review tree and receive independent exact review before any transport. Final Parent/caller/release/supplementary witnesses, installed runtime bodies and empirical stores remain outside this source-only selection and mandatory separately where applicable before numerical release.
''')
m=[]
for p in sorted(O.rglob('*')):
 s=p.lstat();assert stat.S_ISREG(s.st_mode);b=p.read_bytes();m.append({'path':p.relative_to(O).as_posix(),'kind':'file','mode':stat.S_IMODE(s.st_mode),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
(O/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'members':m},sort_keys=True,indent=2)+'\n')
for n in ['READBACK01.json','REPORT01.md','MANIFEST01.json']:print(n,hashlib.sha256((O/n).read_bytes()).hexdigest())
