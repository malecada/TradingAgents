import hashlib,json,stat
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def put(n,b):
 with (H/n).open('xb') as f:f.write(b)
def enc(q):return (json.dumps(q,sort_keys=True,indent=2)+'\n').encode()
for tag,base in [('PRIMARY','financial-genuine-wrapper-root-claimedrun-final-shards-remote01-2026-10-04'),('SUPPLEMENTAL','financial-genuine-wrapper-root-claimedrun-helper-raw-remote01-2026-10-04')]:
 for n in ['REMOTE_RECOVERY01.json','ACTUAL_TOOL_TERMINAL02.json','INTENT01.json','ACTUAL_RECOVERY01.out','ACTUAL_RECOVERY01.err']:put(tag+'_'+n,(B/base/n).read_bytes())
r=json.loads((H/'READBACK01.json').read_bytes());put('MACHINE01.json',enc(dict(r,readback_sha256=sha((H/'READBACK01.json').read_bytes()))))
put('REPORT01.md',('''# Independent actual two-batch external byte outcome

Accepted both original selected-byte transfer outcomes at immutable a9b219042109be78498185cc6539c1454736e3eb. Primary receipt ec84e55cfeae3da74557341d3395a84ce5fe4c0a2f187eaec89acc1ded212440 and supplemental7518301a0862c314c05c379c4f30f249481351a397bcc0e55cfd3c8e91264a30 join the exact independent committed-selection release3d3bfd and unchanged transport0b397.

All695 physical private0600 saved files were checked against original selected bodies, literal-mode metadata, immutable Main tree and fresh recovered Git blobs. The union has689distinct paths /52,795,748B; only six exact mandatory safety anchors overlap. Every fresh blob OID, Git mode, extent, hash and saved byte matches. Both selected namespaces have no omitted or extra regular files or followed links. Exact byte identity carries forward the accepted complete role/archive/census checks, including45literal-link texts and330ownraw originals, fullSource339, final20trees, witness5trees with required direct raw, tooling2/helper6 and retained failed8/c720. Original Source325 wording is preserved literally and is not substituted for actual scope evidence.

Original operation sequences and all per-body size/body output hashes join, as do initial/final remoteHEAD hashes, fetched commit and selected-tree output. All1412recorded operations have exit0, no cleanup failures and bounded durations/stream extents. The two original outer tool exits, raw stdout/stderr, before-exec intents, actual receipt hashes and recorded disk observations agree. Outer stderr is empty. Original init/fetch diagnostics remain their recorded bounded operation hashes; unstored raw diagnostics are not invented.

All1414recorded Root/Git PID identities and their owned process groups are currently absent. This is a present observation plus original recorded terminal evidence, not a claim of continuous history or unrecorded descendant completeness. MainHEAD and original receipts remained unchanged across verification. Local read-only Git verification disabled transport, lazy fetch, replacement objects and optional locks; no network was performed by the reviewer.

Actual complete fresh flat restoration remains pending and must separately bind exact requests, genuine releases, all restored bodies and canonical archive semantics. No POSIX restoration, installed runtime-body recovery, empirical evidence, budget transfer, native capacity or numerical release follows. Neither ordinary transfer is to be replayed.
''').encode())
rows=[]
for p in sorted(H.iterdir()):
 st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1;b=p.read_bytes();rows.append({'path':p.name,'kind':'file','mode':stat.S_IMODE(st.st_mode),'bytes':len(b),'sha256':sha(b)})
put('MANIFEST01.json',enc({'schema_version':1,'members':rows}))
for n in ['MACHINE01.json','READBACK01.json','REPORT01.md','MANIFEST01.json']:print(n,sha((H/n).read_bytes()))
print('members',len(rows))
