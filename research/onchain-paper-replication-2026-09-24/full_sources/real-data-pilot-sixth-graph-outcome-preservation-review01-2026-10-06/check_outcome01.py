from pathlib import Path
import hashlib,json,stat,subprocess,math
H=Path(__file__).resolve().parent;R=H.parents[3];F=H.parent;N='eth-paper-real-pilot-graph-20220606-20261005-01';D=F/'real-data-pilot-sixth-graph01-2026-10-06';P=F/'real-data-pilot-sixth-graph-bodyproof01-2026-10-06';Q=R/'research_runs'/N;S=R/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/N;G=R/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/N;ev={}
def raw(p):
 s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4*1024**2;b=p.read_bytes();t=p.stat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns,t.st_ctime_ns);ev[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def read(p):return json.loads(raw(p))
def bound(ref):
 p=R/ref['path'];v=read(p);assert ev[ref['path']]==ref['sha256'];return v
proof=read(P/'BODY_HASH01.json');assert ev[str((P/'BODY_HASH01.json').relative_to(R))]=='ebab6695dfc9c33fe01537fbbf0b6a4fef7829238272e50eaedebaa8036fb88f'
link=read(P/'ACTUAL_PASS_TOOL01.json');assert link['actual_tool_exit_code']==0 and link['actual_tool_session']==30001 and link['actual_tool_completion_chunk']=='3cfe5c' and link['body_proof']['sha256']==ev[str((P/'BODY_HASH01.json').relative_to(R))] and link['observed_stdout']['proof_sha256']==link['body_proof']['sha256']
claim=read(Q/'claim.json');terminal=read(Q/'complete.json');assert not (Q/'failed.json').exists()
assert terminal['claim_sha256']==ev[str((Q/'claim.json').relative_to(R))]=='89198aa4122144e6754ca9a1b65b65997cf19c12d0bef8d3f3790a49ac92515a'
assert ev[str((Q/'complete.json').relative_to(R))]=='14cd212dbc4062c274038a060c6035594090057d84d60627fefb4b32f530eef8'
assert terminal['experiment_id']==claim['experiment_id']==N and terminal['status']=='complete' and terminal['cell_count']==2 and terminal['unavailable_count']==0
assert claim['source']==claim['design_source']==terminal['source']=='483f92786c5076ec6f6ad0bffa894b8b36653797' and claim['bindings'] is None and claim['bindings_sha256'] is None and claim['effective_attempt_budget']==72
release=read(D/'RELEASE_REVIEW01.json');assert ev[str((D/'RELEASE_REVIEW01.json').relative_to(R))]=='4bbfcf149b9b9f1fb7c702bb4c7afae7f9ae6af23e8780466713e63ba073a54a'
gate=read(D/'gate01.json');assert terminal['registration_sha256']==claim['registration_sha256']==ev[str((D/'gate01.json').relative_to(R))]==release['gate_sha256']
exp=gate['experiments'][N];assert claim['experiment']==exp and exp['parent'] is None and len(exp['source_files'])==192 and len(exp['runtime_hashes'])==7
# Historical source closure is reused from the accepted independent192-pin entry pass, not rehashed after integration.
prior=read(F/'real-data-pilot-june6-final-entry-review01-2026-10-06/CHECK01.json');assert prior['decision']=='pass' and prior['source_pins']==192
for relative in (str((D/'gate01.json').relative_to(R)),str((D/'RELEASE_REVIEW01.json').relative_to(R))):
 committed=subprocess.check_output(['git','show',claim['source']+':'+relative],cwd=R);assert hashlib.sha256(committed).hexdigest()==ev[relative]
for ref in claim['inputs'].values():bound(ref)
for name,expected in terminal['output_sha256'].items():raw(Q/'outputs'/name);assert ev[str((Q/'outputs'/name).relative_to(R))]==expected
index=bound(proof['artifact_index']);manifest=bound(proof['manifest']);assert proof['identity']==N and proof['status']=='passed' and len(proof['files'])==6
files=[];payloadpaths={row['path'] for row in proof['files']};assert len(payloadpaths)==6
for row in proof['files']:
 p=R/row['path'];s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode)
 sig=[s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,stat.S_IMODE(s.st_mode)]
 assert sig==row['stat_identity_before']==row['stat_identity_after'] and sig[2]==1 and s.st_size==row['bytes'] and index[row['path']]=={'bytes':row['bytes'],'sha256':row['sha256']}
 out={'path':row['path'],'sha256':row['sha256'],'bytes':row['bytes'],'stat_identity':sig[:6],'mode':sig[6]}
 if 'header' in row:
  h=row['header'];assert h['version']==[1,0] and h['payload_offset']==128 and h['fortran_order'] is False
  width=168 if h['dtype']=='<U42' else 8;assert h['dtype'] in ('<U42','float64','int64') and 128+math.prod(h['shape'])*width==row['bytes'];out['header']=h
 files.append(out)
