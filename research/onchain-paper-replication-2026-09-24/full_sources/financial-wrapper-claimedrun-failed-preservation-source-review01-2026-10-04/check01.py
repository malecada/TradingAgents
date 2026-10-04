import ast,hashlib,io,json,os,stat,sys,tarfile
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent;REPO=F.parents[2];C=F/'financial-wrapper-claimedrun-failed-capture01-2026-10-04';T=F/'financial-wrapper-claimedrun-failed-remote01-2026-10-04';P=F/'financial-batch-output-genuine-byte-bridge-preparation03-2026-10-04';sys.path.insert(0,str(P));import recovery04 as R
sha=lambda b:hashlib.sha256(b).hexdigest()
checks=[];roles=[]
def ok(v,msg):
 assert v,msg
 checks.append(msg)
cap=json.loads((C/'CAPTURE01.json').read_bytes());ok(sha((C/'CAPTURE01.json').read_bytes())=='08f69b601770c81572e5223f1f5cdec21e2c48072ba86394255b0c5bcddc9ae1','capture pin')
ok(sha((P/'recovery04.py').read_bytes())=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','R4 original pin')
def inventory(root,exclude_git=False,only=None):
 rows=[]
 def walk(path,rel):
  for p in sorted(path.iterdir()):
   n=p.name if not rel else rel+'/'+p.name
   if not rel and exclude_git and n=='.git':continue
   if not rel and only is not None and n not in only:continue
   s=p.lstat();r={'path':n,'mode':stat.S_IMODE(s.st_mode)}
   if stat.S_ISDIR(s.st_mode):r['kind']='directory';rows.append(r);walk(p,n)
   else:
    ok(stat.S_ISREG(s.st_mode)and s.st_nlink==1 and p.resolve()==p,'ordinary opaque source '+n)
    raw=R.read(root,n);r.update(kind='file',bytes=len(raw),sha256=sha(raw));rows.append(r)
 walk(root,'');return sorted(rows,key=lambda r:r['path'])
for role,scope in cap['scopes'].items():
 mp=C/(role.upper()+'_MANIFEST01.json');m=json.loads(mp.read_bytes());snapshot=Path(scope['snapshot']);origin=Path(scope['origin']);archive=C/('complete-'+role+'01.tar.gz');raw=archive.read_bytes()
 ok(R.encode(m)==mp.read_bytes()and sha(mp.read_bytes())==scope['manifest_sha256'],'canonical manifest '+role)
 R.validate(m);ok(R.scan(snapshot)==m,'whole snapshot '+role)
 original=inventory(origin,scope['git_directory_excluded'],{r['path']for r in m['members']}if role=='root'else None)
 ok(original==m['members'],'full original member-byte-mode join '+role)
 ok(len(raw)==scope['archive']['bytes']and sha(raw)==scope['archive']['sha256'],'archive actual pin '+role)
 ok(len(m['members'])==scope['members']and sum(r['kind']=='file'for r in m['members'])==scope['regular_bodies']and sum(r.get('bytes',0)for r in m['members'])==scope['regular_bytes'],'exact denominators '+role)
 members=list(R.framed_members(raw));ok(len(members)==len(m['members']),'raw bounded framing '+role)
 for (n,t,body),row in zip(members,m['members']):
  ok(n==row['path']and t.mode==row['mode']and t.uid==t.gid==0 and t.mtime==0 and t.uname==t.gname=='','canonical header '+role+'/'+n)
  ok((t.isdir()and row['kind']=='directory'and body==b'')or(t.isfile()and row['kind']=='file'and len(body)==row['bytes']and sha(body)==row['sha256']),'opaque archived body '+role+'/'+n)
 sink=io.BytesIO();R.tar_stream(snapshot,m,sink);ok(sink.getvalue()==raw,'complete canonical gzip/TAR reencoding '+role)
 ok(R.scan(snapshot)==m and inventory(origin,scope['git_directory_excluded'],{r['path']for r in m['members']}if role=='root'else None)==m['members'],'second stable complete scope '+role)
 roles.append({'role':role,'origin':str(origin),'origin_root_mode':stat.S_IMODE(origin.stat().st_mode),'snapshot_root_mode':m['root_mode'],'archive_sha256':sha(raw),'manifest_sha256':sha(mp.read_bytes()),'members':len(members),'regular_bodies':scope['regular_bodies'],'bytes':scope['regular_bytes'],'canonical_equal':True})
source=(T/'recover01.py').read_bytes();inverse=json.loads((T/'SOURCE_INVERSE01.json').read_bytes());old=Path(inverse['predecessor']).read_bytes();ok(sha(source)==inverse['source_sha256']=='b1b6618949cacbe5db7230ca27b7b9cb06c356f95d4fbecc3df6d013b3acd9a9','new source pin');ok(sha(old)==inverse['predecessor_sha256']=='0b397ccd0a014f60a414ce79d67dfd53c58a0fb61ca616a6576cc43da4bbf0aa','original accepted source pin')
made=old.decode()
for change in inverse['changes']:
 ok(made.count(change['original'])==1,'unique literal substitution');made=made.replace(change['original'],change['replacement'])
ok(made.encode()==source,'whole literal inverse')
# Extract only pure local validators/reducer/write; never main/git/entry invocation.
tree=ast.parse(source);names={'require','digest','encode','_raise_retained','write','validate_fixed_selection'};nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names];required=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='REQUIRED'for t in n.targets)))
ns={'os':os,'Path':Path,'hashlib':hashlib,'json':json,'FILE':4*1024**2,'REQUIRED':required};exec(compile(ast.Module(body=nodes,type_ignores=[]),'exact-local-source-only','exec'),ns)
rows=[dict(path=n,**v)for n,v in sorted(required.items())];q={'remote_commit':None,'rows':rows};ns['validate_fixed_selection'](q)
ok(len(rows)==8 and sum(r['bytes']for r in rows)==2594804,'eight exact mandatory bodies')
for r in rows:ok(len((REPO/r['path']).read_bytes())==r['bytes']and sha((REPO/r['path']).read_bytes())==r['sha256'],'required body '+r['path'])
for name in ('fresh-claimedrun-failed-source339-01.git','selected','REMOTE_RECOVERY01.json','FAILED01.json'):
 ok(not os.path.lexists(T/name),'fresh unexecuted '+name)
