import datetime,gzip,hashlib,io,json,os,stat,sys,tarfile
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;MAIN=B.parents[2];ROOT=B/'financial-genuine-wrapper-root-claimedrun-tooling-helper-flat01-2026-10-04';OUT=ROOT/'flat-eight-scopes01';checks=0;categories={}
sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v,n):
 global checks
 if not v:raise AssertionError(n)
 checks+=1;categories[n]=categories.get(n,0)+1
def pin(p,h):b=p.read_bytes();ok(sha(b)==h,'exact pin');return b
pin(ROOT/'restore_scopes01.py','82ac718ccca22234a6d4425d99c5aa41aba0b6173c1d0fa5424b8f1ae084fdab')
for n,h in {'recovery04.py':'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}.items():pin(ROOT/n,h)
sys.path.insert(0,str(ROOT));import recovery04 as R
qraw=pin(ROOT/'REQUEST_BOUND02.json','21607fad8becf3ba6c7f52f1fdc5d400d08dd9730c73e40c610ae48065546760');q=json.loads(qraw);draft=json.loads(pin(ROOT/'REQUEST_DRAFT01.json','42981fa8219e36288027946c1fdcae216fda09777898fa7761214cbe775b4043'));ok({k for k in q if q[k]!=draft[k]}=={'actual_execution','remote_commit','remote_receipt_sha256'} and set(q)==set(draft),'exact three-field binding');ok(q['actual_execution'] is True,'actual release')
recovery=json.loads(pin(OUT/'RECOVERY01.json','683d3f2ff60463975cd61eb6de7753fb7d3a06220edae1d2d3e2191a102d19e0'));terminal=json.loads((ROOT/'ACTUAL_TOOL_TERMINAL02.json').read_bytes());ok(sha((ROOT/'ACTUAL_TOOL_TERMINAL02.json').read_bytes()).startswith('6892a6aa'),'actual terminal supplied pin');whole_before=R.scan(OUT)
remote_review=B/'financial-genuine-wrapper-claimedrun-final-actual-two-batch-remote-review01-2026-10-04';pin(remote_review/'MANIFEST01.json','ef5d56545b20e89ef9c4311fbbfe0f1f6f4950d872978f294b4a01a9ddf8c1c5');pin(remote_review/'MACHINE01.json','236918fc76a2ce7119a4ac959b2398e849307528a9ede73566328571626c501f')
receipts=[];selected={};remote_summaries=[]
for dirname,h,count in [('financial-genuine-wrapper-root-claimedrun-final-shards-remote01-2026-10-04','ec84e55cfeae3da74557341d3395a84ce5fe4c0a2f187eaec89acc1ded212440',359),('financial-genuine-wrapper-root-claimedrun-helper-raw-remote01-2026-10-04','7518301a0862c314c05c379c4f30f249481351a397bcc0e55cfd3c8e91264a30',336)]:
 remote=B/dirname;receipt=json.loads(pin(remote/'REMOTE_RECOVERY01.json',h));ok(receipt['remote_commit']==q['remote_commit']=='a9b219042109be78498185cc6539c1454736e3eb' and receipt['genuine_run_or_native_started'] is False,'actual remote context');ok(len(receipt['selected_blobs'])==receipt['selected_count']==count,'remote complete count');seen=set();total=0
 for row in receipt['selected_blobs']:
  path=row['path'];ok(path not in seen,'unique receipt path');seen.add(path);body=R.read(remote/'selected',path);ok(len(body)==row['bytes']<=4194304 and sha(body)==row['sha256'],'actual selected bytes');oid=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest();ok(row['git_object']==oid and row['git_mode'] in ('100644','100755'),'actual selected Gitblob and mode');total+=len(body)
  if path in selected:ok(selected[path][1]==row,'duplicate anchors exact')
  else:selected[path]=(remote,row)
 ok(total==receipt['selected_logical_bytes']<64*1024**2,'actual selected logical bytes');remote_summaries.append({'receipt_sha256':h,'paths':count,'bytes':total,'commit':receipt['remote_commit']})
ok(len(selected)==689,'two receipt exact unique union')
primary=Path(q['remote_root']);ok(q['remote_receipt_sha256']==remote_summaries[0]['receipt_sha256'],'actual request remote binding')
# Fresh root contents are data to inspect, not an invocation of restore.
results=[];regulars=logical=originalfiles=originallinks=originalbytes=originaltypes=0;history=0
for index,(scope,result) in enumerate(zip(q['scopes'],recovery['scopes'])):
 dest=OUT/('scope-'+str(index).zfill(2));ok(str(dest)==result['output'] and scope['label']==result['label'],'fixed actual scope destination');ok(dest.resolve()==dest and stat.S_IMODE(dest.lstat().st_mode)==0o700,'actual private scope');r=result['result'];mr=R.read(primary/'selected',scope['manifest']['path']);ar=R.read(primary/'selected',scope['archive']['path']);m=json.loads(mr);R.validate(m)
 ok(mr==(MAIN/scope['manifest']['path']).read_bytes() and ar==(MAIN/scope['archive']['path']).read_bytes(),'remote exact current original archives');ok(sha(mr)==scope['manifest']['sha256']==r['manifest_sha256'] and sha(ar)==scope['archive']['sha256']==r['archive_sha256'],'archive manifest result hash chain');mdraw=R.read(dest,r['metadata_file']);ok(sha(mdraw)==r['metadata_sha256'],'flat metadata pin');md=json.loads(mdraw);ok(md['manifest']==m,'full original manifest recovered');mapping=md['flat_members'];file_rows=[x for x in m['members'] if x['kind']=='file'];ok(set(mapping)=={x['path'] for x in file_rows} and len(set(mapping.values()))==len(mapping)==r['regular_bodies'],'exact complete flat mapping');ok(set(p.name for p in dest.iterdir())==set(mapping.values())|{r['metadata_file']},'exact actual flat namespace noextra')
 for name in [*mapping.values(),r['metadata_file']]:
  st=(dest/name).lstat();ok(stat.S_ISREG(st.st_mode) and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==0o600,'actual flat private file type')
 gen=R.framed_members(ar);seen=[]
 try:
  for name,t,body in gen:
   x=m['members'][len(seen)];ok(name==x['path'] and t.mode==x['mode'] and t.uid==t.gid==t.mtime==0 and t.uname==t.gname=='','full ordered canonical header');ok((x['kind']=='directory' and t.isdir() and not body) or (x['kind']=='file' and t.isfile() and len(body)==t.size==x['bytes'] and sha(body)==x['sha256']),'full body type/extent/hash')
   if x['kind']=='file':ok(R.read(dest,mapping[name])==body,'every restored body exact archive');logical+=len(body);regulars+=1
   seen.append(name)
 finally:gen.close()
 ok(len(seen)==len(m['members'])==r['members']==scope['ordinary_members'],'whole archive denominator/footer')
 # Independent canonical re-encoding directly from all recovered opaque bodies.
 sink=R.ExactSink(ar)
 with gzip.GzipFile(filename='',mode='wb',fileobj=sink,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
   for x in m['members']:
    t=tarfile.TarInfo(x['path']);t.mode=x['mode'];t.uid=t.gid=t.mtime=0;t.uname=t.gname=''
    if x['kind']=='directory':t.type=tarfile.DIRTYPE;tf.addfile(t)
    else:body=R.read(dest,mapping[x['path']]);t.size=len(body);tf.addfile(t,io.BytesIO(body))
 ok(sink.count==len(ar) and sink.hash.hexdigest()==sha(ar),'canonical full recovered reencoding')
 omraw=R.read(dest,mapping['CAPTURE_ORIGINAL_TREE01.json']);ok(sha(omraw)==scope['original_metadata_sha256'],'original tree metadata exact');om=json.loads(omraw);tree=om['original_tree'];orig=Path(tree['original_root']);expected=tree['members'];observed=[]
 def walk(p,rel):
  nonlocal_placeholder=None
  st=p.lstat();sig=R.sig(st);x={'path':rel,'mode':stat.S_IMODE(st.st_mode)}
  if stat.S_ISLNK(st.st_mode):x.update(kind='lexical-symlink',target=os.readlink(p))
  elif stat.S_ISDIR(st.st_mode):
   x['kind']='directory'
   for c in sorted(p.iterdir()):walk(c,c.name if rel=='.' else rel+'/'+c.name)
  else:
   raw=R.read(orig,rel);x.update(kind='file',bytes=len(raw),sha256=sha(raw),union_path=tree['scope']+'/'+rel);ok(raw==R.read(dest,mapping[rel]),'every original body equals actually recovered body')
  ok(R.sig(p.lstat())==sig,'current original stable signature');observed.append(x)
 walk(orig,'.');observed.sort(key=lambda x:x['path']);ok(observed==expected,'complete original census modes emptydirs links')
 originalfiles+=sum(x['kind']=='file' for x in observed);originallinks+=sum(x['kind']=='lexical-symlink' for x in observed);originalbytes+=sum(x.get('bytes',0) for x in observed);originaltypes+=len(observed);history+=sum(x['kind']=='file' and any(w in x['path'].lower() for w in ['failed','failure','partial','.err']) for x in observed)
 ok(om['source_commit']=='0a2e7639b42b9423b90743feadcda4078aa21816' and om['research_authority'] is False and om['links_followed_or_extracted'] is False,'original provenance noauthority');ok(json.loads((OUT/('COMPLETED_SCOPE'+str(index).zfill(2)+'.json')).read_bytes())==result,'actual individual completion');results.append({'label':scope['label'],'restored_bodies':r['regular_bodies'],'members':r['members'],'metadata_sha256':r['metadata_sha256'],'archive_sha256':sha(ar),'original_files':sum(x['kind']=='file' for x in observed),'original_links':sum(x['kind']=='lexical-symlink' for x in observed),'complete_original_modes_join':True,'canonical_from_actual_restored_bytes':True})
ok(len(results)==len(q['scopes'])==len(recovery['scopes'])==8 and regulars==4544 and logical==recovery['whole_logical_bytes']==52444730,'whole8actual closure');ok(originalfiles==4536 and originallinks==67 and originalbytes==51074489,'whole original counts')
# Authenticate the complete330 own exporter/review raw bodies and45 literal metadata rows across both transports.
censuspath='research/onchain-paper-replication-2026-09-24/full_sources/financial-genuine-wrapper-claimedrun-final-selected-closure-census02-2026-10-04/COMPLETE_TYPED_ROOTS02.json';remote,row=selected[censuspath];census=json.loads(R.read(remote/'selected',censuspath));ownfiles=links=0
for role in ['complete_six_capture_exporter_own_source','complete_six_capture_exporter_own_review']:
 tree=census[role];root=Path(tree['root']);rows=tree['members'];names=[]
 def enumerate_names(p,rel):
  names.append(rel)
  if stat.S_ISDIR(p.lstat().st_mode):
   for c in sorted(p.iterdir()):enumerate_names(c,c.name if rel=='.' else rel+'/'+c.name)
 enumerate_names(root,'.');ok(sorted(names)==[x['path'] for x in rows],'own330 complete typed source denominator')
 for x in rows:
  p=root/x['path'];st=p.lstat();ok(stat.S_IMODE(st.st_mode)==x['mode'],'own original literal mode')
  if x['kind']=='file':
   relative=str(p.relative_to(MAIN));rem,ref=selected[relative];raw=R.read(rem/'selected',relative);ok(len(raw)==x['bytes'] and sha(raw)==x['sha256'] and raw==R.read(root,x['path']),'own raw body actually selected and original exact');ownfiles+=1
  elif x['kind']=='lexical-symlink':ok(stat.S_ISLNK(st.st_mode) and os.readlink(p)==x['target'],'own literal link metadata exact');links+=1
  else:ok(stat.S_ISDIR(st.st_mode),'own empty directory metadata')
ok(ownfiles==330 and links==45,'own330files45link metadata recovered across transports')
intent=json.loads((OUT/'INTENT01.json').read_bytes());ok(intent==terminal['actual_intent'] and terminal['actual_tool']=={'session':13984,'start_chunk':'f1a511','completion_chunk':'c3f3d8','exit_code':0},'actual tool intent join');ok((OUT/'REQUEST01.json').read_bytes()==qraw,'actually used request exact');stdout=pin(ROOT/'ACTUAL_RESTORE01.out',terminal['actual_stdout_sha256']);ok(pin(ROOT/'ACTUAL_RESTORE01.err',terminal['actual_stderr_sha256'])==b'','actual empty stderr');ok(json.loads(stdout)=={'status':recovery['status'],'scopes':8,'whole_logical':52444730},'actual stdout summary');ok(recovery['elapsed_seconds']<120 and recovery['free_bytes']>=10*1024**3,'recorded actual resourcebounds');ok(not Path('/proc',str(intent['actual_pid'])).exists(),'original actualPID absent');members=[];denied=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:v=(p/'stat').read_text().rsplit(')',1)[1].split()
 except (FileNotFoundError,ProcessLookupError):continue
 except PermissionError:denied.append(int(p.name));continue
 if int(v[2])==intent['pgid']:members.append(int(p.name))
ok(members==[],'currently observed original group absent');R.same(OUT,whole_before);ok(True,'full actual restored output unchanged throughout verification')
for n in ['ACTUAL_RESTORE01.out','ACTUAL_RESTORE01.err','ACTUAL_TOOL_TERMINAL02.json','ACTUAL_BINDING02.json','REQUEST_BOUND02.json']:
 with (H/('ORIGINAL_'+n)).open('xb') as f:f.write((ROOT/n).read_bytes())
for n in ['RECOVERY01.json','INTENT01.json']:
 with (H/('ORIGINAL_'+n)).open('xb') as f:f.write((OUT/n).read_bytes())
report={'schema_version':1,'status':'ACCEPTED_ACTUAL_EIGHT_ORDINARY_FLAT_BYTE_RECOVERY','checks':checks,'categories':categories,'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scopes':results,'whole_restored_bodies':regulars,'whole_restored_logical_bytes':logical,'whole_original_files':originalfiles,'whole_original_bytes':originalbytes,'whole_original_literal_links':originallinks,'whole_original_typed':originaltypes,'preserved_failure_named_original_files':history,'transport_union':remote_summaries,'selected_unique_paths':len(selected),'own_exporter_review_raw_bodies':ownfiles,'own_original_literal_metadata_links':links,'remote_Git_object_joins':'Every selected recovered byte independently recomputes its recorded Git blob OID; actual tree/HEAD/network provenance retains independently accepted236918/ef5d review. No new Git/network invoked.','actual_output_manifest_sha256':sha(R.encode(whole_before)),'actual_output_members':len(whole_before['members']),'current_originalPID_absent':True,'observed_group_members':members,'proc_permission_denied':denied,'historical_process_descendants_complete':False,'full20caller_and_five_witness_restores_reviewed_here':False,'research_runtime_or_POSIX_authority':False,'numerical_release':False}
with (H/'READBACK01.json').open('x') as f:json.dump(report,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'readback_sha256':sha((H/'READBACK01.json').read_bytes()),'readback_bytes':(H/'READBACK01.json').stat().st_size,'restored_bodies':regulars,'logical':logical,'own_raw':ownfiles,'ownlinks':links}))
