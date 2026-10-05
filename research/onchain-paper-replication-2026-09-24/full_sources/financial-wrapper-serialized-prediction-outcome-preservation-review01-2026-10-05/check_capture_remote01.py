from pathlib import Path
import json,hashlib,stat,tarfile,subprocess,shutil,os,datetime,collections,ast
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';C=F/'heartbeat-root-checkpoint10-2026-10-04';D=F/'financial-wrapper-serialized-prediction-outcome-preservation-review01-2026-10-05';Q=F/'financial-wrapper-serialized-prediction-outcome-capture01-2026-10-05';B=F/'financial-wrapper-serialized-prediction-binding-review01-2026-10-05';V=F/'financial-wrapper-serialized-prediction-outcome-review01-2026-10-05';R=F/'financial-wrapper-serialized-prediction-outcome-remote01-2026-10-05';P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-predict-serialized-storage-root-launch-20261005-01');CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes())}
def load(p):return json.loads(p.read_bytes())
def put(n,d):
 p=D/n;b=(json.dumps(d,sort_keys=True,separators=(',',':'))+'\n').encode()
 with p.open('xb') as f:f.write(b)
 p.chmod(0o444);print(n,sha(b))
c=load(Q/'snapshot/COMPOSITION01.json');a=load(Q/'archive-manifest.json');record=load(Q/'CAPTURE01.json');root=load(C/'SERIALIZED_PREDICTION_OUTCOME_CAPTURE01_ROOT_EXIT.json')
assert root['actual_root_tool']['exit_code']==0 and root['capture_sha256']==sha((Q/'CAPTURE01.json').read_bytes())
for k in ('actual_stdout','actual_stderr'):assert sha(Path(root[k]['path']).read_bytes())==root[k]['sha256']
assert sha((Q/'increment.tar.gz').read_bytes())==record['archive']['sha256']=='b37afd04fa53bb7d1b5d53adbe653ff1a34019e0b4e4af1706964da455c3354f'
assert sha((Q/'archive-manifest.json').read_bytes())==record['archive']['manifest_sha256']=='b6c5811de6ed0429a405c09e9c353863f8f52c60d000368996310bb4b9ae92fd'
assert len(c['materialized'])==85 and sum(r['bytes'] for r in c['materialized'].values())==2837266
bases={'CAP':CAP,'Git':CAP/'.git','Parent':P,'outcome-review':V,'Root':C,'post-preparation-phase':B};counts=collections.Counter()
for name,row in c['materialized'].items():
 prefix,n=name.split('/',1);p=bases[prefix]/n;b=p.read_bytes();counts[prefix]+=1
 assert len(b)==row['bytes'] and sha(b)==row['sha256'] and (Q/'snapshot'/row['flat']).read_bytes()==b
assert counts['CAP']==25 and counts['Parent']==15
members={r['path']:r for r in a['members']};assert len(members)==86
with tarfile.open(Q/'increment.tar.gz','r:gz') as t:
 ts=t.getmembers();assert len(ts)==86 and {r.name for r in ts}==set(members)
 for x in ts:
  r=members[x.name];b=t.extractfile(x).read();assert x.isfile() and x.mode==r['mode'] and len(b)==r['bytes'] and sha(b)==r['sha256'] and b==(Q/'snapshot'/x.name).read_bytes()
old=load(F/'financial-wrapper-serialized-prediction-current-capture01-2026-10-05/snapshot/COMPOSITION01.json')
for key in ('basis','final_envelope_basis'):assert sha(Path(c[key]['path']).read_bytes())==c[key]['sha256']
for key in ('capsule','Git','Parent'):
 now=c[key] if key=='capsule' else c[key]['manifest'];before=old[key] if key=='capsule' else old[key]['manifest'];by={x['path']:x for x in now['members']}
 assert now['root_mode']==before['root_mode']
 for r in before['members']:assert by[r['path']]==r