for name,desc in manifest['arrays'].items():
 row=proof['arrays'][name];assert row['path']==str((S/'graph-2022-06-06'/desc['path']).relative_to(R)) and row['sha256']==desc['sha256'] and row['bytes']==desc['bytes']
assert proof['nodes']==1581761 and proof['edges']==2355230 and proof['arrays']['node_features']['header']['shape']==[1581761,4] and proof['arrays']['edge_index']['header']['shape']==[2,2355230]
assert sum(x['bytes'] for x in files)==proof['bytes_read']==3528523496 and sum(x['bytes'] for x in proof['arrays'].values())==429403880
for path,desc in index.items():
 if path not in payloadpaths:b=raw(R/path);assert len(b)==desc['bytes'] and ev[path]==desc['sha256']
actual={str(p.relative_to(R)) for p in S.rglob('*') if p.is_file()};assert actual==set(index)
cells=terminal['cells'];assert cells[0]['rows']==7293215 and [c['id'] for c in cells]==exp['cells'] and all(c['status']=='complete' for c in cells)
cell=cells[1];coverage=read(R/cell['coverage_path']);assert ev[cell['coverage_path']]==cell['coverage_sha256'] and coverage['claim_sha256']==terminal['claim_sha256'] and coverage['graph_manifest_sha256']==proof['manifest']['sha256']
assert coverage['members']==read(S/'source-coverage.json')['members'] and len(coverage['members'])==7 and sum(x['expected_rows'] for x in coverage['members'])==7293215
assert cell['admitted_count']==3392241 and cell['admitted_count']+sum(cell['exclusion_counts'].values())==cell['raw_count']==7293215
agg=read(S/'aggregation/complete.json');assert agg['status']=='complete' and agg['error'] is None and agg['rows']==7293215 and agg['source_boundaries']==7 and agg['database_sha256']==files[0]['sha256']
total=0
for i,member in enumerate(coverage['members']):
 a=read(S/'aggregation'/f'source-{i:06d}.json');total+=a['rows'];assert a['rows']==member['expected_rows'] and a['source_hash']==member['sha256'] and a['sequence']==i and a['total_rows']==total
