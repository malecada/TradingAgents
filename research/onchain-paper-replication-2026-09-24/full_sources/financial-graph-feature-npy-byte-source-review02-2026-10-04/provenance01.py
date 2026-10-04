from pathlib import Path
import json,hashlib,os,stat,sys
H=Path(__file__).resolve().parent;B=H.parent;A=B/'financial-graph-feature-npy-byte-preparation02-2026-10-04';sys.path.insert(0,str(H/'replay'));import npy_bytes03 as N
sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
for name,pin in [('financial-graph-feature-npy-byte-preparation01-2026-10-04','c8b40a1d731d8fbef5e7e55712bd87b92454eeda3e4893df03a6764be22987c9'),('financial-graph-feature-npy-byte-source-review01-2026-10-04','10c52643f4431a3ecc791ade86773b2fee18128b9982682110dff8b205ef6cd7')]:
 root=B/name;m=root/'MANIFEST01.json';ok(sha(m.read_bytes())==pin,'original seal '+name);rows=json.loads(m.read_bytes())['members'];ok({p.relative_to(root).as_posix() for p in root.rglob('*') if p!=m}=={x['path'] for x in rows}-{'.'},'complete original membership')
 for x in rows:
  p=root/x['path'];s=p.lstat();mode=int(x['mode'],8) if isinstance(x['mode'],str) else x['mode'];ok(stat.S_IMODE(s.st_mode)==mode,'mode '+x['path'])
  if x['kind']=='file':ok(stat.S_ISREG(s.st_mode) and s.st_size==x['bytes'] and sha(p.read_bytes())==x['sha256'],'body '+x['path'])
  elif x['kind']=='symlink':ok(stat.S_ISLNK(s.st_mode) and os.readlink(p)==x['target'],'literal link')
  else:ok(stat.S_ISDIR(s.st_mode),'directory')
old=B/'financial-graph-feature-npy-byte-preparation01-2026-10-04';records=json.loads((old/'SAMPLED_BOUNDARY01.json').read_bytes())['records'];accepted=[]
for row in records:
 p=old/'boundary01'/str(row['case'])/'array-000000.npy';ok(sha(p.read_bytes())==row['current_sha256']!=row['expected_sha256'],'retained changed bytes');ok(list(N.fingerprint(p.stat()))==row['after'],'retained original stat')
 if row['accepted']:
  ok(row['before']==row['after'],'original equal fingerprints');accepted.append(row['case'])
  try:N.Cursor(p,b'not-authority')
  except PermissionError:checks.append('current ordinary route refuses actual old path before metadata')
  else:raise AssertionError('accepted old path')
ok(accepted==[2,4,5,7,10],'exact five original accepted cases; no rerun')
pins=json.loads((A/'SOURCE_PINS03.json').read_bytes())
for x in pins['sources']:
 p=Path(x['path']);ok(p.stat().st_size==x['bytes'] and sha(p.read_bytes())==x['sha256'],'actual pinned source '+str(p))
for source,copy in [('/usr/include/linux/fcntl.h','UAPI_linux_fcntl.h'),('/usr/include/asm-generic/fcntl.h','UAPI_asm_generic_fcntl.h'),('/usr/include/linux/memfd.h','UAPI_memfd.h')]:ok(Path(source).read_bytes()==(A/copy).read_bytes(),'actual UAPI '+source)
s=(A/'UAPI_linux_fcntl.h').read_text();ok(all(t in s for t in ['F_LINUX_SPECIFIC_BASE + 9','F_LINUX_SPECIFIC_BASE + 10','F_SEAL_SEAL\t0x0001','F_SEAL_SHRINK\t0x0002','F_SEAL_GROW\t0x0004','F_SEAL_WRITE\t0x0008']),'exact seal constants')
ok('#define F_LINUX_SPECIFIC_BASE\t1024' in (A/'UAPI_asm_generic_fcntl.h').read_text(),'exact base')
completion=json.loads((A/'COMPLETION02.json').read_bytes());ok(sha((A/'MANIFEST01.json').read_bytes())==completion['first_manifest_sha256'],'first seal remains');failure=json.loads((A/'FREEZE01_FAILURE.json').read_bytes());ok(failure['source_or_control_execution_repeated'] is False and failure['first_manifest_preserved'] is True,'late summary error additive history')
(H/'PROVENANCE01.json').write_text(json.dumps({'checks':len(checks),'names':checks,'old_currentness_cases_not_rerun':True,'ordinary_path_refusals':accepted,'scientific_imports':False},indent=2)+'\n');print(json.dumps({'checks':len(checks),'passed':True}))
