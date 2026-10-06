from pathlib import Path
import hashlib,json,stat
R=Path.cwd();N='eth-paper-real-pilot-graph-20220523-20261005-01';S='50df679a64cfee1b28b35554acab70d5ff4fa9c7';O=Path(__file__).parent;P=R/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-fourth-graph01-2026-10-06';run=R/'research_runs'/N;art=R/'research_artifacts/onchain-paper-replication-2026-09-24';ev={}
def read(p):
 assert p.stat().st_size<4*1024**2;raw=p.read_bytes();ev[str(p.relative_to(R))]=hashlib.sha256(raw).hexdigest();return json.loads(raw)
def digest(p):
 assert p.stat().st_size<4*1024**2,'no payload re-read';return hashlib.sha256(p.read_bytes()).hexdigest()
c=read(run/'claim.json');t=read(run/'complete.json');g=read(P/'gate01.json');e=g['experiments'][N];root=read(P/'ROOT_TERMINAL01.json');guard=read(art/'runs'/N/'guard/final.json');outer=read(P/'outer-exit01.json');idx=read(run/'outputs/artifact-index.json');body=read(O/'BODY_HASH01.json')
assert c['source']==t['source']==S and c['experiment']==e and t['claim_sha256']==digest(run/'claim.json') and c['registration_sha256']==t['registration_sha256']==digest(P/'gate01.json')
assert c['effective_attempt_budget']==71 and e['parent'] is None and len(e['source_files'])==178 and len(e['inputs'])==32 and len(e['runtime_hashes'])==7
for n,h in e['source_files'].items():assert digest(R/n)==h,n;ev[n]=h
for n,h in e['runtime_hashes'].items():assert digest(R/'tradingagents/research'/n)==h,n
for info in e['inputs'].values():p=R/info['path'];assert p.stat().st_size<4*1024**2 and digest(p)==info['sha256'];ev[info['path']]=info['sha256']
assert t['status']=='complete' and t['cell_count']==2 and all(x['status']=='complete' for x in t['cells']) and t['unavailable_count']==0
assert [x['id'] for x in t['cells']]==e['cells'] and t['cells'][0]['rows']==t['cells'][1]['raw_count']==7581075 and t['cells'][1]['admitted_count']==3762748
for n,h in t['output_sha256'].items():assert digest(run/'outputs'/n)==h;ev[str((run/'outputs'/n).relative_to(R))]=h
assert root['actual_root_tool_exit_code']==0 and root['original_outer_exit_code']==0 and root['source_commit']==S
assert guard['phase']=='complete' and guard['child_exit_code']==0 and guard['cleanup_verified'] is True and guard['cleanup_stop_returncode']==5
assert not Path(guard['cgroup']).exists() and all(not Path('/proc',str(pid)).exists() for pid in root['selected_recorded_pids'])
assert root['current_unit_readback_exit_code']==0 and 'ActiveState=inactive' in root['current_unit_properties_raw'] and 'MainPID=0' in root['current_unit_properties_raw']
bodies={v['path']:v for v in body['files']};assert len(bodies)==6 and body['total_bytes']==3720674424
for n,v in idx.items():
 if n in bodies:assert bodies[n]['sha256']==v['sha256'] and bodies[n]['bytes']==v['bytes'];continue
 p=R/n;assert p.stat().st_size==v['bytes'] and digest(p)==v['sha256'];ev[n]=v['sha256']
for base in (run,art/'runs'/N,art/'sources'/N):
 for p in base.rglob('*'):
  if p.is_file() and str(p.relative_to(R)) not in bodies:
   assert p.stat().st_size<4*1024**2 and not p.is_symlink();ev[str(p.relative_to(R))]=digest(p)
