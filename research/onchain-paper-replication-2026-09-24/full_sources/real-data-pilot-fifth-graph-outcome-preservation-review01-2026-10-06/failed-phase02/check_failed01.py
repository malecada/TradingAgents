"""Independent failed-scope metadata reconstruction; never opens payload bodies."""
import ast, hashlib, json, os, stat
from pathlib import Path
R=Path.cwd().resolve(); O=Path(__file__).resolve().parent
F='research/onchain-paper-replication-2026-09-24/full_sources/'
P=F+'real-data-pilot-fifth-graph-failed-outcome-preservation-preparation01-2026-10-06/'
C=F+'real-data-pilot-fifth-graph01-2026-10-06/'
ID='eth-paper-real-pilot-graph-20220530-20261005-01'
SOURCE='14414c1637256dd286eafbe92391129dee3d29bf'
roots=['research_runs/'+ID,'research_artifacts/onchain-paper-replication-2026-09-24/runs/'+ID,'research_artifacts/onchain-paper-replication-2026-09-24/sources/'+ID]
E={}; cache={}
def sha(b): return hashlib.sha256(b).hexdigest()
def sig(s): return [s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def read(p, expected=None):
 if p not in cache:
  q=R/p;s=q.lstat();assert q.resolve(strict=True)==q and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2,p
  with q.open('rb') as h:
   assert sig(os.fstat(h.fileno()))==sig(s);raw=h.read();assert sig(os.fstat(h.fileno()))==sig(s)
  assert sig(q.lstat())==sig(s);cache[p]=raw;E[p]=sha(raw)
 assert expected is None or E[p]==expected,(p,E[p],expected)
 return cache[p]
def js(p,h=None): return json.loads(read(p,h))
def put(name,x):
 raw=(json.dumps(x,sort_keys=True,indent=2)+'\n').encode();(O/name).write_bytes(raw);return {'path':str((O/name).relative_to(R)),'sha256':sha(raw)}
B=F+'real-data-pilot-fifth-graph-failed-root-bodyproof01-2026-10-06/BODY_HASH01.json'
bp=js(B,'1f2c21fcc1751a13e0f52aa63c09df602a30b2af177816ba5ece407939c39039')
read(B.replace('BODY_HASH01.json','body_check01.py'))
assert bp['decision']=='pass' and bp['total_bytes']==3278655680 and bp['index_sha256'] is None
assert bp['one_streaming_pass_per_body'] and not bp['numerical_imports'] and not bp['sqlite_queries']
payloads={x['path']:x for x in bp['files']};assert len(payloads)==3
for p,row in payloads.items():
 q=R/p;s=q.lstat();assert q.resolve(strict=True)==q and stat.S_ISREG(s.st_mode) and sig(s)==row['stat_identity'] and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==row['mode']
controls=[];directories=[]
for root in roots:
 for base,dirs,names in os.walk(R/root,followlinks=False):
  assert len(controls)+len(directories)<4096
  for d in [Path(base)]+[Path(base)/n for n in dirs]: assert not d.is_symlink()
  directories.append(str(Path(base).relative_to(R)))
  for n in sorted(names):
   p=str((Path(base)/n).relative_to(R))
   if p not in payloads:
    assert Path(p).suffix in ('.json','.jsonl','.log'),p
    read(p);controls.append(p)
claim=js(roots[0]+'/claim.json','63e94692f690373cc238bbb7d7c7e5147129f145c8df18b650a1040736b50a76')
failed=js(roots[0]+'/failed.json','f5e452d0352424a13db233a914ffb1ce742244a49de0481ef1b011459b2b569b')
guard=js(roots[1]+'/guard/final.json','8cfef38cd9fc43484742fcb61b5440e1eac8909ff46389793d2a3c770d12f823')
root=js(C+'ROOT_TERMINAL01.json','498bee3919eee4a79d3b983746cd5f0090963780b58e272128b5a70f3548cc1a')
outer=js(C+'outer-exit01.json'); launch=js(C+'launch-attempt01.json');cells=js(roots[1]+'/postmortem-cells.json')
assert claim['source']==claim['design_source']==SOURCE and claim['experiment_id']==ID and claim['effective_attempt_budget']==71
assert claim['bindings'] is None and claim['bindings_sha256'] is None
assert failed['status']=='failed' and failed['claim_sha256']==E[roots[0]+'/claim.json'] and failed['output_sha256']=={}
assert guard['phase']=='failed' and guard['child_exit_code']==125 and guard['cleanup_verified'] is True and guard['cleanup_stop_returncode']==0
assert root['actual_root_tool_exit_code']==root['actual_parent_exit_code']==outer['exit_code']==1
assert root['failed_marker_sha256']==E[roots[0]+'/failed.json'] and root['guard_final_sha256']==E[roots[1]+'/guard/final.json']
assert not Path(guard['cgroup']).exists() and root['actual_current_cgroup_absent'] is True
pids=root['actual_selected_recorded_pids'];assert len(set(pids))==len(pids)==5 and all(not Path('/proc',str(p)).exists() for p in pids)
assert 'MainPID=0' in root['actual_current_unit_properties_text'] and 'ActiveState=failed' in root['actual_current_unit_properties_text']
assert len(cells)==2 and cells[0]['status']=='complete' and cells[0]['rows']==7507236 and cells[1]['status']=='unavailable'
assert launch['source']==SOURCE and launch['source_pins']==178 and launch['compact_input_pins']==32 and launch['original_raw_extents_stat_only']==250
read(claim['registration'],claim['registration_sha256'])
sources=claim['experiment']['source_files'];assert len(sources)==178
for p,h in sources.items(): read(p,h)
inputs=claim['inputs'];assert len(inputs)==32
for row in inputs.values(): read(row['path'],row['sha256'])
extent=js(inputs['raw_extent']['path']); raw_count=0
for day in extent['daily_members']:
 mapping=js(day['mapping_path'],day['mapping_sha256']); assert len(mapping['spans'])==len(day['segments'])
 for row,span in zip(day['segments'],mapping['spans']):
  p=Path(row['path']);s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode)
  assert [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]==[row[k] for k in ('device','inode','bytes','mtime_ns','ctime_ns')]
  assert row['path']==span['path'] and row['expected_stored_sha256']==span['stored_sha256'];raw_count+=1
