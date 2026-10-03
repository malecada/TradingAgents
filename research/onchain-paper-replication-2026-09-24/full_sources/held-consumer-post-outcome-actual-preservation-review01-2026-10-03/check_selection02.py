"""Exact offline selected-file preflight; never invokes transport."""
import ast,hashlib,json,os,pathlib,shutil,stat,subprocess,time
ROOT=pathlib.Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');BASE=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources';OUT=pathlib.Path(__file__).resolve().parent
REMOTE=BASE/'held-consumer-post-outcome-root-remote-recovery01-2026-10-03';CAPTURE=BASE/'held-consumer-post-outcome-root-capture01-2026-10-03'
COMMIT='a000e04f692d07d826fdc6cf1800b4818489f7e3';H=lambda b:hashlib.sha256(b).hexdigest();checks=0
def ok(v,msg):
 global checks
 if not v:raise AssertionError(msg)
 checks+=1
def read(p):
 s=p.lstat();ok(p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2,'regular bounded source')
 b=p.read_bytes();ok(len(b)==s.st_size and p.stat().st_mtime_ns==s.st_mtime_ns,'stable body');return b
def git(*args):
 r=subprocess.run(['git','--no-optional-locks','-C',str(ROOT),*args],capture_output=True,timeout=30,check=True,env={**os.environ,'GIT_NO_REPLACE_OBJECTS':'1'});ok(len(r.stdout)<1024**2 and not r.stderr,'bounded offline Git');return r.stdout
selraw=read(REMOTE/'SELECTED_BODIES01.json');s=json.loads(selraw);pin=H(selraw)
ok(pin=='fd3dfaf31b0ce9e3498fdf8ccfb7723955e69ab8b1f80bde5c615601ff535fc1','exact external selection pin')
ok((json.dumps(s,sort_keys=True,indent=2)+'\n').encode()==selraw and s['remote_commit']==COMMIT,'canonical selection')
rows=s['rows'];names=[r['path'] for r in rows];ok(len(rows)==323 and len(rows)<=506 and names==sorted(set(names)),'finite exact unique order')
ok(sum(r['bytes'] for r in rows)==10920229<64*1024**2 and all(type(r['bytes'])is int and 0<=r['bytes']<=4*1024**2 for r in rows),'byte limits')
ok(s['estimated_success_git_operations']==11+2*len(rows)==657<1024,'corrected inherited operation constraint')
for n in names:
 p=pathlib.PurePosixPath(n);ok(n.startswith('research/') and p.as_posix()==n and '..' not in p.parts and not p.is_absolute(),'literal selected research path')
 ok(not any(c.lower() in {'keys','apis','.env','.ssh','hf_token.txt'} or c.lower().endswith(('.pem','.key')) for c in p.parts),'no protected source')
tree=git('ls-tree','-r','-z',COMMIT,'--',*names);objects={}
for raw in tree.split(b'\0'):
 if not raw:continue
 left,n=raw.split(b'\t');mode,kind,oid=left.decode().split();objects[n.decode()]=(mode,kind,oid)
ok(set(objects)==set(names),'nonrecursive exact file selection no directory expansion')
readback=[]
for r in rows:
 b=read(ROOT/r['path']);mode,kind,oid=objects[r['path']]
 ok(kind=='blob' and mode in ('100644','100755'),'selected actual regular Git mode')
 ok(len(b)==r['bytes'] and H(b)==r['sha256'],'actual selected bytes')
 ok(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid,'actual Git blob OID join')
 ok(mode==('100755' if (ROOT/r['path']).stat().st_mode&0o111 else '100644'),'local executable mode join')
 readback.append({**r,'git_mode':mode,'git_oid':oid,'local_mode':stat.S_IMODE((ROOT/r['path']).stat().st_mode)})
parent=git('rev-parse',COMMIT+'^').decode().strip();diff=git('diff-tree','--no-commit-id','--name-only','-r','-z',COMMIT);changed=set(x.decode() for x in diff.split(b'\0') if x)
excluded={r['path'] for r in s['excluded_symlink_witnesses']};ok(len(excluded)==3 and changed==set(names)|excluded,'all changed regular paths and exactly3 excluded links')
linkmeta=git('ls-tree','-r','-z',COMMIT,'--',*sorted(excluded));links=[]
for row in linkmeta.split(b'\0'):
 if not row:continue
 left,n=row.split(b'\t');mode,kind,oid=left.decode().split();name=n.decode();p=ROOT/name
 ok(mode=='120000' and kind=='blob' and p.is_symlink(),'historical symlink retained Git/current')
 body=os.readlink(p).encode();ok(hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==oid,'symlink own opaque target-string OID without following')
 links.append({'path':name,'git_mode':mode,'git_oid':oid,'target_string_bytes':len(body),'target_string_sha256':H(body),'restored':False})
