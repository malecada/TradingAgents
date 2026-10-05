from pathlib import Path
import sys,time,json,hashlib,os
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import capture01 as C
R=C.R
roots={}
for role in ('capsule','parent'):
 p=D/('opaque-'+role);p.mkdir(mode=0o700);roots[role]=p;(p/'empty').mkdir(mode=0o700)
 for i in range(2):
  (p/('body-%d'%i)).write_bytes(bytes([i+1])*900000);os.chmod(p/('body-%d'%i),0o640)
# A tiny original Git marker is excluded only from capsule; no Git command used.
(roots['capsule']/'.git').mkdir(mode=0o700);(roots['capsule']/'.git'/'HEAD').write_bytes(b'opaque\n')
r=C.capture(roots,D/'owned-capture',time.monotonic());assert len(r['pieces'])==2
seen=set()
for row in r['pieces']:
 base=D/'owned-capture';m=json.loads((base/row['manifest']).read_bytes());dest=D/('flat-%d'%row['id']);dest.mkdir(mode=0o700);out=R.restore(base/row['archive'],row['archive_pin'],m,dest);meta=json.loads((dest/out['metadata_file']).read_bytes())
 for body in row['bodies']:
  key=(body['role'],body['path']);assert key not in seen;seen.add(key);raw=(dest/meta['flat_members'][body['member']]).read_bytes();assert raw==(roots[key[0]]/key[1]).read_bytes()
assert len(seen)==4 and all(any(x['path']=='empty' and x['kind']=='directory' for x in v['manifest']['members']) for v in r['originals'].values())
assert not any(x['path'].startswith('.git') for x in r['originals']['capsule']['manifest']['members'])
try:C.capture(roots,D/'owned-capture',time.monotonic())
except ValueError:pass
else:raise AssertionError('reused output accepted')
m={'schema_version':1,'root_mode':448,'members':[{'path':'oversized','kind':'file','mode':384,'bytes':C.GROUP+1,'sha256':'0'*64}]}
try:C.plan({'capsule':m})
except ValueError as e:assert '3MiB' in str(e)
else:raise AssertionError('oversize silently split')
pins=C.signatures(roots['parent'],C.inventory(roots['parent']));(roots['parent']/'late').write_bytes(b'x')
try:C.unchanged(pins)
except ValueError:pass
else:raise AssertionError('late membership signature unnoticed')
assert not any(x in sys.modules for x in ('numpy','torch','pandas'))
(D/'CHECKS01.json').write_text(json.dumps({'real_shards':2,'real_whole_restored_bodies':4,'empty_directories_metadata':True,'capsule_Git_only_exclusion':True,'fresh_output_refusal':True,'oversized_body_refusal':True,'late_membership_refusal':True,'actual_Root_capture':False,'numerical_imports':False},indent=2)+'\n');print('two actual opaque PAX shards/four bodies passed')
