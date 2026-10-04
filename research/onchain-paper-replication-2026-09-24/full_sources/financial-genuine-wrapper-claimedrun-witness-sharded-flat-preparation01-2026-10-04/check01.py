import ast,copy,hashlib,json,os,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import restore_witness01 as M
R=M.R;checks=[]
def ok(v,n):assert v,n;checks.append(n)
def refuse(fn,n):
 try:fn()
 except (ValueError,KeyError,TypeError,OSError):ok(True,n)
 else:raise AssertionError(n)
s=(H/'restore_witness01.py').read_text();x=s
for e in reversed(json.loads((H/'INVERSE01.json').read_bytes())['edits']):ok(x.count(e['new'])==e['count'],'inverse occurrence');x=x.replace(e['new'],e['old'])
o=(H/'original-restore_sharded01.py').read_text();ok(x==o and ast.dump(ast.parse(x))==ast.dump(ast.parse(o)),'completebyteASTinverse')
for n,pin in M.PINS.items():ok(R.digest(R.read(H,n))==pin,'exact source '+n)
# Actual capture metadata authentication only, no actual restoration.
C=H.parent/'financial-genuine-wrapper-root-claimedrun-sharded-witness-capture02-2026-10-04';prefix=str(C.relative_to(Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')))
def ref(n):b=R.read(C,n);return {'path':prefix+'/'+n,'bytes':len(b),'sha256':R.digest(b)}
m=json.loads(R.read(C,'union-manifest.json'));q={'schema_version':1,'remote_root':None,'remote_receipt_sha256':None,'remote_commit':None,'manifest':ref('union-manifest.json'),'shard_index':ref('SHARD_INDEX01.json'),'union_auth':ref('UNION_AUTHENTICATION01.json'),'direct_body':{'path':M.DIRECT['source_path'],'bytes':M.DIRECT['bytes'],'sha256':M.DIRECT['sha256']},'expected_members':2703,'expected_files':2302,'expected_logical_bytes':sum(r.get('bytes',0) for r in m['members']),'expected_shards':57,'output_root':str(M.BASE/'financial-genuine-wrapper-claimedrun-witness-sharded-flat-20261004-01'),'review':None,'framer_review':None,'release':None}
R.put(H/'REQUEST_TEMPLATE01.json',q);refuse(lambda:M.request(q),'NULL genuine remote/release refuses');idx,plans,refs=M.validate_index(q,m,R.read(C,'SHARD_INDEX01.json'));ok(len(plans)==57 and len(refs)==114,'actual57 bounded plans')
mapraw=R.read(C/'union-bytes01','ORIGINAL_TREES01.json');authraw=R.read(C,'UNION_AUTHENTICATION01.json');summary=M.authenticate_union(q,m,idx,authraw,mapraw);ok(summary['original_trees']==5 and summary['original_regular_members']==2302 and summary['original_lexical_links']==59,'complete actual5census+direct57metadata')
for mutation in ('missing','duplicate','mode','path','hash'):
 bad=copy.deepcopy(idx)
 if mutation=='missing':bad['direct_bodies']=[]
 elif mutation=='duplicate':bad['direct_bodies']*=2
 elif mutation=='mode':bad['direct_bodies'][0]['mode']^=1
 elif mutation=='path':bad['direct_bodies'][0]['source_path']+='/redirect'
 else:bad['direct_bodies'][0]['sha256']='0'*64
 refuse(lambda:M.validate_index(q,m,R.encode(bad)),'direct index '+mutation)
for i in range(5):
 trees=json.loads(mapraw)['scope_trees'];trees[i]['members'].pop();refuse(lambda:M.validate_expected_trees(trees),'full scope truncation '+str(i))
for name in ('expected_files','expected_members','expected_shards','expected_logical_bytes'):
 bad=copy.deepcopy(q);bad[name]-=1
 if name in ('expected_files','expected_shards'):refuse(lambda:M.validate_index(bad,m,R.read(C,'SHARD_INDEX01.json')),'wrong denominator '+name)
 else:refuse(lambda:M.manifest_join(bad,R.read(C,'union-manifest.json')),'wrong denominator '+name)
# Independent three tiny canonical shards; no releases/receipts are synthesized.
root=H/'tiny';root.mkdir(mode=0o700);virtual=root/'original';virtual.mkdir(mode=0o700)
for i in range(513):
 with R.new_file(virtual/('f%04d'%i)) as fd:os.write(fd,b'x')
mm=R.scan(virtual);pp=M.PLAN.partition(mm);ok(len(pp)==3,'real3tinyshards');remote=root/'opaque';(remote/'selected/research/tiny/shards').mkdir(parents=True);records=[]
for i,p in enumerate(pp):
 name='shard-%04d'%i;tree=root/name;tree.mkdir(mode=0o700)
 for row in p['manifest']['members']:
  with R.new_file(tree/row['path']) as fd:os.write(fd,R.read(virtual,row['path']))
 ap='shards/'+name+'.tar.gz';info=R.pack(tree,p['manifest'],remote/'selected/research/tiny'/ap);records.append({'id':name,'regular_paths':p['regular_paths'],'archive':dict(info,path=ap)})
qi={'shard_index':{'path':'research/tiny/SHARD_INDEX01.json'}};ii={'shards':records};out=root/'fresh';M.reserve(out);progress={};files,progress=M.restore_shards(remote,qi,mm,ii,pp,out,lambda:None,progress);ok(len(files)==513 and len(progress)==3,'full actual tiny fresh3shard restoration')
for name,r in files.items():ok(R.read(out/r['shard'],r['file'])==b'x','tiny original body '+name)
bad=copy.deepcopy(ii);bad['shards'][1]['archive']['sha256']='0'*64;partial=root/'partial';M.reserve(partial);progress={};refuse(lambda:M.restore_shards(remote,qi,mm,bad,pp,partial,lambda:None,progress),'second corruption refuses');ok(set(progress)=={'shard-0000'} and (partial/'shard-0001').is_dir(),'completedfirst partialsecond retained')
# Authentic direct raw body is copied only into this owned utility-control namespace.
main=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');raw=R.read(main,M.DIRECT['source_path']);dout=H/'owned-direct';M.reserve(dout);d=M.restore_direct(dout,raw);ok(d['sha256']==M.DIRECT['sha256'] and d['actual_private_mode']==384 and not d['research_authority'],'actual authenticated direct private bytejoin')
refuse(lambda:M.restore_direct(dout,raw),'one-use direct refuses');refuse(lambda:M.restore_direct(H,raw+b'x'),'wrong direct body refuses')
for firstcls in (MemoryError,KeyboardInterrupt):
 for secondcls in (OSError,MemoryError,KeyboardInterrupt):
  fd=os.open(H/'fd-witness',os.O_CREAT|os.O_WRONLY,0o600);first=firstcls('first');second=secondcls('close');events=[]
  def close():os.close(fd);events.append(1);raise second
  def done():events.append(2)
  try:
   try:raise first
   finally:R._cleanup((close,done))
  except BaseException as e:ok(e is first,'original firstfatal')
  ok(events==[1,2] and not Path('/proc/self/fd/'+str(fd)).exists(),'actual closedfd allcallbacks')
ok(not any(x in sys.modules for x in ('numpy','torch','scipy','pandas')),'no numerical imports')
R.put(H/'CHECKS01.json',{'checks':len(checks),'names':checks,'actual_root_restore':False,'actual_remote_or_release':False,'utility_authenticated_direct_body_copy':True});print('PASS',len(checks))
