import ast,copy,gzip,hashlib,io,json,os,stat,sys,tarfile
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;MAIN=B.parents[2];A=B/'financial-genuine-wrapper-claimedrun-final-selected-closure-census02-2026-10-04';sys.path.insert(0,str(B/'financial-genuine-wrapper-claimedrun-witness-pax-framer-correction-preparation01-2026-10-04'));import recovery_pax01 as R
count=0;results=[]
def ck(v,n):
 global count
 assert v,n;count+=1
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return R.read(p.parent,p.name)
def doc(p,pin=None):
 b=read(p);ck(pin is None or sha(b)==pin,'pinned actual metadata');return json.loads(b)
def scan(root):
 rows=[]
 def visit(p,name):
  t=p.lstat();r={'path':name,'mode':stat.S_IMODE(t.st_mode)}
  if stat.S_ISLNK(t.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
  elif stat.S_ISDIR(t.st_mode):
   r['kind']='directory';rows.append(r)
   for c in sorted(p.iterdir()):visit(c,c.name if name=='.' else name+'/'+c.name)
   return
  else:ck(stat.S_ISREG(t.st_mode) and t.st_nlink==1,'ordinary singlelink');b=R.read(root,name);r.update(kind='file',bytes=len(b),sha256=sha(b))
  rows.append(r)
 visit(root,'.');return sorted(rows,key=lambda r:r['path'])
seal=doc(A/'MANIFEST01.json','1aad852dd1e89c07da3a8bf588b1ddd1cfb4ec34e3972ee6b71403c2b8e4a20d');actual=scan(A);ck([r for r in actual if r['path'] not in ('.','MANIFEST01.json')]==seal['members'],'complete frozen census');rows=doc(A/'CANDIDATE_ROWS02.json','70ff2feb00e4d334a14897a87222077b943643d96bff087a275bbcdd3b43569f')['rows'];groups=doc(A/'TRANSPORT_BATCHES02.json','8f3e9ef773fdd9d2a815b3133bd28297930d02043182a4f4a8c68d982159f095')['batches'];typed=doc(A/'COMPLETE_TYPED_ROOTS02.json','4bef328d0e47ffcf45dbcc04c220e7928a76c818dd2d2313eeab5a1689f06f53');by={r['path']:r for r in rows}
ck(len(rows)==len(by)==689 and [r['path'] for r in rows]==sorted(by),'689 sorted distinct bodies');ck(sum(r['bytes'] for r in rows)==52795748,'distinct byte total')
for r in rows:
 p=MAIN/r['path'];s=p.lstat();b=read(p);ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and p.resolve()==p and stat.S_IMODE(s.st_mode)==r['mode'] and len(b)==r['bytes']<=4194304 and sha(b)==r['sha256'],'every current actual row bytes/mode')
transport_roots=[B/'financial-genuine-wrapper-root-claimedrun-final-shards-remote01-2026-10-04',B/'financial-genuine-wrapper-root-claimedrun-helper-raw-remote01-2026-10-04'];required=None
for root in transport_roots:
 b=read(root/'recover01.py');ck(sha(b)=='0b397ccd0a014f60a414ce79d67dfd53c58a0fb61ca616a6576cc43da4bbf0aa','both original accepted transport source');tree=ast.parse(b);node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REQUIRED' for t in n.targets));req=ast.literal_eval(node.value);ck(required is None or req==required,'identical mandatory anchor map');required=req
 ck(not any((root/n).exists() for n in ('REMOTE_RECOVERY01.json','INTENT01.json','selected','fresh-recordfix-source325-01.git')),'no actual transport namespace yet')
