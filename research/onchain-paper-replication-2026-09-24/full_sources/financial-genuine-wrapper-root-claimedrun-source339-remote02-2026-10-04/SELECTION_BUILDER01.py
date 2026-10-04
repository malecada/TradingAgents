import hashlib,json,subprocess
from pathlib import Path
M=Path.cwd();B=M/'research/onchain-paper-replication-2026-09-24/full_sources';old=B/'financial-genuine-wrapper-root-claimedrun-source339-remote01-2026-10-04';H=B/'financial-genuine-wrapper-root-claimedrun-source339-remote02-2026-10-04'
commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();assert commit=='6514f20fc208e0d2f7ada31bc285b4e0b5c33ff8';assert not(H/'SELECTED_BODIES01.json').exists()
oldselection=json.loads((old/'SELECTED_BODIES01.json').read_bytes());paths={M/r['path']for r in oldselection['rows']};assert len(paths)==176
trees=[B/'financial-genuine-wrapper-claimedrun-actual-admission-review01-2026-10-04',B/'financial-genuine-wrapper-claimedrun-source339-selection-review01-2026-10-04',old]
for tree in trees:
 for p in tree.iterdir():
  assert p.is_file()and not p.is_symlink();paths.add(p)
paths.add(H/'recover01.py');rows=[]
for p in sorted(paths):
 raw=p.read_bytes();rel=p.relative_to(M).as_posix();assert len(raw)<=4*1024**2;assert subprocess.check_output(['git','show',commit+':'+rel])==raw
 rows.append({'path':rel,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
assert len(rows)<=506 and sum(r['bytes']for r in rows)<=64*1024**2
body=(json.dumps({'remote_commit':commit,'rows':rows},sort_keys=True,indent=2)+'\n').encode()
with(H/'SELECTED_BODIES01.json').open('xb')as f:f.write(body)
r={'selection_sha256':hashlib.sha256(body).hexdigest(),'selected_count':len(rows),'logical_bytes':sum(r['bytes']for r in rows),'remote_commit':commit,'original01_withheld_preserved':True,'correction':'Full original five-file actual-admission-review01/24e6451d/proof059232d0 added, plus full original selection/refusal bodies; all176 earlier selected byte rows remain unchanged. New complete Source339 capture still defines source scope; legacy six Source325 pins supplemental only. Final Parent/caller/release/full witness supplements/runtime/empirical remain excluded and independently required before numerical release.','actual_external':False,'new_claim_or_native':False}
with(H/'SELECTION_SCOPE01.json').open('x')as f:json.dump(r,f,sort_keys=True,indent=2);f.write('\n')
with(H/'SELECTION_BUILDER01.py').open('xb')as f:f.write(Path(__file__).read_bytes())
print(json.dumps(r,sort_keys=True))
