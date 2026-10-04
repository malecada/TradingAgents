import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;sha=lambda b:hashlib.sha256(b).hexdigest();r=json.loads((H/'READBACK01.json').read_bytes());c=json.loads((H/'CHECKS02.json').read_bytes())
v={'schema_version':1,'reviewer':'combined_worker_review','status':'ACCEPTED_SOURCE_ONLY','codec_sha256':'f10f6803a637735bc490de8846056a34e9090451d92773d075a7025b19bd3d55','sink_sha256':'ceec61446f678f8749fa1e24530b5b4e3e344a59cce75f7906e322f03dd8ad89','author_manifest_sha256':'a513146948a0c469120eaa26844e2298cc5350e0135742c5bbe7d411c9c4238e','checks':r['checks']+c['checks'],'readback_sha256':sha((H/'READBACK01.json').read_bytes()),'supplement_sha256':sha((H/'CHECKS02.json').read_bytes()),'report_sha256':sha((H/'REPORT01.md').read_bytes()),'prior_withheld_review_preserved':'21c95e8ca55a7c76f7eb6cdb4cd293e1efb7f77d0122587dd67a2cb92f22e1f0','actual64MiB_capacity_measured':False,'filesystem_universal_bound_or_kernel_quota':False,'production_storage_allocation_policy_admitted':False,'genuine_live_integration':None,'transport_recovery_or_numerical_release':None,'representation_complete':False,'new_harness_failures':[]}
with (H/'VERDICT01.json').open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
rows=[]
def rec(p,rel):
 st=p.lstat();r={'path':rel,'mode':stat.S_IMODE(st.st_mode)}
 if stat.S_ISLNK(st.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
 elif stat.S_ISDIR(st.st_mode):
  r['kind']='directory'
  for c in sorted(p.iterdir()):rec(c,rel+'/'+c.name)
 else:
  assert stat.S_ISREG(st.st_mode);b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b))
 rows.append(r)
for p in sorted(H.iterdir()):rec(p,p.name)
with (H/'MANIFEST01.json').open('x') as f:json.dump({'schema_version':1,'members':sorted(rows,key=lambda r:r['path'])},f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'manifest':sha((H/'MANIFEST01.json').read_bytes()),'verdict':sha((H/'VERDICT01.json').read_bytes()),'readback':sha((H/'READBACK01.json').read_bytes()),'members':len(rows),'files':sum(x['kind']=='file' for x in rows),'bytes':sum(x.get('bytes',0) for x in rows),'checks':v['checks']}))
