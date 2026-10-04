import hashlib,json,stat
from pathlib import Path
O=Path(__file__).resolve().parent;x=json.loads((O/'READBACK01.json').read_text())
(O/'REPORT01.md').write_text('''# Independent successor Source339 selection

Accepted exact selection02 SHA38bc70a9 at actual committed6514f20f for a separate original transport. All195 sorted unique paths total18,500,231 bytes and require401 Git operations. Every selected working body, immutable Git blob/OID, Git mode and literal local mode joins. All176 prior rows and object identities are unchanged; all19 new committed bodies were independently read. Complete earlier canonical archive verification is reused by unchanged full-body SHA, size and immutable OID, preserving the91,220-check original evidence rather than rerunning identical controls.

The original blocker is resolved: all five original actual-admission-review files are selected, including complete manifest24e6451d and independent proof059232d0. Every sealed member body/mode joins. This exact actual metadata admission is current=design0a2/339 tracked/338 pins/eight roles, effective metadata19, one globally spent claim and highest actual claim ceiling18. Fresh claim, full external flat recovery and final Parent release remain null. The selected actual-source-admission review remains distinct.

All selected self-owned manifest regular bodies close in the selection. Current Source339 remains byte-identical to its complete captured manifest and all338 proof-source bodies. The full failed partial Source01, actual Source02 ordinary preparation/history/generation/assembly evidence, four-handoff witness archive and recovery02/03 original witness archives retain their earlier verified complete bodies. Six inherited Source325 bodies are supplemental historical requirements, not substitutes for new Source339.

The accepted transport0b397 is unchanged. The successor fresh repo, selected output, receipt/failure/intent namespaces were absent; original selection01 remains withheld and unexecuted. Bounds remain506 selected paths/64 MiB aggregate/4 MiB individual/1,024 operations, with actual401 expected calls. The600-second entry threshold is not a universal wall-clock supervisor;60-second per-operation bounds and first-fatal cleanup remain inherited source semantics. Local committed selection is not an external-origin receipt. Root alone may perform the single separate remote02 operation; actual remote outcome and fresh Source339 recovery require independent subsequent review.

No network, restore, metadata admission, claim, Source mutation or numerical imports were performed. Final Parent/caller/release and supplementary witnesses, installed runtime bodies and empirical stores remain excluded and cannot be inferred recovered or released by this source selection.
''')
m=[]
for p in sorted(O.rglob('*')):
 s=p.lstat();assert stat.S_ISREG(s.st_mode);b=p.read_bytes();m.append({'path':p.relative_to(O).as_posix(),'kind':'file','mode':stat.S_IMODE(s.st_mode),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
(O/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'members':m},sort_keys=True,indent=2)+'\n');print('checks',x['checks'])
for n in ['READBACK01.json','REPORT01.md','MANIFEST01.json']:print(n,hashlib.sha256((O/n).read_bytes()).hexdigest())
