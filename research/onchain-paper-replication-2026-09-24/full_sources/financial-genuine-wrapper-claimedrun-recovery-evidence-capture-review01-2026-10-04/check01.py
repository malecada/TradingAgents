import ast,gzip,hashlib,io,json,os,stat,sys,tarfile
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;P=F/'financial-genuine-wrapper-root-claimedrun-recovery-evidence-capture01-2026-10-04';U=F/'held-consumer-final-recovery-preparation04-2026-10-03';sys.path.insert(0,str(U));import recovery04 as a
sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):assert v,m;checks.append(m)
def read(p):return a.read(p.parent,p.name)
for n,pin in [('recovery04.py','b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a'),('owned_io.py','09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb'),('bounded_git01.py','db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f')]:ck(sha(read(U/n))==pin,'accepted exact primitive')
t=ast.parse(read(F/'held-consumer-final-released-scope-capture-review01-2026-10-03/check01.py'));exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('decode','recode')],type_ignores=[]),'<independent bounded raw framing>','exec'))
c=json.loads(read(P/'CAPTURE01.json'));ck(set(c['records'])=={'preparation02','review02','preparation03','review03'},'exact four roles');results={};seals=0
for role,info in c['records'].items():
 root=Path(info['original_root']);m=json.loads(read(P/(role+'-manifest.json')));raw=read(P/(role+'.tar.gz'));ck(info['archive']=={'bytes':len(raw),'sha256':sha(raw),'manifest_sha256':sha(read(P/(role+'-manifest.json')))},'exact actual archive receipt chain');ck(a.scan(root)==m,'whole original current before');bodies,framing=decode(raw,m);ck(recode(m,bodies)==raw,'whole canonical compressed inverse');by={r['path']:r for r in m['members']}
 for r in m['members']:
  p=root/r['path'];s=p.lstat();ck(stat.S_IMODE(s.st_mode)==r['mode'],'literal archived original mode')
  if r['kind']=='file':ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and read(p)==bodies[r['path']],'every opaque original body')
  else:ck(stat.S_ISDIR(s.st_mode),'original directory')
 seal=info['original_seal'];ck(sha(bodies[seal['path']])==seal['sha256'],'actual complete frozen original seal');doc=json.loads(bodies[seal['path']]);ck({r['path'] for r in doc['members']}|{seal['path']}==set(by),'whole frozen original closure no copied reference substitution')
 for r in doc['members']:
  v=by[r['path']];mode=int(r['mode'],8) if isinstance(r['mode'],str) else r['mode'];ck(r['kind']==v['kind'] and mode==v['mode'],'every seal type/mode')
  if r['kind']=='file':ck(r['bytes']==v['bytes'] and r['sha256']==v['sha256'],'every sealed opaque body')
  seals+=1
 ck(a.scan(root)==m,'whole original current after');ck(info['members']==len(m['members']) and info['regular_bodies']==sum(r['kind']=='file' for r in m['members']),'actual full denominator');results[role]={'archive':info['archive'],'members':info['members'],'regular_bodies':info['regular_bodies'],'logical_bytes':sum(r.get('bytes',0) for r in m['members']),'seal':seal,'framing':framing}
ck(c['observed_pid']==431674 and c['observed_start_ticks']=='15745332','original capture recorded PID/ticks');ck(not Path('/proc/431674').exists(),'current original recorded PID absent');ck(c['disk_free_after_bytes']>=10*1024**3 and c['new_claim_or_native'] is False and c['actual_external_recovery'] is False and c['actual_source339_flat'] is False,'scope/floor exclusions remain')
# End-of-review current membership of all four originals, independently of sequential capture order.
for role,info in c['records'].items():ck(a.scan(Path(info['original_root']))==json.loads(read(P/(role+'-manifest.json'))),'all four full current scopes at final observation')
ck(not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules),'no research/numerical import')
x={'schema_version':1,'decision':'ACCEPTED_ACTUAL_COMPLETE_FOUR_RECOVERY_PREPARATION_REVIEW_LOCAL_CAPTURES','capture_sha256':sha(read(P/'CAPTURE01.json')),'caller_sha256':sha(read(P/'CAPTURE01.py')),'checks':len(checks),'complete_sealed_member_joins':seals,'roles':results,'total_typed_members':sum(r['members'] for r in results.values()),'total_regular_bodies':sum(r['regular_bodies'] for r in results.values()),'observed_original_pid':431674,'observed_original_start_ticks':'15745332','current_original_pid_absent':True,'original_process_group_history':'unrecorded; no inference','reported_tool':{'session':47856,'start':'1a7997','completion':'951f63','exit':0,'provenance':'Root message; separate persisted terminal absent at check start'},'generic_Git_witness_graphs_are_ResearchRun_claims':False,'source339_flat_recovery':False,'external_recovery':False,'numerical_authority':False};(O/'READBACK01.json').write_text(json.dumps(x,sort_keys=True,indent=2)+'\n');print(json.dumps({'checks':len(checks),'typed':x['total_typed_members'],'files':x['total_regular_bodies']}))
