import ast,gzip,hashlib,io,json,os,stat,subprocess,sys,tarfile
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;ROOT=Path.cwd();D=F/'financial-genuine-wrapper-root-claimedrun-source339-remote01-2026-10-04';U=F/'held-consumer-final-recovery-preparation04-2026-10-03';sys.path.insert(0,str(U));import recovery04 as a
sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):assert v,m;checks.append(m)
def read(p):return a.read(p.parent,p.name)
def git(args):
 p=subprocess.run(['git','--no-replace-objects','-c','protocol.allow=never',*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,env={'PATH':'/usr/bin:/bin','GIT_NO_LAZY_FETCH':'1','GIT_OPTIONAL_LOCKS':'0','GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','GIT_TERMINAL_PROMPT':'0'});ck(p.returncode==0 and len(p.stdout)<=8*1024**2 and len(p.stderr)<=65536,'bounded local readonlyGit');return p.stdout
sel=read(D/'SELECTED_BODIES01.json');ck(sha(sel)=='3b2d2525aa6cd75bef7e5e3516a75227ccabe372664f15ae97ba28662fab3d44','frozen original selection');q=json.loads(sel);rows=q['rows'];H=q['remote_commit'];ck(H=='c29b1580b0a198aa5a55c17215869e2d914a9580','exact committed selection');names=[r['path'] for r in rows];ck(names==sorted(set(names)) and len(rows)==176 and sum(r['bytes'] for r in rows)==17783124,'exact unique sorted176/bytes');ck(len(rows)<=506 and 11+2*len(rows)<=1024 and sum(r['bytes'] for r in rows)<=64*1024**2,'finite selected bound');rawtree=git(['ls-tree','-r','-z',H,'--',*names]);tree={}
for item in rawtree.split(b'\0'):
 if item:head,n=item.split(b'\t',1);mode,kind,oid=head.decode().split();tree[n.decode()]=(mode,kind,oid)
ck(set(tree)==set(names),'exact actual Git member closure');joins=[]
for r in rows:
 p=ROOT/r['path'];s=p.lstat();b=read(p);mode,kind,oid=tree[r['path']];ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and len(b)==r['bytes']<=4*1024**2 and sha(b)==r['sha256'],'every selected original mode/type/body');ck(mode in ('100644','100755') and kind=='blob' and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid,'every original actual Git blob OID');ck(git(['cat-file','blob',oid])==b,'immutable committed body independently read');joins.append(dict(r,git_mode=mode,git_object=oid,literal_mode=stat.S_IMODE(s.st_mode)))
ck(sha(read(D/'recover01.py'))=='0b397ccd0a014f60a414ce79d67dfd53c58a0fb61ca616a6576cc43da4bbf0aa','unchanged safe remotehelper');helper=read(D/'recover01.py').decode();ck("'fresh-recordfix-source325-01.git'" in helper,'inherited namespace explicit');ck(not any(os.path.lexists(D/n) for n in ['fresh-recordfix-source325-01.git','selected','REMOTE_RECOVERY01.json','FAILED01.json','ACTUAL_INTENT01.json']),'fresh actual remote outputs absent')
# All nine selected archives are independently raw-framed/canonically reconstructed. No extraction.
t=ast.parse(read(F/'held-consumer-final-released-scope-capture-review01-2026-10-03/check01.py'));exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('decode','recode')],type_ignores=[]),'<independent raw framing>','exec'))
archive_results=[];archive_bodies={}
for r in rows:
 if not r['path'].endswith('.tar.gz'):continue
 p=ROOT/r['path'];stem=p.name[:-7];mp=p.parent/(stem+'-manifest.json');ck(mp.relative_to(ROOT).as_posix() in names,'every archive manifest selected');m=json.loads(read(mp));raw=read(p);bodies,framing=decode(raw,m);ck(recode(m,bodies)==raw,'entire exact selected canonical archive');archive_bodies[str(p)]=(m,bodies);archive_results.append({'path':r['path'],'sha256':r['sha256'],'members':len(m['members']),'regular':sum(v['kind']=='file' for v in m['members']),'framing':framing})
C=F/'financial-genuine-wrapper-root-claimedrun-source339-capture01-2026-10-04';m,b=archive_bodies[str(C/'source.tar.gz')];S=Path(json.loads(read(C/'CAPTURE01.json'))['source_root']);ck(a.scan(S)==m and len(m['members'])==1029 and sum(r['kind']=='file' for r in m['members'])==747,'whole currentSource339 archive current');ck(git(['-C',str(S),'rev-parse','HEAD']).decode().strip()=='0a2e7639b42b9423b90743feadcda4078aa21816','actual sourceHEAD');st=git(['-C',str(S),'ls-tree','-r','-z','HEAD']);count=0
for item in st.split(b'\0'):
 if not item:continue
 head,n=item.split(b'\t',1);mode,kind,oid=head.decode().split();body=b[n.decode()];ck(kind=='blob' and hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==oid,'every current339 committed source archive body');count+=1
