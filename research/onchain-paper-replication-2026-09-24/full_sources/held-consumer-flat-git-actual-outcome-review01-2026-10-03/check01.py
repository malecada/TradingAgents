"""Independent read-only actual outcome: no prove/populate/create/Owner/native/network."""
import hashlib,json,os,shutil,stat,sys,time
from pathlib import Path
from unittest.mock import patch
O=Path(__file__).resolve().parent;F=O.parent;P=F/'held-consumer-flat-git-root-specification01-2026-10-03';H=F/'held-consumer-flat-git-recovery-preparation01-2026-10-03';sys.path.insert(0,str(H));import git_recovery01 as m
from bounded_git_fd01 import git
sha=lambda b:hashlib.sha256(b).hexdigest();checks=[];observed=[];queries=[];pins={}
def ck(ok,label):
 assert ok,label
 checks.append(label)
def pinned(path,pin):
 raw=m.a.read(path.parent,path.name);ck(sha(raw)==pin,'pin '+str(path));pins[str(path)]={'bytes':len(raw),'sha256':sha(raw)};return raw
def document(path,pin=None):
 raw=pinned(path,pin) if pin else m.a.read(path.parent,path.name);value=json.loads(raw);ck(m.a.encode(value)==raw,'canonical '+path.name);return value
