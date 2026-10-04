import ast,gzip,hashlib,importlib.util,io,json,os,stat,sys,tarfile
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;ROOT=B/'financial-genuine-wrapper-root-claimedrun-sharded-witness-capture02-2026-10-04';PR=B/'held-consumer-final-recovery-preparation04-2026-10-03';sys.path.insert(0,str(PR));import recovery04 as a
sha=lambda b:hashlib.sha256(b).hexdigest();count=0;checks={};pins=[]
def ck(v,n):
 global count
 if not v:raise AssertionError(n)
 count+=1;checks[n]=checks.get(n,0)+1
def raw(root,name,pin=None):
 b=a.read(root,name);ck(pin is None or sha(b)==pin,'exact pinned body');return b
def doc(root,name,pin=None):return json.loads(raw(root,name,pin))
# Reuse only independent bounded raw decoder/reencoder definitions, not its original task code.
src=ast.parse((B/'held-consumer-final-released-scope-capture-review01-2026-10-03/check01.py').read_bytes());defs=[n for n in src.body if isinstance(n,ast.FunctionDef) and n.name in ('decode','recode')];exec(compile(ast.Module(body=defs,type_ignores=[]),'independent bounded framing','exec'))
auth=doc(ROOT,'UNION_AUTHENTICATION01.json','d0af9053a4cb894bf17155afe4e4ca4abc9f3d8ea4dcd051d1af795d899ee986');index=doc(ROOT,'SHARD_INDEX01.json','784b3431531b6ffe53a0ef9a94791c878219b316a532a11e0916a75ea07c72dd');virtual=doc(ROOT,'union-manifest.json','42896378dc3fc40396a838e268018bbb41c7c1a9530ebf1be283a388f0d45b6e');terminal=doc(ROOT,'ACTUAL_TOOL_TERMINAL02.json','776e70453aa9ceb15577c8ee50309e080ebfbd6809d66412a9af0efbc7ea3683');intent=doc(ROOT,'INTENT01.json')
source=raw(ROOT,'capture_witness02.py','b275af0c30a4f19227cff1cccbc19c01d7548b3b218e43f78a3be493bfe05ae6');raw(ROOT,'shards01.py','9c38c0893790c22e3b0142a8ab175dceb9b14dd0aeeb80edc206e5329ffcbbba');ns={'__name__':'read_only','__file__':str(ROOT/'capture_witness02.py')};exec(compile(source,'exact definitions','exec'),ns)
for name,pin in ns['PINS'].items():raw(PR,name,pin)
prior=B/'financial-genuine-wrapper-claimedrun-sharded-witness-capture-review02-2026-10-04';raw(prior,'MANIFEST01.json','d0bd935a4f693f56dd5b43a7a4b5f3f9463bdf7afee29995b61aa9ba44016c3f');priorread=doc(prior,'READBACK01.json','f5c40be1b8bcde76694269ab426cd3232f4cb4a8f1e3e43fba8d9dabed14b065')
ck(index['kind']=='complete-witness-shards-plus-direct-v1' and index['direct_bodies']==auth['direct_bodies']==[ns['DIRECT']],'exact required direct descriptor');ck(auth['direct_regular_members']==1 and len(index['shards'])==auth['shard_count']==57,'exact index/auth cardinalities');ck(index['virtual_manifest']['sha256']==auth['index']['virtual_manifest_sha256']==sha(a.encode(virtual)),'virtual manifest lineage');ck(auth['index']['sha256']==sha(ns['encoded'](index)),'index lineage');a.same(ROOT/'union-bytes01',virtual)
sp=importlib.util.spec_from_file_location('actualplanner',ROOT/'shards01.py');planner=importlib.util.module_from_spec(sp);sp.loader.exec_module(planner);expected=planner.partition(virtual);ck(len(expected)==57,'deterministic actual partitions')
allfiles={};results=[];totalcompressed=0;declared=set()
for pos,rec in enumerate(index['shards']):
 ck(rec['id']=='shard-%04d'%pos,'deterministic IDs');mb=raw(ROOT,rec['manifest']['path'],rec['manifest']['sha256']);m=json.loads(mb);ab=raw(ROOT,rec['archive']['path'],rec['archive']['sha256']);ck(len(mb)==rec['manifest']['bytes'] and len(ab)==rec['archive']['bytes']<=4194304,'actual extents');ck(rec['archive']['manifest_sha256']==sha(mb),'archive manifest pin');ck(m==expected[pos]['manifest'] and all(rec[k]==v for k,v in expected[pos].items() if k!='manifest'),'exact complete planned partition');ck(len(m['members'])<=256 and sum(r.get('bytes',0) for r in m['members'])<=2097152,'actual typed parent and logical limits')
 bodies,framing=decode(ab,m);ck(recode(m,bodies)==ab,'whole canonical compressed bytes');a.same(ROOT/'shard-trees'/rec['id'],m)
 for row in m['members']:
  if row['kind']=='file':
   name=row['path'];ck(name not in allfiles,'one-to-one shard body cover');bb=bodies[name];ck(bb==raw(ROOT/'union-bytes01',name)==raw(ROOT/'shard-trees'/rec['id'],name),'every physical shard+union body');allfiles[name]={'bytes':len(bb),'sha256':sha(bb)}
 ck([r['path'] for r in m['members'] if r['kind']=='file']==rec['regular_paths'],'ordered exact regular path list')
 totalcompressed+=len(ab);declared.update((rec['manifest']['path'].split('/')[-1],rec['archive']['path'].split('/')[-1]));results.append({'id':rec['id'],'archive_sha256':sha(ab),'compressed_bytes':len(ab),'members':len(m['members']),**framing})
