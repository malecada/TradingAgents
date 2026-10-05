"""Actual compact outcome and raw extent stat joins; no payload decode/replay."""
from pathlib import Path
import datetime,hashlib,json,os,stat
M=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent
ID='eth-paper-real-pilot-graph-20220502-20261005-01';SOURCE='fc1e8f1e0e45ad122660a1d62a8c7e95c9d4519e';BASE='research/onchain-paper-replication-2026-09-24'
E=M/BASE/'full_sources/real-data-pilot-first-graph01-2026-10-05';R=M/'research_runs'/ID;S=M/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/ID;G=M/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/ID;evidence={}
def raw(p):
 p=Path(p);s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<=4*1024**2 and p.suffix not in ('.npy','.sqlite','.zst'),str(p)
 b=p.read_bytes();evidence[str(p.relative_to(M))]=hashlib.sha256(b).hexdigest();return b
def read(p):return json.loads(raw(p))
def hashed(p,expected):
 b=raw(p);assert hashlib.sha256(b).hexdigest()==expected,str(p);return json.loads(b)
claim=read(R/'claim.json');claimsha=evidence[str((R/'claim.json').relative_to(M))];assert claimsha=='38bc05d04362aea4364698d87b8d50d9f0c7240d4f33969948ba698c580b3806'
assert claim['source']==claim['design_source']==SOURCE and claim['experiment_id']==ID
gate=hashed(M/claim['registration'],claim['registration_sha256']);assert gate['experiments'][ID]==claim['experiment']
assert claim['effective_attempt_budget']==71 and claim['experiment']['cells']==['source-000000','graph-2022-05-02']
complete=read(R/'complete.json');assert complete['claim_sha256']==claimsha and complete['source']==SOURCE and complete['registration_sha256']==claim['registration_sha256'] and complete['status']=='complete' and complete['cell_count']==2 and complete['unavailable_count']==0
outputs={name:hashed(R/'outputs'/name,pin) for name,pin in complete['output_sha256'].items()};assert set(outputs)==set(claim['experiment']['outputs'])
assert outputs['cell-ledger.json']==complete['cells'] and all(c['status']=='complete' for c in complete['cells'])
inputs={role:hashed(M/v['path'],v['sha256']) for role,v in claim['inputs'].items()};assert len(inputs)==24
# Source body checks are bounded code/metadata only; no runtime/binary imports.
for rel,pin in claim['experiment']['source_files'].items():assert hashlib.sha256(raw(M/rel)).hexdigest()==pin,rel
index=outputs['artifact-index.json'];body=read(D/'BODY_HASH01.json');assert body['index_sha256']==complete['output_sha256']['artifact-index.json'] and body['decision']=='pass'
bodyrows={r['path']:r for r in body['files']};assert len(bodyrows)==6
for rel,v in index.items():
 if rel in bodyrows:assert bodyrows[rel]['sha256']==v['sha256'] and bodyrows[rel]['bytes']==v['bytes']
 else:assert len(raw(M/rel))==v['bytes'] and evidence[rel]==v['sha256']
