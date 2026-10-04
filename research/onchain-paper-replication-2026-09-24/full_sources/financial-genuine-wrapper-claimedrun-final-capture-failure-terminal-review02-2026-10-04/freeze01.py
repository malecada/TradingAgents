import hashlib,json,stat
from pathlib import Path
O=Path(__file__).resolve().parent;x=json.loads((O/'READBACK01.json').read_text());(O/'REPORT01.md').write_text('''# Additive genuine failed-capture terminal and preservation scope

Verified exact terminalef8e9f17: original tool62650/dcf485/133355 exit1, matching raw stdout/stderr, original partial archivefc7d4f78/4,190,463 bytes and prepackmanifestc72030b4. Original OS PID/start ticks/process-group history remain null. Both archive-cap body/cleanup errors remain in unchanged raw stderr; the previously verified incomplete gzip remains failed and unauthenticated.

The complete failed-Root manifestfdda7c05 is canonical and matches every1,484 actual member excluding only its own subsequently appended seal. Current Root contains1,485 members including that seal. Every body/type/mode was verified and the complete scope remained stable after reading. All20 original trees still match all1,185 copied regular bodies and50 literal-link targets; no link is followed or extracted.

Original failure review9b29dc2e/readback1533e3d4 is immutable and its FAILED/no-union disposition is unchanged. This supplementary review joins the now persisted actual terminal and closed failed-scope byte inventory; it does not authenticate the partial archive as complete, recoverable final union, successful capture or numerical authority. No replay, archive repair, network, Source/Parent/Root mutation, claim or numerical import occurred. Preserve the permanently closed namespace for any separately reviewed sharded successor.
''');m=[]
for p in sorted(O.rglob('*')):
 s=p.lstat();assert stat.S_ISREG(s.st_mode);b=p.read_bytes();m.append({'path':p.relative_to(O).as_posix(),'kind':'file','mode':stat.S_IMODE(s.st_mode),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
(O/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'members':m},sort_keys=True,indent=2)+'\n');print('checks',x['checks'])
for n in ['READBACK01.json','REPORT01.md','MANIFEST01.json']:print(n,hashlib.sha256((O/n).read_bytes()).hexdigest())
