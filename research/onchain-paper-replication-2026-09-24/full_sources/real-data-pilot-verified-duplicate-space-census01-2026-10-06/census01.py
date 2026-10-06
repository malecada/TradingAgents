from pathlib import Path
import hashlib,json,os,stat,datetime
R=Path(__file__).resolve().parents[4]
B=R/'research/onchain-paper-replication-2026-09-24'; F=B/'full_sources'; OUT=Path(__file__).resolve().parent
names=['closed-ledger-pilot-offload-2026-10-05-01','real-pilot-first-graph-preservation-20261006-01','real-pilot-second-graph-preservation-metadata-20261006-01','real-pilot-third-graph-preservation-20261006-01','real-pilot-fourth-graph-preservation-20261006-01']
reviews=[B/'storage'/names[0]/'closure-review.json',F/'real-data-pilot-first-graph-preservation-outcome-review01-2026-10-06/REVIEW01.json',F/'real-data-pilot-second-graph-union-retirement-review01-2026-10-06/UNION_OUTCOME_REVIEW01.json',F/'third-graph-preservation-outcome-review01-2026-10-06/REVIEW01.json',F/'real-data-pilot-fourth-graph-preservation-outcome-review01-2026-10-06/REVIEW01.json']
reads=[]; total_read=0
def meta(p):
 global total_read
 st=p.lstat(); assert stat.S_ISREG(st.st_mode) and not p.is_symlink()
 assert len(reads)<150 and st.st_size<=1048576 and total_read+st.st_size<=16*1048576
 raw=p.read_bytes(); total_read+=len(raw); assert p.stat()==st
 reads.append({'path':str(p.relative_to(R)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
 return json.loads(raw)
rows=[]
for name,rp in zip(names,reviews):
 p=B/'storage'/name; complete=meta(p/'complete.json'); review=meta(rp)
 assert review['decision']=='accepted'
 regular=[]; dirs=[]; other=[]
 for root,ds,fs in os.walk(p,followlinks=False):
  for n in ds+fs:
   x=Path(root)/n; st=x.lstat()
   rec={'path':str(x.relative_to(R)),'bytes':st.st_size,'allocated_bytes':st.st_blocks*512,'device':st.st_dev,'inode':st.st_ino,'nlink':st.st_nlink,'mtime_ns':st.st_mtime_ns,'ctime_ns':st.st_ctime_ns}
   if stat.S_ISREG(st.st_mode):regular.append(rec)
   elif stat.S_ISDIR(st.st_mode):dirs.append(rec)
   else:other.append(rec)
 assert not other
 gets=[x for x in regular if Path(x['path']).name.endswith('-recovered.bin')]
 rows.append({'directory':str(p.relative_to(R)),'completion':reads[-2],'independent_review':reads[-1],'regular_files':len(regular),'all_regular_logical_bytes':sum(x['bytes'] for x in regular),'all_regular_allocated_bytes':sum(x['allocated_bytes'] for x in regular),'directory_allocated_bytes':sum(x['allocated_bytes'] for x in dirs)+p.stat().st_blocks*512,'largest_regular_file':max(regular,key=lambda x:x['bytes']),'retained_recovered_bin_files':len(gets),'retained_recovered_bin_bytes':sum(x['bytes'] for x in gets),'regular_payload_candidates_at_least_600MB':[x for x in regular if x['bytes']>=600000000]})
logical=sum(x['all_regular_logical_bytes'] for x in rows)
allocated=sum(x['all_regular_allocated_bytes']+x['directory_allocated_bytes'] for x in rows)
assert logical<600000000 and allocated<600000000
result={'schema_version':1,'decision':'no_candidate_within_scope','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'required_startup_bytes':16141242368,'prior_observed_free_bytes':15605964800,'prior_shortfall_bytes':535277568,'target_duplicate_bytes':600000000,'scope':rows,'all_scoped_regular_logical_bytes':logical,'all_scoped_allocated_bytes_including_directories':allocated,'metadata_bodies_read':len(reads),'metadata_bytes_read':total_read,'retirement_release':False,'payload_bytes_read_or_hashed':0,'excluded':['active real-pilot-fifth-graph-failed-preservation-20261006-01','failed real-pilot-second-graph-preservation-20261006-01 (only completed metadata successor included)','original raw/graphs/failed May30 ledger and arrays/model inputs','all other storage directories'],'qualification':'Current stat census only. Completion receipts describe historical recovery, not continued local retention or current remote availability. No nontrivial candidate remains in this completed-directory scope; all files including mandatory controls sum below the shortfall. Allocation totals are conservative stat sums, not promised reclaimable bytes. No current free-space or capacity assertion.'}
(OUT/'CENSUS01.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'decision':result['decision'],'metadata_bodies':len(reads),'metadata_bytes':total_read,'logical_bytes':logical,'allocated_bytes':allocated,'retained_recovered_bin_bytes':sum(x['retained_recovered_bin_bytes'] for x in rows)}))
