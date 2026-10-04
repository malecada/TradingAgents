import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(n,v):
 with (H/n).open('xb') as f:f.write((json.dumps(v,sort_keys=True,indent=2)+'\n').encode())
a=json.loads((H/'CHECKS01.json').read_bytes());b=json.loads((H/'CHECKS02.json').read_bytes());p=json.loads((H/'PROJECTION01.json').read_bytes())
write('VERDICT01.json',{'schema_version':1,'reviewer':'combined_worker_review','status':'ACCEPTED_SOURCE_ONLY','candidate_sha256':'85368444d94a93df1aa4ba8b0f657d2725bc3d4717e9a07beecc3fa59033a167','author_manifest_sha256':'34f28fde09ebce6e586f40555dfbef918a408534ce393e165987c3547085cf7d','checks':a['count']+b['count'],'original_files':316,'original_bytes':41887064,'original_literal_links':50,'original_typed_including_roots':681,'projections':p,'fixed_projected_original_framer_compatible':True,'general_original_PAX_bug_resolved':False,'actual_Root_capture':None,'actual_external_recovery':None,'actual_Root_flat_recovery':None,'numerical_release':False,'runtime_package_verification':False,'scientific_claims_tested':False,'limits_unchanged':True,'report_sha256':sha((H/'REPORT01.md').read_bytes())})
rows=[]
def rec(p,rel):
 s=p.lstat();r={'path':rel,'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISLNK(s.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
 elif stat.S_ISDIR(s.st_mode):
  r['kind']='directory'
  for c in sorted(p.iterdir()):rec(c,rel+'/'+c.name)
 else:
  assert stat.S_ISREG(s.st_mode);body=p.read_bytes();r.update(kind='file',bytes=len(body),sha256=sha(body))
 rows.append(r)
for p in sorted(H.iterdir()):rec(p,p.name)
write('MANIFEST01.json',{'schema_version':1,'members':sorted(rows,key=lambda r:r['path'])})
print(json.dumps({'manifest':sha((H/'MANIFEST01.json').read_bytes()),'verdict':sha((H/'VERDICT01.json').read_bytes()),'projection':sha((H/'PROJECTION01.json').read_bytes()),'report':sha((H/'REPORT01.md').read_bytes()),'members':len(rows),'regular_files':sum(r['kind']=='file' for r in rows),'regular_bytes':sum(r.get('bytes',0) for r in rows),'checks':a['count']+b['count']}))
