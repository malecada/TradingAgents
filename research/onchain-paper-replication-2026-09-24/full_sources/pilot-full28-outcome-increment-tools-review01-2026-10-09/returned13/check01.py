import pathlib,json,hashlib,tarfile,io,os,stat,subprocess,datetime
ROOT=pathlib.Path.cwd();R=pathlib.Path(__file__).resolve().parent;F=R.parent.parent;D=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/outcome13';evidence={};cache={};disk_bytes=git_bytes=0;h=lambda b:hashlib.sha256(b).hexdigest();limit=64*1024**2
sig=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def read(p):
 global disk_bytes
 p=pathlib.Path(p)
 if p not in cache:
  before=p.lstat();assert stat.S_ISREG(before.st_mode) and before.st_nlink==1;data=p.read_bytes();assert sig(p.lstat())==sig(before);disk_bytes+=len(data);assert disk_bytes+git_bytes<=limit;cache[p]=data;evidence[str(p.relative_to(ROOT))]=h(data)
 return cache[p]
def load(p):return json.loads(read(p))
def pin(p,expected):assert h(read(p))==expected
review=load(R.parent/'TOOLS_REVIEW01.json');assert review['decision']=='accepted'
for name,expected in review['helpers'].items():pin(D/name,expected)
r=load(D/'FRESH_GIT_RECOVERY13.json');pin(ROOT/r['capture']['path'],r['capture']['sha256']);c=load(ROOT/r['capture']['path']);pin(ROOT/c['selection']['path'],c['selection']['sha256']);s=load(ROOT/c['selection']['path']);raw=read(ROOT/r['returned_archive']['path']);assert len(raw)==10444800==r['returned_archive']['bytes'] and h(raw)==r['returned_archive']['sha256']==c['archive']['sha256']=='63f929b853b88add412ae0832133dee2a874e448f245b33726812499c1bf1020'
# Capture original independently hashed; returned archive will additionally be reencoded and Git-bound.
assert read(ROOT/c['archive']['path'])==raw
rows=sorted(s['rows']+s['directories'],key=lambda x:x['path']);assert len(s['rows'])==738 and len(s['directories'])==177 and s['symlinks']==0 and sum(x['bytes'] for x in s['rows'])==8907878
bodies={};encoded=io.BytesIO();parsed_member_bytes=0
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tar,tarfile.open(fileobj=encoded,mode='w',format=tarfile.PAX_FORMAT) as out:
 members=tar.getmembers();assert len(members)==len(rows)==len({m.name for m in members})
 for m,row in zip(members,rows,strict=True):
  assert m.name==row['path'] and m.mode==int(row['mode'],8) and m.uid==m.gid==m.mtime==0
  ti=tarfile.TarInfo(row['path']);ti.mode=m.mode;ti.uid=ti.gid=ti.mtime=0
  if row['type']=='directory':assert m.isdir();ti.type=tarfile.DIRTYPE;out.addfile(ti)
  else:
   assert row['type']=='regular' and m.isfile();data=tar.extractfile(m).read();parsed_member_bytes+=len(data);assert len(data)==m.size==row['bytes'] and h(data)==row['sha256'];bodies[row['path']]=data;ti.size=len(data);out.addfile(ti,io.BytesIO(data))
assert encoded.getvalue()==raw
ops=load(D/'GIT_OPERATIONS13.json');assert ops==r['operations'] and len(ops)==13
for op in ops:
 assert op['exit_code']==0
 for kind in ('stdout','stderr'):
  data=read(D/(op['operation']+'.'+kind));assert len(data)==op[kind+'_bytes'] and h(data)==op[kind+'_sha256']
B=pathlib.Path(r['fresh_bare']);env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0'}
def git(args,cwd=ROOT):
 global git_bytes
 result=subprocess.check_output(['git',*args],cwd=cwd,env=env,timeout=15);git_bytes+=len(result);assert disk_bytes+git_bytes<=limit;return result
