from pathlib import Path
import ast,json,hashlib,subprocess,os,shutil,datetime,textwrap
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=Path(__file__).parent;C=F/'heartbeat-root-checkpoint10-2026-10-04';R=F/'financial-wrapper-serialized-prediction-final-direct03-2026-10-05';B=F/'financial-wrapper-serialized-prediction-final-direct02-2026-10-05';sha=lambda b:hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes())}
def save(n,x):
 p=D/n
 with p.open('x') as h:h.write(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n')
 p.chmod(0o444);return ref(p)
old=(B/'recover01.py').read_text();new=(R/'recover01.py').read_text();assert sha(old.encode())=='afee6b3234f29518542a29d9bbf8611e048348d472614274e8d19b75512f8be2';assert sha(new.encode())=='001abd3d558cb3ebc4677f1b300219d1355ca394a95fbf8ea7ec8108ac4129c6'
def assign(t):return [n for n in ast.parse(t).body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='REQUIRED'][-1]
a=assign(old);b=assign(new);required=ast.literal_eval(b.value);lines=new.splitlines(True);lines[b.lineno-1:b.end_lineno]=old.splitlines(True)[a.lineno-1:a.end_lineno];inverse=''.join(lines)
start=inverse.index('            owned_fetch_objects = None\n');end=inverse.index("            require(time.monotonic() - begun < 60",start);newblock=inverse[start:end];oldblock=next(x+'\n' for x in old.splitlines() if 'watch(owned_fetch_objects=' in x)
inverse=inverse[:start]+oldblock+inverse[end:];inverse=inverse.replace('    last_watch_context = None\n','').replace("'operation_args':list(args), 'cwd':str(cwd), 'last_watch_context':last_watch_context, 'original_error':None if first is None else repr(first), ",'').replace('FINAL_POPULATION_COUNT = 47','FINAL_POPULATION_COUNT = 36').replace('fresh-serialized-prediction-final-direct03.git','fresh-serialized-prediction-final-direct02.git').replace('fresh-actual-serialized-prediction-final-direct03-recovered','fresh-actual-serialized-prediction-final-direct02-recovered');assert inverse==old
# Evaluate only the isolated changed eligibility statements, no receiver import/execution.
class Child:
 pid=123
 def __init__(self,value):self.value=value;self.calls=0
 def poll(self):self.calls+=1;return self.value
cases=[]
for args,cwd,value in [(['fetch'],R/'fresh-serialized-prediction-final-direct03.git',None),(['fetch'],R/'fresh-serialized-prediction-final-direct03.git',0),(['fetch'],R/'wrong.git',None),(['ls-remote'],R/'fresh-serialized-prediction-final-direct03.git',None),([],R/'fresh-serialized-prediction-final-direct03.git',None)]:
 results=[]
 for code in [oldblock.replace('final-direct02.git','final-direct03.git'),newblock]:
  child=Child(value);seen=[];ns={'Path':Path,'HERE':R,'args':args,'cwd':cwd,'child':child,'watch':lambda **kw:seen.append(kw)};exec(textwrap.dedent(code),ns);results.append((seen,child.calls))
 assert results[0]==results[1];cases.append({'args':args,'cwd_matches':cwd.name=='fresh-serialized-prediction-final-direct03.git','poll_result':value,'poll_calls':results[1][1],'allowed':results[1][0][0]['owned_fetch_objects'] is not None})
assert ref(R/'watch01.py')['sha256']=='8489c36dacc5ef2d4280ad4ed0bf9f5e19e6f452e3ab653838bb6d253764bcbe';assert (R/'watch01.py').read_bytes()==(F/'financial-wrapper-serialized-final-watcher-diagnostics01-2026-10-05/watch01.py').read_bytes();assert ref(R/'utilities/owned_io.py')['sha256']=='09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb'
raw=(R/'SELECTED_BODIES01.json').read_bytes();assert sha(raw)=='7852e1f3b737c80220c635bfda74c6af4647e7556632a8fecabac39aa3b3cc60';s=json.loads(raw);assert len(s['rows'])==47 and sum(x['bytes'] for x in s['rows'])==6268031;assert required=={x['path']:{k:v for k,v in x.items() if k!='path'} for x in s['rows']};assert all(x in s['rows'] for x in json.loads((B/'SELECTED_BODIES01.json').read_bytes())['rows'])
assert s['remote_commit']=='0a12c9cc2442984c5d54e25842f18299a428af52';c=json.loads((C/'REMOTE_CONFIRMATION81.json').read_bytes());assert c['actual_remote_readback']==c['commit']==s['remote_commit'];assert all(c[k]['exit_code']==0 for k in ['actual_commit_tool','actual_push_tool','actual_readback_tool'])
output=subprocess.check_output(['git','ls-tree','-r','-z',s['remote_commit'],'--',*[x['path'] for x in s['rows']]],cwd=M);tree={}
for item in output.split(b'\0'):
 if item:
  h,n=item.split(b'\t',1);tree[n.decode()]=h.decode().split()
assert set(tree)=={x['path'] for x in s['rows']}
for row in s['rows']:
 body=(M/row['path']).read_bytes();assert len(body)==row['bytes'] and sha(body)==row['sha256'] and len(body)<=4194304;assert tree[row['path']]==['100644','blob',hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()]
assert len({x[2] for x in tree.values()})==45
absent=['fresh-serialized-prediction-final-direct03.git','selected','REMOTE_RECOVERY01.json','FAILED01.json','ACTUAL_ROOT_EXIT01.json'];assert all(not os.path.lexists(R/n) for n in absent);active=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  args=(p/'cmdline').read_bytes().split(b'\0')
  if any(x.endswith((b'/recover01.py',b'/recover02.py',b'/parent01.py')) and b'financial-wrapper-' in x for x in args) or any(x==b'tradingagents.research.onchain_replication.job' for x in args):active.append(int(p.name))
 except (FileNotFoundError,PermissionError,ProcessLookupError):pass
assert not active;free=shutil.disk_usage(R).free;assert free>=10737418240
check=save('FINAL_DIRECT03_SOURCE_CHECK01.json',{'schema_version':1,'decision':'accepted-exact-diagnostic-receiver03-source-selection','source':ref(R/'recover01.py'),'baseline_source':ref(B/'recover01.py'),'watcher_source':ref(R/'watch01.py'),'diagnostic_source_review':ref(D/'WATCHER_DIAGNOSTIC_SOURCE_CHECK01.json'),'owned_io':ref(R/'utilities/owned_io.py'),'inverse_after_explicit_context_and_literal_changes_exact':True,'isolated_poll_eligibility_cases':cases,'new_recorded_fields':['operation_args','cwd','last_watch_context','original_error'],'qualification':'Single poll stays short-circuited to owned fetch only; matching active child gets identical owned_objects scope. Exceptions, strict pre/post watches, deadlines, limits and cleanup unchanged. Context records the last active-stream sample; it is not a claim about a later pre/post phase. No actual receiver execution or historical cause inferred.','selection':ref(R/'SELECTED_BODIES01.json'),'prior36_rows_retained':True,'selected_count':47,'selected_bytes':6268031,'unique_objects':45,'expected_operations':149,'both_failed_archives_included':True,'independent_committed_tree_all_paths_modes_and_OIDs':True,'committed_tree_output_sha256':sha(output),'numerical_authority':False})
entry=save('FINAL_DIRECT03_ENTRY_RELEASE01.json',{'schema_version':1,'decision':'accepted-exact-once-final-direct03-retrieval-only','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':ref(R/'recover01.py'),'source_check':check,'selection':ref(R/'SELECTED_BODIES01.json'),'commit':s['remote_commit'],'actual_push_readback':ref(C/'REMOTE_CONFIRMATION81.json'),'Root_committed_tree_join':ref(R/'COMMITTED_SELECTED_TREE_JOIN01.json'),'independent_committed_paths':47,'selected_bytes':6268031,'unique_blobs':45,'expected_operations':149,'one_use':True,'fresh_namespaces_absent':absent,'active_receiver_parent_job_pids':active,'free_disk_bytes':free,'agent_snapshot':'Root/reviewer running; other two team agents errored. No additional source owner or numerical work assigned.','cwd':str(M),'argv':[str(M/'.venv/bin/python'),'-B',str(R/'recover01.py'),'--selection-sha256',sha(raw)],'unchanged_limits':{'whole_seconds':600,'Git_seconds':60,'logical':67108864,'allocated':100663296,'file':4194304,'floor':10737418240},'preflight_authority':False,'numerical_authority':False,'qualification':'Only Root may execute this fresh receiver once. Both earlier failed identities remain terminal/reserved. Actual47 recovered body/OID/typed-envelope joins and fresh restoration of both failed archives are required before Parent preflight release; no outcome predicted.'})
print(json.dumps({'source':check,'entry':entry}))
