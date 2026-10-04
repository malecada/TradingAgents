import hashlib,json,stat
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def put(n,b):
 with (H/n).open('xb') as f:f.write(b)
def enc(q):return (json.dumps(q,sort_keys=True,indent=2)+'\n').encode()
for tag,name in [('PRIMARY','financial-genuine-wrapper-root-claimedrun-final-shards-remote01-2026-10-04'),('SUPPLEMENTAL','financial-genuine-wrapper-root-claimedrun-helper-raw-remote01-2026-10-04')]:put(tag+'_SELECTION01.json',(B/name/'SELECTED_BODIES01.json').read_bytes());put(tag+'_FREEZE01.json',(B/name/'SELECTION_FREEZE01.json').read_bytes())
r=json.loads((H/'READBACK01.json').read_bytes());m=dict(r,readback_sha256=sha((H/'READBACK01.json').read_bytes()));put('MACHINE01.json',enc(m))
put('REPORT01.md',('''# Independent committed two-selection review

Accepted the two exact committed selections at Main a9b219042109be78498185cc6539c1454736e3eb. Primary selection SHA28f95d42e6f53c243d31ed9867724fedd89b04cb601b63de199ac2616c0f49c9 and supplemental SHAc8dd51669514a49a1c75ad6e74572579d1a0590bad8c1da0d44d70245c54c4ea are canonical and match the previously accepted complete census rows exactly. Only the commit binding and removal of census-only role/mode fields distinguish the transport schema.

Every one of the 689 distinct paths was read from the immutable commit and compared to its actual local body, extent, SHA256, Git blob OID, tracked mode and original literal mode. Current HEAD remained unchanged before/after. Local Git calls disabled lazy fetch, replacements, optional locks and all transport protocols, with finite time/output bounds. No network or Git mutation occurred. The earlier full archive/original-tree closure review064d78 remains immutable and is joined by exact identical row bodies; its canonical framing work was not substituted with counts.

Primary359 /52,374,727B /729 maximum Git operations and supplemental336 /4,362,239B /683 operations satisfy the original506-path,64MiB,4MiB-body and1024-operation limits. The only overlap is six exact mandatory Source325 safety anchors. The supplemental retains all330 exporter-own raw bodies; complete typed metadata binds45literal links, directory/root modes and empty directories. These shared bytes do not transfer identity or budget.

Both installed transport source bodies remain exact0b397ccd. Fresh bare repositories, selected directories, intents, receipts and failure outputs are absent. Source/caller/PAX/full-scope/proof roles remain exactly those accepted in census02; failed original capture8/c720 and direct c47f bytes remain selected without altered disposition.

This permits one original ordinary byte-transfer invocation per fresh namespace after Root confirms the actual remote commit. This review did not observe a remote readback, fetch or recovery and does not assert that either transfer has succeeded. Root must retain original outcomes and independently verify both actual receipts and complete combined recovery. No numerical, runtime, empirical, capacity or native release follows.
''').encode())
rows=[]
for p in sorted(H.iterdir()):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1;b=p.read_bytes();rows.append({'path':p.name,'kind':'file','mode':stat.S_IMODE(s.st_mode),'bytes':len(b),'sha256':sha(b)})
put('MANIFEST01.json',enc({'schema_version':1,'members':rows}))
for n in ['MACHINE01.json','READBACK01.json','MANIFEST01.json']:print(n,sha((H/n).read_bytes()))
print('members',len(rows))
