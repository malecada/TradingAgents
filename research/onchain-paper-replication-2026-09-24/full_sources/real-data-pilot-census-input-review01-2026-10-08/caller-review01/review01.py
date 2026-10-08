import ast,hashlib,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
BASE=HERE.parents[1]
launch=BASE/'real-data-pilot-seven-graph-census-launch01-2026-10-08'
sha=lambda b:hashlib.sha256(b).hexdigest()
raw=(launch/'REQUEST01.json').read_bytes()
assert sha(raw)=='7c80faed623a172fe48600d9647d5b5610e2202d0ef45ff49274d8b2e02d99a7'
r=json.loads(raw)
for role,ref in r['sources'].items():
 b=(ROOT/ref['path']).read_bytes();assert len(b)==ref['bytes'] and sha(b)==ref['sha256'],role
 ast.parse(b)
sref=r['settings'];b=(ROOT/sref['path']).read_bytes();assert sha(b)==sref['sha256'] and len(b)==sref['bytes'];s=json.loads(b)
i=s['inputs'];b=(ROOT/i['path']).read_bytes();assert sha(b)==i['sha256'] and len(b)==i['bytes'];rows=json.loads(b)
assert len(rows)==7 and s['caller_sha256']==r['sources']['caller']['sha256'] and s['helper_sha256']==r['sources']['helper']['sha256']
for row in rows:
 for k in ('manifest','node_count_reference'):
  ref=row[k];b=(ROOT/ref['path']).read_bytes();assert sha(b)==ref['sha256'] and len(b)==ref['bytes']
 m=json.loads((ROOT/row['manifest']['path']).read_bytes());c=json.loads((ROOT/row['node_count_reference']['path']).read_bytes())
 assert c['rows']==row['node_count'] and c['graph_manifest_sha256']==row['manifest']['sha256'] and c['node_features_sha256']==m['arrays']['node_features']['sha256']
 assert m['graph_hash']==row['graph_hash']
 for k in ('edge_index','node_ids'):
  assert m['arrays'][k]['sha256']==row[k]['sha256'] and m['arrays'][k]['bytes']==row[k]['bytes']
  assert Path(row[k]['path'])==Path(row['manifest']['path']).parent/m['arrays'][k]['path']
chunks=sum(math.ceil(x['node_count']/s['chunk_centers']) for x in rows)
payload=sum(x['node_count']*8 for x in rows)
assert chunks<100 and payload+chunks*128<r['limits']['storage']['max_logical_bytes']
assert 8*s['chunk_centers']+128<r['limits']['file_size_bytes']
result={'decision':'ACCEPT exact topology-only engineering entry, conditional on Root commit/remote confirmation/fresh resources/no active unit','request_sha256':sha(raw),'caller_sha256':s['caller_sha256'],'settings_sha256':sref['sha256'],'input_list_sha256':i['sha256'],'count_chunks':chunks,'count_payload_bytes':payload,'checks':['all10 source pins and syntax match','settings/helper/caller/input pins joined','seven graph manifests/count JSON hashes and companion declarations joined without payload reads','NPY chunk file envelope and total declared vector payload fit requested limits'],'test_evidence':'nine retained synthetic caller checks independently inspected and reused; no NumPy/native/graph execution in this review'}
(HERE/'CHECKS01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
