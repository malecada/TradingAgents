"""Exact four concrete receiver binding readback. Local Git only; no receiver entry."""
from verify_capture01 import *
import importlib.util,ast,shutil
P=F/'financial-wrapper-compatibility-complete100-outcome-recovery-preparation03-2026-10-05';COMMIT='718c29220e52697e5ff9cc9bb0b469157d8b1b95'
rd=Reader();summary_raw=rd.read(C/'FOUR_LANE_REMOTE_BINDING01.json');summary=json.loads(summary_raw);confirmation_raw=rd.read(C/'REMOTE_CONFIRMATION56.json');confirmation=json.loads(confirmation_raw)
rd.need(summary['actual_confirmed_main_commit']==COMMIT and summary['entry_releases_pending'] is True and len(summary['lanes'])==4,'four concrete actual Root bindings')
rd.need(confirmation['actual_remote_head']==confirmation['main_commit']==COMMIT and confirmation['push']['actual_exit']==confirmation['readback']['actual_exit']==0,'separate actual Root push/readback evidence')
from bounded_git01 import git
rd.need(git(MAIN,['rev-parse','HEAD'],cap=128).decode().strip()==COMMIT,'actual Main HEAD')
sys.path[:0]=[str(P),str(P/'utilities')];spec=importlib.util.spec_from_file_location('entry_source03',P/'outcome01.py');O=importlib.util.module_from_spec(spec);spec.loader.exec_module(O)
rd.need(R.digest(rd.read(P/'outcome01.py'))=='883127897d7f8f6cd3093bcb4ad74222bcd45b6c66c3c7b593cf7b82e23085ec','accepted source03');capture=rd.read(D/'CAPTURE01.json',O.CAPTURE);context=O.context(capture)
proofpins={'source407_basis':'02900ae11c7053a5f691ef2838fa7427b5befd86778331c19b97143e1c6c2e48','outcome_disposition':'27e29cab0b784748bdd0fef2ca484215b39b2b025784a469de443f619ae9b124','cleanup':'67d74e5ac68b9957f5e116753730eb698d6167141f0d61dfda558dd424e69e23','actual_capture_review':'5db589619e8df5cec1755ebc3a36bffa2d3a8cd3e4c66e41e8d68bc9befc7b18'}
blob_cache={};results=[];entries=[];entrypaths=[]
for i,binding in enumerate(summary['lanes']):
 root=O.lane_root(i,'remote');flat=O.lane_root(i,'flat');rd.need(binding['lane']==i and binding['root']==str(root),'actual fixed root/identity')
 rd.pin(root);rd.need(stat.S_IMODE(root.lstat().st_mode)==0o700 and root.lstat().st_uid==os.geteuid(),'private owned receiver')
 cr=rd.read(root/'REMOTE_CONTRACT01.json',binding['contract_sha256']);c=json.loads(cr);qr=rd.read(root/'ROOT_REQUEST01.json',binding['request_sha256']);q=json.loads(qr);sr=rd.read(root/'SELECTED_BODIES01.json',binding['selection_sha256']);selection=json.loads(sr);caller=rd.read(root/'caller01.py',binding['caller_sha256'])
 rd.need(q['commit']==COMMIT and q['lane']==i and q['remote'] is q['profile'] is q['release'] is None,'only current receiver request; future flat evidence null');O.request_core_sha256(q);required=O.selected_required(q,i,context)
 rd.need({k:v['sha256'] for k,v in q['proofs'].items()}==proofpins,'all four genuine immutable proof refs')
 rd.need(selection=={'remote_commit':COMMIT,'rows':[dict(path=n,**p) for n,p in sorted(required.items())]},'complete literal selection schema')
 rd.need(c['schema_version']==1 and c['status']=='ROOT_BOUND_OUTCOME_LANE%02d_ENTRY'%(i+1) and c['phase']=='REMOTE' and c['owned_root']==str(root) and c['main_commit']==COMMIT and c['numerical_authority'] is False,'actual contract scope')
 rd.need(c['request']=={'path':'ROOT_REQUEST01.json','sha256':binding['request_sha256']} and c['selection']=={'path':'SELECTED_BODIES01.json','sha256':binding['selection_sha256']},'actual exact request/selection joins')
 for k in ('flat_release','remote_receipt','remote_root_exit','selected_mode_profile'):rd.need(c[k] is None,'future dependency stays null')
 expected=O.generate(q,capture);rd.need(caller==expected['callers']['remote'].encode(),'exact generated accepted caller; no extra transforms')
 rd.need(rd.read(root/'recover01.py',c['helpers']['recover01.py'])==expected['receiver'].encode(),'exact generated receiver table/inverse');rd.need(rd.read(root/'receipt01.py',c['helpers']['receipt01.py'])==expected['receipt'].encode(),'exact generated receipt status')
 helpernames={'cohort01.py','flat_primitives01.py','join01.py','original_tree01.py','outcome01.py','receipt01.py','recover01.py','restore_bundle01.py','space01.py','utilities/bounded_git01.py','utilities/owned_io.py','utilities/recovery_pax01.py','watch01.py'}
 rd.need(set(c['helpers'])==helpernames,'exact13 helper closure')
 for n,h in c['helpers'].items():
  b=rd.read(root/n,h);rd.need(stat.S_IMODE((root/n).lstat().st_mode)==0o600,'private installed source files')
  if n not in ('recover01.py','receipt01.py'):rd.need(b==rd.read(P/n),'exact source03/accepted dependency '+n)
  # Future flat helper body installation is authenticated, with no future release.
  rd.need(rd.read(flat/n,h)==b,'eight-root literal source correction/readback '+n)
 fresh=['fresh-compatibility-complete100-outcome-lane%02d.git'%(i+1),'selected','REMOTE_RECOVERY01.json','FAILED01.json'];rd.need(c['fresh_names']==fresh,'exact fresh receiver population')
 prefix='ROOT_OUTCOME_LANE%02d_REMOTE01'%(i+1)
 # Derive actual prefix literal from caller rather than guessing its inherited version suffix.
 tree=ast.parse(caller);prefixes=[n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='prefix' for t in n.targets)]
 rd.need(len(prefixes)==1,'one actual caller prefix');expr=prefixes[0];rd.need(all(isinstance(n,(ast.BinOp,ast.Add,ast.Constant,ast.Name,ast.Load)) for n in ast.walk(expr)) and all(not isinstance(n,ast.Name) or n.id=='phase' for n in ast.walk(expr)),'bounded prefix expression');prefix=eval(compile(ast.Expression(expr),'<actual caller prefix>','eval'),{'__builtins__':{},'phase':'REMOTE'})
 absent=fresh+[prefix+s for s in ('_INTENT.json','_SPAWN.json','.stdout','.stderr','_EXIT.json')]+['REMOTE_ENTRY_RELEASE01.json']
 for n in absent:rd.need(not os.path.lexists(root/n),'fresh one-use receiver namespace '+n)
 entrypaths += [str(root/'recover01.py').encode(),str(root/'caller01.py').encode()]
 rows=[]
 for n,pin in sorted(required.items()):
  b=rd.read(MAIN/n,pin['sha256']);rd.need(len(b)==pin['bytes'],'actual selected source extent')
  if n not in blob_cache:
   listing=git(MAIN,['ls-tree','-z',COMMIT,'--',n],cap=8192);records=listing.rstrip(b'\0').split(b'\0');rd.need(len(records)==1,'one exact committed selected path');header,name=records[0].split(b'\t',1);mode,kind,oid=header.split();rd.need(name.decode()==n and mode in (b'100644',b'100755') and kind==b'blob','regular committed selected blob');body=git(MAIN,['cat-file','blob',oid.decode()],cap=R.FILE);rd.need(body==b and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid.decode(),'actual commit blob/body/OID join');blob_cache[n]=(oid.decode(),mode.decode())
  oid,mode=blob_cache[n];rows.append(dict(path=n,**pin,git_object=oid,git_mode=mode))
 count=len(rows);logical=sum(x['bytes'] for x in rows);unique=len({x['git_object'] for x in rows});rd.need(count==binding['required_files']==(19 if i<2 else 17) and logical==binding['required_bytes'],'complete selected denominator')
 census=O.W.census(root);results.append({'lane':i,'root':str(root),'contract_sha256':binding['contract_sha256'],'caller_sha256':binding['caller_sha256'],'request_sha256':binding['request_sha256'],'selection_sha256':binding['selection_sha256'],'selected_files':count,'selected_bytes':logical,'unique_blobs':unique,'expected_git_operations':10+unique+2*count,'census':census,'selected_blobs':rows,'helpers':c['helpers']})
 entries.append({'schema_version':1,'decision':'ACCEPTED_EXACT_ONE_USE_OUTCOME_LANE%02d_REMOTE'%(i+1),'contract_sha256':binding['contract_sha256'],'caller_sha256':binding['caller_sha256'],'numerical_authority':False})