assert {str(p.relative_to(M)) for p in S.rglob('*') if p.is_file()}==set(index)
manifest=read(S/'graph-2022-05-02/manifest.json');coverage=read(S/'graph-2022-05-02/coverage.json');summary=outputs['source-summary.json'];weekly=inputs['weekly_source'];plan=inputs['graph_plan'];extent=inputs['raw_extent'];sourcecov=read(S/'source-coverage.json')
assert summary==read(S/'result.json') and summary['financial_run_admitted'] is False
assert plan['expected_weeks']==summary['expected_weeks']==['2022-05-02T00:00:00Z'] and plan['coverage']==[['2022-05-02T00:00:00Z','2022-05-09T00:00:00Z']]
assert coverage['claim_sha256']==claimsha and coverage['plan_sha256']==summary['plan_sha256']==claim['inputs']['graph_plan']['sha256']
assert coverage['graph_manifest_sha256']==complete['cells'][1]['manifest_sha256']==index[str((S/'graph-2022-05-02/manifest.json').relative_to(M))]['sha256']
assert coverage['members']==sourcecov['members'] and coverage['graph_config_hash']==summary['graph_config_hash']==manifest['metadata']['graph_config_hash']
config=hashlib.sha256(json.dumps(inputs['graph_config'],sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest();assert config==summary['graph_config_hash']
assert manifest['metadata']['start_utc']==weekly['start_utc']=='2022-05-02T00:00:00Z' and manifest['metadata']['end_utc']==weekly['end_utc']=='2022-05-09T00:00:00Z' and manifest['metadata']['available_at']=='2022-05-10T00:00:00Z'
assert extent['segments']==223 and extent['days']==weekly['expected_members']==len(coverage['members'])==7
counts=[];segments=0;rawstats=[]
for i,(member,cov,ex) in enumerate(zip(weekly['members'],coverage['members'],extent['daily_members'],strict=True)):
 role=f'daily_map_{i:02d}';mapping=inputs[role];assert Path(member['path'])==M/claim['inputs'][role]['path'] and member['sha256']==cov['sha256']==ex['mapping_sha256']==claim['inputs'][role]['sha256']
 assert member['start_utc']==cov['start_utc'] and member['end_utc']==cov['end_utc'] and member['expected_rows']==cov['expected_rows']==ex['expected_rows']
 if i:assert weekly['members'][i-1]['end_utc']==member['start_utc']
 counts.append(member['expected_rows']);daily=read(S/f'aggregation/source-{i:06d}.json');assert daily==dict(rows=counts[-1],sequence=i,source_hash=member['sha256'],total_rows=sum(counts))
 assert len(mapping['spans'])==len(ex['segments'])
 for span,entry in zip(mapping['spans'],ex['segments'],strict=True):
  assert span['path']==entry['path'] and span['stored_sha256']==entry['expected_stored_sha256'] and span['stored_bytes']==entry['bytes'];p=Path(entry['path']);s=p.lstat();assert stat.S_ISREG(s.st_mode)
  actual=[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns];expected=[entry[k] for k in ('device','inode','bytes','mtime_ns','ctime_ns')];assert actual==expected
  segments+=1;rawstats.append({'path':entry['path'],'stat_identity':actual})
assert segments==223 and sum(counts)==weekly['expected_rows']==extent['declared_rows']==7734878
meta=manifest['metadata'];assert meta['raw_count']==sum(counts)==meta['admitted_count']+sum(meta['exclusion_counts'].values())
assert sorted(claim['inputs'][f'daily_map_{i:02d}']['sha256'] for i in range(7))==meta['source_hashes']
for name,row in manifest['arrays'].items():assert index[str((S/'graph-2022-05-02'/row['path']).relative_to(M))]=={'bytes':row['bytes'],'sha256':row['sha256']}
agg=read(S/'aggregation/complete.json');assert agg['status']=='complete' and agg['error'] is None and agg['rows']==7734878 and agg['source_boundaries']==7 and agg['database_sha256']==index[str((S/'aggregation/ledger.sqlite').relative_to(M))]['sha256']
guard=read(G/'guard/final.json');child=read(G/'guard/child_exit.json');root=read(E/'ROOT_TERMINAL_GRAPH_OBSERVATION01.json');outer=read(E/'outer-exit01.json');wait=read(E/'RAM_WAIT_EXIT01.json');launch=read(E/'launch-attempt01.json');job=inputs['execution_job']
assert root['guard_final_sha256']==evidence[str((G/'guard/final.json').relative_to(M))]
assert guard['phase']=='complete' and guard['child_exit_code']==child['exit_code']==outer['exit_code']==wait['actual_launcher_exit_code']==root['actual_root_session_exit_code']==0 and guard['cleanup_verified'] and child['snapshot_error'] is None
assert root['source']==outer['source']==wait['source']==launch['source']==SOURCE and launch['registration_sha256']==claim['registration_sha256']
assert root['root_session']==16028 and root['root_session_completion_tool']=='9b6fb7'
assert guard['owner_identity']==read(G/'owner.json') and guard['owner_identity']['experiment']==ID and guard['owner_identity']['source_commit']==SOURCE
for k,v in job['resources'].items():assert guard[k]==v,(k,guard.get(k),v)
assert guard['kernel_controls']=={'memory.high':str(guard['memory_high_bytes']),'memory.max':str(guard['memory_max_bytes']),'memory.swap.max':'0'}
assert guard['cleanup_unit_properties']['ActiveState']=='inactive' and guard['cleanup_unit_properties']['SubState']=='dead' and guard['cleanup_unit_properties']['ExecMainStatus']=='0' and not guard['cleanup_unit_properties']['ControlGroup']
pids=set(map(int,root['actual_selected_pid_exists']));pids.add(child['workload_pid']);pids.add(guard['monitor_pid']);pids.update(map(int,guard['cpu_thread_readback']));assert not Path(guard['cgroup']).exists() and not any(Path('/proc',str(pid)).exists() for pid in pids)
assert not (R/'failed.json').exists()
result={'decision':'pass','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'claim_sha256':claimsha,'source':SOURCE,'gate_sha256':claim['registration_sha256'],'source_pins':len(claim['experiment']['source_files']),'compact_inputs':len(inputs),'raw_extent_stat_checks':segments,'daily_rows':counts,'raw_rows':sum(counts),'graph_metadata':meta,'graph_hash':manifest['graph_hash'],'body_hash_total_bytes':body['total_bytes'],'selected_pids_absent':sorted(pids),'recorded_cgroup_absent':True,'telemetry':{k:guard[k] for k in ('elapsed_seconds','optional_memory_telemetry','peak_sampled_memory_current_bytes','memory_events','storage_peak_allocated_bytes','storage_peak_logical_file_bytes','storage_peak_entries','minimum_sampled_disk_free_bytes','storage_budget','cpu_enforcement','cpu_quota_controller_available','cleanup_stop_returncode')},'root_actual_exit':{'session':16028,'tool':'9b6fb7','exit_code':0},'evidence':evidence,'raw_extent_current_stats':rawstats,'limits':['Raw transaction bodies not read; original source worker decoding/semantic graph construction not rerun.','Body hashes establish artifact consistency, not an independent reaggregation or graph semantic reconstruction.','One weekly graph only: no full MCM, GAT/training, financial result, future eligibility or complete unrecorded PID-history claim.']}
(D/'METADATA_CHECK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('decision','source_pins','compact_inputs','raw_extent_stat_checks','raw_rows','body_hash_total_bytes','selected_pids_absent')},indent=2))