ck(set(p.name for p in (ROOT/'shards').iterdir())==declared,'no missing or extra archive files');ck(set(p.name for p in (ROOT/'shard-trees').iterdir())=={r['id'] for r in index['shards']},'no extra shard trees');ck(totalcompressed==20123201,'actual archive compressed total');ck(set(allfiles)=={r['path'] for r in virtual['members'] if r['kind']=='file'} and len(allfiles)==index['regular_bodies']==2302,'complete virtual cover')
mb=raw(ROOT/'union-bytes01','ORIGINAL_TREES01.json',auth['union_mapping_sha256']);mapping=json.loads(mb);ns['partition_join'](mapping['scope_trees'],virtual,ns['DIRECT']);ck(mapping['direct_bodies']==index['direct_bodies'] and mapping['direct_regular_bodies']==1 and mapping['archived_regular_bodies']==2301,'mapping direct/archived exact count')
def observe(root):
 rows=[]
 def visit(p,name):
  s=p.lstat();r={'path':name,'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISLNK(s.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
  elif stat.S_ISDIR(s.st_mode):
   r['kind']='directory';rows.append(r)
   for c in sorted(p.iterdir()):visit(c,c.name if name=='.' else name+'/'+c.name)
   return
  else:
   ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1,'current original type/link');b=raw(root,name);r.update(kind='file',bytes=len(b),sha256=sha(b))
  rows.append(r)
 visit(root,'.');return sorted(rows,key=lambda r:r['path'])
originalcount=links=logical=typed=0;direct_seen=0
ck({t['scope'] for t in mapping['scope_trees']}==set(ns['SCOPES']),'exact original five scope labels')
priorcensus=doc(prior,'ACTUAL_CENSUS01.json')['scope_trees']
for tree in mapping['scope_trees']:
 label=tree['scope'];root=ns['SCOPES'][label];ck(tree['original_root']==str(root),'actual fixed original root');actual=observe(root);old=next(t for t in priorcensus if t['scope']==label);ck(actual==old['members'],'unchanged complete pre-capture current scope');transformed=[]
 for row in actual:
  rr=dict(row)
  if rr['kind']=='file':
   originalcount+=1;logical+=rr['bytes'];ns['bind_member'](label,rr['path'],rr,ns['DIRECT'])
   if 'direct_source_path' in rr:
    direct_seen+=1;bb=raw(ns['MAIN'],rr['direct_source_path']);ck(len(bb)==rr['bytes'] and sha(bb)==rr['sha256'] and rr['mode']==384,'exact sole raw direct original');ck(label+'/'+rr['path'] not in allfiles,'direct not silently archived')
   else:ck(allfiles[rr['union_path']]=={k:rr[k] for k in ('bytes','sha256')},'every original to canonical archive body')
  elif rr['kind']=='lexical-symlink':links+=1
  transformed.append(rr)
 ck(transformed==tree['members'],'complete original mode/path/link mapping');typed+=len(actual)
 sealname='MANIFEST02.json' if label=='actual-capture-review' else 'MANIFEST01.json';seal=doc(root,sealname,ns['SEALS'][label]);by={r['path']:r for r in actual}
 for r in seal['members']:
  rr=dict(r);rr['kind']='lexical-symlink' if rr['kind']=='symlink' else rr['kind'];ck(by[rr['path']]==rr,'every original sealed member')
 ck(set(by)=={r['path'] for r in seal['members']}|{'.',sealname},'full seal closure')
