from pathlib import Path
import importlib.util,hashlib,json,os
H=Path(__file__).resolve().parent;P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01/preclaim01.py');assert hashlib.sha256(P.read_bytes()).hexdigest()=='557b7bcb38b48e3bf1e9e5b5b1eae25ab4908b8567820e17700dc08774b48d16'
s=importlib.util.spec_from_file_location('_controls_actual_reader',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);d=H/'tiny';d.mkdir(mode=0o700);a=d/'a';b=d/'b';a.write_bytes(b'opaque0123456789');b.write_bytes(a.read_bytes());checks=[]
r=m.Reader();assert r.read(a)==a.read_bytes();n=r.total;r.read(a);assert r.total==n;checks.append('same canonical path cache is reused');r.read(b);assert r.total==2*n;checks.append('same bytes at distinct actual paths still charged');r.finish();assert r.total==4*n;checks.append('complete finish rereads every actual path')
r=m.Reader();raw=r.read(a);a.write_bytes(b'opaque9876543210')
try:r.finish()
except m.Unavailable:checks.append('actual changed bytes/currentness refuse')
else:raise AssertionError('changed bytes accepted')
r=m.Reader()
try:r.reference({'path':str(b),'sha256':'0'*64})
except m.Unavailable:checks.append('wrong literal hash refuses')
else:raise AssertionError('wrong hash accepted')
(d/'link').symlink_to(b)
r=m.Reader()
try:r.read(d/'link')
except m.Unavailable:checks.append('redirect canonical path refuses')
else:raise AssertionError('redirect accepted')
assert m.TOTAL==8388608 and m.FILE==4194304;checks.append('original8MiB4MiB constants unchanged')
(H/'CONTROLS01.json').write_text(json.dumps({'checks':checks,'count':len(checks),'genuine_reader':True,'public_validator':False,'authority':False},sort_keys=True)+'\n');print(json.dumps(checks))
