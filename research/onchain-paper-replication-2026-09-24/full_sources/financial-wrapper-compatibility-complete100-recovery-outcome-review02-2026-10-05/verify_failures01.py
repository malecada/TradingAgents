"""Read-only failed receiver closure; no rerun or broad completed-outcome replay."""
from pathlib import Path
import sys,os,json,ast,stat,math
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05';sys.path.insert(0,str(OLD));from verify_capture01 import Reader,R,F,C,MAIN
rd=Reader();basis=json.loads(rd.read(OLD/'REMOTE_ENTRY_CHECKS01.json'));rows=[];recorded=[];groups=[]
for i,b in enumerate(basis['lanes']):
 root=Path(b['root']);prefix='ROOT_OUTCOME_LANE%02d_REMOTE02'%(i+1)
 paths={k:root/n for k,n in {'failure':'FAILED01.json','exit':prefix+'_EXIT.json','spawn':prefix+'_SPAWN.json','intent':prefix+'_INTENT.json','stdout':prefix+'.stdout','stderr':prefix+'.stderr','selection':'SELECTED_BODIES01.json','caller':'caller01.py','receiver':'recover01.py'}.items()};raw={k:rd.read(p) for k,p in paths.items()};failure=json.loads(raw['failure']);outer=json.loads(raw['exit']);spawn=json.loads(raw['spawn']);intent=json.loads(raw['intent'])
 rd.need(failure['status']=='failed-original-attempt' and failure['error']=='frozen canonical selection' and failure['error_type']=='ValueError' and failure['operations']==[] and failure['initial_owned_allocation'] is None and failure['whole_tree_observations']==[] and failure['genuine_run_or_native_started'] is False,'actual pre-Git canonical-selection refusal')
 rd.need(outer['child_exit']==1 and outer['actual_parent_exit'] is None and outer['parent_failure_type'] is None and outer['cleanup_failures']==[] and outer['parent_fsize_readback']==[4194304,4194304] and type(outer['elapsed_seconds']) in (float,int) and 0<=outer['elapsed_seconds']<630,'actual child1, cleanup and unchanged Parent null')
 rd.need(raw['stdout']==b'' and b'frozen canonical selection' in raw['stderr'],'raw actual child output matches refusal')
 rd.need(R.digest(raw['caller'])==b['caller_sha256'] and R.digest(raw['receiver'])==b['helpers']['recover01.py'] and R.digest(raw['selection'])==b['selection_sha256'],'original exact released source/selection retained')
 tree=ast.parse(raw['receiver']);encode=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='encode');ns={'json':json};exec(compile(ast.Module(body=[encode],type_ignores=[]),str(paths['receiver']),'exec'),ns)
 obj=json.loads(raw['selection']);canonical=ns['encode'](obj);rd.need(canonical!=raw['selection'],'actual encoded-byte mismatch reproduced')
 rd.need(json.loads(canonical)==obj and canonical==R.encode(obj),'same object; exact receiver canonical encoding identified')
 rd.need(intent['contract_sha256']==b['contract_sha256'] and intent['claim_started'] is False and spawn['argv']==intent['argv'] and spawn['argv'][-1]==b['selection_sha256'],'actual fixed attempted identity')
 for pid in (intent['parent_pid'],spawn['pid']):rd.need(type(pid)is int and pid>0 and not os.path.lexists(Path('/proc')/str(pid)),'actual recorded PID absent');recorded.append(pid)
 groups.append(spawn['pid'])
 for n in ('selected','REMOTE_RECOVERY01.json','fresh-compatibility-complete100-outcome-lane%02d.git'%(i+1)):rd.need(not os.path.lexists(root/n),'no selected or Git store created')
 m=R.scan(root);rd.tree(root,m)
 for row in m['members']:
  if row['kind']=='file':rd.read(root/row['path'],row['sha256'])
 rows.append({'lane':i,'root':str(root),'status':'FAILED_PERMANENTLY_BEFORE_ANY_GIT_OPERATION','manifest':m,'error':'frozen canonical selection','actual_git_operations':0,'inner_child_exit':1,'original_parent_exit':None,'cleanup_failures':[],'parent_pid':intent['parent_pid'],'child_pid':spawn['pid'],'literal_selection_sha256':R.digest(raw['selection']),'canonical_same_object_sha256':R.digest(canonical),'evidence':{k:{'path':str(paths[k]),'sha256':R.digest(v),'bytes':len(v)} for k,v in raw.items() if k not in ('caller','receiver','selection')},'review_omission':'Prior review checked parsed table and Git/body/hash joins but omitted receiver encode equality.'})
# Exact inherited bounded reader for virtual process stat, no guessed start ticks.
caller_tree=ast.parse(raw['caller']);rawfunc=next(n for n in caller_tree.body if isinstance(n,ast.FunctionDef) and n.name=='raw');ns={'os':os,'FILE':R.FILE};exec(compile(ast.Module(body=[rawfunc],type_ignores=[]),'<accepted caller raw>','exec'),ns)
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:body=ns['raw'](p/'stat');rd.total+=len(body);rd.tick()
  except (FileNotFoundError,ProcessLookupError,PermissionError):continue
  values=body.decode().rsplit(')',1)[1].split();rd.need(int(values[2]) not in groups,'recorded owned child process group absent')
# Reuse closed complete100 disposition and capture pins; no epoch/PID-history rerun.
refs={'outcome':F/'financial-wrapper-compatibility-complete100-outcome-review01-2026-10-05/MACHINE01.json','capture':F/'financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/CAPTURE01.json','capture_review':OLD/'ACTUAL_CAPTURE_REVIEW01.json'}
pins={'outcome':'27e29cab0b784748bdd0fef2ca484215b39b2b025784a469de443f619ae9b124','capture':'ef82889318080bf2fec673d6c558c4afe3d95260c1a4d783c9b5eb16d8979442','capture_review':'5db589619e8df5cec1755ebc3a36bffa2d3a8cd3e4c66e41e8d68bc9befc7b18'}
for k,p in refs.items():rd.read(p,pins[k])
rd.finish();result={'schema_version':1,'decision':'ACCEPTED_ACTUAL_FOUR_FAILED_METADATA_RECEIVER_DISPOSITIONS_ONLY','lanes':rows,'recorded_pids_absent':recorded,'recorded_owned_child_groups_absent':groups,'universal_process_history':None,'existing_complete100_and_capture_pins_unchanged':pins,'complete100_disposition_unchanged':True,'new_financial_claims':0,'external_recovery_accepted':False,'checks':rd.checks,'read_bytes':rd.total,'numerical_authority':False}
(HERE/'FAILED_READBACK01.json').write_bytes(R.encode(result));print(json.dumps({k:v for k,v in result.items() if k!='lanes'}))
