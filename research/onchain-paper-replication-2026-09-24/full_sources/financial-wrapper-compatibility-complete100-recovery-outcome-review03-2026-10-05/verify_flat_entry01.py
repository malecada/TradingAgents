"""Exact concrete caller/request validation only; never invokes main or child."""
from pathlib import Path
import sys,os,json,ast,hashlib,stat,importlib.util
HERE=Path(__file__).resolve().parent;F=HERE.parent
sys.path.insert(0,str(F/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05'))
from verify_capture01 import Reader,R,C,MAIN,D
P=F/'financial-wrapper-compatibility-complete100-outcome-recovery-preparation04-2026-10-05';sys.path[:0]=[str(P),str(P/'utilities')]
spec=importlib.util.spec_from_file_location('accepted_outcome04',P/'outcome01.py');O=importlib.util.module_from_spec(spec);spec.loader.exec_module(O)
rd=Reader();binding_raw=rd.read(C/'CANONICAL02_FOUR_FLAT_FINAL_BINDING02.json');binding=json.loads(binding_raw);basis=json.loads(rd.read(HERE/'REMOTE_OUTCOME_AND_FLAT_CORE_READBACK01.json'));earlier=json.loads(rd.read(F/'financial-wrapper-compatibility-complete100-recovery-outcome-review02-2026-10-05/REMOTE_ENTRY_CHECKS01.json'));capture=rd.read(D/'CAPTURE01.json',O.CAPTURE);results=[];releases=[];errors=[]
for i,row in enumerate(binding['lanes']):
 root=O.lane_root(i,'flat');remote=O.lane_root(i,'remote');b=basis['lanes'][i]
 rd.need(row['lane']==i and row['root']==str(root),'fixed lane/root')
 cr=rd.read(root/'FLAT_CONTRACT02.json',row['contract_sha256']);c=json.loads(cr);qr=rd.read(root/'REQUEST_FLAT_FINAL01.json',row['request_sha256']);q=json.loads(qr);draft=json.loads(rd.read(root/'REQUEST_FLAT_DRAFT01.json',b['draft_request_sha256']));ir=rd.read(root/'FLAT_RELEASE01.json',row['inner_release_sha256'])
 rd.need(ir==rd.read(HERE/('LANE%02d_INNER_FLAT_RELEASE01.json'%(i+1))) and q==dict(draft,release={'name':'FLAT_RELEASE01.json','sha256':R.digest(ir)}) and O.request_core_sha256(q)==b['request_core_sha256']==row['request_core_sha256'],'literal genuine release and only release-ref added')
 generated=O.generate(q,capture);caller=rd.read(root/'caller01.py',row['caller_sha256']);rd.need(caller==generated['callers']['flat'].encode(),'entire actual caller equals accepted generated body')
 ns={'Path':Path,'os':os,'stat':stat,'hashlib':hashlib,'D':root,'RECEIVER':remote,'FILE':R.FILE,'IOPIN':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','pins':{}}
 names={'sig','raw','read','rejoin','local','evidence','contract'};nodes=[n for n in ast.parse(caller).body if isinstance(n,ast.FunctionDef) and n.name in names];rd.need(len(nodes)==len(names),'actual extracted pre-entry validators');exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual caller validators>','exec'),ns);rd.need(ns['contract'](c)=='FLAT','actual contract predicate')
 oldraw=rd.read(root/'FLAT_CONTRACT01.json');old=json.loads(oldraw);rd.need({k:v for k,v in c.items() if k not in ('remote_receipt','remote_root_exit')}=={k:v for k,v in old.items() if k not in ('remote_receipt','remote_root_exit')},'only retained wrong receiver paths corrected')
 for key in ('remote_receipt','remote_root_exit'):
  p=ns['evidence'](old[key]['path']);rd.need(not os.path.lexists(p),'retained original path refusal');errors.append({'lane':i,'original_contract_sha256':R.digest(oldraw),'field':key,'actual_resolved_path':str(p),'result':'FileNotFoundError before child'})
 rd.need(c['remote_receipt']=={'path':'REMOTE_RECOVERY01.json','sha256':b['actual_remote_receipt_sha256']} and c['remote_root_exit']=={'path':'ACTUAL_ROOT_EXIT01.json','sha256':b['actual_root_exit_sha256']},'exact real receiver evidence')
 rd.need(c['request']=={'path':'REQUEST_FLAT_FINAL01.json','sha256':R.digest(qr)} and c['flat_release']=={'path':'FLAT_RELEASE01.json','sha256':R.digest(ir)},'outer binds actual full request/release')
 for key in ('selection','request','remote_receipt','remote_root_exit','selected_mode_profile','flat_release'):
  ref=c[key];p=(ns['evidence'] if key in ('selection','remote_receipt','remote_root_exit','selected_mode_profile') else ns['local'])(ref['path']);rd.need(ns['read'](p,ref['sha256'])==rd.read(p,ref['sha256']),'actual caller evidence read target')
 rd.need(c['helpers']==earlier['lanes'][i]['helpers'] and len(c['helpers'])==13,'all accepted helper pins unchanged')
 for n,h in c['helpers'].items():rd.read(root/n,h)
 rd.need(rd.read(root/'recover01.py')==generated['receiver'].encode() and rd.read(root/'receipt01.py')==generated['receipt'].encode(),'entire generated receiver/receipt body')
 rd.need(rd.read(remote/'SELECTED_BODIES01.json',c['selection']['sha256'])==generated['selection_body'] and c['main_commit']==q['commit']=='5245e7550ea08325bb521ca450d2c8a5e4452dc9','actual canonical committed selection')
 expected={'BUNDLE_FLAT_INTENT01.json','BUNDLE_FLAT_RECOVERY01.json','BUNDLE_FLAT_FAILED01.json','LANE_RECOVERY01.json'}|{'flat-piece-%03d'%j for j in O.LANES[i]};rd.need(set(c['fresh_names'])==expected and len(c['fresh_names'])==len(expected),'entire fixed fresh scope')
 prefix='ROOT_OUTCOME_LANE%02d_CANONICAL02_FLAT02'%(i+1)
 for n in expected|{prefix+x for x in ('_INTENT.json','_SPAWN.json','.stdout','.stderr','_EXIT.json')}:rd.need(not os.path.lexists(root/n),'unused one-use entry/output')
 rd.need(root.resolve()==root and stat.S_IMODE(root.stat().st_mode)==0o700,'owned root private/canonical');census=O.W.census(root);ns['rejoin']()
 release={'schema_version':1,'decision':'ACCEPTED_EXACT_ONE_USE_OUTCOME_LANE%02d_CANONICAL02_FLAT'%(i+1),'contract_sha256':R.digest(cr),'caller_sha256':R.digest(caller),'numerical_authority':False};releases.append(release);results.append({'lane':i,'root':str(root),'contract_file':'FLAT_CONTRACT02.json','contract_sha256':R.digest(cr),'request_sha256':R.digest(qr),'request_core_sha256':O.request_core_sha256(q),'caller_sha256':R.digest(caller),'inner_release_sha256':R.digest(ir),'sampled_census':census,'actual_receiver_paths_pass':True,'fresh_outputs':True})
# Single bounded process inventory; no invocation or synthetic Popen.
for p in Path('/proc').iterdir():
 if p.name.isdigit() and int(p.name)!=os.getpid():
  try:args=ns['raw'](p/'cmdline').split(b'\0')
  except (FileNotFoundError,ProcessLookupError,PermissionError):continue
  for i in range(4):
   root=O.lane_root(i,'flat');rd.need(not any(str(root/n).encode() in args for n in ('caller01.py','restore_bundle01.py','recover01.py')),'no actual flat process already running')
rd.finish()
for i,r in enumerate(releases):R.put(HERE/('LANE%02d_OUTER_FLAT_RELEASE01.json'%(i+1)),r)
result={'schema_version':1,'decision':'ACCEPTED_EXACT_FOUR_ONE_USE_CANONICAL02_FLAT_ENTRIES_ONLY','binding_sha256':R.digest(binding_raw),'lanes':results,'retained_unused_contract01_refusals':errors,'checks':rd.checks,'read_bytes':rd.total,'source_semantics_reused':True,'watch_self_review':False,'numerical_authority':False,'actual_flat_outcome_accepted':False,'release_files':[{'path':'LANE%02d_OUTER_FLAT_RELEASE01.json'%(i+1),'sha256':R.digest(R.encode(r))} for i,r in enumerate(releases)]};R.put(HERE/'FLAT_ENTRY_READBACK01.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('lanes','retained_unused_contract01_refusals')}))
