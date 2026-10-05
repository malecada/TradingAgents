from pathlib import Path
import hashlib,json,stat
D=Path(__file__).resolve().parent;R=D.parents[3];S=R/'research/onchain-paper-replication-2026-09-24/storage/real-pilot-first-graph-preservation-20261006-01'
h=lambda raw:hashlib.sha256(raw).hexdigest()
raw=(S/'selection01.json').read_bytes();assert h(raw)=='2180e24442e631c4bb80e14841a10cf63fbcc99050c42f010566efce1de8d384';c=json.loads(raw)
r=c['graph_outcome_review'];rr=(R/r['path']).read_bytes();assert h(rr)==r['sha256'];assert json.loads(rr)['decision']=='accepted'
b=c['independent_body_hash'];br=(R/b['path']).read_bytes();assert h(br)==b['sha256'];basis=json.loads(br);large={x['path']:x for x in basis['files']}
assert len(c['files'])==c['count']==36 and sum(x['bytes'] for x in c['files'])==c['total_bytes']==3794768609
assert len({x['path'] for x in c['files']})==36 and len(c['directories'])==8
metadata=[];reused=[]
for row in c['files']:
 p=R/row['path'];s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==row['nlink']==1
 assert [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]==row['stat_identity']
 assert stat.S_IMODE(s.st_mode)==row['mode'] and s.st_size==row['bytes']
 if row['path'] in large:
  old=large[row['path']];assert old['sha256']==row['sha256'] and old['bytes']==row['bytes'];a=old['stat_identity'];assert [a[0],a[1],a[3],a[4],a[5]]==row['stat_identity'] and a[2]==1;reused.append(row['path'])
 else:
  assert s.st_size<4*1024**2;assert h(p.read_bytes())==row['sha256'];metadata.append(row['path'])
for row in c['directories']:
 p=R/row['path'];s=p.lstat();assert p.resolve()==p and stat.S_ISDIR(s.st_mode) and stat.S_IMODE(s.st_mode)==row['mode']
assert len(reused)==6 and len(metadata)==30
# Exact finite payload reserve includes dd round-up per get, per-file restore
# metadata, and finish's completion candidate; formatting follows cold03.publish.
encode=lambda x:(json.dumps(x,indent=2)+'\n').encode()
reserve=lambda n:n+(n//32768+1)*32768
records=[];budget=0
for i,row in enumerate(c['files']):
 rec={**row,'remote_object':c['remote']+f'/{i:02d}.bin','remote_restore':c['remote']+f'/{i:02d}-restore.json','body_roundtrip_verified':True,'restoration':'Download remote_object to a new temporary file; verify bytes and SHA-256; restore original path only when absent. Never launch the old job.'}
 budget+=reserve(row['bytes'])+reserve(len(encode(rec)));rec.update(original_retained=True,recovered_body_retained=True);records.append(rec)
result={'identity':c['identity'],'selection':c,'files':records,'count':len(records),'bytes_preserved':sum(x['bytes'] for x in records),'originals_retained':True,'recoveries_retained':True,'no_automatic_retry':True}
budget+=reserve(len(encode(result)));assert budget<8*1024**3
record={'selection_sha256':h(raw),'count':36,'selected_bytes':c['total_bytes'],'reused_independent_payload_hashes':reused,'metadata_bodies_authenticated':len(metadata),'directories_name_modes_checked':8,'exact_transport_reserved_payload_bytes':budget,'transport_budget_bytes':8*1024**3,'payload_hash_pass_repeated':False,'scope':'point-in-time source name/mode/stat and existing independent payload hash joins; no external recovery claim'}
(D/'SELECTION_CHECK01.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n');print(json.dumps(record))
