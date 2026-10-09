import pathlib,json,hashlib,tarfile,io,os,stat,subprocess,datetime
ROOT=pathlib.Path.cwd();R=pathlib.Path(__file__).resolve().parent;F=R.parent.parent;D=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/outcome11'
h=lambda b:hashlib.sha256(b).hexdigest(); evidence={}
def load(p):
 b=p.read_bytes();evidence[str(p.relative_to(ROOT))]=h(b);return json.loads(b)
def pin(p,sha):assert h(p.read_bytes())==sha; evidence[str(p.relative_to(ROOT))]=sha
review=load(R.parent/'TOOLS_REVIEW01.json');assert evidence[str((R.parent/'TOOLS_REVIEW01.json').relative_to(ROOT))]=='026d250adfdea4a4cd811e755cada03715b4e6a302267190c4956c32e3de51d2'
for ref in review['helpers']:pin(ROOT/ref['path'],ref['sha256'])
r=load(D/'FRESH_GIT_RECOVERY11.json');pin(ROOT/r['capture']['path'],r['capture']['sha256']);c=load(ROOT/r['capture']['path']);pin(ROOT/c['selection']['path'],c['selection']['sha256']);s=load(ROOT/c['selection']['path'])
a=ROOT/r['returned_archive']['path'];raw=a.read_bytes();assert len(raw)==r['returned_archive']['bytes']==1976320 and h(raw)==r['returned_archive']['sha256']==c['archive']['sha256'];assert raw==(ROOT/c['archive']['path']).read_bytes();pin(a,h(raw))
rows=sorted(s['rows']+s['directories'],key=lambda x:x['path']);assert len(s['rows'])==178 and len(s['directories'])==58 and s['symlinks']==0 and sum(x['bytes'] for x in s['rows'])==1603541
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
ops=load(D/'GIT_OPERATIONS11.json');assert ops==r['operations'] and len(ops)==13
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
prior=load(ROOT/s['baseline_actual_recovery']['path']);assert h((ROOT/s['baseline_actual_recovery']['path']).read_bytes())==s['baseline_actual_recovery']['sha256'] and prior['source']==s['baseline_source'];priorselection=load((ROOT/s['baseline_actual_recovery']['path']).parent/'SELECTION10.json');old={x['path']:x for x in priorselection['rows']}
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
terminal=[k for k in bodies if k.endswith('full27-entry01-2026-10-09/ROOT_TERMINAL01.json')];assert len(terminal)==1 and h(bodies[terminal[0]])=='818fd2901a7ed8c2aa33d71b499c99fce3dcc4da6d7bbbb8ddcd3a507428ebc1'
assert not any('full28' in k or '20261009-28' in k for k in bodies)
outcome=next(k for k in bodies if k.endswith('full27-outcome-review01-2026-10-09/OUTCOME_REVIEW01.json'));o=json.loads(bodies[outcome]);assert o['scientific_disposition']['durable_journal_cells']==4096 and o['scientific_disposition']['completed_cell_credit']==0 and o['scientific_disposition']['training'] is None
v={'decision':'accepted','scope':'Actual returned full27 outcome11 selected public increment only','source':source,'archive_sha256':h(raw),'archive_bytes':len(raw),'regular_bodies':178,'regular_bytes':1603541,'directories':58,'symlinks':0,'git_operations_all_zero':13,'tracked_public_bodies_joined_to_captured_commit':tracked,'reused_prior_regular_rows':len(s['exact_unchanged_prior_rows_reused']),'same_archive_reencoding':True,'seven_scope_current_inventory_join':True,'no_alternates':True,'offline_git_no_lazy_fetch':True,'evidence':evidence,'qualifications':['No network, archive extraction or array decoding; binary records/scores/origins authenticated as opaque bytes only.','Commit-only/direct selected blob recovery, not whole Git tree, installed runtime, POSIX restoration or deletion authority.','Partial4096 cells remain zero scientific completion; no completed MCM or training inference.','Root terminal remains Root-reported tool observation, not raw terminal transcript export.','Later full28 preparation excluded; current source may evolve after captured commit without changing this receipt.'],'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(R/'RECOVERY_REVIEW01.json').write_text(json.dumps(v,indent=2)+'\n');print(h((R/'RECOVERY_REVIEW01.json').read_bytes()))
