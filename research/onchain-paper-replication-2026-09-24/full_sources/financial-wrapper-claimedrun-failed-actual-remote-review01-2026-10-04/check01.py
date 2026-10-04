import ast,hashlib,json,os,stat,subprocess,time
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent;ROOT=F.parents[2];T=F/'financial-wrapper-claimedrun-failed-remote01-2026-10-04';H=F/'heartbeat-root-checkpoint10-2026-10-04';checks=[];sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def pinned(p,h):
 b=p.read_bytes();ok(sha(b)==h,'pin '+str(p));return b
receipt=pinned(T/'REMOTE_RECOVERY01.json','8f294d8140030deb66b0db32481247019a0b86d279b54b965ee3d19bff87d268');r=json.loads(receipt)
selection=pinned(T/'SELECTED_BODIES01.json','716a22930e6671dea25e16224c98ec352dcbd5674c961d75b5f612e54f10a928');q=json.loads(selection);commit='fab9462e111fcf12a0be0e37e50b72a80cabe4bf'
for name,prefix in [('financial-wrapper-claimedrun-failed-preservation-source-review01-2026-10-04','0c858a94'),('financial-wrapper-claimedrun-failed-selection-release-review01-2026-10-04','c252f9e3')]:
 scope=F/name;mf=scope/'MANIFEST01.json';m=mf.read_bytes();ok(sha(m).startswith(prefix),'accepted scope seal');rows=json.loads(m)['members'];ok({p.relative_to(scope).as_posix() for p in scope.rglob('*') if p!=mf}=={x['path'] for x in rows}-{'.'},'complete review membership')
 for x in rows:
  p=scope/x['path'];s=p.lstat();mode=int(x['mode'],8) if isinstance(x['mode'],str) else x['mode'];ok(stat.S_IMODE(s.st_mode)==mode,'literal prior mode')
  if x['kind']=='file':ok(stat.S_ISREG(s.st_mode) and len(p.read_bytes())==x['bytes'] and sha(p.read_bytes())==x['sha256'],'prior body')
  else:ok(stat.S_ISDIR(s.st_mode),'prior directory')
 (D/(name+'.manifest.json')).write_bytes(m)
