from pathlib import Path
import os,resource
os.sched_setaffinity(0,{2,3});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
import hashlib,json,tarfile
F=Path('research/onchain-paper-replication-2026-09-24/full_sources');D=F/'pilot40-prefix-inputs-2026-10-12';C=F/'pilot40-parent-accounting-continuation-candidate-2026-10-12';h=lambda b:hashlib.sha256(b).hexdigest()
roles=json.loads((D/'REGISTERED_ROLE_MAP.json').read_text());contract=json.loads((C/'EXACT_CONTRACT03.json').read_text());out=[]
score=json.loads((D/'RECOVERED_SCORE_SCOPE01.json').read_text());numeric=json.loads((D/'RECOVERED_NUMERIC_SCOPE01.json').read_text());archive=Path(score['actual_archive_source']['path']);assert h(archive.read_bytes())=='9356d093879b3c2dc2565ec11994e92adb29b793f1d574d37ec080a1528a770e'
with tarfile.open(archive,'r:') as t:
 for v,scope,indices in [(score,'score_offload',(0,1,2)),(numeric,'numeric_origin',(3,4,5))]:
  assert v['status']=='recovered' and v['scope']==scope and v['parent_experiment']==contract['parent'] and v['actual_archive_source']==score['actual_archive_source']
  assert set(v['body_sha256'])=={row[j] for row in contract['batches'] for j in indices}
  assert len(v['body_sha256'])==48
  for ref in v['original_evidence']:
   p=Path(roles[ref['role']]['path']);assert h(p.read_bytes())==ref['sha256']==roles[ref['role']]['sha256']
  assert len(v['original_evidence'])==4
  for row in v['actual_returned_member_joins']:
   m=t.getmember(row['name']);assert m.isfile() and m.size==row['bytes'];raw=t.extractfile(m).read();assert h(raw)==row['sha256']
  for i,row in enumerate(v['origin_derivations']):
   m=t.getmember(row['source']);assert m.isfile() and m.size==65536*9
   raw=t.extractfile(m).read();assert h(raw)==row['source_sha256'];assert row['offset']==i*4096*9 and row['bytes']==4096*9
   part=raw[row['offset']:row['offset']+row['bytes']];assert h(part)==row['sha256']==contract['batches'][i][3];assert part==Path(roles[row['role']]['path']).read_bytes()
  assert len(v['actual_returned_member_joins'])==(48 if scope=='score_offload' else 32)
  assert len(v['origin_derivations'])==(0 if scope=='score_offload' else 16)
  out.append({'scope':scope,'returned_members':len(v['actual_returned_member_joins']),'derived_ranges':len(v['origin_derivations']),'body_digests':48})
print(json.dumps({'status':'PASS_actual_normalization_only','checks':out,'archive_sha256':h(archive.read_bytes()),'evidence':{str(D/n):h((D/n).read_bytes()) for n in ['RECOVERED_SCORE_SCOPE01.json','RECOVERED_NUMERIC_SCOPE01.json']},'origin_slices_separate_original_remote_members':False,'new_network_or_numerical_execution':False},indent=2))