assert not (B/'objects/info/alternates').exists() and not (B/'objects/info/http-alternates').exists();source=r['source'];assert source==r['actual_remote_head']==r['actual_fetch_head']==git(['rev-parse','FETCH_HEAD'],B).decode().strip()=='dde0a0de34389aa503bdd1e2820460b45932c81f'
commit=git(['cat-file','commit',source],B);assert commit==git(['cat-file','commit',source])==read(D/'actual_external_commit_body.stdout') and h(commit)==r['commit_body_sha256'];assert read(D/'remote_actual_branch_readback.stdout').decode().split()[0]==source
assert git(['ls-tree',source,'--',c['archive']['path']]).decode().strip()==r['local_commit_tree_join'];assert git(['cat-file','blob',r['archive_git_blob_oid']],B)==raw;assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==r['archive_git_blob_oid']
prior=load(ROOT/s['baseline_actual_recovery']['path']);assert h(read(ROOT/s['baseline_actual_recovery']['path']))==s['baseline_actual_recovery']['sha256'] and prior['source']==s['baseline_source'];priorselection=load((ROOT/s['baseline_actual_recovery']['path']).parent/'SELECTION12.json');old={x['path']:x for x in priorselection['rows']}
for name in s['exact_unchanged_prior_rows_reused']:
 row=old[name];p=ROOT/name;st=p.lstat();assert name not in bodies and stat.S_ISREG(st.st_mode) and format(stat.S_IMODE(st.st_mode),'04o')==row['mode'] and st.st_size==row['bytes'] and h(read(p))==row['sha256']
for name in s['exact_already_recovered_duplicate_exclusions']:assert name not in bodies and h(read(ROOT/name))==prior['returned_archive']['sha256']
selected={x['path']:x for x in rows}
for scope in s['actual_scope_states']:
 p=ROOT/scope['path'];assert p.exists()==scope['exists']
 for q in [p,*p.rglob('*')]:
  rel=str(q.relative_to(ROOT));assert rel in selected;row=selected[rel];st=q.lstat();assert format(stat.S_IMODE(st.st_mode),'04o')==row['mode']
  if stat.S_ISREG(st.st_mode):assert h(read(q))==row['sha256']
tracked=0
for name,body in bodies.items():
 if name.startswith(('research_artifacts/','research_runs/')):continue
 line=git(['ls-tree',source,'--',name]).decode().strip();assert line;mode,kind,rest=line.split(maxsplit=2);oid,path=rest.split('\t',1);assert path==name and kind=='blob' and hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==oid;tracked+=1
# Exact installed composition, failed28 and separately recovered original group are included.
install_name=next(n for n in bodies if n.endswith('pilot-full28-to-successor-root-integration01-2026-10-09/INSTALL01.json'));install=json.loads(bodies[install_name]);assert len(install['files'])==17
for row in install['files']:assert h(bodies[row['path']])==row['after_sha256']
outcome_name=next(n for n in bodies if n.endswith('full28-outcome-review01-2026-10-09/OUTCOME_REVIEW01.json'));outcome=json.loads(bodies[outcome_name]);assert outcome['scientific_disposition']['confirmed_post_sink_cells']==61440 and outcome['scientific_disposition']['whole_cell_credit']==0 and outcome['scientific_disposition']['training'] is None
group=next(n for n in bodies if n.endswith('full28-group-fresh-return01-2026-10-09/original-group-return01.tar'));assert len(bodies[group])==3532800 and h(bodies[group])=='4526a050543542cb47de4bcc393d36f904ef3ad0fa07f01ee5b3b4a8c60b81a8';assert any(n.endswith('full28-entry01-2026-10-09/ROOT_TERMINAL01.json') for n in bodies)
v={'decision':'accepted','scope':'Actual returned full28 outcome13 selected public increment only','source':source,'archive_sha256':h(raw),'archive_bytes':len(raw),'regular_bodies':738,'regular_bytes':8907878,'directories':177,'git_operations_all_zero':13,'tracked_public_bodies_commit_oid_joined':tracked,'prior_rows_reused':len(s['exact_unchanged_prior_rows_reused']),'exact_duplicate_exclusions':len(s['exact_already_recovered_duplicate_exclusions']),'seven_scopes_current_inventory_joined':True,'seventeen_installed_sources_joined':True,'fresh_original_group_archive_included':True,'same_archive_reencoding':True,'no_alternates':True,'GIT_NO_LAZY_FETCH':'1','disk_read_bytes':disk_bytes,'offline_git_output_bytes':git_bytes,'total_external_read_bytes':disk_bytes+git_bytes,'read_cap_bytes':limit,'in_memory_member_parse_bytes':parsed_member_bytes,'in_memory_reencoded_bytes':len(encoded.getvalue()),'evidence':evidence,'qualification':['No network, extraction, numerical imports, Owner/Run or Git mutation. Opaque binary members authenticated by bytes only.','Selected commit/blob recovery, not whole Git tree/runtime/graph store, POSIX reconstruction or deletion authority.','Full28 remains FAILED:65536 journal-recorded,61440 confirmed post-sink,zero complete MCM/trainingnull. Original independent group semantic review remains separate.','Metadata/code after captured scope is not included by implication. Root terminal remains qualified author tool-return transcription.']}
p=R/'RECOVERY_REVIEW01.json';p.write_text(json.dumps(v,indent=2)+'\n');print(h(p.read_bytes()),disk_bytes+git_bytes)
