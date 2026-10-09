import pathlib,json,hashlib,tarfile,io,os,stat,subprocess,datetime
ROOT=pathlib.Path.cwd();R=pathlib.Path(__file__).resolve().parent;F=R.parent.parent;D=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/full29increment14';evidence={};cache={};disk_bytes=git_bytes=0;h=lambda b:hashlib.sha256(b).hexdigest();limit=64*1024**2
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
r=load(D/'FRESH_GIT_RECOVERY14.json');pin(ROOT/r['capture']['path'],r['capture']['sha256']);c=load(ROOT/r['capture']['path']);pin(ROOT/c['selection']['path'],c['selection']['sha256']);s=load(ROOT/c['selection']['path']);raw=read(ROOT/r['returned_archive']['path']);assert len(raw)==5672960==r['returned_archive']['bytes'] and h(raw)==r['returned_archive']['sha256']==c['archive']['sha256']=='0d5513e17436ff370cca4ded4b29b8e3336468371957191c559d4fab7c1e9041'
# Capture original independently hashed; returned archive will additionally be reencoded and Git-bound.
assert read(ROOT/c['archive']['path'])==raw
rows=sorted(s['rows']+s['directories'],key=lambda x:x['path']);assert len(s['rows'])==197 and len(s['directories'])==20 and s['symlinks']==0 and sum(x['bytes'] for x in s['rows'])==5289275
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
ops=load(D/'GIT_OPERATIONS14.json');assert ops==r['operations'] and len(ops)==13
for op in ops:
 assert op['exit_code']==0
 for kind in ('stdout','stderr'):
  data=read(D/(op['operation']+'.'+kind));assert len(data)==op[kind+'_bytes'] and h(data)==op[kind+'_sha256']
B=pathlib.Path(r['fresh_bare']);env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0'}
def git(args,cwd=ROOT):
 global git_bytes
 result=subprocess.check_output(['git',*args],cwd=cwd,env=env,timeout=15);git_bytes+=len(result);assert disk_bytes+git_bytes<=limit;return result
assert not (B/'objects/info/alternates').exists() and not (B/'objects/info/http-alternates').exists();source=r['source'];assert source==r['actual_remote_head']==r['actual_fetch_head']==git(['rev-parse','FETCH_HEAD'],B).decode().strip()=='f58540f5e55ca701bab4b20969a5b77ad43e5260'
commit=git(['cat-file','commit',source],B);assert commit==git(['cat-file','commit',source])==read(D/'actual_external_commit_body.stdout') and h(commit)==r['commit_body_sha256'];assert read(D/'remote_actual_branch_readback.stdout').decode().split()[0]==source
assert git(['ls-tree',source,'--',c['archive']['path']]).decode().strip()==r['local_commit_tree_join'];assert git(['cat-file','blob',r['archive_git_blob_oid']],B)==raw;assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==r['archive_git_blob_oid']
prior=load(ROOT/s['baseline_actual_recovery']['path']);assert h(read(ROOT/s['baseline_actual_recovery']['path']))==s['baseline_actual_recovery']['sha256'] and prior['source']==s['baseline_source'];priorselection=load((ROOT/s['baseline_actual_recovery']['path']).parent/'SELECTION13.json');old={x['path']:x for x in priorselection['rows']}
for name in s['exact_unchanged_prior_rows_reused']:
 row=old[name];p=ROOT/name;st=p.lstat();assert name not in bodies and stat.S_ISREG(st.st_mode) and format(stat.S_IMODE(st.st_mode),'04o')==row['mode'] and st.st_size==row['bytes'] and h(read(p))==row['sha256']
for name in s['exact_already_recovered_duplicate_exclusions']:assert name not in bodies and h(read(ROOT/name))==prior['returned_archive']['sha256']
selected={x['path']:x for x in rows}
for scope in s['actual_scope_states']:
 p=ROOT/scope['path'];assert p.exists()==scope['exists']
 for q in [p,*p.rglob('*')]:
  rel=str(q.relative_to(ROOT));assert rel in selected;row=selected[rel];st=q.lstat();assert format(stat.S_IMODE(st.st_mode),'04o')==row['mode']
  if stat.S_ISREG(st.st_mode):assert h(read(q))==row['sha256']
# New selected public bodies individually commit-bound where tracked; untracked logs
# remain authenticated through the committed archive, never asserted separately tracked.
tree=git(['ls-tree','-r',source]).decode();treepins={line.split('\t',1)[1]:line.split()[2] for line in tree.splitlines() if '\t'in line};tracked=0;archive_only=[]
for name,body in bodies.items():
 oid=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
 if name in treepins:assert treepins[name]==oid;tracked+=1
 else:archive_only.append(name)
