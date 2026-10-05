from pathlib import Path
import json,hashlib,tarfile,stat,os,collections,subprocess
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'held-consumer-canonical-increment-preservation-review01-2026-10-05';Q=F/'held-consumer-canonical-current-capture01-2026-10-05';C=F/'heartbeat-root-checkpoint10-2026-10-04';S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-native-20261005-01/source');P=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-root-launch-20261005-01');A=F/'held-consumer-canonical-root-binding01-2026-10-05'
def h(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())
def ref(p):return {'path':str(p),'sha256':h(p.read_bytes())}
cap=load(Q/'CAPTURE01.json');c=load(Q/'snapshot/COMPOSITION01.json');manifest=load(Q/'snapshot-manifest.json');root=load(C/'CANONICAL_CURRENT_CAPTURE_ROOT_EXIT01.json')
assert ref(Q/'CAPTURE01.json')['sha256']==root['capture_sha256']=='f29c52858dd466d398209b61b21130e39865ac4a6d272cacb9181cb908effde4' and root['actual_root_exit']==0
for k in ('stdout','stderr'):assert h((C/('CANONICAL_CURRENT_CAPTURE01.'+k)).read_bytes())==root[k+'_sha256']
assert ref(Q/'increment.tar.gz')['sha256']==cap['archive']['sha256']=='5655787612895dd1fbdf6fec7f52eca2df88adb5da6ab8af1123e36b2dfcaf71'
assert ref(Q/'snapshot-manifest.json')['sha256']==cap['archive']['manifest_sha256']=='1bf39e5fa3b15a3b77017023b0ccbd21d89d5610f10e9b9a6aa9f4b5c7da620a'
basepath=Path(c['original_capsule_metadata']['path']);assert ref(basepath)==c['original_capsule_metadata'];base=load(basepath);old={r['path']:r for r in base['manifest']['members'] if r['kind']=='file'};assert len(old)==716
for row in c['inherited_recovery'].values():assert ref(Path(row['path']))==row
roots={'Capsule':S,'Parent':P,'Root':A,'gate-review':F/'held-consumer-canonical-gate-draft-review01-2026-10-05','parent-review':F/'held-consumer-canonical-parent-review01-2026-10-05'}
expectedjoins={};counts={}
for label,m in c['manifests'].items():
 assert len({r['path'] for r in m['members']})==len(m['members']);assert stat.S_IMODE(roots[label].stat().st_mode)==m['root_mode']
 actual=set()
 for b,dirs,files in os.walk(roots[label],followlinks=False):
  for n in dirs+files:actual.add(str((Path(b)/n).relative_to(roots[label])))
 assert actual=={r['path'] for r in m['members']}
 for r in m['members']:
  p=roots[label]/r['path'];st=p.lstat();assert stat.S_IMODE(st.st_mode)==r['mode']
  if r['kind']=='file':
   assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_size==r['bytes'];expectedjoins[label+'/'+r['path']]=r
  else:assert stat.S_ISDIR(st.st_mode)
 counts[label]={'regular':sum(r['kind']=='file' for r in m['members']),'typed':len(m['members'])}
assert counts==root['current_manifests'] and set(c['body_joins'])==set(expectedjoins)
newrows={r['snapshot_name']:r for r in c['body_joins'].values() if r['kind']=='new-body'};assert len(newrows)==134 and sum(r['bytes'] for r in newrows.values())==1432931
cache={}
for name,row in newrows.items():
 b=(Q/'snapshot'/name).read_bytes();assert len(b)==row['bytes'] and h(b)==row['sha256'];cache[name]=b
kinds=collections.Counter()
for name,join in c['body_joins'].items():
 row=expectedjoins[name];assert join['bytes']==row['bytes'] and join['sha256']==row['sha256'];kinds[join['kind']]+=1
 if join['kind']=='inherited-original-body':
  prior=old[join['original_path']];assert prior['sha256']==join['sha256'] and prior['bytes']==join['bytes']
 else:
  label,n=name.split('/',1);assert (roots[label]/n).read_bytes()==cache[join['snapshot_name']]
assert kinds=={'inherited-original-body':658,'new-body':166}
cache['COMPOSITION01.json']=(Q/'snapshot/COMPOSITION01.json').read_bytes();expected={r['path']:r for r in manifest['members']};assert len(expected)==135 and set(expected)==set(cache)
with tarfile.open(Q/'increment.tar.gz','r:gz') as tf:
 members=tf.getmembers();assert len(members)==135 and {x.name for x in members}==set(expected)
 for t in members:
  r=expected[t.name];b=tf.extractfile(t).read();assert t.isfile() and t.mode==r['mode'] and len(b)==r['bytes'] and h(b)==r['sha256'] and b==cache[t.name]
assert c['source']==subprocess.check_output(['git','rev-parse','HEAD'],cwd=S).decode().strip()=='468d756c16b3825e83a931c082ab4072764a873d'
assert cap['external_recovery'] is False and cap['execution_admitted'] is False
assert ref(A/'capture_increment01.py')==load(D/'SOURCE_CHECK01.json')['source']
result={'schema_version':1,'decision':'accepted-actual-canonical-local-increment-capture','capture':ref(Q/'CAPTURE01.json'),'composition':ref(Q/'snapshot/COMPOSITION01.json'),'archive':ref(Q/'increment.tar.gz'),'snapshot_manifest':ref(Q/'snapshot-manifest.json'),'actual_root_exit':ref(C/'CANONICAL_CURRENT_CAPTURE_ROOT_EXIT01.json'),'source':ref(A/'capture_increment01.py'),'scope_counts':counts,'new_unique_bodies':134,'new_unique_bytes':1432931,'new_logical_body_joins':166,'accepted_old_inherited_logical_joins':658,'accepted_old_regular_basis':716,'snapshot_archive_regular_bodies':135,'historical_raw_bodies_reread':False,'current_typed_names_modes_extents_checked':True,'current_source':'468d756c16b3825e83a931c082ab4072764a873d','external_recovery':False,'execution_release':False,'qualification':'All new snapshot/origin/archive bytes joined; each inherited hash/extent joined to exact old accepted metadata without old body reread. Complete current typed membership checked, physical Git included. Hash inheritance authenticates bytes, not old POSIX topology or restored runtime. Old fiveFAILED and original guard null/cleanup unknown unchanged. Actual remote-selected/fresh flat recovery remains pending.'}
p=D/'CAPTURE_CHECK01.json'
with p.open('x') as f:json.dump(result,f,sort_keys=True,separators=(',',':'));f.write('\n')
p.chmod(0o444);print(h(p.read_bytes()))
