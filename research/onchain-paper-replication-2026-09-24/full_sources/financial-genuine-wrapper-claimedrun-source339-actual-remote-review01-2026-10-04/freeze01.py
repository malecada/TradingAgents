import hashlib,json,stat
from pathlib import Path
O=Path(__file__).resolve().parent;x=json.loads((O/'READBACK01.json').read_text())
(O/'REPORT01.md').write_text('''# Independent actual Source339 selected remote recovery

Accepted exact actual remote receipt9e6d7dd7 for selection38bc70a9/current committed6514f20f. All195 original bodies, fetched immutable Git blobs/OIDs/modes and saved0600 single-link bodies agree exactly; total18,500,231 bytes. Saved membership has no extras or omissions. All selected remote archives were independently bounded-raw framed and canonically recompressed byte-for-byte. Complete Source3391029/747/current0a2 and genuine copied failed claim remain unchanged; actual independent admission proof0592/manifest24e is present and authenticated. Earlier accepted complete archive/witness scope joins remain bound by identical original and remote bytes.

All401 original Git operations match the exact expected sequence, return0 and report no cleanup failures. Initial and final actual remote HEAD output hashes bind6514f20f; commit/tree output hashes and every390 object-size/body operation hash bind the actual fetched bytes. Root's retained stdout/empty stderr, original intent and terminal bind session70954/start8d9766/completion24df16 exit0. Recorded Root PID451048/start ticks15906391/group/session451045 and all401 original child PIDs/process groups are currently absent. This is current absence plus original recorded identity, not fabricated lifetime history. Individual raw Git streams were not retained as separate files; their receipt hashes are joined where outputs are reconstructable.

Original inherited source325 status and qualification are preserved verbatim. This report supplies the distinct actual195-body Source339 scope; legacy six Source325 bodies remain supplemental. Actual new Source339 flat/Git recovery, final Parent/caller/review closure, installed runtime bodies, empirical stores, POSIX reinstantiation and numerical capacity/eligibility remain separate and unproved here.

No network, capture/recovery replay, bare repository reconstruction, admission, claim, numerical import or Source mutation occurred. One reviewer hash-literal transcription failure and a pending Path-expression typo are retained under check01/HARNESS_FAILURE01; separate check02 corrects only reviewer code and passes against unchanged actual artifacts. Root alone may next prepare the exact flat request for separately reviewed genuine release.
''')
m=[]
for p in sorted(O.rglob('*')):
 s=p.lstat();assert stat.S_ISREG(s.st_mode);b=p.read_bytes();m.append({'path':p.relative_to(O).as_posix(),'kind':'file','mode':stat.S_IMODE(s.st_mode),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
(O/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'members':m},sort_keys=True,indent=2)+'\n');print('checks',x['checks'])
for n in ['READBACK01.json','REPORT01.md','MANIFEST01.json']:print(n,hashlib.sha256((O/n).read_bytes()).hexdigest())