anchors=set(required);ck(len(anchors)==6,'exact six inherited safety anchors')
for p,r in required.items():ck(p in by and all(by[p][k]==r[k] for k in ('bytes','sha256')),'mandatory actual anchor bytes')
def validate(gs):
 ck(len(gs)==2,'exact two batches');sets=[]
 for g in gs:
  rr=g['rows'];names=[r['path'] for r in rr];ck(names==sorted(set(names)) and all(r==by[r['path']] for r in rr),'exact sorted batch bodyrows');ck(len(rr)<=506 and sum(r['bytes'] for r in rr)<=67108864 and max(r['bytes'] for r in rr)<=4194304 and 11+2*len(rr)<=1024,'finite unchanged batch caps');ck(set(g['mandatory_shared_anchors'])==anchors,'exact shared anchors');ck(all(g[k] is None for k in ('actual_remote_namespace','actual_commit','actual_receipt')),'future operational evidence remains NULL');sets.append(set(names))
 ck(sets[0]&sets[1]==anchors and sets[0]|sets[1]==set(by),'complete union only6overlap');ck(len(sets[1]-anchors)==330,'complete supplemental own330')
validate(groups);ck([(len(g['rows']),sum(r['bytes'] for r in g['rows'])) for g in groups]==[(359,52374727),(336,4362239)],'actual primary supplemental denominators');links=0
for role,t in typed.items():
 rr=scan(Path(t['root']));ck(rr==t['members'],'complete typed actual root')
 for r in rr:
  if r['kind']=='file':p=(Path(t['root'])/r['path']).relative_to(MAIN).as_posix();ck(p in by and all(by[p][k]==r[k] for k in ('bytes','sha256','mode')),'every typed file in selected union')
  elif r['kind']=='lexical-symlink':links+=1
ck(links==45,'complete45 literal links');ck(str((A/'COMPLETE_TYPED_ROOTS02.json').relative_to(MAIN)) in by,'literal directory root modes mapping selected')
core=doc(B/'financial-genuine-wrapper-claimedrun-final-preservation-selection-census01-2026-10-04/CURRENT_CORE_ROWS01.json')['rows'];ck(len(core)==117,'original core117');
for r in core:ck(r['path'] in by and all(by[r['path']][k]==r[k] for k in ('bytes','sha256','mode')),'original117 unchanged')
# All actual archive chains decoded and independently reencoded, opaque bodies only.
def selected(p):
 n=str(p.relative_to(MAIN));ck(n in by,'required closure body selected');return read(p)
