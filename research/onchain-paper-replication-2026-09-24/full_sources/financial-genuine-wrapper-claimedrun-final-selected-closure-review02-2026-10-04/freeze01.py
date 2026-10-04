import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-genuine-wrapper-claimedrun-final-selected-closure-census02-2026-10-04'
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(q):return (json.dumps(q,sort_keys=True,indent=2)+'\n').encode()
def put(n,b):
 with (H/n).open('xb') as f:f.write(b)
for n in ['census02.py','MANIFEST01.json','READBACK01.json','ACTUAL_HELPER_REVIEW_BINDING01.json']:put('CANDIDATE_'+n,(A/n).read_bytes())
r=json.loads((H/'READBACK01.json').read_bytes());m={k:r[k] for k in ['schema_version','decision','census_manifest_sha256','rows_sha256','batches_sha256','checks','distinct_paths','distinct_bytes','primary','supplemental','shared_anchor_paths','supplemental_own_raw','literal_links','actual_commit','actual_remote_receipt','numerical_authority']};m['readback_sha256']=sha((H/'READBACK01.json').read_bytes());put('MACHINE01.json',enc(m))
put('REPORT01.md',('''# Independent current selected-scope closure review

Accepted as the exact current two-packet scope candidate, not a committed selection or remote result. CANDIDATE_ROWS02 SHA 70ff2feb00e4d334a14897a87222077b943643d96bff087a275bbcdd3b43569f and TRANSPORT_BATCHES02 SHA 8f3e9ef773fdd9d2a815b3133bd28297930d02043182a4f4a8c68d982159f095 bind the reviewed rows. The entire frozen census and every current selected regular file, mode, size, SHA and canonical path were authenticated.

Primary contains 359 paths / 52,374,727 bytes / 729 bounded Git operations. Supplemental contains 336 paths / 4,362,239 bytes / 683 operations. Their union is 689 distinct paths / 52,795,748 bytes. Only the exact six mandatory Source325 anchors overlap; all payloads are disjoint. Each packet fits 506 paths, 64 MiB total, 4 MiB per body and 1,024 operations. Both installed transport bodies are unchanged 0b397ccd. All future commit, namespace and receipt fields remain null. Shared anchors are read-only safety context, not a numerical identity, budget transfer or replay.

Complete typed metadata matches every declared current root, including all 330 raw exporter-own source/review files and all 45 literal links, root/directory modes and empty directories. Every regular typed member is selected, and the typed mapping itself is selected. Both exact installed caller closures and genuine actual-six review92f349 are present; no future review placeholder is inferred as acceptance.

All actual canonical preservation archives were independently framed, checked member-by-member and exactly recompressed: the eleven-shard 20-tree caller union, 57-shard five-tree witness union, two tooling archives, six helper archives and complete Source339 archive. Every archived original tree was reenumerated against current names, kinds, literal modes, body hashes and link targets. The sole unarchived c47f raw direct body is selected exactly. Shards alone remain incomplete. The complete original CORE117 bytes/modes are unchanged.

All eight original failed-capture outer bodies are present, including raw errors, original terminal, partial gzip and failed seal. The original c720 prepack manifest is byte-identical to the successful eleven-shard virtual manifest, so full failed union membership is represented without changing its failed disposition. The partial fc7d archive remains opaque failed evidence, never a successful gzip claim. Current Source339 and the no-attempt Parent state remain unchanged.

Missing, duplicated, changed hash/mode/path, removed anchor and oversized batch mutations were refused. No network, actual transport, restoration, admission or numerical execution occurred. Original runtime/empirical stores and native capacity remain excluded. Root must bind the reviewed row bodies to actual committed selections, perform and independently verify both fresh transports, and obtain complete final recovery acceptance before any numerical release. This report and final census metadata are external audit artifacts; no self-hash recursion is claimed.
''').encode())
rows=[]
for p in sorted(H.iterdir()):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1;b=p.read_bytes();rows.append({'path':p.name,'kind':'file','mode':stat.S_IMODE(s.st_mode),'bytes':len(b),'sha256':sha(b)})
put('MANIFEST01.json',enc({'schema_version':1,'members':rows}))
for n in ['MACHINE01.json','READBACK01.json','REPORT01.md','MANIFEST01.json']:print(n,sha((H/n).read_bytes()))
print('members',len(rows))
