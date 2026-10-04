import hashlib,json,stat
from pathlib import Path
O=Path(__file__).resolve().parent;x=json.loads((O/'READBACK01.json').read_text())
(O/'REPORT01.md').write_text('''# Original final capture FAILED — no complete union archive

Verified the original failed attempt and retained evidence. The4,190,463-byte partial union.tar.gz is incomplete: bounded gzip reading raises EOFError because the end-of-stream marker is absent. It is not accepted as a complete or recoverable final-union archive. UNION_AUTHENTICATION01.json is absent. The unchanged4 MiB archive cap rejected aggregate compressed output; the largest copied regular body is575,475 bytes, so this was not an individual-body overflow or demonstrated RAM/capacity failure.

Original raw stderr is retained byte-for-byte. It contains the body ValueError archive exceeds4MiB; retain failed attempt and a second equal ValueError from gzip close, grouped as two body/cleanup failures, followed by original owned_io.CleanupFailure. Neither error is discarded, coerced into success or replaced by a synthetic receipt. Original stdout is empty.

All copied prepack1,476 typed members/1,186 regular bodies (including the mapping) match the actual saved manifest and stable retained union tree. Every one of the20 original roots still matches the accepted source-review census:1,185 bodies/18,864,635 bytes and50 literal symlink targets, with exact original paths/types/modes and copied opaque bytes. Literal links remain metadata, never followed or instantiated. Original Source339 remains entirely unchanged; final Parent request529c remains unchanged, no Parent attempt exists and no new claim was created.

Root reported original unified session62650/start dcf485/completion133355 exit1. Separate terminal was pending at verification time. Original OS PID/start ticks/process group are unobserved and null; no process-history or cleanup observation is fabricated from tool IDs. Later genuine terminal records may be joined additively without changing this failed disposition.

The original namespace is permanently closed and must remain unchanged except additive documentary preservation. No capture rerun, archive repair, restore, network, numerical import or Root/Source/Parent mutation was performed. Prior source-only acceptanceb5a6 remains an immutable source review; this actual outcome is FAILED. Any successor needs a separately reviewed complete sharding scheme under the same body/archive caps and full preservation of this failure, followed by actual complete capture/external/fresh-recovery review. No numerical or final-union authority follows here.
''')
m=[]
for p in sorted(O.rglob('*')):
 s=p.lstat();assert stat.S_ISREG(s.st_mode);b=p.read_bytes();m.append({'path':p.relative_to(O).as_posix(),'kind':'file','mode':stat.S_IMODE(s.st_mode),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
(O/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'members':m},sort_keys=True,indent=2)+'\n');print('checks',x['checks'])
for n in ['READBACK01.json','REPORT01.md','MANIFEST01.json']:print(n,hashlib.sha256((O/n).read_bytes()).hexdigest())
