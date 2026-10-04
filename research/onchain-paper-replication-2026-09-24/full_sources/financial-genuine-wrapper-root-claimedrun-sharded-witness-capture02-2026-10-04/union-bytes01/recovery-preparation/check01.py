import ast,copy,gzip,json,os,sys
from pathlib import Path
import restore_sharded01 as M
R=M.R;P=M.PLAN;H=Path(__file__).resolve().parent;checks=[]
def ok(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def refuse(n,f):
 try:f()
 except (ValueError,KeyError,TypeError,FileExistsError):ok(n,True)
 else:raise AssertionError(n)
q={k:None for k in ('remote_root','remote_receipt_sha256','remote_commit','manifest','shard_index','union_auth','expected_members','expected_files','expected_logical_bytes','expected_shards','review','release')};q.update(schema_version=1,output_root=str(M.BASE/'financial-genuine-wrapper-claimedrun-final-union-sharded-flat-20261004-01'));R.put(H/'REQUEST_TEMPLATE01.json',q);refuse('actual future NULL request refuses',lambda:M.request(q))
expected=json.loads(R.read(H,'EXPECTED_ORIGINALS01.json'));ok('exact20 source census unchanged',M.validate_expected_trees(expected['scope_trees'])==expected)
for i,t in enumerate(expected['scope_trees']):
 x=copy.deepcopy(expected['scope_trees']);x[i]['members'].pop();refuse('omitted census member '+t['scope'],lambda x=x:M.validate_expected_trees(x))
 x=copy.deepcopy(expected['scope_trees']);x[i]['original_root']='/opaque/redirected';refuse('redirected original '+t['scope'],lambda x=x:M.validate_expected_trees(x))
root=H/'owned01';root.mkdir();virtualroot=root/'tiny-virtual';virtualroot.mkdir(mode=0o700);(virtualroot/'bodies').mkdir(mode=0o700);(virtualroot/'empty-retained').mkdir(mode=0o700)
for i in range(260):
 with R.new_file(virtualroot/'bodies'/('item-'+str(i).zfill(4))) as fd:os.write(fd,b'opaque'+bytes([i%251]))
with R.new_file(virtualroot/'literal-metadata.json') as fd:os.write(fd,R.encode({'scope':'tiny opaque control only','literal_link':'/never/follow-this','not_actual_capture':True}))
m=R.scan(virtualroot);plans=P.partition(m);ok('actual tiny multiple shards',len(plans)==2);ok('all261 files exact disjoint',len([n for p in plans for n in p['regular_paths']])==261 and len(set(n for p in plans for n in p['regular_paths']))==261);ok('empty directory virtual only',all('empty-retained' not in {r['path'] for r in p['manifest']['members']} for p in plans))
remote=root/'opaque-shard-input';(remote/'selected/research/opaque/shards').mkdir(parents=True);prefix='research/opaque';shards=[]
for i,plan in enumerate(plans):
 ident='shard-'+str(i).zfill(4);src=root/(ident+'-source');src.mkdir(mode=m['root_mode'])
 for row in plan['manifest']['members']:
  p=src/row['path']
  if row['kind']=='directory':p.mkdir(mode=row['mode'])
  else:
   with R.new_file(p) as fd:os.write(fd,R.read(virtualroot,row['path']))
 mrbody=R.encode(plan['manifest']);mrpath='shards/'+ident+'-manifest.json';(remote/'selected'/prefix/mrpath).write_bytes(mrbody);arpath='shards/'+ident+'.tar.gz';info=R.pack(src,plan['manifest'],remote/'selected'/prefix/arpath)
 ok('actual compressed archive within original cap '+ident,info['bytes']<=R.FILE);ok('actual tar bound '+ident,len(gzip.decompress(R.read(remote/'selected'/prefix,arpath)))==plan['tar_bytes_bound']);ok('conservative gzip bound '+ident,info['bytes']<=P.gzip_bound(plan['tar_bytes_bound']))
 row={'id':ident,'regular_paths':plan['regular_paths'],'manifest':{'path':mrpath,'bytes':len(mrbody),'sha256':R.digest(mrbody)},'archive':dict(info,path=arpath),'members':plan['members'],'regular_bodies':plan['regular_bodies'],'logical_bytes':plan['logical_bytes'],'tar_bytes_bound':plan['tar_bytes_bound']};shards.append(row)
mbody=R.encode(m);index={'schema_version':1,'kind':'complete-final-union-shards-v1','virtual_manifest':{'path':'union-manifest.json','bytes':len(mbody),'sha256':R.digest(mbody)},'limits':{'logical_bytes':2097152,'typed_members':256,'archive_bytes':4194304},'regular_bodies':261,'shards':shards};ib=R.encode(index);qc={'manifest':{'path':prefix+'/union-manifest.json','bytes':len(mbody),'sha256':R.digest(mbody)},'shard_index':{'path':prefix+'/SHARD_INDEX01.json','bytes':len(ib),'sha256':R.digest(ib)},'expected_members':len(m['members']),'expected_files':261,'expected_logical_bytes':sum(r.get('bytes',0) for r in m['members']),'expected_shards':2}
ok('complete tiny virtual manifest',M.manifest_join(qc,mbody)==m);got,gotplans,refs=M.validate_index(qc,m,ib);ok('actual tiny index/planner join',got==index and gotplans==plans and len(refs)==4)
for kind in ('omit-shard','duplicate-shard','reverse-shards','omit-body','duplicate-body','reverse-files','wrong-mode','limit','wrong-archive-hash','wrong-shard-count','wrong-tar-bound','wrong-manifest-pin','redirect-path','bool-count'):
 z=copy.deepcopy(index);zm=copy.deepcopy(m);zq=copy.deepcopy(qc)
 if kind=='omit-shard':z['shards'].pop()
 elif kind=='duplicate-shard':z['shards'].append(copy.deepcopy(z['shards'][0]))
 elif kind=='reverse-shards':z['shards'].reverse()
 elif kind=='omit-body':z['shards'][0]['regular_paths'].pop()
 elif kind=='duplicate-body':z['shards'][1]['regular_paths'][0]=z['shards'][0]['regular_paths'][0]
 elif kind=='reverse-files':z['shards'][0]['regular_paths'].reverse()
 elif kind=='wrong-mode':zm['members'][0]['mode']^=1
 elif kind=='limit':z['limits']['archive_bytes']+=1
 elif kind=='wrong-archive-hash':z['shards'][0]['archive']['sha256']=None
 elif kind=='wrong-shard-count':zq['expected_shards']=3
 elif kind=='wrong-tar-bound':z['shards'][0]['tar_bytes_bound']+=1
 elif kind=='wrong-manifest-pin':z['shards'][0]['manifest']['sha256']='0'*64
 elif kind=='redirect-path':z['shards'][0]['archive']['path']='../escape'
 else:z['shards'][0]['members']=True
 refuse('shard schema '+kind,lambda z=z,zm=zm,zq=zq:M.validate_index(zq,zm,R.encode(z)))
link=copy.deepcopy(m);link['members'][-1]={'path':'literal-metadata.json','kind':'symlink','mode':511,'target':'/never-follow'};refuse('virtual actual link forbidden',lambda:M.manifest_join(qc,R.encode(link)))
# Exact physical caps enforced by pure planner, without creating oversized bodies.
for size in (2097152+1,4194304):
 z={'schema_version':1,'root_mode':448,'members':[{'path':'opaque','kind':'file','mode':384,'bytes':size,'sha256':'0'*64}]};refuse('single oversized logical body '+str(size),lambda z=z:P.partition(z))
z={'schema_version':1,'root_mode':448,'members':[{'path':'opaque','kind':'file','mode':384,'bytes':2097152,'sha256':'0'*64}]};ok('2MiB logical boundary',len(P.partition(z))==1)
flat=root/'tiny-sharded-flat';M.reserve(flat);results={};global_files,results=M.restore_shards(remote,qc,m,index,plans,flat,lambda:None,results);ok('all actual tiny261 bodies recovered',len(global_files)==261 and len(results)==2)
for name,ref in global_files.items():ok('actual tiny body '+name,R.read(flat/ref['shard'],ref['file'])==R.read(virtualroot,name))
ok('all original no authority flags retained',all(r['research_authority'] is False and r['instantiated_posix_tree'] is False and r['runtime_package_bodies_recovered'] is False for r in results.values()));refuse('repeat output reservation',lambda:M.reserve(flat))
# Corrupt second actual shard: first completed result retained, partial directory retained.
bad=copy.deepcopy(index);bad['shards'][1]['archive']['sha256']='0'*64;partial=root/'partial';M.reserve(partial);progress={};refuse('actual second-shard tamper refuses',lambda:M.restore_shards(remote,qc,m,bad,plans,partial,lambda:None,progress));ok('first shard completion retained after second failure',set(progress)=={'shard-0000'} and (partial/'shard-0000/body-metadata.json').is_file() and (partial/'shard-0001').is_dir())
(virtualroot/'late-extra').write_bytes(b'opaque');refuse('actual late-extra original source refuses',lambda:R.same(virtualroot,m))
redirect=root/'redirect';redirect.symlink_to(flat,target_is_directory=True);refuse('redirected output parent refuses',lambda:M.reserve(redirect/'new'))
# Original primitive and descriptor reservation byte identities.
old=(H/'original-restore_union01.py').read_text();new=(H/'restore_sharded01.py').read_text();functions=lambda s:{n.name:ast.get_source_segment(s,n) for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)};a=functions(old);b=functions(new)
for n in ('hashed','reference','contract','reserve','restore_ordinary','validate_expected_trees'):ok('unchanged function '+n,a[n]==b[n])
for n,pin in M.PINS.items():ok('unchanged primitive '+n,R.digest(R.read(H,n))==pin)
for first in (ValueError('ordinary'),MemoryError('fatal'),KeyboardInterrupt('fatal')):
 for second in (OSError('ordinary'),MemoryError('fatal'),KeyboardInterrupt('fatal')):
  events=[]
  def fail():events.append(1);raise second
  def done():events.append(2)
  caught=None
  try:R._cleanup((fail,done),primary=first)
  except BaseException as e:caught=e
  fatal=lambda e:isinstance(e,MemoryError) or not isinstance(e,Exception)
  ok('first fatal '+type(first).__name__+'/'+type(second).__name__,caught is None if fatal(first) else caught is second if fatal(second) else type(caught).__name__=='CleanupFailure' and caught.failures==(first,second));ok('all cleanup attempted',events==[1,2])
ok('no numerical imports',not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')))
R.put(H/'CHECKS01.json',{'checks':len(checks),'check_names':checks,'actual_capture':None,'actual_final_union_recovery':None,'only_tiny_opaque_shards':True,'genuine_approved_request_created':False,'network':False,'numerical_execution':False});print('PASS',len(checks))
