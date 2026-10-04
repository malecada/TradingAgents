import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-genuine-wrapper-claimedrun-sharded-witness-capture-preparation02-2026-10-04'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(name,b):
 with (H/name).open('xb') as f:f.write(b)
def encode(q):return (json.dumps(q,sort_keys=True,indent=2)+'\n').encode()
for n in ('capture_witness02.py','shards01.py','INVERSE01.json','MANIFEST01.json'):
 put('CANDIDATE_'+n,(A/n).read_bytes())
r=json.loads((H/'READBACK01.json').read_bytes());extra=json.loads((H/'ADDITIONAL03.json').read_bytes())
m={'schema_version':1,'decision':'accepted-source-only-sharded-witness-capture-plus-exact-direct','source_sha256':r['source_sha256'],'author_manifest_sha256':r['author_manifest_sha256'],'readback_sha256':sha((H/'READBACK01.json').read_bytes()),'additional_sha256':sha((H/'ADDITIONAL03.json').read_bytes()),'independent_checks':r['count']+extra['count'],'source_current':'0a2e7639b42b9423b90743feadcda4078aa21816','original_regular_bodies':2302,'literal_links':59,'original_bytes':61971030,'mapping_bytes':r['mapping_bytes'],'whole_logical_bytes_including_direct_and_mapping':r['whole_logical_including_mapping'],'projected_shards':r['projected_shards'],'direct_body':r['direct_body'],'requires_index_kind':'complete-witness-shards-plus-direct-v1','actual_capture':False,'actual_external_recovery':False,'shards_alone_complete':False,'native_or_numerical_authority':False,'limitations':['Root must independently preserve and recover the exact directly selected raw body together with every shard and mapping.','Original Source339 recovery and twenty-tree caller union remain separate required scopes.','No installed runtime bodies, empirical stores, POSIX tree restoration, numerical capacity or execution release is established.','The first reviewer harness failed on symlink versus lexical-symlink schema spelling. Exact target and mode comparison in check02 passed; original failure is retained.']}
put('MACHINE01.json',encode(m))
put('REPORT01.md',('''# Independent witness exporter02 source review

Accepted narrowly for the exact source body and source-only five-tree byte capture. No actual Root capture or external recovery occurred in this review.

The complete candidate seal and all five original seals were checked against their entire live typed membership. The census independently matches 2,302 regular bodies, 61,971,030 bytes and 59 literal links. Every original body hash, size, literal mode and path was authenticated; links were read only as metadata. The full current Source339 manifest, final Parent request and actual binding/full-source proof pins still match.

The only direct body is the original actual-capture-review READBACK01.json, 2,532,973 bytes, SHA c47fcb6875375ecb8ea5c60926bae307955007751cdf52bec2473c44964e17e3 and mode 0600. It is not replaced by its gzip, compact view or an invented receipt. The remaining bodies plus mapping project into 57 shards; parent overhead is counted in each 256-member bound. Original bodies including the direct body plus the 845,648-byte mapping total 62,816,678 bytes, below 64 MiB. Individual body/archive caps remain 4 MiB, shard logical cap 2 MiB, floor 10 GiB and source wall bound 120 seconds. No generic oversized-body fallback exists.

A real owned three-shard pipeline restored every archived byte through unchanged R4, independently recompressed each canonical archive, and joined the actual 2,532,973-byte raw body to reconstruct all projected originals. The executed index uses complete-witness-shards-plus-direct-v1 and carries the exact direct descriptor. Shards alone are explicitly incomplete. Missing, duplicate, wrong hash/mode/path direct metadata, archived omissions/extras, late body/mode/member/literal-link changes, missing direct input and reused owned namespace were refused. Real MemoryError, SystemExit and KeyboardInterrupt retained their original identity through actual put/new_file cleanup when close also raised; both real body and parent descriptors were closed.

The documented inverse reproduces the complete previous withheld exporter bytes and AST. The planner and all three original primitives match accepted originals. Source checks do not turn previous withheld preparation into a successful capture. The original first reviewer harness failed because one genuine manifest spells a literal link kind symlink rather than lexical-symlink; check02 explicitly normalizes only that spelling and retains exact link target/mode. All original failed harness evidence is preserved.

Root must execute the original fresh namespace once, then obtain independent actual capture, selected transport and full recovery verification. The directly selected original raw body must be present and joined in that actual union. Current Source339 and the twenty-tree final caller union are separate preservation scopes. No numerical release, installed runtime recovery, empirical result, POSIX instantiation or capacity claim follows.
''').encode())
rows=[]
def walk(p,rel):
 st=p.lstat();r={'path':rel,'mode':stat.S_IMODE(st.st_mode)}
 if stat.S_ISLNK(st.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
 elif stat.S_ISDIR(st.st_mode):
  r['kind']='directory';rows.append(r)
  for c in sorted(p.iterdir()):walk(c,c.name if rel=='.' else rel+'/'+c.name)
  return
 else:
  assert stat.S_ISREG(st.st_mode) and st.st_nlink==1
  b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b))
 rows.append(r)
for p in sorted(H.iterdir()):walk(p,p.name)
put('MANIFEST01.json',encode({'schema_version':1,'members':sorted(rows,key=lambda r:r['path'])}))
for n in ('MACHINE01.json','READBACK01.json','REPORT01.md','MANIFEST01.json'):print(n,sha((H/n).read_bytes()))
print('members',len(rows),'checks',m['independent_checks'])