ext=read(P/'RAW_EXTENT01.json');count=0
for d in ext['daily_members']:
 assert digest(R/d['mapping_path'])==d['mapping_sha256']
 for s in d['segments']:
  p=Path(s['path']);a=p.lstat();assert not p.is_symlink() and stat.S_ISREG(a.st_mode);assert (a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==tuple(s[k] for k in ('device','inode','bytes','mtime_ns','ctime_ns'));count+=1
assert count==241
manifest=read(art/'sources'/N/'graph-2022-05-23/manifest.json');assert digest(art/'sources'/N/'graph-2022-05-23/manifest.json')==t['cells'][1]['manifest_sha256']
for v in manifest['arrays'].values():row=bodies[str((art/'sources'/N/'graph-2022-05-23'/v['path']).relative_to(R))];assert v['sha256']==row['sha256'] and v['bytes']==row['bytes']
assert root['actual_root_tool_session']==17660 and root['actual_root_tool_completion_chunk']=='1aa097' and len(root['selected_recorded_pids'])==3
assert root['selected_recorded_pids_present']==[] and root['cgroup_present'] is False
assert outer['exit_code']==0 and outer['source']==S and outer['experiment']==N
assert not (run/'failed.json').exists() and not (run/'failed.json').is_symlink()
assert all(guard['memory_events'][k]==0 for k in ('max','oom','oom_kill'))
assert guard['memory_max_bytes']==5905580032 and guard['memory_high_bytes']==5368709120 and guard['memory_swap_max_bytes']==0 and guard['wall_seconds']==28800
assert body['index_sha256']==digest(run/'outputs/artifact-index.json') and body['decision']=='pass' and body['headers_captured_same_pass']==5
for row in body['files']:
 info=(R/row['path']).lstat();assert row['stat_identity']==[info.st_dev,info.st_ino,info.st_nlink,info.st_size,info.st_mtime_ns,info.st_ctime_ns]
headers={Path(row['path']).stem:row['npy_header'] for row in body['files'] if 'npy_header' in row}
Nnodes=headers['node_ids']['shape'][0];Nedges=headers['edge_index']['shape'][1]
assert headers['node_features']['shape']==[Nnodes,4] and headers['edge_index']['shape']==[2,Nedges]
assert headers['edge_features']['shape']==[Nedges,2] and headers['edge_aggregates']['shape']==[Nedges,2]
assert headers['node_features']['descr']=='<f8' and headers['edge_features']['descr']=='<f8' and headers['edge_aggregates']['descr']=='<f8' and headers['edge_index']['descr']=='<i8'
coverage=read(R/t['cells'][1]['coverage_path']);assert digest(R/t['cells'][1]['coverage_path'])==t['cells'][1]['coverage_sha256']
assert coverage['claim_sha256']==t['claim_sha256'] and coverage['graph_manifest_sha256']==t['cells'][1]['manifest_sha256'] and coverage['plan_sha256']==e['inputs']['graph_plan']['sha256']
weekly=read(R/e['inputs']['weekly_source']['path']);assert weekly['expected_rows']==t['cells'][0]['rows']==sum(x['expected_rows'] for x in coverage['members']) and len(coverage['members'])==7
for i,(m,w) in enumerate(zip(coverage['members'],weekly['members'])):
 assert m['sha256']==w['sha256']==e['inputs'][f'daily_map_{i:02d}']['sha256'] and m['expected_rows']==w['expected_rows'] and m['start_utc']==w['start_utc'] and m['end_utc']==w['end_utc'] and m['source_manifest_sha256']==e['inputs']['weekly_source']['sha256']
meta=manifest['metadata'];assert meta['raw_count']==t['cells'][1]['raw_count']==meta['admitted_count']+sum(meta['exclusion_counts'].values())
assert meta['admitted_count']==t['cells'][1]['admitted_count'] and meta['exclusion_counts']==t['cells'][1]['exclusion_counts'] and meta['source_hashes']==t['cells'][1]['source_hashes']==sorted(m['sha256'] for m in coverage['members'])
assert meta['graph_config_hash']==coverage['graph_config_hash'] and coverage['week']==meta['start_utc']=='2022-05-23T00:00:00Z' and coverage['end_utc']==meta['end_utc']=='2022-05-30T00:00:00Z'
measure=read(P/'GRAPH_MEASUREMENTS01.json');assert measure['native_seconds']==guard['elapsed_seconds'] and measure['raw_rows']==meta['raw_count'] and measure['admitted_rows']==meta['admitted_count'] and measure['six_payload_bytes']==body['total_bytes']
assert measure['last_unit_kernel_peak_bytes']==guard['optional_memory_telemetry']['unit']['kernel_peak_bytes'] and measure['peak_sampled_memory_current_bytes']==guard['peak_sampled_memory_current_bytes']
review={'schema_version':1,'decision':'accepted','experiment':N,'source':S,'claim_sha256':digest(run/'claim.json'),'root_actual_exit':{'exit_code':0,'receipt':str((P/'ROOT_TERMINAL01.json').relative_to(R)),'actual_tool_chunk':root['actual_root_tool_completion_chunk']},'cleanup':{'original_guard_cleanup_verified':True,'recorded_cgroup_absent':True,'selected_recorded_pids_absent':True,'original_cleanup_stop_returncode':5,'lifetime_pid_history_complete':False},'evidence':dict(sorted(ev.items())),'checks':{'source':178,'inputs':32,'runtime':7,'raw_stats':241,'complete_cells':2,'payloads':6,'same_pass_headers':5,'raw_daily_body_reads':0},'qualification':'Actual graph/source completion only. One six-body streaming hash pass; five headers captured in same pass. No numerical value decode, feature/MCM/training/financial completion, remote preservation or future storage release inferred.'}
review['derived_header_counts']={'nodes':Nnodes,'edges':Nedges}
review['original_selected_pid_count']=3
review['native_telemetry']={'seconds':guard['elapsed_seconds'],'last_unit_kernel_peak_bytes':measure['last_unit_kernel_peak_bytes'],'sampled_memory_current_peak_bytes':measure['peak_sampled_memory_current_bytes'],'events':guard['memory_events'],'qualification':'Kernel peak includes charged cache, not RSS. Ancestor is not job-only. Named tree excludes unnamed files; sampled whole-volume floor includes them and unrelated activity. Complete lifetime PID history remains unknown.'}
(O/'OUTCOME_REVIEW01.json').write_text(json.dumps(review,sort_keys=True,indent=2)+'\n');print(json.dumps({'review_sha256':digest(O/'OUTCOME_REVIEW01.json'),'body_sha256':digest(O/'BODY_HASH01.json'),'evidence_count':len(ev)}))
