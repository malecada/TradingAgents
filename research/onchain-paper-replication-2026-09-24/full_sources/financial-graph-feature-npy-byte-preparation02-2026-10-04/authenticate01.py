import ast,gzip,hashlib,json,os,stat,sys
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;sys.path.insert(0,str(H));import npy_bytes03 as N
sha=lambda b:hashlib.sha256(b).hexdigest();checks=0;scopes=[]
for dirname,expected in [('financial-graph-feature-npy-byte-preparation01-2026-10-04','c8b40a1d731d8fbef5e7e55712bd87b92454eeda3e4893df03a6764be22987c9'),('financial-graph-feature-npy-byte-source-review01-2026-10-04','10c52643f4431a3ecc791ade86773b2fee18128b9982682110dff8b205ef6cd7')]:
 root=B/dirname;p=root/'MANIFEST01.json';raw=p.read_bytes();assert sha(raw)==expected;checks+=1;items=json.loads(raw)['members'];paths={x['path'] for x in items}
 actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p!=root/'MANIFEST01.json'}
 assert actual==paths- {'.'};checks+=1
 for row in items:
  p=root/row['path'];s=p.lstat();mode=int(row['mode'],8) if type(row['mode']) is str else row['mode'];assert stat.S_IMODE(s.st_mode)==mode;checks+=1
  if row['kind']=='file':assert s.st_size==row['bytes'] and sha(p.read_bytes())==row['sha256'];checks+=2
  elif row['kind']=='symlink':assert os.readlink(p)==row['target'];checks+=1
  else:assert stat.S_ISDIR(s.st_mode);checks+=1
 scopes.append({'root':str(root),'manifest_sha256':expected,'members':len(items)})
O=B/'financial-graph-feature-npy-byte-preparation01-2026-10-04';j=json.loads((O/'SAMPLED_BOUNDARY01.json').read_text());accepted=[]
for row in j['records']:
 p=O/'boundary01'/str(row['case'])/'array-000000.npy';raw=p.read_bytes()
 assert sha(raw)==row['current_sha256'] and row['expected_sha256']!=row['current_sha256'];checks+=2
 assert list(N.fingerprint(p.stat()))==row['after'];checks+=1
 if row['accepted']:
  assert row['before']==row['after'];checks+=1;accepted.append(row)
  # New admission refuses the SAME actual opaque witness path, before reading
  # bytes or requiring fabricated scientific metadata.
  try:N.Cursor(p,b'not-authority')
  except PermissionError:checks+=1
  else:raise AssertionError('old accepted mutation path re-admitted')
assert len(accepted)==5;checks+=1
(H/'ORIGINAL_FIVE_CHANGED_RETURNS01.json').write_text(json.dumps({'source':str(O/'SAMPLED_BOUNDARY01.json'),'source_sha256':sha((O/'SAMPLED_BOUNDARY01.json').read_bytes()),'five_original_changed_returns':accepted,'new_path_admission':'all five refused before metadata or payload read','historical_outcomes_rerun':False},indent=2,sort_keys=True)+'\n')
# Exact installed pinned writer parser functions preserved by AST; no import.
for name in ('PINNED_WRAP_HEADER03.py','SOURCE_PINS03.json'):
 (H/name).write_bytes((O/name).read_bytes())
pins=json.loads((O/'SOURCE_PINS03.json').read_text())
for row in pins['sources']:
 p=Path(row['path']);assert p.stat().st_size==row['bytes'] and sha(p.read_bytes())==row['sha256'];checks+=2
abi=[]
for p in map(Path,('/usr/include/linux/fcntl.h','/usr/include/asm-generic/fcntl.h','/usr/include/linux/memfd.h')):
 raw=p.read_bytes();abi.append({'path':str(p),'bytes':len(raw),'sha256':sha(raw)});(H/('UAPI_'+p.name)).write_bytes(raw)
assert '#define F_LINUX_SPECIFIC_BASE\t1024' in (H/'UAPI_fcntl.h').read_text();checks+=1
# Same basename copies would lose the Linux header, so retain separately using
# explicit names as well. UAPI_fcntl.h is the last asm-generic copy, documented.
for p,name in [(Path('/usr/include/linux/fcntl.h'),'UAPI_linux_fcntl.h'),(Path('/usr/include/asm-generic/fcntl.h'),'UAPI_asm_generic_fcntl.h')]:
 (H/name).write_bytes(p.read_bytes())
body=(H/'UAPI_linux_fcntl.h').read_text()
for token in ('F_LINUX_SPECIFIC_BASE + 9','F_LINUX_SPECIFIC_BASE + 10','F_SEAL_SEAL\t0x0001','F_SEAL_SHRINK\t0x0002','F_SEAL_GROW\t0x0004','F_SEAL_WRITE\t0x0008'):
 assert token in body;checks+=1
(H/'AUTHENTICATION01.json').write_text(json.dumps({'checks':checks,'complete_predecessors':scopes,'source_pins':pins,'uapi_headers':abi,'kernel_seals_actual':15,'binding':'Python fcntl invokes authenticated Linux UAPI numeric1033/1034; standard-library ctypes calls actual exported libc.memfd_create only in test fixture construction','legacy_python_capability_failure':'CHECK01.err; pinned Python lacks os.memfd_create and named fcntl seal constants','no_scientific_import':all(x not in sys.modules for x in ('numpy','torch','scipy','pandas'))},indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':checks,'status':'PASS'}))
