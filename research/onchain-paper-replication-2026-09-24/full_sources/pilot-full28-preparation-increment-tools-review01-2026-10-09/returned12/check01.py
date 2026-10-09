import pathlib,json,hashlib,tarfile,io,os,stat,subprocess,datetime
ROOT=pathlib.Path.cwd();R=pathlib.Path(__file__).resolve().parent;F=R.parent.parent;D=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/full28increment12'
h=lambda b:hashlib.sha256(b).hexdigest(); evidence={}
def load(p):
 b=p.read_bytes();evidence[str(p.relative_to(ROOT))]=h(b);return json.loads(b)
def pin(p,sha):assert h(p.read_bytes())==sha; evidence[str(p.relative_to(ROOT))]=sha
review=load(R.parent/'TOOLS_REVIEW01.json');assert evidence[str((R.parent/'TOOLS_REVIEW01.json').relative_to(ROOT))]=='eb2aab24c2ae78af600a56a164448df9ac4d8f28d5f61607444affaa49b90033'
for ref in review['helpers'].values():pin(ROOT/ref['path'],ref['sha256'])
r=load(D/'FRESH_GIT_RECOVERY12.json');pin(ROOT/r['capture']['path'],r['capture']['sha256']);c=load(ROOT/r['capture']['path']);pin(ROOT/c['selection']['path'],c['selection']['sha256']);s=load(ROOT/c['selection']['path'])
a=ROOT/r['returned_archive']['path'];raw=a.read_bytes();assert len(raw)==r['returned_archive']['bytes']==4311040 and h(raw)==r['returned_archive']['sha256']==c['archive']['sha256'];assert raw==(ROOT/c['archive']['path']).read_bytes();pin(a,h(raw))
rows=sorted(s['rows']+s['directories'],key=lambda x:x['path']);assert len(s['rows'])==172 and len(s['directories'])==18 and s['symlinks']==0 and sum(x['bytes'] for x in s['rows'])==3977317
bodies={};reencoded=io.BytesIO()
with tarfile.open(fileobj=io.BytesIO(raw),mode='r') as t,tarfile.open(fileobj=reencoded,mode='w',format=tarfile.PAX_FORMAT) as out:
 members=t.getmembers();assert len(members)==len(rows)==len({x.name for x in members})
 for m,x in zip(members,rows,strict=True):
  assert m.name==x['path'] and m.mode==int(x['mode'],8) and m.uid==m.gid==m.mtime==0
  ti=tarfile.TarInfo(x['path']);ti.mode=int(x['mode'],8);ti.uid=ti.gid=ti.mtime=0
  if x['type']=='directory':assert m.isdir();ti.type=tarfile.DIRTYPE;out.addfile(ti)
  else:
   assert x['type']=='regular' and m.isfile();body=t.extractfile(m).read();assert len(body)==m.size==x['bytes'] and h(body)==x['sha256'];bodies[x['path']]=body;ti.size=len(body);out.addfile(ti,io.BytesIO(body))
assert reencoded.getvalue()==raw
ops=load(D/'GIT_OPERATIONS12.json');assert ops==r['operations'] and len(ops)==13
for op in ops:
 assert op['exit_code']==0
 for kind in ('stdout','stderr'):
  p=D/(op['operation']+'.'+kind);b=p.read_bytes();assert len(b)==op[kind+'_bytes'] and h(b)==op[kind+'_sha256'];evidence[str(p.relative_to(ROOT))]=h(b)
B=pathlib.Path(r['fresh_bare']);env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0'}
def git(args,cwd=ROOT):return subprocess.check_output(['git',*args],cwd=cwd,env=env,timeout=10)
assert not (B/'objects/info/alternates').exists() and not (B/'objects/info/http-alternates').exists()
source=r['source'];assert source==r['actual_remote_head']==r['actual_fetch_head']==git(['rev-parse','FETCH_HEAD'],B).decode().strip()
commit=git(['cat-file','commit',source],B);assert commit==git(['cat-file','commit',source])==(D/'actual_external_commit_body.stdout').read_bytes() and h(commit)==r['commit_body_sha256']
assert (D/'remote_actual_branch_readback.stdout').read_text().split()[0]==source
assert git(['ls-tree',source,'--',c['archive']['path']]).decode().strip()==r['local_commit_tree_join'];assert git(['cat-file','blob',r['archive_git_blob_oid']],B)==raw
assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==r['archive_git_blob_oid']
prior=load(ROOT/s['baseline_actual_recovery']['path']);assert h((ROOT/s['baseline_actual_recovery']['path']).read_bytes())==s['baseline_actual_recovery']['sha256'] and prior['source']==s['baseline_source'];priorselection=load((ROOT/s['baseline_actual_recovery']['path']).parent/'SELECTION11.json');old={x['path']:x for x in priorselection['rows']}
for name in s['exact_unchanged_prior_rows_reused']:
 x=old[name];p=ROOT/name;st=p.lstat();assert name not in bodies and stat.S_ISREG(st.st_mode) and format(stat.S_IMODE(st.st_mode),'04o')==x['mode'] and st.st_size==x['bytes'] and h(p.read_bytes())==x['sha256']