required={}
def need(p,role,pin=None):
 n=str(p.relative_to(ROOT));ok(n in names,'required selection membership '+role);b=read(p)
 if pin is not None:ok(H(b)==pin,'required pin '+role)
 required[n]={'role':role,'sha256':H(b),'bytes':len(b)}
q=json.loads(read(CAPTURE/'REQUEST01.json'));capture=json.loads(read(CAPTURE/'bundle01/capture.json'))
need(CAPTURE/'REQUEST01.json','exact request','23cf258b1f49feff79802bdfe04d0c91563ed81c6e75dfbbab0e8983b260ffe6')
need(CAPTURE/'ACTUAL_CAPTURE_TERMINAL01.json','actual capture terminal')
need(CAPTURE/'bundle01/capture.json','actual capture','8dda0e91ea7e70c6164139a52d96b9c056befecac28e4d86f056eb3fc3312111')
for name in ('capsule','external'):
 need(CAPTURE/'bundle01'/f'{name}.tar.gz','complete current '+name+' archive',capture['archives'][name]['sha256'])
 need(CAPTURE/'bundle01'/f'{name}-manifest.json','current '+name+' typed metadata',capture['archives'][name]['manifest_sha256'])
for category,prefix in [('support_bodies','support-'),('evidence','')]:
 for n,v in q[category].items():
  need(CAPTURE/'bundle01'/(prefix+n+'.body'),category+':'+n,v['sha256'])
  ok(read(pathlib.Path(v['path']))==read(CAPTURE/'bundle01'/(prefix+n+'.body')),'original duplicate exact without whole historical directory requirement')
need(BASE/'held-consumer-post-outcome-closed-review01-2026-10-03/CLOSED_TREE_REVIEW01.json','genuine closed-tree decision','ec1d9736bf4a3f5be400e8d477530a74439ea6274abebb85a2031a0c541c7c43')
for name in ['post_outcome01.py','recovery04.py','bounded_git01.py','owned_io.py']:need(BASE/'held-consumer-post-outcome-archive-preparation01-2026-10-03'/name,'actual capture source dependency')
need(REMOTE/'recover_post_outcome01.py','exact reviewed transport source','4d16cb824ca1e301cc0cc80303966806011bd8a1c8f2eb1bbebfc1a65dac4284')
need(OUT/'INITIAL_REVIEW01.md','independent initial review','1f5c66f0c6c22868963fcf5076e14997b00bc2ef41be8181059508b02ebeb449')
need(OUT/'MANIFEST01.json','immutable initial review manifest','139957bcf1a3a35972a7b365bb1f77cc2048ec194c75d06bf1749dc78ceed302')
new=ast.parse(read(REMOTE/'recover_post_outcome01.py'));old=ast.parse(read(BASE/'held-consumer-final-released-scope-root-remote-recovery01-2026-10-03/recover_final03.py'))
for name in ['git','write']:
 n=next(x for x in new.body if isinstance(x,ast.FunctionDef) and x.name==name);o=next(x for x in old.body if isinstance(x,ast.FunctionDef) and x.name==name);ok(ast.dump(n,include_attributes=False)==ast.dump(o,include_attributes=False),'unchanged owned IO '+name)
for name in ['fresh-post-outcome01.git','selected','REMOTE_RECOVERY01.json','FAILED01.json']:ok(not os.path.lexists(REMOTE/name),'actual transport namespace absent '+name)
free=shutil.disk_usage(REMOTE).free;ok(free>=10*1024**3,'actual current10GiB floor')
ok(H(read(REMOTE/'SELECTED_BODIES01.json'))==pin,'final selection stability')
result={'schema_version':1,'decision':'ACCEPTED_EXACT_SELECTION_PREFLIGHT_ONLY','selection_sha256':pin,'commit':COMMIT,'commit_parent':parent,'assertions':checks,'count':len(rows),'logical_bytes':sum(r['bytes'] for r in rows),'estimated_operations':657,'required_complete_scope':required,'exact_rows':readback,'excluded_committed_symlinks':links,'local_free_bytes':free,'observed_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'actual_remote_push_or_HEAD_verified':False,'actual_transport_executed':False,'actual_flat_recovery_verified':False,'selection_and_this_review_created_after_selected_commit':True,'runtime_store_or_POSIX_recovery':False}
with (OUT/'SELECTION_CHECKS02.json').open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'files':323,'bytes':10920229,'calls':657,'required_roles':len(required),'excluded_links':3,'free':free,'remote_verified':False}))