for i in range(8):
 bad={'remote_commit':None,'rows':rows[:i]+rows[i+1:]}
 try:ns['validate_fixed_selection'](bad)
 except ValueError:checks.append('missing required refuses '+str(i))
 else:raise AssertionError('missing accepted')
for bad in [rows+rows[:1],[dict(rows[0],bytes=True)]+rows[1:],[dict(rows[0],sha256='0'*64)]+rows[1:],[dict(rows[0],path='../bad')]+rows[1:]]:
 try:ns['validate_fixed_selection']({'remote_commit':None,'rows':bad})
 except ValueError:checks.append('malformed exact local selection refused')
 else:raise AssertionError('bad accepted')
# Real O_EXCL local write and complete first fatal precedence matrix.
local=D/'tiny-write';local.mkdir();ns['write'](local/'saved',b'opaque')
try:ns['write'](local/'saved',b'other')
except FileExistsError:checks.append('existing ordinary body refused')
else:raise AssertionError('overwrite')
for a in (ValueError('a'),MemoryError('a'),SystemExit('a')):
 for b in (ValueError('b'),MemoryError('b'),SystemExit('b')):
  chosen=a if isinstance(a,MemoryError)or not isinstance(a,Exception)else b if isinstance(b,MemoryError)or not isinstance(b,Exception)else a
  try:ns['_raise_retained'](a,[b])
  except BaseException as e:ok(e is chosen,'exact first fatal identity')
ok(cap['original_parent_exit']is None and cap['actual_root_exit']==cap['actual_child_exit']==1,'original null vs actual exit1 preserved')
ok(all(r['free_bytes']>=R.FLOOR for r in cap['disk_floor_observations']),'all recorded disk floors')
outcome=F/'financial-wrapper-claimedrun-native-outcome-review01-2026-10-04/MACHINE01.json';o=json.loads(outcome.read_bytes());ok(o['spent_claims']==2 and o['highest_actual_allowance']==19 and o['original_parent_exit']is None and not o['native_checkpoint_tensor_validation'],'separate outcome metadata qualification')
(D/'READBACK01.json').write_bytes(R.encode({'checks':len(checks),'checks_detail':checks,'roles':roles,'source_sha256':sha(source),'capture_sha256':sha((C/'CAPTURE01.json').read_bytes()),'required_selection':q,'exact_git_calls_for_8':27,'outcome_machine_sha256':sha(outcome.read_bytes()),'remote_commit':None,'actual_remote':False,'actual_flat':False,'root_scope_is_six_named_files_not_whole_heartbeat_directory':True}))
print(json.dumps({'checks':len(checks),'roles':roles}))