def archive(root,record,m):
 raw=selected(root/record['path']);ck(len(raw)==record['bytes'] and sha(raw)==record['sha256'],'actual archive pin');frames=list(R.framed_members(raw));ck(len(frames)==len(m['members']),'complete framed manifest');bodies={}
 for (name,t,b),r in zip(frames,m['members']):
  ck(name==r['path'] and t.mode==r['mode'] and ((t.isdir() and not b) if r['kind']=='directory' else (t.isfile() and len(b)==r['bytes'] and sha(b)==r['sha256'])),'whole framed original body/mode');bodies[name]=b
 out=io.BytesIO()
 with gzip.GzipFile(fileobj=out,mode='wb',filename='',mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
   for r in m['members']:
    t=tarfile.TarInfo(r['path']);t.mode=r['mode'];t.uid=t.gid=t.mtime=0;t.uname=t.gname=''
    if r['kind']=='directory':t.type=tarfile.DIRTYPE;tf.addfile(t)
    else:t.size=len(bodies[r['path']]);tf.addfile(t,io.BytesIO(bodies[r['path']]))
 ck(out.getvalue()==raw,'complete canonical gzip archive');return bodies
scope_summaries=[]
def originals(mapping,bodypins,direct=False):
 summaries=[]
 for t in mapping['scope_trees']:
  root=Path(t['original_root']);actual=scan(root);expected=[{k:v for k,v in r.items() if k not in ('union_path','direct_source_path')} for r in t['members']];ck(actual==expected,'all complete original tree paths/modes/links/currentbytes')
  for r in t['members']:
   if r['kind']=='file':
    if 'direct_source_path' in r:
     ck(direct and r['direct_source_path'] in by and all(by[r['direct_source_path']][k]==r[k] for k in ('bytes','sha256','mode')),'exact direct selected raw c47f')
    else:ck(bodypins[r['union_path']]==(r['bytes'],r['sha256']),'complete original archived regular mapping')
  summaries.append({'scope':t['scope'],'typed':len(actual),'regular':sum(r['kind']=='file' for r in actual)})
 return summaries
for basename,expectedshards,expectedtrees in [('financial-genuine-wrapper-root-claimedrun-final-capture02-2026-10-04',11,20),('financial-genuine-wrapper-root-claimedrun-sharded-witness-capture02-2026-10-04',57,5)]:
 root=B/basename;idx=json.loads(selected(root/'SHARD_INDEX01.json'));m=json.loads(selected(root/'union-manifest.json'));auth=json.loads(selected(root/'UNION_AUTHENTICATION01.json'));ck(len(idx['shards'])==expectedshards,'actual shard count');pins={};mapping=None
 for row in idx['shards']:
  mm=json.loads(selected(root/row['manifest']['path']));ck(sha(R.encode(mm))==row['manifest']['sha256'],'selected shard manifest');bb=archive(root,row['archive'],mm)
  for r in mm['members']:
   if r['kind']=='file':ck(r['path'] not in pins,'disjoint shard cover');pins[r['path']]=(r['bytes'],r['sha256'])
  if 'ORIGINAL_TREES01.json' in bb:mapping=json.loads(bb['ORIGINAL_TREES01.json']);ck(sha(bb['ORIGINAL_TREES01.json'])==auth['union_mapping_sha256'],'full mapping authentication')
 ck(set(pins)=={r['path'] for r in m['members'] if r['kind']=='file'},'full virtual shard cover');ck(mapping is not None and len(mapping['scope_trees'])==expectedtrees,'exact original scope count');scope_summaries.extend(originals(mapping,pins,expectedtrees==5));results.append({'root':basename,'archives':expectedshards,'original_trees':expectedtrees,'regular_virtual':len(pins)})
for basename,expectedtrees in [('financial-genuine-wrapper-root-claimedrun-witness-tooling-capture01-2026-10-04',2),('financial-genuine-wrapper-root-claimedrun-recovery-helper-witness-capture01-2026-10-04',6)]:
 root=B/basename;auth=json.loads(selected(root/'UNION_AUTHENTICATION01.json'));mapping=json.loads(selected(root/'union-bytes01/ORIGINAL_TREES01.json'));ck(sha(R.encode(mapping))==auth['union_mapping_sha256'] and len(auth['archives'])==expectedtrees,'actual scope archive auth');pins={}
 for scope,rec in auth['archives'].items():
  mm=json.loads(selected(root/rec['manifest']['path']));bb=archive(root,rec['archive'],mm);meta=json.loads(bb['CAPTURE_ORIGINAL_TREE01.json']);ck(meta['original_tree']==next(t for t in mapping['scope_trees'] if t['scope']==scope),'individual full scope metadata join')
  for r in mm['members']:
   if r['kind']=='file' and r['path']!='CAPTURE_ORIGINAL_TREE01.json':pins[scope+'/'+r['path']]=(r['bytes'],r['sha256'])
 scope_summaries.extend(originals(mapping,pins));results.append({'root':basename,'archives':expectedtrees,'original_trees':expectedtrees,'original_regular':len(pins)})
# Old failed outer eight stay byte-identical; full failed union c720 is identical to successful11 virtual.
failed=B/'financial-genuine-wrapper-root-claimedrun-final-capture01-2026-10-04';names={'ACTUAL_CAPTURE01.err','ACTUAL_CAPTURE01.out','ACTUAL_TOOL_TERMINAL02.json','FAILED_SCOPE_MANIFEST03.json','ROOT_ADOPTION01.json','capture01.py','union-manifest.json','union.tar.gz'}
for n in names:selected(failed/n)
ck(sha(read(failed/'union-manifest.json'))=='c72030b48f422bcfa52b1bbb2ca3202b9c8a8447387330f818edd20a58fb8b5d' and read(failed/'union-manifest.json')==read(B/'financial-genuine-wrapper-root-claimedrun-final-capture02-2026-10-04/union-manifest.json'),'full failed c720 represented unchanged successful shards');ck(sha(read(failed/'union.tar.gz'))=='fc7d4f78ae2db603aec2b84d14d9b98558ad9ea7d356df0983253eeab019972b','failed partial bytes retained never accepted as completegzip')
# Genuine actual six review and both installed exact caller modules.
binding=doc(A/'ACTUAL_HELPER_REVIEW_BINDING01.json');selected(Path(binding['root'])/binding['manifest_name']);ck(sha(read(Path(binding['root'])/binding['manifest_name']))==binding['manifest_sha256']=='92f34904bab2f80c8465a538a47c3edb19145c10f2de2297b07257bd8cf2a73a','closed actual six review seal')
for role,expected in [('complete_installed_final11_flat_caller','f0fa6231ed61dea322021e75578187c604633df21c3acee7eade4f0497e9cab7'),('complete_installed_witness57_direct_flat_caller','5352c2e42d11d585e92187f2d51be9c42eaadcfc9b03f8e11e9a7097bf7c28ac')]:ck(any(r['sha256']==expected and role in r['roles'] for r in rows),'exact installed caller selected')
source=B/'financial-genuine-wrapper-root-claimedrun-source339-capture01-2026-10-04';sm=json.loads(selected(source/'source-manifest.json'));ab=selected(source/'source.tar.gz');ck(sha(ab)=='b5b6aad2f515447dc6566cfb716a20ef90031313d48f1ac903ab756735431e24' and sha(R.encode(sm))=='fdf77348b81a4d6df8b420b98530f5485900a0461636e1c201506106b036dfd8','actual complete Source339 selected');source_root=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');R.same(source_root,sm);archive(source,{'path':'source.tar.gz','bytes':len(ab),'sha256':sha(ab)},sm);ck(not Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-root-launch-20261004-01/attempt').exists(),'no new Parent attempt')
for mutation in ('missing','duplicate','hash','mode','path','anchor','cap'):
 bad=copy.deepcopy(groups)
 if mutation=='missing':bad[1]['rows'].pop()
 elif mutation=='duplicate':bad[1]['rows'].append(copy.deepcopy(bad[1]['rows'][-1]))
 elif mutation=='hash':bad[1]['rows'][0]['sha256']='0'*64
 elif mutation=='mode':bad[1]['rows'][0]['mode']^=1
 elif mutation=='path':bad[1]['rows'][0]['path']+='x'
 elif mutation=='anchor':bad[1]['mandatory_shared_anchors'].pop()
 else:bad[1]['rows'][0]['bytes']=4194305
 try:validate(bad)
 except (AssertionError,KeyError):pass
 else:raise AssertionError('mutation not refused '+mutation)
ck(not any(n in sys.modules for n in ('torch','numpy','pandas','scipy')),'no numerical imports')
out={'schema_version':1,'decision':'accepted-current-two-packet-scope-candidate-not-committed-selection','census_manifest_sha256':'1aad852dd1e89c07da3a8bf588b1ddd1cfb4ec34e3972ee6b71403c2b8e4a20d','rows_sha256':'70ff2feb00e4d334a14897a87222077b943643d96bff087a275bbcdd3b43569f','batches_sha256':'8f3e9ef773fdd9d2a815b3133bd28297930d02043182a4f4a8c68d982159f095','checks':count,'distinct_paths':689,'distinct_bytes':52795748,'primary':{'paths':359,'bytes':52374727,'operations':729},'supplemental':{'paths':336,'bytes':4362239,'operations':683},'shared_anchor_paths':6,'supplemental_own_raw':330,'literal_links':45,'archive_groups':results,'original_scope_denominators':scope_summaries,'actual_commit':None,'actual_remote_receipt':None,'numerical_authority':False,'qualification':'Complete current candidate bodies and archived originals verified. Exact committed selections, both real transports and actual combined recovery remain pending; six safety anchors do not transfer numerical identity or budget.'}
(H/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print('PASS',count)