# Only exact entry argv absence, never an assertion about universal process history.
raw_node=next(n for n in ast.parse(caller).body if isinstance(n,ast.FunctionDef) and n.name=='raw');raw_ns={'os':os,'FILE':R.FILE};exec(compile(ast.Module(body=[raw_node],type_ignores=[]),'<exact accepted caller raw>','exec'),raw_ns)
for p in Path('/proc').iterdir():
 if p.name.isdigit() and int(p.name)!=os.getpid():
  try:b=raw_ns['raw'](p/'cmdline');rd.total+=len(b);rd.tick()
  except (FileNotFoundError,ProcessLookupError,PermissionError):continue
  rd.need(not any(x in b.split(b'\0') for x in entrypaths),'no current exact receiver entry process')
O.W.check();free=shutil.disk_usage(F).free;rd.need(free>=10*1024**3+805306368,'shared sampled floor plus768MiB');rd.finish()
for i,entry in enumerate(entries):R.put(HERE/('LANE%02d_REMOTE_ENTRY_RELEASE01.json'%(i+1)),entry)
result={'schema_version':1,'decision':'ACCEPTED_EXACT_FOUR_ONE_USE_OUTCOME_REMOTE_ENTRIES_ONLY','main_commit':COMMIT,'Root_binding_sha256':R.digest(summary_raw),'actual_push_readback_sha256':R.digest(confirmation_raw),'lanes':results,'unique_selected_paths':len(blob_cache),'checks':rd.checks,'read_bytes':rd.total,'shared_free_bytes':free,'shared_extra_margin_bytes':805306368,'flat_released':False,'actual_recovery_accepted':False,'numerical_authority':False,'release_files':[{ 'path':'LANE%02d_REMOTE_ENTRY_RELEASE01.json'%(i+1),'sha256':R.digest(R.encode(e))} for i,e in enumerate(entries)]}
(HERE/'REMOTE_ENTRY_CHECKS01.json').write_bytes(R.encode(result));print(json.dumps({k:v for k,v in result.items() if k!='lanes'}))
