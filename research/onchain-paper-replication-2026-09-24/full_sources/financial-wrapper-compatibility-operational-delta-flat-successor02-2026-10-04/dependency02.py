from pathlib import Path
import json,hashlib,stat,os
O=Path(__file__).resolve().parent;F=O.parent;W=F/'financial-wrapper-operational-forensic-watch-correction04-2026-10-04';h=lambda b:hashlib.sha256(b).hexdigest();m=json.loads((W/'MANIFEST01.json').read_bytes())
for x in m['members']:
 p=W/x['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==x['mode']
 if x['kind']=='file':assert stat.S_ISREG(s.st_mode) and s.st_nlink==x['nlink'] and h(p.read_bytes())==x['sha256'] and s.st_size==x['bytes']
 elif x['kind']=='directory':assert stat.S_ISDIR(s.st_mode)
 elif x['kind']=='symlink':assert stat.S_ISLNK(s.st_mode) and os.readlink(p)==x['target']
 elif x['kind']=='fifo':assert stat.S_ISFIFO(s.st_mode)
 else:raise AssertionError('unknown type')
assert {p.relative_to(W).as_posix() for p in W.rglob('*')}=={x['path'] for x in m['members']}|{'MANIFEST01.json'}
b=(W/'watch01.py').read_bytes();assert h(b)=='bdeacaadc053e615245b3e2175089842708719448ec7da970d981e5dc077ca18';assert not (O/'watch01.py').exists();(O/'watch01.py').write_bytes(b)
for n in ['MANIFEST01.json','MACHINE01.json','REPORT01.md']:(O/('WATCH_'+n)).write_bytes((W/n).read_bytes())
(O/'DEPENDENCY_AUTHENTICATION02.json').write_text(json.dumps({'watch_preparation_root':str(W),'watch_manifest_sha256':h((W/'MANIFEST01.json').read_bytes()),'watch_source_sha256':h(b),'members_verified':len(m['members']),'fifo_not_read':True,'links_not_followed':True,'independent_watch_review':None,'actual_entry_release':None},indent=2)+'\n');print('pinned',h((W/'MANIFEST01.json').read_bytes()))
