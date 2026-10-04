import ast,copy,hashlib,json,os,stat,sys
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;A=B/'financial-genuine-wrapper-claimedrun-witness-sharded-flat-preparation01-2026-10-04';sys.path.insert(0,str(A));import restore_witness01 as M
R=M.R;count=0;refusals=[]
def ck(v,n):
 global count
 assert v,n;count+=1
def sha(b):return hashlib.sha256(b).hexdigest()
def refuse(fn,n):
 try:fn()
 except (ValueError,TypeError,KeyError,OSError) as e:refusals.append({'control':n,'exception':type(e).__name__,'message':str(e)});ck(True,n)
 else:raise AssertionError('not refused '+n)
def scan(root):
 rows=[]
 def visit(p,name):
  s=p.lstat();r={'path':name,'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISLNK(s.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
  elif stat.S_ISDIR(s.st_mode):
   r['kind']='directory';rows.append(r)
   for c in sorted(p.iterdir()):visit(c,name+'/'+c.name)
   return
  else:ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1,'regular singlelink');b=R.read(root,name);r.update(kind='file',bytes=len(b),sha256=sha(b))
  rows.append(r)
 for p in sorted(root.iterdir()):visit(p,p.name)
 return sorted(rows,key=lambda r:r['path'])
raw=R.read(A,'MANIFEST01.json');ck(sha(raw)=='632a29c65c95ae68b674f07b81314bd374404f8937e1bd971e1070525b1ef516','author frozen seal');actual=scan(A);ck([r for r in actual if r['path']!='MANIFEST01.json']==json.loads(raw)['members'],'every author typed body/mode')
s=R.read(A,'restore_witness01.py');ck(sha(s)=='5352c2e42d11d585e92187f2d51be9c42eaadcfc9b03f8e11e9a7097bf7c28ac','candidate source');x=s.decode()
for e in reversed(json.loads(R.read(A,'INVERSE01.json'))['edits']):ck(x.count(e['new'])==e['count'],'inverse exact occurrence');x=x.replace(e['new'],e['old'])
o=R.read(A,'original-restore_sharded01.py');ck(x.encode()==o and ast.dump(ast.parse(x))==ast.dump(ast.parse(o)),'entire byte AST inverse')
for n,p in M.PINS.items():ck(sha(R.read(A,n))==p,'actual imported closure pin')
fr=B/'financial-genuine-wrapper-claimedrun-witness-pax-framer-correction-review01-2026-10-04';frbody=R.read(fr,'MACHINE01.json');ck(sha(frbody)=='64bc091e50fda054306df6ef7d966582b8a4580d5591049fe6cf409105503588','genuine framer review');ck(sha(R.read(fr,'MANIFEST01.json'))=='da12eec6346157fed9ad113403bdac04b44165fd5bd9c01a6b64b04be5bb052f','genuine framer full review seal')
C=B/'financial-genuine-wrapper-root-claimedrun-sharded-witness-capture02-2026-10-04';q=json.loads(R.read(A,'REQUEST_TEMPLATE01.json'));refuse(lambda:M.request(q),'actual NULL remote/release draft');ck(not Path(q['output_root']).exists(),'fresh actual output absent');m=M.manifest_join(q,R.read(C,'union-manifest.json'));idx,plans,refs=M.validate_index(q,m,R.read(C,'SHARD_INDEX01.json'));mapping=R.read(C/'union-bytes01','ORIGINAL_TREES01.json');auth=R.read(C,'UNION_AUTHENTICATION01.json');summary=M.authenticate_union(q,m,idx,auth,mapping);ck(summary['original_regular_members']==2302 and summary['original_lexical_links']==59 and len(plans)==57 and len(refs)==114,'actual complete five witness population');ck(sum(r['bytes'] for r in refs)+sum(q[k]['bytes'] for k in ('manifest','shard_index','union_auth','direct_body'))<=64*1024**2,'actual selected compressed+direct total bound')
ck(R.digest(R.read(A,'EXPECTED_ORIGINALS01.json'))==M.EXPECTED_ORIGINALS_SHA256,'full expected originals pin')
for role,pin in M.ACTUAL_CAPTURE_PINS.items():ck(sha(R.read(C,role))==pin,'actual capture fixedpin')
for row,plan in zip(idx['shards'],plans):
 raw=R.read(C,row['archive']['path']);ck(sha(raw)==row['archive']['sha256'],'actual shard pin');frames=list(R.framed_members(raw));ck(len(frames)==len(plan['manifest']['members']),'all57 PAX compatible framing')
 for (n,t,b),r in zip(frames,plan['manifest']['members']):ck(n==r['path'] and t.mode==r['mode'] and ((not b and t.isdir()) if r['kind']=='directory' else (t.isfile() and len(b)==r['bytes'] and sha(b)==r['sha256'])),'all57 exact framed body')
 sink=R.ExactSink(raw);R.tar_stream(C/'shard-trees'/row['id'],plan['manifest'],sink);ck(sink.count==len(raw),'all57 full canonical equality')