spec=document(P/'SPEC01.json','1565b8533578ee862d019bdfe036b012011f6946bdcf3e22b1cbc4aaea877c4f');expected=document(Path(spec['expected_file']),spec['expected_sha256']);root=Path(spec['output_root']);proofraw=pinned(root/'proof.json','b4544ebb75a5411b99d07fccd5c34ed72e5c40f9f53a6e6558dfaf9bb3523c5c');proof=json.loads(proofraw);ck(m.a.encode(proof)==proofraw,'canonical actual proof')
for name,pin in [('git_recovery01.py','f0c7bab42387eb75d3f37b45f785de591090e12b49f0fed1e2c67d0c742dbc59'),('bounded_git_fd01.py','4f997af0a6bdbe64e588241759ce596d751ee556357793af2f1c63cd0fdef87a'),('archive03.py','785b957f93e22b18b1d3c00a73cacc75b6028bab9566d737b40903dcffc4964e')]:pinned(H/name,pin)
run=document(P/'ACTUAL_RUN_REQUEST01.json');terminal=document(P/'ACTUAL_TERMINAL01.json');pid=document(P/'ACTUAL_PID01.json');ck(terminal['exit']==0 and terminal['pid']==pid['pid']==3995769 and terminal['proof_sha256']==sha(proofraw) and not Path('/proc/'+str(pid['pid'])).exists(),'actual terminal exit/pin and observed parent absent');ck(terminal['elapsed_seconds']<300 and terminal['free_bytes']>=m.a.FLOOR,'actual elapsed/floor observation');ck(run['existing_private_output']==str(root) and run['argv']==[str(Path('/home/malecada/master_thesis/TradingAgents-audit-fixes/.venv/bin/python')),'-B',str(H/'git_recovery01.py'),'--spec',str(P/'SPEC01.json'),'--spec-sha256','1565b8533578ee862d019bdfe036b012011f6946bdcf3e22b1cbc4aaea877c4f'],'exact actual command')
for stream in ('stdout','stderr'):raw=m.a.read(P,'GIT_PROOF01.'+stream);ck(raw==b'' and sha(raw)==terminal[stream+'_sha256'],'empty actual '+stream)
for name,pin in [('FINAL03.md',run['exact_spec_review_sha256']),('MANIFEST03.json',run['exact_spec_review_manifest_sha256'])]:pinned(F/'held-consumer-flat-git-root-specification-review01-2026-10-03'/name,pin)
originreview=F/'held-consumer-final-baseline-remote-recovery-review02-2026-10-03';pinned(originreview/'REVIEW02.md',run['complete_archival_review_sha256']);originmanifest=sha((originreview/'MANIFEST02.json').read_bytes());ck(originmanifest.startswith('3623'),'exact external-review manifest prefix supplied by Root')
remote=F/'held-consumer-final-baseline-root-remote-recovery02-2026-10-03';pinned(remote/'REMOTE_RECOVERY02.json','e4c0d191f87816717e3239c627421d5096e79466f4234a85ed6d4cdaf610ea9d')
view=m.FlatView(Path(spec['flat_root']));view.begin();fd=None
try:
 with patch.object(m,'ObjectStore',side_effect=AssertionError('proof rerun forbidden')),patch.object(m.a,'framed_members',side_effect=AssertionError('unused failed decoder')):
  q=m.chain(view,Path(spec['bundle']),Path(spec['request_file']),spec['request_sha256'],spec['capture_sha256'],spec['recovery_sha256'])
 ck(len(view.expected)==676,'complete actual676 flat files');maps=view.maps['capsule'];archive={r['path']:r for r in view.manifests['capsule']['members']};selected=[r for r in archive.values() if r['kind']=='file' and (m.LOOSE.fullmatch(r['path']) or m.PACK.fullmatch(r['path']))];listed=[{k:r[k] for k in ('path','mode','bytes','sha256')} for r in selected];ck(proof['object_files']==listed and len(listed)==354,'exact all354 recovered object metadata')
 files={'HEAD':b'ref: refs/heads/unborn\n','config':b'[core]\nrepositoryformatversion = 0\nbare = true\n','proof.json':proofraw};names=set(files)|{r['path'][5:] for r in selected};dirs={'objects','refs'}
 for name in names:
  parent=Path(name).parent
  while str(parent)!='.':dirs.add(str(parent));parent=parent.parent
 actual_files=set();actual_dirs=set()
 for path in root.rglob('*'):
  s=path.lstat();name=str(path.relative_to(root));ck(path.resolve()==path,'no redirected store path '+name)
  if stat.S_ISDIR(s.st_mode):ck(stat.S_IMODE(s.st_mode)==0o700,'private store directory '+name);actual_dirs.add(name)
  else:ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600,'singleton600 file '+name);actual_files.add(name)
 ck(actual_files==names and actual_dirs==dirs,'complete exact proof-store skeleton/objects/no extras')
 for r in selected:
  name=r['path'][5:];raw=m.a.read(root,name);flatbody=view.body(r['path']);ck(raw==flatbody and len(raw)==r['bytes'] and sha(raw)==r['sha256'],'installed object exact recovered bytes '+name);observed.append({'path':name,'bytes':len(raw),'sha256':sha(raw),'original_mode_metadata':r['mode'],'actual_mode':stat.S_IMODE((root/name).stat().st_mode)})
 for n,b in files.items():ck(m.a.read(root,n)==b,'fixed/result file '+n)
 fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);st=os.fstat(fd);rootpin=(st.st_dev,st.st_ino,st.st_mode,st.st_uid);ck(stat.S_IMODE(st.st_mode)==0o700 and st.st_uid==os.geteuid(),'actual root acquired private')
 def query(args,request=b''):
  before=os.fstat(fd);ck((before.st_dev,before.st_ino,before.st_mode,before.st_uid)==rootpin,'held root before query');out=git(fd,['--no-replace-objects','--literal-pathspecs','--git-dir=.',*args],request,cap=8*1024**2);after=root.lstat();ck((after.st_dev,after.st_ino,after.st_mode,after.st_uid)==rootpin,'held root after query');queries.append({'args':args,'request_bytes':len(request),'returned_bytes':len(out)});return out
 groups={expected['source']:list(expected['current']),expected['selected_c6']['commit']:list(expected['selected_c6']['rows'])}
 for row in expected['historical']['lookups']:groups.setdefault(row['commit'],[]).append({k:v for k,v in row.items() if k!='commit'})
 all_bodies={};trees={};commit_bodies={}
 for commit,rows in groups.items():
  raw=query(['cat-file','--batch'],(commit+'\n').encode());end=raw.index(b'\n');head=raw[:end].split();body=raw[end+1:-1];ck(len(head)==3 and head[0].decode()==commit and head[1]==b'commit' and int(head[2])==len(body) and raw[-1:]==b'\n' and hashlib.sha1(b'commit '+str(len(body)).encode()+b'\0'+body).hexdigest()==commit,'real commit body/OID '+commit);commit_bodies[commit]=body
  raw=query(['ls-tree','-r','-z',commit]);ck(raw.endswith(b'\0'),'tree frame '+commit);tree={}
  for item in raw.split(b'\0')[:-1]:
   h,n=item.split(b'\t',1);mode,kind,oid=h.decode().split();name=n.decode();ck(name not in tree,'tree unique '+name);tree[name]=(mode,kind,oid)
  trees[commit]=tree
  if commit==expected['source']:ck(set(tree)=={r['path'] for r in rows} and len(tree)==246,'actual exact current246 tree')
  for off in range(0,len(rows),128):
   batch=rows[off:off+128];req=''.join(commit+':'+r['path']+'\n' for r in batch).encode();raw=query(['cat-file','--batch'],req);pos=0
   for r in batch:
    m.row_check(r);name=r['path'];end=raw.index(b'\n',pos);h=raw[pos:end].split();n=int(h[2]);start=end+1;b=raw[start:start+n];ck(len(h)==3 and h[1]==b'blob' and n==r['bytes']<=m.a.FILE and raw[start+n:start+n+1]==b'\n','actual blob framing '+name);oid=hashlib.sha1(b'blob '+str(n).encode()+b'\0'+b).hexdigest();ck(oid==h[0].decode()==r['object'] and sha(b)==r['sha256'] and tree[name]==(r['git_mode'],'blob',oid),'actual tree/blob/OID/size/hash '+name);all_bodies[(commit,name)]=b
    if commit==expected['source']:ck(view.body(name)==b and r['git_mode']==('100755' if archive[name]['mode']&0o100 else '100644'),'current Git vs recovered flat '+name)
    pos=start+n+1
   ck(pos==len(raw),'batch complete no extras')
 source=expected['source'];regraw=view.body(q['registration']);ck(sha(regraw)==q['registration_sha256'] and all_bodies[(source,q['registration'])]==regraw,'actual recovered current registration');reg=json.loads(regraw);ex=reg['experiments']['original-import-held-success-20261003-01'];refs=dict(ex['source_files']);refs[q['registration']]=q['registration_sha256'];ck(len(refs)==205 and all(sha(all_bodies[(source,name)])==pin for name,pin in refs.items()),'all205 actual committed source/registration joins');ck(len(ex['inputs'])==33,'33 actual opaque inputs')
 for name,r in ex['inputs'].items():ck(sha(view.body(r['path']))==r['sha256'],'opaque input '+name)
 required=set();history=[]
 for r in expected['historical']['claims']:
  ident=r['identity'];claimraw=view.body('research_runs/'+ident+'/claim.json');termraw=view.body('research_runs/'+ident+'/failed.json');c=json.loads(claimraw);t=json.loads(termraw);ck(sha(claimraw)==r['claim_sha256'] and sha(termraw)==r['terminal_sha256'],'original failed body pins '+ident);ck(c['source']==r['source'] and c['design_source']==r['design_source'] and c['registration']==r['registration'] and c['registration_sha256']==r['registration_sha256'] and c['experiment_id']==t['experiment_id']==ident and t['claim_sha256']==sha(claimraw) and t['status']=='failed','original failed/source/design gate '+ident);ck(c['effective_attempt_budget']==r['effective_budget'] and c['family']['attempt_budget']==2 and c['family']['prior_attempts']==0 and 'research_runs/'+ident+'/complete.json' not in maps,'original budget/failure-only '+ident)
  refs=dict(c['experiment']['source_files']);refs[c['experiment']['charter']['path']]=c['experiment']['charter']['sha256']
  for name,pin in refs.items():ck(sha(all_bodies[(c['source'],name)])==pin,'historical source/charter '+name);required.add((c['source'],name))
  for commit in (c['source'],c['design_source']):
   body=all_bodies[(commit,c['registration'])];gate=json.loads(body);ck(sha(body)==c['registration_sha256'] and gate['program_id']==c['program_id'] and gate['experiments'][ident]==c['experiment'] and gate['families'][c['experiment']['family']]==c['family'],'actual committed original gate/family '+ident);required.add((commit,c['registration']))
  history.append({'identity':ident,'status':t['status'],'effective_budget':c['effective_attempt_budget'],'source':c['source'],'design_source':c['design_source']})
 ck(required=={(r['commit'],r['path']) for r in expected['historical']['lookups']} and len(required)==638,'entire exact historical638 required union')
 for flag in ('full_c6_ancestry','full_original_filesystem','original_posix_modes_instantiated','external_origin_proved','runtime_recovered','outside_stores_recovered','research_authority'):ck(proof[flag] is False,'scope false '+flag)
 ck(proof['current_committed_files']==246 and proof['source_registration_joins']==205 and proof['opaque_inputs']==33 and proof['selected_c6_paths']==26 and proof['historical_lookups']==638,'actual independently derived cardinalities');ck(proof['git_operations']==1589<=m.MAX_CALLS and proof['git_returned_bytes']==17348330<=m.TOTAL,'recorded operation/return counters finite')
 for field in ('request_sha256','capture_sha256','recovery_sha256','expected_sha256'):ck(proof[field]==spec[field],'actual exact proof pin '+field)
 ck(m.a.read(root,'proof.json')==proofraw,'proof unchanged after readonly verification');view.finish();allocated=root.stat().st_blocks*512+sum(p.lstat().st_blocks*512 for p in root.rglob('*'));logical=sum(p.stat().st_size for p in root.rglob('*') if p.is_file());ck(allocated<=m.TOTAL and logical<=m.TOTAL,'actual complete store allocated/logical bound');free=shutil.disk_usage(root).free;ck(free>=m.a.FLOOR,'fresh observed10GiBfloor')
 result={'decision':'ACCEPTED_ACTUAL_SELECTED_RECOVERED_GIT_JOINS_ONLY','proof_sha256':sha(proofraw),'source':source,'actual_parent':{'pid':pid['pid'],'terminal_exit':terminal['exit'],'recorded_elapsed_seconds':terminal['elapsed_seconds'],'currently_absent':not Path('/proc/'+str(pid['pid'])).exists()},'independent_current_rows':246,'independent_source_registration_rows':205,'independent_opaque_inputs':33,'independent_selected_c6_rows':26,'independent_historical_lookups':638,'history':history,'actual_object_files':len(selected),'actual_object_bytes':sum(r['bytes'] for r in selected),'store_logical_bytes':logical,'store_allocated_bytes':allocated,'free_bytes_observed':free,'independent_git_calls':len(queries),'independent_git_returned_bytes':sum(r['returned_bytes'] for r in queries),'checks':len(checks),'external_origin_review_sha256':run['complete_archival_review_sha256'],'external_origin_review_manifest_sha256':originmanifest,'proof_helper_rerun':False,'actual_store_modified':False,'full_c6_ancestry':False,'native_or_research_authority':False};(O/'READBACK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');(O/'OBJECT_INVENTORY01.json').write_text(json.dumps(observed,indent=2)+'\n');(O/'QUERIES01.json').write_text(json.dumps(queries,indent=2)+'\n');(O/'PINS01.json').write_text(json.dumps(pins,sort_keys=True,indent=2)+'\n');print(json.dumps(result,indent=2))
finally:
 if fd is not None:os.close(fd)
 view.close()