assert len(c['capsule']['members'])==1563 and sum(x['kind']=='file' for x in c['capsule']['members'])==1213
assert c['Git_object_inventory']==old['Git_object_inventory'] and c['Git_logical_objects']==473
assert c['original_parent_exit'] is None and c['actual_Root_exit']==c['actual_child_exit']==0 and c['native_PID_history_complete'] is False
assert c['optimizer_updates']==c['paper_financial_fits']==0
capture={'schema_version':1,'decision':'accepted-actual-prediction-outcome-increment-capture','capture':ref(Q/'CAPTURE01.json'),'composition':ref(Q/'snapshot/COMPOSITION01.json'),'archive':ref(Q/'increment.tar.gz'),'manifest':ref(Q/'archive-manifest.json'),'actual_root_exit':ref(C/'SERIALIZED_PREDICTION_OUTCOME_CAPTURE01_ROOT_EXIT.json'),'original_body_counts':dict(counts),'original_bodies':85,'original_bytes':2837266,'archive_members':86,'CAP_regular':1213,'CAP_typed':1563,'Parent_regular':28,'Git_logical_objects':473,'accepted_old_CAP_regular':1188,'accepted_old_Parent_regular':13,'original_parent_exit':None,'actual_Root_exit':0,'native_PID_history_complete':False,'external_recovery':False,'qualification':'All85 new originals joined once to materialized and archive bytes; exact prior manifest rows reused without historical body reread. Opaque arrays not decoded. No economic, runtime-body, POSIX, writer-exclusion or capacity claim.'}
put('CAPTURE_CHECK01.json',capture)
base=F/'financial-wrapper-serialized-prediction-final-direct03-2026-10-05'
pins={'recover01.py':'001abd3d558cb3ebc4677f1b300219d1355ca394a95fbf8ea7ec8108ac4129c6','watch01.py':'8489c36dacc5ef2d4280ad4ed0bf9f5e19e6f452e3ab653838bb6d253764bcbe','utilities/owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb'}
for n,h in pins.items():assert sha((base/n).read_bytes())==h
assert sha((R/'recover01.py').read_bytes())=='ade968a43acc12b88027e088e9797e3bbeea5da918e6086f2dfb1e6a6cc2a5fa'
ast.parse((R/'recover01.py').read_text());flat=C/'SERIALIZED_PREDICTION_OUTCOME_FLAT01.py';ast.parse(flat.read_text())
s=load(R/'SELECTED_BODIES01.json');assert sha((R/'SELECTED_BODIES01.json').read_bytes())=='feb5ef6a2d6973ad7cfd7065e713b4569d92103b9b8c2bd68a1b0d7d6a31d20d';assert len(s['rows'])==8 and sum(x['bytes'] for x in s['rows'])==1252014
conf=load(C/'REMOTE_CONFIRMATION83.json');assert conf['commit']==conf['actual_remote_readback']==s['remote_commit']=='e260b040baba493449e89d3e91cab3d89ae4a55e';assert conf['actual_push_tool']['exit_code']==conf['actual_readback_tool']['exit_code']==0
ls=subprocess.check_output(['git','ls-tree','-rz',s['remote_commit'],'--',*[r['path'] for r in s['rows']]],cwd=M);entries={}
for line in ls.split(b'\0'):
 if line:
  meta,p=line.split(b'\t');mode,typ,oid=meta.decode().split();entries[p.decode()]=(mode,typ,oid)
assert len(entries)==8
for r in s['rows']:
 b=(M/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256'];mode,typ,oid=entries[r['path']];assert typ=='blob' and mode in ('100644','100755') and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid
put('REMOTE_SOURCE_CHECK01.json',{'schema_version':1,'decision':'accepted-exact-fixed-context-outcome-receiver','source':ref(R/'recover01.py'),'unchanged_imported_sources':pins,'selection':ref(R/'SELECTED_BODIES01.json'),'committed_rows_verified':8,'qualification':'Only HERE, REQUIRED and FINAL_POPULATION_COUNT are rebound before inherited entry. Both fetch scope and fresh bare path resolve dynamic HERE. CLI SHA guards actual selection before network. Inherited receipt status is historical literal; declared scope is these8 rows only. No numerical authority.'})
put('FLAT_SOURCE_CHECK01.json',{'schema_version':1,'decision':'accepted-fixed-outcome-flat-source-only','source':ref(flat),'regular_bodies':86,'required_actual_receiver_operations':34,'qualification':'Unchanged authenticated R4 restore with fixed archive/manifest and actual Root0/reaped0/cleanup/FSIZE guards. No execution entry until actual receiver receipt accepted. Original nulls and inherited byte scope remain unchanged.'})
absent=['fresh-serialized-prediction-final-direct03.git','selected','REMOTE_RECOVERY01.json','FAILED01.json'];assert all(not os.path.lexists(R/n) for n in absent)
active=[]
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:
   args=(p/'cmdline').read_bytes().split(b'\0');texts=[x.decode(errors='replace') for x in args];exe=(p/'comm').read_text().strip()
   if 'python' in exe and any(x.endswith(('/recover01.py','/parent01.py')) for x in texts):active.append(int(p.name))
  except (FileNotFoundError,ProcessLookupError,PermissionError):pass
assert not active
free=shutil.disk_usage(F).free;assert free>=10*1024**3
put('REMOTE_ENTRY_RELEASE01.json',{'schema_version':1,'decision':'accepted-exact-once-outcome-byte-receiver','one_use':True,'source':ref(R/'recover01.py'),'source_check':ref(D/'REMOTE_SOURCE_CHECK01.json'),'capture_check':ref(D/'CAPTURE_CHECK01.json'),'selection':ref(R/'SELECTED_BODIES01.json'),'remote_confirmation':ref(C/'REMOTE_CONFIRMATION83.json'),'remote_commit':s['remote_commit'],'cwd':str(M),'argv':[str(M/'.venv/bin/python'),'-B',str(R/'recover01.py'),'--selection-sha256',sha((R/'SELECTED_BODIES01.json').read_bytes())],'selected_count':8,'selected_bytes':1252014,'expected_operations':34,'fresh_absent_names':absent,'active_receiver_parent_pids':active,'free_bytes':free,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'numerical_authority':False,'qualification':'Root alone may run once; preserve any failure. Exact eight committed paths/OIDs joined independently. Actual fresh recovery and flat validation remain pending.'})