source=pinned(T/'recover01.py','b1b6618949cacbe5db7230ca27b7b9cb06c356f95d4fbecc3df6d013b3acd9a9');pinned(T/'restore01.py','1cdfe7bfaf9001ec7a0ea27925f48a3d8e371d290d2da807de6e782aab244440')
inv=json.loads((T/'SOURCE_INVERSE01.json').read_bytes());s=source.decode()
for x in reversed(inv['changes']):ok(x['replacement'] in s,'inverse replacement');s=s.replace(x['replacement'],x['original'])
ok(s.encode()==pinned(Path(inv['predecessor']),inv['predecessor_sha256']),'full inherited transport inverse')
required=ast.literal_eval(next(n.value for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REQUIRED' for t in n.targets)))
ok(q['rows']==[dict(path=k,**v) for k,v in sorted(required.items())],'exact eight required rows');ok(len(q['rows'])==r['selected_count']==8 and sum(x['bytes'] for x in q['rows'])==r['selected_logical_bytes']==2594804,'count and byte denominator')
ok(r['remote_commit']==q['remote_commit']==commit and r['selection_sha256']==sha(selection),'commit selection join')
bare=Path(r['fresh_git_root']);ok(bare==T/'fresh-claimedrun-failed-source339-01.git' and bare.resolve()==bare,'fixed canonical bare')
ok((bare/'FETCH_HEAD').read_text().split()[0]==commit,'actual FETCH_HEAD')
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_NO_REPLACE_OBJECTS='1',GIT_ALLOW_PROTOCOL='',GIT_TERMINAL_PROMPT='0');calls=[]
def git(root,args):
 p=subprocess.run(['git','--no-replace-objects','--git-dir',str(root),*args],env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
 ok(p.returncode==0 and not p.stderr and len(p.stdout)<=4*1024**2,'offline bounded Git '+args[0]);calls.append({'root':str(root),'args':args,'bytes':len(p.stdout),'sha256':sha(p.stdout),'exit':p.returncode});return p.stdout
paths=[x['path'] for x in q['rows']];tree=git(bare,['ls-tree','-z',commit,'--',*paths]);objects={}
for entry in tree.rstrip(b'\0').split(b'\0'):
 a,b=entry.split(b'\t');objects[b.decode()]=a.decode().split()
ok(set(objects)==set(paths),'exact fetched tree entries')
main_tree=git(ROOT/'.git',['ls-tree','-z',commit,'--',*paths]);ok(main_tree==tree,'local committed vs fresh external tree')
selected=[]
for x,y in zip(q['rows'],r['selected_blobs'],strict=True):
 name=x['path'];mode,kind,oid=objects[name];ok(y==dict(x,git_mode=mode,git_object=oid),'receipt full object join');ok(mode=='100644' and kind=='blob','Git mode/type');p=T/'selected'/name;st=p.lstat();body=p.read_bytes();ok(stat.S_ISREG(st.st_mode) and stat.S_IMODE(st.st_mode)==0o600 and st.st_nlink==1,'private selected literal mode/type');ok(len(body)==x['bytes'] and sha(body)==x['sha256'],'saved selected body');ok(hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==oid,'authentic Git blobOID');ok(git(bare,['cat-file','blob',oid])==body==(ROOT/name).read_bytes(),'fresh bare saved current byte equality');selected.append(dict(y,literal_mode=stat.S_IMODE(st.st_mode)))
ok({p.relative_to(T/'selected').as_posix() for p in (T/'selected').rglob('*') if p.is_file()}==set(paths),'no extra saved body')
operations=r['operations'];ok(len(operations)==27==11+2*8 and r['elapsed_seconds']<600 and r['free_bytes']>=10*1024**3,'actual finite operation/time/floor')
for op in operations:ok(op['exit']==0 and op['cleanup_failures']==[] and op['seconds']<60,'successful drained bounded original operation')
pids={x['pid'] for x in operations};ok(all(not Path('/proc',str(p)).exists() for p in pids),'all original Git PIDs currently absent');groups=[]
for p in Path('/proc').iterdir():
 if p.name.isdecimal():
  try:parts=(p/'stat').read_text().rsplit(')',1)[1].split()
  except (FileNotFoundError,ProcessLookupError,PermissionError):continue
  if int(parts[2]) in pids:groups.append(int(p.name))
ok(not groups,'no current process in original Git groups')
exitp=H/'ROOT_FAILED_REMOTE01_EXIT.json';exitraw=exitp.read_bytes();ok(sha(exitraw).startswith('7071b601'),'Root actual exit pin');e=json.loads(exitraw);ok(e['actual_exit_code']==0 and e['exec_session_id']==29504 and e['launch_tool']=='233ede' and e['actual_completion_tool']=='4677b4' and e['remote_receipt_sha256']==sha(receipt),'actual tool and receipt join')
for key,name in [('root_intent_sha256','ROOT_FAILED_REMOTE01_INTENT.json'),('root_stdout_sha256','ROOT_FAILED_REMOTE01.stdout'),('root_stderr_sha256','ROOT_FAILED_REMOTE01.stderr')]:
 p=H/name
 if not p.exists():
  matches=[x for x in H.glob('ROOT_FAILED_REMOTE01*') if x.is_file() and sha(x.read_bytes())==e[key]];ok(len(matches)==1,'exact retained '+key);p=matches[0]
 ok(sha(p.read_bytes())==e[key],'Root actual retained '+key);(D/p.name).write_bytes(p.read_bytes())
for name in ['flat-capsule01','flat-parent01','flat-root01','FLAT_INTENT01.json','FLAT_RECOVERY01.json']:ok(not os.path.lexists(T/name),'flat still absent '+name)
for n in ['REMOTE_RECOVERY01.json','SELECTED_BODIES01.json','SOURCE_INVERSE01.json']:(D/n).write_bytes((T/n).read_bytes())
(D/'ROOT_FAILED_REMOTE01_EXIT.json').write_bytes(exitraw)
(D/'READBACK01.json').write_text(json.dumps({'checks':len(checks),'names':checks,'selected':selected,'offline_git_calls':calls,'network_enabled':False,'actual_original_operations':27,'original_pids':sorted(pids),'current_group_members':groups,'pid_start_ticks_not_observed':True,'fresh_flat_recovery':False,'observation_unix':time.time()},indent=2)+'\n');print(json.dumps({'checks':len(checks),'selected':len(selected),'local_offline_git_calls':len(calls)}))