for name in s['exact_already_recovered_duplicate_exclusions']:assert name not in bodies and h((ROOT/name).read_bytes())==prior['returned_archive']['sha256']
selected={x['path']:x for x in rows}
for scope in s['actual_scope_states']:
 p=ROOT/scope['path'];assert p.exists()==scope['exists']
 for q in [p,*p.rglob('*')]:
  rel=str(q.relative_to(ROOT));assert rel in selected
  x=selected[rel];st=q.lstat();assert format(stat.S_IMODE(st.st_mode),'04o')==x['mode']
  if q.is_file():assert h(q.read_bytes())==x['sha256']
# Authenticate tracked selected public code/docs at captured commit; ignored outcome stores are archive-bound.
tracked=0
for name,body in bodies.items():
 if name.startswith(('research_artifacts/','research_runs/')):continue
 line=git(['ls-tree',source,'--',name]).decode().strip();assert line
 mode,kind,rest=line.split(maxsplit=2);oid,path=rest.split('\t',1);assert path==name and kind=='blob' and git(['cat-file','blob',oid])==body;tracked+=1

assert not s['actual_scope_states'] and not any(k.startswith(('research_artifacts/','research_runs/')) for k in bodies)
entry='research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full28-entry01-2026-10-09/'
release=json.loads(bodies[entry+'RELEASE_REVIEW01.json']);binding=json.loads(bodies[entry+'BINDING01.json']);gate=json.loads(bodies[entry+'gate01.json'])
assert release['decision']=='accepted' and len(release['evidence'])==537 and release['actual_final_binding_sha256']==h(bodies[entry+'BINDING01.json'])
inputs=json.loads(bodies['research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full28-transport-binding01-2026-10-09/ALL_INPUT_REFS01.json']);assert len(inputs)==64
private=inputs['archive_transport'];assert private['path'] not in bodies
# Public source/input closure is authenticated at captured commit; private ref is never opened.
public_joined=0
for name,digest in release['evidence'].items():
 if name==private['path']:continue
 line=git(['ls-tree',source,'--',name]).decode().strip();assert line,name
 mode,kind,rest=line.split(maxsplit=2);oid,path=rest.split('\t',1);assert kind=='blob' and path==name
 assert h(git(['cat-file','blob',oid]))==digest,name
 public_joined+=1
for name in ['root_io28_01.py','preflight28_01.py','preflight28_01-PREDECESSOR01.py','gate01-PREDECESSOR01.json','gate01-PREDECESSOR02.json','ADMISSION_CHECK01.json','ADMISSION_CHECK02.json','LIVE_CHECK01.json']:
 assert entry+name in bodies,name
source_review=json.loads(bodies['research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full28-final-entry-review01-2026-10-09/SOURCE_REVIEW01.json']);assert source_review['source_count']==416 and source_review['input_count']==64
assert source=='90d55a1ed5fd810f84f0d951c7895f502fa279fc' and h(raw)=='a68955180b2adbad5075177201a607b588dca1362fa88921d6e3dcab5cea2722'
assert (D/'local_head.stdout').read_text().strip()==source and (D/'fetched_head_readback.stdout').read_text().strip()==source
assert hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest()==source
assert (D/'actual_external_archive_blob_return.stdout').read_bytes()==raw
assert (D/'local_archive_git_tree_join.stdout').read_text().strip()==r['local_commit_tree_join']
v={'decision':'accepted','scope':'Actual returned declared full28 preparation12 public increment only','source':source,'archive_sha256':h(raw),'archive_bytes':len(raw),'regular_bodies':172,'regular_bytes':3977317,'directories':18,'symlinks':0,'git_operations_all_zero':13,'tracked_public_bodies_joined_to_captured_commit':tracked,'release_evidence_refs':537,'public_release_refs_joined_at_captured_commit':public_joined,'private_ref_body_opened':False,'private_ref_absent_from_archive':True,'source_count':416,'input_count':64,'original_predecessor_gate_caller_checks_preserved':True,'same_archive_reencoding':True,'no_alternates':True,'offline_git_no_lazy_fetch':True,'evidence':evidence,'qualifications':['Recorded actual fresh remote return verified offline; no new network operation or current remote availability claim.','No extraction, graph/numerical imports, private930-byte dispatch body, installed runtime restoration, POSIX reconstruction or deletion authority.','Public source/inputs/537-reference release bytes authenticated at captured source, not future capacity/admission or empirical completion.','Full27 failed outcome remains separately preserved predecessor; this archive has no empirical output scopes.','Source tooling review reused; no new source matrix, numerical run, claim or launch.'],'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(R/'RECOVERY_REVIEW01.json').write_text(json.dumps(v,indent=2)+'\n');print(h((R/'RECOVERY_REVIEW01.json').read_bytes()))