assert raw_count==250
inverse=js(P+'INVERSE01.json');inverse_results={}
for name,record in inverse.items():
 raw=read(P+name,record['candidate_sha256']);ast.parse(raw);lines=raw.decode().splitlines(keepends=True)
 for h in sorted(record['hunks'],key=lambda h:h['candidate_start'],reverse=True):
  assert lines[h['candidate_start']:h['candidate_end']]==h['candidate'];lines[h['candidate_start']:h['candidate_end']]=h['original']
 assert ''.join(lines).encode()==read(record['baseline'],record['baseline_sha256']);inverse_results[name]=len(record['hunks'])
ns={'__name__':'independent_source_check'};exec(compile(read(P+'prepare01.py'),P+'prepare01.py','exec'),ns)
try: ns['select'](R,None,None)
except ValueError as error: assert 'draft nulls refuse' in str(error)
else: raise AssertionError('null review accepted')
review={'schema_version':1,'decision':'accepted','scope':'actual FAILED original scope and preservation source only; not execution release','experiment':ID,'source':SOURCE,'root_actual_exit':{'exit_code':1,'session_id':36176,'tool_chunk':'3d2573'},'claim_sha256':E[roots[0]+'/claim.json'],'parent_status':'failed','source_cell':cells[0],'graph_cell':cells[1],'cleanup':{'original_guard_cleanup_verified':True,'original_cleanup_stop_returncode':0,'original_native_child_exit_code':125,'recorded_cgroup_absent':True,'recorded_pids_absent':pids,'lifetime_pid_history':'unknown','unit_properties_source':'actual Root readback; not independently rerun systemctl'},'source_pins_verified':178,'input_pins_verified':32,'raw_extents_stat_only':raw_count,'body_hash_pass_inherited':{'path':B,'sha256':E[B]},'current_payload_stat_joins':3,'payload_bytes':bp['total_bytes'],'graph_complete':False,'external_byte_recovery':False,'retirement_release':False,'qualification':'Fresh failed-scope hashes are preservation evidence with current non-atomic stat joins, not prior expected scientific content hashes, SQLite integrity, writer exclusion, complete graph, numerical equivalence, runtime-body recovery or capacity. No payload reread; original failed identity remains spent. Monitor lease loss cause unknown.','evidence':dict(sorted(E.items()))}
ref=put('OUTCOME_REVIEW01.json',review)
selection=ns['select'](R,ref,{'path':B,'sha256':E[B]});put('SELECTION_CHECK_DRAFT01.json',selection)
put('SOURCE_CHECK01.json',{'decision':'accepted-source-only','candidate_manifest_sha256':sha(read(P+'MANIFEST01.json')),'exact_inverse_hunk_counts':inverse_results,'missing_review_refusal':True,'actual_selector_pass':True,'selected_files':selection['count'],'selected_bytes':selection['total_bytes'],'selected_directories':len(selection['directories']),'no_payload_reads':True,'no_native_network_or_authority_execution':True,'final_entry_release':'pending exact installed selection/envelope/current bindings'})
print(json.dumps({'outcome_review':ref,'selected_files':selection['count'],'selected_bytes':selection['total_bytes'],'control_files':len(controls),'source_pins':178,'inputs':32,'raw_stat_joins':250,'payload_stat_joins':3}))
