import pathlib,json,hashlib,os,subprocess
ROOT=pathlib.Path.cwd();R=pathlib.Path(__file__).resolve().parent;F=R.parent.parent;D=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/full29increment14';E=F/'real-data-pilot-full29-entry01-2026-10-09';j=lambda p:json.loads(p.read_bytes());h=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:str(p.relative_to(ROOT));env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0'}
r=j(D/'FRESH_GIT_RECOVERY14.json');s=j(D/'SELECTION14.json');rows={v['path']:v for v in s['rows']};old=j(D.parent/'outcome13/SELECTION13.json');priorrows={v['path']:v for v in old['rows']};pr=j(F/'pilot-full28-outcome-increment-tools-review01-2026-10-09/returned13/RECOVERY_REVIEW01.json');oldrelease=j(F/'real-data-pilot-full28-final-entry-review01-2026-10-09/RELEASE_REVIEW01.json');inherited={**oldrelease['evidence'],**pr['evidence']};release=j(E/'RELEASE_REVIEW02.json');binding=j(E/'BINDING02.json');gate=j(E/'gate04.json');x=gate['experiments'][release['identity']];assert pr['decision']=='accepted'
# Earlier checker stopped only AFTER all archive/operation/bare assertions.
err=(R/'CHECK01.stderr').read_text();assert "tree=git(['ls-tree','-r',source])" in err and err.rstrip().endswith('AssertionError')
for p in (E/'RELEASE_REVIEW02.json',E/'BINDING02.json',E/'gate04.json',E/'preflight29_02.py',E/'root_io29_02.py'):
 assert rows[rel(p)]['sha256']==h(p.read_bytes())
# Exact inherited reference in the previously accepted full28 scratch declaration.
ob=j(F/'real-data-pilot-full28-entry01-2026-10-09/BINDING01.json');sp=ob['input_refs']['matching_ordered_edge_scratch'];sb=(ROOT/sp['path']).read_bytes();assert h(sb)==oldrelease['evidence'][sp['path']];sv=json.loads(sb)
for ref in sv.values():
 if isinstance(ref,dict) and {'path','sha256'}<=ref.keys():inherited[ref['path']]=ref['sha256']
deps=j(F/'real-data-pilot-transport-binding-preparation01-2026-10-06/DEPENDENCIES01.json')
inherited.update({v['path']:v['sha256'] for v in deps.values()})
coverage={'returned14':[],'returned13_members':[],'accepted_inherited_earlier':[],'opaque_excluded':[]};pending={}
for name,sha in release['evidence'].items():
 if name==binding['transport']['path']:coverage['opaque_excluded'].append(name);continue
 if name in rows:assert rows[name]['sha256']==sha;coverage['returned14'].append(name)
 elif name in priorrows:assert priorrows[name]['sha256']==sha;coverage['returned13_members'].append(name);pending[name]=sha
 else:
  assert inherited.get(name)==sha,('missing inherited proof',name)
  coverage['accepted_inherited_earlier'].append(name);pending[name]=sha
# Exact paths only, no recursive repository census.
names=list(rows);out=subprocess.check_output(['git','ls-tree',r['source'],'--',*names],env=env);lines=out.decode().splitlines();treepins={v.split('\t',1)[1]:v.split()[2] for v in lines};tracked=0;archive_only=[];read_bytes=len(out)
for name,row in rows.items():
 if name not in treepins:archive_only.append(name);continue
 data=(ROOT/name).read_bytes();read_bytes+=len(data);assert h(data)==row['sha256'];assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==treepins[name];tracked+=1
paths=list(pending);data=subprocess.check_output(['git','cat-file','--batch'],input=('\n'.join(s['baseline_source']+':'+p for p in paths)+'\n').encode(),env=env);read_bytes+=len(data);pos=0
for name in paths:
 end=data.index(b'\n',pos);hdr=data[pos:end].split();assert len(hdr)==3 and hdr[1]==b'blob',(name,hdr);n=int(hdr[2]);pos=end+1;assert h(data[pos:pos+n])==pending[name];pos+=n+1
assert pos==len(data);assert len(coverage['opaque_excluded'])==1
assert len(x['source_files'])==458 and len(x['inputs'])==64 and len(release['evidence'])==559
assert all(release['evidence'][p]==sha for p,sha in x['source_files'].items());assert all(release['evidence'][v['path']]==v['sha256'] for v in x['inputs'].values())
v={'decision':'accepted','scope':'Actual returned declared full29 public increment14 plus explicitly inherited accepted public evidence','source':r['source'],'archive_sha256':r['returned_archive']['sha256'],'archive_bytes':5672960,'regular_bodies':197,'regular_bytes':5289275,'directories':20,'archive_names_types_modes_sizes_hashes_verified':True,'same_archive_reencoding':True,'git_operations_all_zero':13,'commit_body_remote_FETCH_HEAD_local_tree_blob_join':True,'no_alternates':True,'GIT_NO_LAZY_FETCH':'1','tracked_selected_bodies':tracked,'selected_archive_only_bodies':archive_only,'reused_prior_selected_rows':0,'duplicate_exclusions':3,'release_evidence_coverage':{k:len(a) for k,a in coverage.items()},'coverage_paths':coverage,'source_pins':458,'input_roles':64,'release_sha256':h((E/'RELEASE_REVIEW02.json').read_bytes()),'binding_sha256':h((E/'BINDING02.json').read_bytes()),'inherited_reference_qualification':'One prior validation review is joined through accepted28 scratch; unchanged builder through original accepted binder dependencies. These are transitive source references locally committed at baseline13, not freshly returned14 members.', 'read_accounting_qualification':'CHECK01 passed archive/member/reencoding/13operations/offlinebare joins before an unnecessarily broad ls-tree output exceeded its64MiB bookkeeping assertion. No64MiB total-read claim is made. CHECK01 raw failure retained. finish02 used exact selected paths and inherited refs only; archive matrix was not rerun.','finish_exact_body_and_git_bytes':read_bytes,'evidence':{rel(p):h(p.read_bytes()) for p in (D/'FRESH_GIT_RECOVERY14.json',D/'CAPTURE14.json',D/'SELECTION14.json',R/'CHECK01.stderr',R/'check01.py',R/'finish04.py',E/'RELEASE_REVIEW02.json',E/'BINDING02.json')},'qualification':['Inherited earlier release bodies are locally joined to baseline13 committed blobs; no assertion all were freshly transferred in13 or14.','Sole opaque private dispatch and runtime package/raw graph stores excluded. No complete-tree/POSIX reconstruction/deletion/scientific-completion claim.','No network/numerical imports/arrays/Owner/Run/Git mutation. Original wrapper failures and preclaim refusals remain; no current resource eligibility or resolution of disk gap.']}
(R/'RECOVERY_REVIEW01.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');print(json.dumps({'review_sha256':h((R/'RECOVERY_REVIEW01.json').read_bytes()),'coverage':v['release_evidence_coverage'],'finish_bytes':read_bytes}))
