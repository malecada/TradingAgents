"""Offline full opaque byte capture audit; no imports of research or arrays."""
import gzip,hashlib,io,json,os,pathlib,stat,subprocess,tarfile,time
ROOT=pathlib.Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');BASE=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
P=BASE/'held-consumer-post-outcome-root-capture01-2026-10-03';B=P/'bundle01';OUT=pathlib.Path(__file__).resolve().parent
FILE=4*1024**2;H=lambda b:hashlib.sha256(b).hexdigest();checks=0
def ok(v,msg):
 global checks
 if not v:raise AssertionError(msg)
 checks+=1
def read(p):
 p=pathlib.Path(p);s=p.lstat();ok(p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=FILE,'read type/path/extent')
 ok(not any(x.lower() in {'keys','apis','.env','.ssh','hf_token.txt'} or x.lower().endswith(('.key','.pem')) for x in p.parts),'protected path')
 b=p.read_bytes();ok(len(b)==s.st_size and p.stat().st_mtime_ns==s.st_mtime_ns,'stable read');return b
def js(p):return json.loads(read(p))
def enc(x):return (json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def save(n,x):
 with (OUT/n).open('x') as f:json.dump(x,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
qraw=read(P/'REQUEST01.json');q=json.loads(qraw);cr=read(B/'capture.json');c=json.loads(cr)
ok(H(qraw)=='23cf258b1f49feff79802bdfe04d0c91563ed81c6e75dfbbab0e8983b260ffe6','request exact')
ok(H(cr)=='8dda0e91ea7e70c6164139a52d96b9c056befecac28e4d86f056eb3fc3312111' and c['request_sha256']==H(qraw),'capture exact')
ok(H(enc(q['baseline']))==q['baseline_sha256']=='660a715bc4da9bfd93e4076cee4d82730301024b9fa95668c8182a48d9ac2061','original baseline')
def scan(root):
 rows=[];allocated=root.stat().st_blocks*512;logical=0
 def visit(p):
  nonlocal allocated,logical
  for child in sorted(p.iterdir()):
   st=child.lstat();rel=str(child.relative_to(root));ok(len(rows)<32768 and len(child.relative_to(root).parts)<=32 and child.resolve()==child and st.st_dev==root.stat().st_dev,'scan boundary')
   r={'path':rel,'mode':stat.S_IMODE(st.st_mode)};allocated+=st.st_blocks*512
   if stat.S_ISDIR(st.st_mode):r['kind']='directory';rows.append(r);visit(child)
   else:b=read(child);logical+=len(b);r.update(kind='file',bytes=len(b),sha256=H(b));rows.append(r)
 return_rows=None
 visit(root)
 return {'schema_version':1,'root_mode':stat.S_IMODE(root.stat().st_mode),'members':sorted(rows,key=lambda x:x['path'])},logical,allocated
summaries={};maps={};opaque={}
for kind in ('capsule','external'):
 root=pathlib.Path(q['baseline'][kind+'_root']);m=q['current_manifests'][kind];old=q['baseline'][kind+'_manifest'];maps[kind]={r['path']:r for r in m['members']}
 ok(H(enc(m))==q['current_manifest_sha256'][kind]==c['archives'][kind]['manifest_sha256'],'manifest canonical hash')
 ok(read(B/(kind+'-manifest.json'))==enc(m),'captured manifest bytes')
 ok(all(maps[kind].get(r['path'])==r for r in old['members']) and m['root_mode']==old['root_mode'],'original subset exact')
 got,logical,allocated=scan(root);ok(got==m,'full actual tree equal')
 archive=read(B/(kind+'.tar.gz'));ok(H(archive)==c['archives'][kind]['sha256'] and len(archive)==c['archives'][kind]['bytes'],'archive pin')
 original_order=[];bodies={}
 with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as tar:
  for member in tar:
   ok(member.name in maps[kind] and member.name not in original_order,'exact unique archive member');original_order.append(member.name);r=maps[kind][member.name]
   ok(member.mode==r['mode'] and member.uid==member.gid==member.mtime==0 and member.uname==member.gname=='','canonical member attributes')
   ok(member.isdir() if r['kind']=='directory' else member.isreg(),'canonical member type')
   if r['kind']=='directory':ok(member.size==0,'directory size')
   else:
    ok(member.size==r['bytes']<=FILE,'body size');f=tar.extractfile(member);body=f.read(FILE+1);f.close();ok(len(body)==r['bytes'] and H(body)==r['sha256'],'opaque archive hash');bodies[member.name]=body
 ok(original_order==[r['path'] for r in m['members']],'complete archive order')
 output=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',fileobj=output,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tar:
   for r in m['members']:
    t=tarfile.TarInfo(r['path']);t.mode=r['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0
    if r['kind']=='directory':t.type=tarfile.DIRTYPE;t.size=0;tar.addfile(t)
    else:t.size=r['bytes'];tar.addfile(t,io.BytesIO(bodies[r['path']]))
 ok(output.getvalue()==archive,'full canonical archive recompression')
 summaries[kind]={'members':len(m['members']),'regular_files':len(bodies),'logical_bytes':logical,'allocated_bytes':allocated,'archive_sha256':H(archive),'archive_bytes':len(archive),'baseline_members':len(old['members']),'canonical_recompression_exact':True};opaque[kind]=bodies
 ok(scan(root)[0]==m,'final full tree stability')
for category,prefix,pins in [('evidence','',c['evidence_sha256']),('support_bodies','support-',c['support_sha256'])]:
 for name,r in q[category].items():
  b=read(pathlib.Path(r['path']));ok(H(b)==r['sha256']==pins[name],'actual supporting origin pin');ok(read(B/(prefix+name+'.body'))==b,'captured support exact')
capture_terminal=js(P/'ACTUAL_CAPTURE_TERMINAL01.json');ok(capture_terminal['actual_exec_session']==86910 and capture_terminal['completion_tool']=='13403e' and capture_terminal['exit']==0 and capture_terminal['capture_sha256']==H(cr),'actual capture terminal')
ok(capture_terminal['actual_remote_or_flat_recovery'] is False,'no future recovery inferred')
cap=pathlib.Path(q['baseline']['capsule_root']);parent=pathlib.Path(q['baseline']['external_root']);identity=q['identity'];source=q['baseline']['source'];reg=js(cap/q['baseline']['registration']);exp=reg['experiments'][identity]
def git(*args):
 r=subprocess.run(['git','--no-optional-locks','-C',str(cap),*args],capture_output=True,timeout=30,check=True,env={**os.environ,'GIT_NO_REPLACE_OBJECTS':'1'});ok(len(r.stdout)<1024**2 and not r.stderr,'bounded offline Git');return r.stdout
ok(git('rev-parse','HEAD').decode().strip()==source,'actual current capsule source')
tree=git('ls-tree','-r','-z',source);objects={}
for part in tree.split(b'\0'):
 if part:
  info,name=part.split(b'\t');mode,kind,oid=info.decode().split();ok(kind=='blob','tracked blob');objects[name.decode()]=(mode,oid)
ok(len(objects)==246,'tracked246')
for name,(mode,oid) in objects.items():
 b=opaque['capsule'][name];ok(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid,'tracked actual archive blob OID');ok(mode==('100755' if maps['capsule'][name]['mode']&0o111 else '100644'),'tracked executable mode')
source_pins={**exp['source_files'],q['baseline']['registration']:q['baseline']['registration_sha256']};ok(len(source_pins)==205,'source-registration205')
for name,pin in source_pins.items():ok(H(opaque['capsule'][name])==pin and name in objects,'source-registration exact')
ok(len(exp['inputs'])==33,'registered inputs33')
for item in exp['inputs'].values():ok(H(opaque['capsule'][item['path']])==item['sha256'],'registered opaque input exact')
def body_json(kind,name):return json.loads(opaque[kind][name])
run='research_runs/'+identity;claim=body_json('capsule',run+'/claim.json');failed=body_json('capsule',run+'/failed.json')
ok(failed['claim_sha256']==H(opaque['capsule'][run+'/claim.json']) and failed['status']=='failed','actual failed claim join')
ok(claim['source']==source and claim['effective_attempt_budget']==6 and claim['inputs']==exp['inputs'],'actual source/allowance/input claim')
ok(run+'/complete.json' not in maps['capsule'],'complete absent')
for output,pin in failed['output_sha256'].items():ok(H(opaque['capsule'][run+'/outputs/'+output])==pin,'failed output denominator')
ledger=body_json('capsule',run+'/outputs/cell-ledger.json');ok([x['status'] for x in ledger]==['failed','unavailable'],'failed/unavailable cell dispositions')
guard='research_artifacts/onchain-paper-replication-2026-09-24/runs/'+identity+'/guard/'
g=body_json('capsule',guard+'final.json');child=body_json('capsule',guard+'child_exit.json')
ok(g['child_exit_code'] is None and g['cleanup_verified'] is False,'original null false preserved')
root_terminal=js(B/'terminal.body');cleanup=js(B/'cleanup.body')
ok(root_terminal['actual_guard_final_sha256']==H(opaque['capsule'][guard+'final.json']) and root_terminal['actual_failed_run_sha256']==H(opaque['capsule'][run+'/failed.json']),'root actual receipts join')
ok(root_terminal['separate_actual_child_exit_code']==125 and root_terminal['actual_root_exit']==1 and root_terminal['native_result']=='timeout','original failed result')
ok(len(cleanup['actual_pid_absence'])==10 and all(cleanup['actual_pid_absence'].values()) and not pathlib.Path(cleanup['actual_cgroup']).exists(),'additive cleanup closed')
ok(all(not pathlib.Path('/proc',pid).exists() for pid in cleanup['actual_pid_absence']),'current exact ten PIDs absent')
hist=[]
for name in reg['experiments']:
 k='research_runs/'+name
 if k+'/claim.json' in maps['capsule']:
  cl=body_json('capsule',k+'/claim.json');fl=body_json('capsule',k+'/failed.json');ok(fl['claim_sha256']==H(opaque['capsule'][k+'/claim.json']) and k+'/complete.json' not in maps['capsule'],'historical original failed join');hist.append(name)
ok(len(hist)==5,'five actual failed claims')
dependent='original-import-held-publication-failure-20261003-01'
ok(not any(('research_runs/'+dependent) in n for n in maps['capsule']) and not any(('attempt/'+dependent) in n for n in maps['external']),'dependent absent')
ok(sum(x['logical_bytes'] for x in summaries.values())<128*1024**2 and sum(x['allocated_bytes'] for x in summaries.values())<128*1024**2,'whole supplied tree bounded')
save('CAPTURE_RESULTS01.json',{'schema_version':1,'assertions':checks,'capture_sha256':H(cr),'request_sha256':H(qraw),'trees':summaries,'source_join':{'source':source,'source_and_registration':205,'tracked':246,'opaque_inputs':33},'original_failed_claims':hist,'ledger':ledger,'original_guard':{'child_exit_code':g['child_exit_code'],'cleanup_verified':g['cleanup_verified']},'separate_child_receipt':child,'actual_capture_exit':0,'actual_remote_recovery_verified':False,'actual_flat_recovery_verified':False,'credentials_read':False,'numerical_imports':False,'runtime_or_scientific_completion':False,'pid_cgroup_observation_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'fd_visibility':'No independent universal FD census; prior closed-tree scope correction remains applicable'})
print(json.dumps({'checks':checks,'trees':summaries,'source205_inputs33_tracked246':True,'actual_remote_or_flat':False}))
