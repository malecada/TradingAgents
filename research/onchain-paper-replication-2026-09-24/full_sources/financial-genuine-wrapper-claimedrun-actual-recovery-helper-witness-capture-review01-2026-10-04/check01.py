import datetime,hashlib,json,os,stat,sys
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;ROOT=B/'financial-genuine-wrapper-root-claimedrun-recovery-helper-witness-capture01-2026-10-04';OLD=B/'financial-genuine-wrapper-claimedrun-recovery-helper-witness-capture-review01-2026-10-04';P=B/'held-consumer-final-recovery-preparation04-2026-10-03'
checks=0;categories={}
def ok(v,c):
 global checks
 if not v:raise AssertionError(c)
 checks+=1;categories[c]=categories.get(c,0)+1
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p,h):b=p.read_bytes();ok(sha(b)==h,'exact pinned body');return b
for n,h in {'recovery04.py':'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}.items():pin(P/n,h)
sys.path.insert(0,str(P));import recovery04 as R
s=pin(ROOT/'capture_helpers01.py','06f1a923e4b1d77d019276117a55d34f5942990c7e19f631783a62116224d4da');ns={'__name__':'metadata_only','__file__':str(ROOT/'capture_helpers01.py')};exec(compile(s,'exact capture source','exec'),ns)
a=json.loads(pin(ROOT/'UNION_AUTHENTICATION01.json','e8dce46bcde9adb75b0e989c4e8fa46c23c2a0cabee9013d6daf90a0d37e87ae'));u=json.loads(pin(ROOT/'union-manifest.json','dea93174e23acb5fa80ecaff9475bdafe85f05265a8c0a170424f35edb70e8b2'));t=json.loads(pin(ROOT/'ACTUAL_TOOL_TERMINAL02.json','9f148d2690c58b54a7ef51d67e0ea0fce3e16d3e120beea3e86c1ebbcf7eb123'))
pin(OLD/'MANIFEST01.json','128cffb0c122368ba8731be9f849f49dab148beef61cd2447cf5c36936e8657c')
projection=json.loads((OLD/'READBACK01.json').read_bytes())['feasibility'];actual_before=R.scan(ROOT);R.same(ROOT/'union-bytes01',u);adoption=json.loads((ROOT/'ROOT_ADOPTION01.json').read_bytes());pin(B/'financial-genuine-wrapper-claimedrun-recovery-helper-witness-capture-preparation01-2026-10-04/MANIFEST01.json',adoption['source_manifest_sha256']);ok(adoption['source_sha256']==sha(s) and adoption['independent_review_manifest_sha256']=='128cffb0c122368ba8731be9f849f49dab148beef61cd2447cf5c36936e8657c','actual source adoption exact')
mappingraw=R.read(ROOT/'union-bytes01','ORIGINAL_TREES01.json');ok(sha(mappingraw)==a['union_mapping_sha256'],'mapping auth');mapping=json.loads(mappingraw)
def census(root):
 rows=[]
 def walk(p,rel):
  x=p.lstat();sig=R.sig(x);r={'path':rel,'mode':stat.S_IMODE(x.st_mode)}
  if stat.S_ISLNK(x.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
  elif stat.S_ISDIR(x.st_mode):
   r['kind']='directory'
   for q in sorted(p.iterdir()):walk(q,q.name if rel=='.' else rel+'/'+q.name)
  else:
   ok(stat.S_ISREG(x.st_mode) and x.st_nlink==1 and x.st_size<=R.FILE,'original regular extent/type');raw=R.read(root,rel);r.update(kind='file',bytes=len(raw),sha256=sha(raw))
  ok(R.sig(p.lstat())==sig,'stable original signature');rows.append(r)
 walk(root,'.');return sorted(rows,key=lambda r:r['path'])
archive_results=[];totalbytes=files=links=typescount=0
ok(set(a['archives'])==set(ns['SCOPES'])=={x['scope'] for x in mapping['scope_trees']},'exact6 scopes')
for scope,original in sorted(ns['SCOPES'].items()):
 c=census(original);sealed=json.loads((original/'MANIFEST01.json').read_bytes())['members'];ok([r for r in c if r['path'] not in ('.','MANIFEST01.json')]==sealed,'original full equality to complete original seal');pin(original/'MANIFEST01.json',ns['SEALS'][scope]);mapped=next(x for x in mapping['scope_trees'] if x['scope']==scope)
 rows=[dict(r,union_path=scope+'/'+r['path']) if r['kind']=='file' else r for r in c];ok(mapped=={'scope':scope,'original_root':str(original),'members':rows},'exact complete original mapping')
 typescount+=len(c);files+=sum(r['kind']=='file' for r in c);links+=sum(r['kind']=='lexical-symlink' for r in c);totalbytes+=sum(r.get('bytes',0) for r in c)
 record=a['archives'][scope];mr=pin(ROOT/record['manifest']['path'],record['manifest']['sha256']);m=json.loads(mr);R.validate(m);ok(len(mr)==record['manifest']['bytes'],'manifest bytes');ar=pin(ROOT/record['archive']['path'],record['archive']['sha256']);ok(len(ar)==record['archive']['bytes']<=4194304,'archive extent');ok(record['archive']['manifest_sha256']==sha(mr),'archive manifest join')
 pr=next(x for x in projection if x['scope']==scope);ok(sha(ar)==pr['archive_sha256'] and len(ar)==pr['archive_bytes'],'actual archive exact independently frozen projection hash')
 expected=[dict(r,mode=384 if r['kind']=='file' else 448) for r in c if r['path']!='.' and r['kind']!='lexical-symlink'];metadata=ns['encoded']({'schema_version':1,'original_tree':mapped,'source_commit':mapping['source_commit'],'links_followed_or_extracted':False,'research_authority':False});expected.append({'path':'CAPTURE_ORIGINAL_TREE01.json','kind':'file','mode':384,'bytes':len(metadata),'sha256':sha(metadata)});expected.sort(key=lambda r:r['path']);ok(m=={'schema_version':1,'root_mode':448,'members':expected},'exact physical manifest and originalmode metadata')
 ok(record['original_metadata_sha256']==sha(metadata),'per-tree metadata join');ok(R.read(ROOT/'union-bytes01'/scope,'CAPTURE_ORIGINAL_TREE01.json')==metadata,'actual per-tree metadata body')
 R.same(ROOT/'union-bytes01'/scope,m)
 stream=R.framed_members(ar);seen=[]
 try:
  for name,info,body in stream:
   idx=len(seen);ok(idx<len(expected),'no archive extras');r=expected[idx];ok(name==r['path'] and info.mode==r['mode'] and info.uid==info.gid==info.mtime==0 and info.uname==info.gname=='','ordered canonical header');ok((info.isdir() and r['kind']=='directory' and info.size==0 and body==b'') or (info.isfile() and r['kind']=='file' and info.size==len(body)==r['bytes'] and sha(body)==r['sha256']),'actual full archive body/type')
   if r['kind']=='file':ok(body==R.read(ROOT/'union-bytes01'/scope,name),'actual archive physical body equality')
   seen.append(name)
 finally:stream.close()
 ok(len(seen)==record['ordinary_members']==pr['ordinary_typed'],'complete archive denominator and footer')
 sink=R.ExactSink(ar);R.tar_stream(ROOT/'union-bytes01'/scope,m,sink);ok(sink.count==len(ar) and sink.hash.hexdigest()==sha(ar),'full canonical recompression equality')
 ok(census(original)==c,'current original complete after readback')
 archive_results.append({'scope':scope,'archive_sha256':sha(ar),'archive_bytes':len(ar),'manifest_sha256':sha(mr),'members':len(seen),'canonical_recompression':True,'original_R4_framing':True,'original_files':sum(r['kind']=='file' for r in c),'original_root_mode':c[0]['mode']})
ok((files,links,totalbytes,typescount)==(4220,17,9187425,4432),'whole exact originals');ok(a['original_trees']==6 and a['original_regular_members']==files and a['original_lexical_links']==links and a['original_typed_members']==typescount and mapping['original_regular_logical_bytes']==totalbytes,'authentication exact counts');ok(len(u['members'])==a['ordinary_members']==4422,'whole virtual4415 plus6scoperoots plusmapping');ok(a['free_bytes']>=10*1024**3 and a['elapsed_seconds']<120,'recorded actual limits');ok(a['genuine_native_or_numerical_started'] is False and mapping['links_followed_or_extracted'] is False and mapping['runtime_bodies_or_empirical_stores_recovered'] is False,'no authority flags')
sm=json.loads(pin(ns['SOURCE_CAPTURE']/'source-manifest.json','fdf77348b81a4d6df8b420b98530f5485900a0461636e1c201506106b036dfd8'));pin(ns['SOURCE_CAPTURE']/'source.tar.gz','b5b6aad2f515447dc6566cfb716a20ef90031313d48f1ac903ab756735431e24');R.same(ns['SOURCE'],sm);ok(len(sm['members'])==1029,'complete Source339 actual unchanged')
q=json.loads(pin(ns['PARENT']/'REQUEST_FINAL03.json','529c9bf3c587e6160a217e8eb339882e59433b6fc0f759d0009d261f872b2bd8'));pin(ns['PARENT']/'parent01.py',q['caller_sha256'])
for ref in [*q['proofs'].values(),q['final_review']]:pin(Path(ref['path']),ref['sha256'])
for n,h in q['helper_hashes'].items():pin(ns['PARENT']/n,h)
ok(not os.path.lexists(ns['PARENT']/'attempt'),'still prelaunch Parent observation');ok(q['design_source']==mapping['source_commit']=='0a2e7639b42b9423b90743feadcda4078aa21816','current source field');pin(ns['SOURCE']/q['registration'],q['registration_sha256'])
intent=json.loads((ROOT/'INTENT01.json').read_bytes());ok(intent==t['intent'],'original intent terminal join');ok(t['actual_tool']=={'session':42360,'start_chunk':'e82f06','completion_chunk':'43aec8','exit_code':0},'actual Root tool transcript fields');out=pin(ROOT/'ACTUAL_CAPTURE01.out',t['stdout']['sha256']);err=pin(ROOT/'ACTUAL_CAPTURE01.err',t['stderr']['sha256']);ok(err==b'','empty original stderr');parsed=json.loads(out);ok(parsed['archives']==a['archives'] and parsed['original_trees']==6 and parsed['original_regular_members']==4220 and parsed['original_lexical_links']==17,'full original stdout auth join')
ok(not Path('/proc',str(intent['actual_root_pid'])).exists(),'original capture PID currently absent');groups=[];unreadable=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:v=(p/'stat').read_text().rsplit(')',1)[1].split()
 except (FileNotFoundError,ProcessLookupError):continue
 except PermissionError:unreadable.append(int(p.name));continue
 if int(v[2])==intent['actual_pgid'] or int(v[3])==intent['actual_sid']:groups.append({'pid':int(p.name),'pgrp':int(v[2]),'sid':int(v[3]),'ticks':int(v[19])})
ok(groups==[],'currently observed capture group/session absent');R.same(ROOT,actual_before);ok(True,'whole Root capture stable before after')
# Copy small raw actual records and source only; never restore originals.
for n in ('ACTUAL_CAPTURE01.out','ACTUAL_CAPTURE01.err','ACTUAL_TOOL_TERMINAL02.json','INTENT01.json','LAUNCH01.py','ROOT_ADOPTION01.json','UNION_AUTHENTICATION01.json','capture_helpers01.py'):
 with (H/('ORIGINAL_'+n)).open('xb') as f:f.write((ROOT/n).read_bytes())
result={'schema_version':1,'status':'ACCEPTED_ACTUAL_LOCAL_SIX_HELPER_CAPTURE','checks':checks,'categories':categories,'archives':archive_results,'original_regular_files':files,'original_bytes':totalbytes,'literal_links':links,'original_typed_including_roots':typescount,'virtual_members':4422,'archive_members':4415,'Root_complete_manifest':actual_before,'source_manifest_sha256':sha((ns['SOURCE_CAPTURE']/'source-manifest.json').read_bytes()),'actual_authentication_sha256':sha((ROOT/'UNION_AUTHENTICATION01.json').read_bytes()),'actual_terminal_sha256':sha((ROOT/'ACTUAL_TOOL_TERMINAL02.json').read_bytes()),'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'capture_pid_currently_absent':True,'observed_group_session_members':groups,'proc_permission_denied_pids':unreadable,'historical_process_tree_complete':False,'original_R4_fixed_six_scope_compatible':True,'general_PAX_defect_cleared':False,'actual_external_recovery':None,'actual_fresh_Root_restore':None,'numerical_release':False,'runtime_packages_rehashed_or_imported':False}
with (H/'READBACK01.json').open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'archives':archive_results,'readback_sha256':sha((H/'READBACK01.json').read_bytes()),'readback_bytes':(H/'READBACK01.json').stat().st_size,'proc_permission_denied':len(unreadable)}))