for label in ('missing','duplicate','mode','path','hash'):
 bad=copy.deepcopy(idx)
 if label=='missing':bad['direct_bodies']=[]
 elif label=='duplicate':bad['direct_bodies']*=2
 elif label=='mode':bad['direct_bodies'][0]['mode']^=1
 elif label=='path':bad['direct_bodies'][0]['source_path']+='x'
 else:bad['direct_bodies'][0]['sha256']='0'*64
 refuse(lambda:M.validate_index(q,m,R.encode(bad)),'direct '+label)
for label in ('order','omitted','duplicate','path','logical'):
 bad=copy.deepcopy(idx)
 if label=='order':bad['shards'].reverse()
 elif label=='omitted':bad['shards'].pop()
 elif label=='duplicate':bad['shards'][1]=copy.deepcopy(bad['shards'][0])
 elif label=='path':bad['shards'][0]['regular_paths'][0]+='x'
 else:bad['shards'][0]['logical_bytes']+=1
 refuse(lambda:M.validate_index(q,m,R.encode(bad)),'index '+label)
# Self-consistent counter changes cannot weaken fixed whole original census.
for label in ('missing','mode','link','extra','direct-hash'):
 mp=json.loads(mapping);au=json.loads(auth);vm=copy.deepcopy(m);trees=mp['scope_trees']
 if label=='missing':trees[0]['members'].pop()
 elif label=='extra':trees[0]['members'].append(dict(trees[0]['members'][-1]))
 elif label=='mode':trees[0]['members'][0]['mode']^=1
 elif label=='link':next(r for t in trees for r in t['members'] if r['kind']=='lexical-symlink')['target']='changed'
 else:next(r for t in trees for r in t['members'] if 'direct_source_path' in r)['sha256']='0'*64
 mb=R.encode(mp);au['union_mapping_sha256']=sha(mb);rr=next(r for r in vm['members'] if r['path']=='ORIGINAL_TREES01.json');rr.update(bytes=len(mb),sha256=sha(mb));refuse(lambda:M.authenticate_union(q,vm,idx,R.encode(au),mb),'consistent population mutation '+label)
# Owned ordinary byte pipeline; no request/release/remote outcome is fabricated.
tiny=H/'tiny';tiny.mkdir(mode=0o700);origin=tiny/'original';origin.mkdir(mode=0o700)
for i in range(513):
 with R.new_file(origin/('opaque-%04d'%i)) as fd:os.write(fd,bytes([i%251]))