ck((typed,originalcount,links,direct_seen)==(2762,2302,59,1),'full original denominator');ck(logical==61971030 and logical+len(mb)==62816678<=67108864,'64MiB includes direct and mapping');ck(len(virtual['members'])==auth['ordinary_members']==2703,'full ordinary manifest denominator');ck(auth['original_typed_members']==typed and auth['original_regular_members']==originalcount and auth['original_lexical_links']==links,'authentication full counts')
sm=doc(ns['SOURCE_CAPTURE'],'source-manifest.json','fdf77348b81a4d6df8b420b98530f5485900a0461636e1c201506106b036dfd8');a.same(ns['SOURCE'],sm);raw(ns['SOURCE_CAPTURE'],'source.tar.gz','b5b6aad2f515447dc6566cfb716a20ef90031313d48f1ac903ab756735431e24');raw(ns['PARENT'],'REQUEST_FINAL03.json','529c9bf3c587e6160a217e8eb339882e59433b6fc0f759d0009d261f872b2bd8');raw(ns['PARENT'],'proofs/FULL_SOURCE_RECOVERY01.json','468dac2c06e570a89a30771c3f7e1b8e064e6f27e610acf01edcccf91c9a2825');ck(not os.path.lexists(ns['PARENT']/'attempt'),'no Parent numerical attempt')
ck(terminal['actual_tool']=={'session':71682,'start':'fa7cfd','completion':'f1219d','exit':0},'recorded actual tools and exit');ck(terminal['actual_root_process']==intent,'original intent exact terminal join');ck(terminal['authentication_sha256']==sha(ns['encoded'](auth)) and terminal['index_sha256']==sha(ns['encoded'](index)) and terminal['virtual_manifest_sha256']==sha(a.encode(virtual)),'terminal body joins');out=raw(ROOT,'ACTUAL_CAPTURE01.out',terminal['out_sha256']);err=raw(ROOT,'ACTUAL_CAPTURE01.err',terminal['err_sha256']);ck(err==b'','actual stderr empty');stdout=json.loads(out);ck(stdout['index']==auth['index'] and stdout['shard_count']==57 and stdout['original_regular_members']==2302,'original stdout joins');ck(intent['source']==sha(source) and intent['planner']=='9c38c0893790c22e3b0142a8ab175dceb9b14dd0aeeb80edc206e5329ffcbbba','intent installed source');ck(intent['free_before']>=10737418240 and auth['free_bytes']>=10737418240 and auth['elapsed_seconds']<120,'actual recorded floors and elapsed')
pid=intent['actual_root_pid'];pg=intent['actual_pgid'];ck(pid==517157 and intent['actual_start_ticks']==16428400 and pg==517154,'original recorded process identity');ck(not Path('/proc',str(pid)).exists(),'original PID currently absent');members=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  text=(p/'stat').read_text();parts=text[text.rfind(')')+2:].split()
  if int(parts[2])==pg:members.append(int(p.name))
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
ck(not members,'original process group currently absent');a.same(ROOT/'union-bytes01',virtual)
ck(not any(k in sys.modules for k in ('torch','numpy','pandas','scipy')),'no numerical modules')
readback={'schema_version':1,'decision':'ACCEPTED_ACTUAL_LOCAL_FIVE_TREE_WITNESS_CAPTURE_PLUS_REQUIRED_DIRECT','source_sha256':sha(source),'authentication_sha256':sha(ns['encoded'](auth)),'index_sha256':sha(ns['encoded'](index)),'virtual_manifest_sha256':sha(a.encode(virtual)),'terminal_sha256':sha(raw(ROOT,'ACTUAL_TOOL_TERMINAL02.json')),'original_trees':5,'original_typed_members':typed,'original_regular_bodies':originalcount,'original_literal_links':links,'virtual_regular_bodies_including_mapping':2302,'archived_original_bodies':2301,'direct_bodies':[ns['DIRECT']],'whole_logical_including_mapping':logical+len(mb),'archives':57,'archive_bytes':totalcompressed,'checks':count,'current_original_pid_absent':True,'current_original_group_members':members,'actual_tool_exit':0,'shards_alone_complete':False,'actual_external_recovery':False,'actual_flat_restore':False,'native_or_numerical_authority':False,'source339_and_final_caller_scope':'separate existing required scopes; this review accepts only five witness trees','observational_limit':'Terminal tool and start identity are original Root records; present PID/group absence was independently observed. No continuous process/disk history is inferred.'}
for n,q in [('READBACK01.json',readback),('SHARDS01.json',results),('CHECK_COUNTS01.json',checks)]:
 with (H/n).open('x') as f:json.dump(q,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps(readback,sort_keys=True))