ck(count==339,'current339tracked');gate=json.loads(b['fixture_inputs/financial_wrapper_claimedrun01/gates.json']);ID='financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01';exp=gate['experiments'][ID];ck(len(exp['source_files'])==338 and len(exp['inputs'])==8,'actual338/eightroles')
for n,pin in exp['source_files'].items():ck(sha(b[n])==pin,'every338 actual sourcepin archived')
for role,r in exp['inputs'].items():ck(sha(b[r['path']])==r['sha256'],'every input archived')
old='financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01';ck(sha(b['research_runs/'+old+'/claim.json'])=='4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128' and sha(b['research_runs/'+old+'/failed.json'])=='35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450','exact copied spent1 failure');ck(not os.path.lexists(S/'research_runs'/ID),'no newclaim')
W=F/'financial-genuine-wrapper-root-claimedrun-witness-capture01-2026-10-04';wm,wb=archive_bodies[str(W/'union.tar.gz')];mapping=json.loads(wb['ORIGINAL_TREES01.json']);links=0;files=0
for tr in mapping['scope_trees']:
 root=Path(tr['original_root']);seen={'.'}|{p.relative_to(root).as_posix() for p in root.rglob('*')};ck(seen=={r['path'] for r in tr['members']},'whole original handoff tree membership')
 for r in tr['members']:
  p=root/r['path'];s=p.lstat();ck(stat.S_IMODE(s.st_mode)==r['mode'],'original witness literal mode')
  if r['kind']=='file':ck(read(p)==wb[r['union_path']] and sha(wb[r['union_path']])==r['sha256'],'every handoff original body archived');files+=1
  elif r['kind']=='lexical-symlink':ck(stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target'],'literal target metadata');links+=1
  else:ck(stat.S_ISDIR(s.st_mode),'original dir')
ck((files,links)==(186,13),'complete original witnesses')
E=F/'financial-genuine-wrapper-root-claimedrun-recovery-evidence-capture01-2026-10-04';ec=json.loads(read(E/'CAPTURE01.json'))
for role,info in ec['records'].items():
 em,eb=archive_bodies[str(E/(role+'.tar.gz'))];ck(a.scan(Path(info['original_root']))==em,'all four current complete recovery witness trees');seal=info['original_seal'];ck(sha(eb[seal['path']])==seal['sha256'],'complete recovery seal pin')
# Original complete selected review manifests bind their own members; inventory snapshots in census describe other roots, not own closure.
selected=set(names);closure_gaps=[]
for r in rows:
 p=ROOT/r['path']
 if p.name.startswith('MANIFEST') and p.suffix=='.json':
  doc=json.loads(read(p))
  for row in doc.get('members',[]):
   target=(p.parent/row['path']).relative_to(ROOT).as_posix()
   if row['kind']=='file' and target not in selected:closure_gaps.append({'manifest':r['path'],'missing':target})
missing=[]
for leaf,pin in [('INDEPENDENT_SOURCE_INPUT_RUNTIME01.json','059232d0f7fc8922cee526a1bd30fef2ecb51ee17103284bcaac18c77e77641c'),('MANIFEST01.json','24e6451d2a9c5ec516b99ca95bb477567e5f9ef5d13adef3bb41c0633b93e5c7')]:
 p=F/'financial-genuine-wrapper-claimedrun-actual-admission-review01-2026-10-04'/leaf;ck(sha(read(p))==pin,'actual required independent admission proof exists');ck(not any(r['sha256']==pin for r in rows),'actual independent proof absent from selected bodies');ck(not any(sha(body)==pin for _,bs in archive_bodies.values() for body in bs.values()),'actual independent proof absent from every selected archive');missing.append({'path':str(p),'sha256':pin})
ck(not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules),'no research numerical imports');x={'schema_version':1,'decision':'WITHHELD_MISSING_ACTUAL_INDEPENDENT_METADATA_ADMISSION_PROOF_TREE','selection_sha256':sha(sel),'commit':H,'selected_count':176,'selected_logical_bytes':17783124,'expected_Git_operations':363,'unique_Git_objects':len({r['git_object'] for r in joins}),'checks':len(checks),'verified_archives':archive_results,'selected_manifest_closure_gaps':closure_gaps,'mandatory_missing_original_proofs':missing,'required_correction':'Preserve this selection unchanged. Freeze successor selection adding the complete actual independent admission-review01 tree including0592/24e, then independently review exact successor; do not conflate actual-source-admission-review with actual-admission-review.','actual_network_or_restore':False,'numerical_authority':False};(O/'READBACK01.json').write_text(json.dumps(x,sort_keys=True,indent=2)+'\n');(O/'COMMITTED_BODY_JOINS01.json').write_text(json.dumps(joins,sort_keys=True,indent=2)+'\n');print(json.dumps({'checks':len(checks),'decision':x['decision'],'closure_gaps':closure_gaps}))