vm=R.scan(origin);pp=M.PLAN.partition(vm);ck(len(pp)==3,'three parent-count bounded tiny shards');remote=tiny/'opaque-input';selected=remote/'selected/research/tiny';(selected/'shards').mkdir(parents=True,mode=0o700);records=[]
for i,p in enumerate(pp):
 name='shard-%04d'%i;tree=tiny/name;tree.mkdir(mode=0o700)
 for r in p['manifest']['members']:
  with R.new_file(tree/r['path']) as fd:os.write(fd,R.read(origin,r['path']))
 ap='shards/'+name+'.tar.gz';info=R.pack(tree,p['manifest'],selected/ap);records.append({'id':name,'regular_paths':p['regular_paths'],'archive':dict(info,path=ap)})
qi={'shard_index':{'path':'research/tiny/SHARD_INDEX01.json'}};ii={'shards':records};out=tiny/'flat';M.reserve(out);files,res=M.restore_shards(remote,qi,vm,ii,pp,out,lambda:None)
ck(len(files)==513 and len(res)==3,'complete tiny pipeline')
for name,r in files.items():ck(R.read(out/r['shard'],r['file'])==R.read(origin,name),'tiny original byte')
# Actual direct raw only copied into this owned fixture.
main=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');direct=R.read(main,M.DIRECT['source_path']);dr=M.restore_direct(out,direct);ck(dr['sha256']==M.DIRECT['sha256'] and dr['actual_private_mode']==384 and dr['research_authority'] is False,'actual direct raw canonical join');refuse(lambda:M.restore_direct(out,direct),'direct namespace reuse');refuse(lambda:M.restore_direct(H,direct[:-1]),'direct truncation');refuse(lambda:M.reserve(out),'outer namespace reuse')
bad=copy.deepcopy(ii);bad['shards'][1]['archive']['sha256']='0'*64;partial=tiny/'partial';M.reserve(partial);progress={};refuse(lambda:M.restore_shards(remote,qi,vm,bad,pp,partial,lambda:None,progress),'second shard corrupt');ck(set(progress)=={'shard-0000'} and (partial/'shard-0001').exists(),'completed first retained without false all-complete')
# Real second-shard partial body fatal, original descriptors and first result retained.
fatal=tiny/'fatal';M.reserve(fatal);progress={};original=M.restore_ordinary;write=os.write;close=os.close;primary=MemoryError('second shard body fatal');closed=[];started=[]
def wrapper(ar,info,mm,destination):
 if destination.name=='shard-0001':
  def badwrite(fd,b):started.append(True);raise primary
  def badclose(fd):
   close(fd)
   if started:closed.append(fd);raise SystemExit('later diagnostic fatal')
  os.write=badwrite;os.close=badclose
 return original(ar,info,mm,destination)
M.restore_ordinary=wrapper
try:
 try:M.restore_shards(remote,qi,vm,ii,pp,fatal,lambda:None,progress)
 except BaseException as e:ck(e is primary,'real partial pipeline first fatal identity')
 else:raise AssertionError('fatal missing')
finally:M.restore_ordinary=original;os.write=write;os.close=close
ck(set(progress)=={'shard-0000'} and len(closed)>=2 and all(not Path('/proc/self/fd/'+str(fd)).exists() for fd in closed),'first complete second partial real closed descriptors')
ck(not any(n in sys.modules for n in ('torch','numpy','pandas','scipy')),'stdlib-only');ck(scan(A)==actual,'author full frozen scope unchanged')
qout={'schema_version':1,'decision':'accepted-source-only-witness-sharded-plus-direct-flat','source_sha256':sha(s),'author_manifest_sha256':sha(raw if False else R.read(A,'MANIFEST01.json')),'checks':count,'refusals':refusals,'actual_57_archive_framing_and_canonical_checked':True,'actual_Root_restore':False,'actual_remote_or_release':False,'original_witness_files':2302,'original_literal_links':59,'direct_descriptor':M.DIRECT,'original_no_authority_fields_preserved':True,'qualification':'Source-only. Future genuine remote, exact release and complete actual recovered union are still required. Source/final caller and runtime/empirical scopes remain separate.'}
(H/'READBACK01.json').write_text(json.dumps(qout,sort_keys=True,indent=2)+'\n');print('PASS',count)