E=F/'real-data-pilot-full29-entry01-2026-10-09';rel=lambda p:str(p.relative_to(ROOT));release_name=rel(E/'RELEASE_REVIEW02.json');assert release_name in bodies;release=json.loads(bodies[release_name]);binding_name=rel(E/'BINDING02.json');binding=json.loads(bodies[binding_name]);gate_name=rel(E/'gate04.json');gate=json.loads(bodies[gate_name]);entry=gate['experiments'][release['identity']];assert release['decision']=='accepted' and len(release['evidence'])==559 and len(entry['source_files'])==458 and len(entry['inputs'])==64
assert h(bodies[binding_name])==release['actual_final_binding_sha256'];assert h(bodies[gate_name])==binding['gate']['sha256']
for p in (E/'preflight29_02.py',E/'root_io29_02.py'):assert h(bodies[rel(p)])==release['evidence'][rel(p)]
prior_review=load(F/'pilot-full28-outcome-increment-tools-review01-2026-10-09/returned13/RECOVERY_REVIEW01.json');assert prior_review['decision']=='accepted' and prior_review['archive_sha256']==prior['returned_archive']['sha256']
# Inherited unchanged sources predate the delta13 archive. Their original accepted
# release evidence and the baseline13 committed tree are joined explicitly.
old_release=load(F/'real-data-pilot-full28-final-entry-review01-2026-10-09/RELEASE_REVIEW01.json');inherited=dict(old_release['evidence']);inherited.update(prior_review['evidence']);inherited.update({k:v['sha256'] for k,v in old.items()})
coverage={'returned14':[],'returned13_members':[],'accepted_inherited_earlier':[],'opaque_excluded':[]};pending={}
for name,pin_value in release['evidence'].items():
 if name==binding['transport']['path']:coverage['opaque_excluded'].append(name);continue
 if name in bodies:assert h(bodies[name])==pin_value;coverage['returned14'].append(name)
 elif name in old:assert old[name]['sha256']==pin_value;coverage['returned13_members'].append(name);pending[name]=pin_value
 else:
  assert inherited.get(name)==pin_value,('not authenticated by selected14/prior13/inherited release',name)
  coverage['accepted_inherited_earlier'].append(name);pending[name]=pin_value
# Verify inherited public body identities at the actual previously recovered source
# commit locally; this does not claim fresh remote transfer of its complete tree.
paths=list(pending);data=git(['cat-file','--batch']) if False else subprocess.check_output(['git','cat-file','--batch'],input=('\n'.join(prior['source']+':'+p for p in paths)+'\n').encode(),cwd=ROOT,env=env,timeout=15);git_bytes+=len(data);assert disk_bytes+git_bytes<=limit;pos=0
for name in paths:
 end=data.index(b'\n',pos);hdr=data[pos:end].split();assert len(hdr)==3 and hdr[1]==b'blob',(name,hdr);n=int(hdr[2]);pos=end+1;assert h(data[pos:pos+n])==pending[name];pos+=n+1
assert pos==len(data)
assert len(coverage['opaque_excluded'])==1
assert all(release['evidence'][p]==sha for p,sha in entry['source_files'].items())
assert all(release['evidence'][v['path']]==v['sha256'] for v in entry['inputs'].values())
assert all(k in bodies for k in [rel(E/'BINDING_DRAFT04.json'),rel(E/'MATCHING_SCRATCH_RESERVATION02.json')])
v={'decision':'accepted','scope':'Actual returned full29 final preparation increment14 only, plus explicitly inherited accepted public evidence','source':source,'archive_sha256':h(raw),'archive_bytes':len(raw),'regular_bodies':197,'regular_bytes':5289275,'directories':20,'same_archive_reencoding':True,'git_operations_all_zero':13,'no_alternates':True,'GIT_NO_LAZY_FETCH':'1','tracked_selected_bodies':tracked,'selected_archive_only_bodies':archive_only,'reused_prior_selected_rows':len(s['exact_unchanged_prior_rows_reused']),'duplicate_exclusions':len(s['exact_already_recovered_duplicate_exclusions']),'release_evidence_coverage':{k:len(a) for k,a in coverage.items()},'coverage_paths':coverage,'source_pins':458,'input_roles':64,'release_sha256':h(bodies[release_name]),'binding_sha256':h(bodies[binding_name]),'disk_read_bytes':disk_bytes,'offline_git_output_bytes':git_bytes,'total_external_read_bytes':disk_bytes+git_bytes,'read_cap_bytes':limit,'in_memory_member_parse_bytes':parsed_member_bytes,'in_memory_reencoded_bytes':len(encoded.getvalue()),'evidence':evidence,'qualifications':['No network/extraction/numerical imports/Owner/Run or Git mutation. Opaque binaries byte-authenticated only.','458 sources/64 roles/559 release references are joined through newly returned14, prior returned13 members, or unchanged earlier accepted release evidence with local baseline13 committed-body joins. No assertion all inherited bodies were transferred in13 or14.','Sole private dispatch excluded; no runtime package/raw graph stores/whole-tree/POSIX reconstruction/deletion proof.','Wrapper02 outer failure, preclaim refusals and failed28 dispositions remain unchanged. No empirical claim or current resource eligibility; last reported disk refusal is not repaired by recovery.']}
p=R/'RECOVERY_REVIEW01.json';p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');print(json.dumps({'review_sha256':h(p.read_bytes()),'coverage':v['release_evidence_coverage'],'read_bytes':disk_bytes+git_bytes}))
