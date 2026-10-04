from pathlib import Path
import json
import restore_sharded01 as M
R=M.R;H=Path(__file__).resolve().parent;C=H.parent/'financial-genuine-wrapper-claimedrun-final-capture-preparation02-2026-10-04';checks=[]
def ck(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
ck('frozen capture source',R.digest(R.read(C,'capture02.py'))=='31f8c7dfdc39fdbadd2149cd0c7d9d18e9d6b766841a7171629d6b5b01e47ab0');ck('frozen capturemanifest',R.digest(R.read(C,'MANIFEST01.json'))=='a2b07ace33f3f6a1394e04949c5089a3552567573d858f76f5a5f1462bcb6ea3');ck('shared pure planner exact',R.read(C,'shards01.py')==R.read(H,'shards01.py'))
root=C/'multiple02';index_raw=R.read(root,'SHARD_INDEX01.json');index=json.loads(index_raw);m=R.scan(root/'ordinary');mb=R.encode(m);q={'manifest':dict(index['virtual_manifest'],path='research/opaque/union-manifest.json'),'shard_index':{'path':'research/opaque/SHARD_INDEX01.json','bytes':len(index_raw),'sha256':R.digest(index_raw)},'expected_members':len(m['members']),'expected_files':sum(r['kind']=='file' for r in m['members']),'expected_logical_bytes':sum(r.get('bytes',0) for r in m['members']),'expected_shards':len(index['shards'])};ck('actual opaque author virtual manifest',M.manifest_join(q,mb)==m);got,plans,refs=M.validate_index(q,m,index_raw);ck('actual author capture index accepted without fabricated authority',got==index and len(plans)==3 and len(refs)==6)
for row in index['shards']:
 raw=R.read(root,row['archive']['path']);ck('real author tiny archive '+row['id'],len(raw)==row['archive']['bytes'] and R.digest(raw)==row['archive']['sha256'])
ck('frozen authorindex unchanged',R.read(root,'SHARD_INDEX01.json')==index_raw)
R.put(H/'INTEROPERABILITY03.json',{'checks':len(checks),'check_names':checks,'capture_source_sha256':'31f8c7dfdc39fdbadd2149cd0c7d9d18e9d6b766841a7171629d6b5b01e47ab0','capture_manifest_sha256':'a2b07ace33f3f6a1394e04949c5089a3552567573d858f76f5a5f1462bcb6ea3','opaque_fixture_index_sha256':R.digest(index_raw),'only_existing_tiny_utility_metadata':True,'capture_rerun':False,'restore_rerun':False,'actual_Root_capture':None});print('PASS',len(checks))
