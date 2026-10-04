from pathlib import Path
import sys,json,os,subprocess,hashlib,copy
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import recover01 as R
n=0
def ok(v):
 global n
 assert v;n+=1
def refuses(fn):
 try:fn()
 except (ValueError,RuntimeError):ok(True)
 else:raise AssertionError('refusal absent')
# Opaque local-only Git; no configured network URL, no original repositories.
t=D/'tiny02';t.mkdir();origin=t/'origin.git';dest=t/'received.git';ok(R.git(['init','--bare',str(origin)]).startswith(b'Initialized'))
blob=b'bounded opaque engineering blob\n';p=subprocess.run(['git','--git-dir',str(origin),'hash-object','-w','--stdin'],input=blob,capture_output=True,check=True);oid=p.stdout.decode().strip();ok(R.git(['init','--bare',str(dest)]).startswith(b'Initialized'));R.git(['fetch','--no-tags',str(origin),oid],dest);ok(R.git(['cat-file','blob',oid],dest)==blob);ok(all(x['actual_child_limits']['fsize']==[4194304,4194304] and x['cleanup_failures']==[] and x['exit']==0 for x in R.CALLS))
# Actual fixed file bound is refused on an owned sparse metadata-only negative.
bad=t/'oversize';fd=os.open(bad,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.ftruncate(fd,4194305);os.close(fd);refuses(lambda:R.W.census(t));# retained negative is outside a newly created tiny census root below
safe=D/'safe02';safe.mkdir();(safe/'opaque').write_bytes(b'abc');a=R.W.census(safe);ok(a['logical_bytes']==3);(safe/'more').write_bytes(b'x');b=R.W.census(safe);ok(b['logical_bytes']==4 and b['members']==a['members']+1)
# Pure bounded policy aliases exercised on owned scope only, no actual64MiB claim.
policy=dict(R.W.POLICY)
for key,value in [('logical',3),('allocated',0),('members',1),('depth',-1),('sample_seconds',0),('floor',10**30)]:
 R.W.POLICY[key]=value
 try:refuses(lambda:R.W.census(safe))
 finally:R.W.POLICY.clear();R.W.POLICY.update(policy)
for p in R.CALLS:ok(not Path('/proc',str(p['pid'])).exists())
# Flat source refuses original81-count semantics after accepted unique-blob fetch change.
import ast
inv=json.loads((D/'SOURCE_INVERSE01.json').read_bytes())
for name,v in inv.items():
 s=(D/name).read_text()
 for e in reversed(v['edits']):ok(s.count(e['new'])==1);s=s.replace(e['new'],e['old'])
 ok(s==(D/('ORIGINAL_'+name)).read_text());ok(ast.dump(ast.parse(s))==ast.dump(ast.parse((D/('ORIGINAL_'+name)).read_text())))
(D/'CHECKS01.json').write_text(json.dumps({'checks':n,'local_git_calls':R.CALLS,'observed_samples':R.WATCHES,'fixed_policy':policy,'actual_external_or_Root_entry':False,'sparse_negative_preserved':str(bad)},indent=2)+'\n');print(n)