root=read(D/'ROOT_TERMINAL01.json');outer=read(D/'outer-exit01.json');guard=read(G/'guard/final.json');child=read(G/'guard/child_exit.json');observer=read(G/'observer.json');owner=read(G/'owner.json')
assert root['actual_root_tool_exit_code']==outer['exit_code']==guard['child_exit_code']==child['exit_code']==0 and guard['phase']=='complete' and guard['cleanup_verified'] is True and guard['cleanup_stop_returncode']==5
assert root['source_commit']==outer['source']==claim['source'] and root['guard_final_sha256']==ev[str((G/'guard/final.json').relative_to(R))]
assert observer['status']=='complete' and observer['all_cells_complete'] is True and observer['cgroup_empty'] is True and observer['financial_completion'] is False and observer['terminal_sha256']==ev[str((Q/'complete.json').relative_to(R))]
assert observer['owner_sha256']==ev[str((G/'owner.json').relative_to(R))]
for path,sha in observer['evidence_sha256'].items():raw(G/path);assert ev[str((G/path).relative_to(R))]==sha
assert json.loads(raw(D/'ROOT_TOOL_STDOUT01.log'))==observer and raw(D/'ROOT_TOOL_STDERR01.log')==b''
pids=set(root['selected_recorded_pids'])|{guard['monitor_pid'],child['workload_pid']}|set(map(int,guard['cpu_thread_readback']));assert all(not Path('/proc',str(p)).exists() for p in pids) and not Path(guard['cgroup']).exists()
u=subprocess.run(['systemctl','--user','show',guard['unit'],'--property=ActiveState,SubState,MainPID'],capture_output=True,text=True);assert u.returncode==0 and 'ActiveState=inactive' in u.stdout and 'MainPID=0' in u.stdout
assert guard['memory_events']['high']==369 and all(guard['memory_events'][k]==0 for k in ('max','oom','oom_kill'))
body={'decision':'pass','identity':N,'index_sha256':proof['artifact_index']['sha256'],'files':files,'total_bytes':3528523496,'body_proof':link['body_proof'],'actual_pass_tool':{'path':str((P/'ACTUAL_PASS_TOOL01.json').relative_to(R)),'sha256':ev[str((P/'ACTUAL_PASS_TOOL01.json').relative_to(R))]},'qualification':'Authenticated actual Root30001/3cfe5c six-body single streaming hash pass and bounded public header evidence; independent current stat7/index/manifest/header arithmetic joins only. No reviewer payload/header/SQL read, no writer exclusion or database semantic consistency claim.'}
(H/'BODY_REVIEW01.json').write_text(json.dumps(body,indent=2)+'\n');raw(H/'BODY_REVIEW01.json')
out={'decision':'accepted','identity':N,'experiment':N,'source':claim['source'],'claim_sha256':terminal['claim_sha256'],'terminal_sha256':ev[str((Q/'complete.json').relative_to(R))],'status':'complete','complete_cells':2,'unavailable_cells':0,'root_actual_exit':{'exit_code':0,'session':root['actual_root_tool_session'],'completion_chunk':root['actual_root_tool_completion_chunk']},'cleanup':{'original_guard_cleanup_verified':True,'recorded_cgroup_absent':True,'recorded_pids_absent':sorted(pids),'lifetime_pid_history_complete':False},'original_cleanup_stop_returncode':5,'scientific_bindings':None,'native_supervisor_owner_receipt_present':True,'financial_completion':False,'raw_count':7293215,'admitted_count':3392241,'nodes':1581761,'edges':2355230,'payload_count':6,'payload_bytes':3528523496,'accounting':{'effective_budget':72,'spent_before':42,'spent_after':43,'remaining':29,'new_graph_claim':1,'new_financial_fits':0,'refunds':0,'old_failed_may30_retained':True},'native_seconds':guard['elapsed_seconds'],'sampled_peak_current_bytes':guard['peak_sampled_memory_current_bytes'],'last_unit_kernel_peak_bytes':guard['optional_memory_telemetry']['unit']['kernel_peak_bytes'],'memory_events':guard['memory_events'],'memory_telemetry_qualification':guard['optional_memory_telemetry']['qualification'],'minimum_sampled_disk_free_bytes':guard['minimum_sampled_disk_free_bytes'],'current_unit':u.stdout,'evidence':ev,'qualification':'Genuine actual two-cell graph outcome and independent metadata/stat joins. Source192/runtime7 acceptance inherited at actual claim/gate; current live package may subsequently integrate accepted changes. All original nulls, failed histories, HIGH events and cleanupstop retained. No MCM/training, financial completion, raw replay, numerical rerun, SQL/body/header read, actual remote backup or capacity claim by review.'}
(H/'OUTCOME_REVIEW01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'decision':'accepted','body_sha256':hashlib.sha256((H/'BODY_REVIEW01.json').read_bytes()).hexdigest(),'outcome_sha256':hashlib.sha256((H/'OUTCOME_REVIEW01.json').read_bytes()).hexdigest(),'known_pids':len(pids)}))
