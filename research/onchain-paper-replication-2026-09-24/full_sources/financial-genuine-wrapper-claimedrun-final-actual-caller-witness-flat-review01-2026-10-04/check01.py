import ast,gzip,hashlib,importlib.util,io,json,os,stat,sys,tarfile
from pathlib import Path
from collections import Counter
H=Path(__file__).resolve().parent;B=H.parent;MAIN=B.parents[2];counts=Counter();evidence={}
sys.path.insert(0,str(B/'held-consumer-final-recovery-preparation04-2026-10-03'));import recovery04 as O
sp=importlib.util.spec_from_file_location('review_pax',B/'financial-genuine-wrapper-claimedrun-witness-pax-framer-correction-preparation01-2026-10-04/recovery_pax01.py');N=importlib.util.module_from_spec(sp);sp.loader.exec_module(N)
def sha(b):return hashlib.sha256(b).hexdigest()
def ok(v,label):
 if not v:raise AssertionError(label)
 counts[label]+=1

def read(p):return O.read(p.parent,p.name)
def js(p):return json.loads(read(p))
def pin(p,value):raw=read(p);ok(sha(raw)==value,'exact body pin');return raw
remote=B/'financial-genuine-wrapper-root-claimedrun-final-shards-remote01-2026-10-04';receipt_raw=pin(remote/'REMOTE_RECOVERY01.json','ec84e55cfeae3da74557341d3395a84ce5fe4c0a2f187eaec89acc1ded212440');receipt=json.loads(receipt_raw);ok(receipt['remote_commit']=='a9b219042109be78498185cc6539c1454736e3eb' and receipt['genuine_run_or_native_started'] is False,'actual remote commit/no numerical');selected={r['path']:r for r in receipt['selected_blobs']};ok(len(selected)==receipt['selected_count']<=506,'actual remote complete unique selected inventory')
def selected_body(ref):
 row=selected[ref['path']];raw=O.read(remote/'selected',ref['path']);ok(len(raw)==ref['bytes']==row['bytes'] and sha(raw)==ref['sha256']==row['sha256'],'actual selected SHA/extent');ok(row['git_object']==hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() and row['git_mode'] in ('100644','100755'),'actual selected Gitblob identity/mode');return raw
# Authenticate the full primary actual selected set, not only archive headers.
for row in receipt['selected_blobs']:selected_body(row)
outputs={};mappings={};all_raw={};snapshots={}
for label,dirname,callername,recovery_pin,helper_pin,kind,expectedfiles,expectedshards in [
 ('final','financial-genuine-wrapper-claimedrun-final-union-sharded-flat-20261004-01','financial-genuine-wrapper-root-claimedrun-final-sharded-flat01-2026-10-04','988ecf43387c7b1632032a7588cd12bd49297c397f3651238fcbcc6b34afca86','f0fa6231ed61dea322021e75578187c604633df21c3acee7eade4f0497e9cab7','accepted-exact-one-use-final-union-sharded-flat',1186,11),
 ('witness','financial-genuine-wrapper-claimedrun-witness-sharded-flat-20261004-01','financial-genuine-wrapper-root-claimedrun-witness-sharded-flat01-2026-10-04','d55f40835c9870fcfa0e64327f04aaaebe520e71cf3b015dd64560047d1a1148','5352c2e42d11d585e92187f2d51be9c42eaadcfc9b03f8e11e9a7097bf7c28ac','accepted-exact-one-use-witness-sharded-plus-direct-flat',2302,57)]:
 out=B/dirname;caller=B/callername;R=O if label=='final' else N;rec=json.loads(pin(out/'RECOVERY01.json',recovery_pin));q=js(caller/'REQUEST_FINAL03.json');ok(js(out/'request.json')==q and q['output_root']==str(out),'actual executed request join');contract=sha(R.encode({k:v for k,v in q.items() if k!='release'}));release=json.loads(pin(Path(q['release']['path']),q['release']['sha256']));review=pin(Path(q['review']['path']),q['review']['sha256']);helper='restore_sharded01.py' if label=='final' else 'restore_witness01.py';pin(caller/helper,helper_pin);ok(release=={'schema_version':1,'decision':kind,'contract_sha256':contract,'helper_sha256':helper_pin,'review_sha256':sha(review)},'actual exact five-field release')
 ok(q['remote_receipt_sha256']==sha(receipt_raw) and q['remote_commit']==receipt['remote_commit'] and q['remote_root']==str(remote),'actual remote request join')
 terminal=js(caller/'ACTUAL_TOOL_TERMINAL02.json');intent=js(out/'intent.json');ok(terminal['actual_tool']['exit_code']==0 and terminal['actual_recovery_sha256']==recovery_pin and terminal['original_actual_intent']==intent and intent['contract_sha256']==contract,'separate tool terminal/intent/recovery join');ok(terminal['actual_root_pid_observed_absent'] is True and not Path('/proc/'+str(intent['pid'])).exists(),'recorded/current PID absence no startticks inference');ok(read(caller/'ACTUAL_RESTORE01.err')==b'' and sha(read(caller/'ACTUAL_RESTORE01.err'))==terminal['actual_stderr_sha256'] and sha(read(caller/'ACTUAL_RESTORE01.out'))==terminal['actual_stdout_sha256'],'original stdout/stderr terminal pins');ok(terminal['free_bytes']>=O.FLOOR and min(rec['observed_free_bytes'])>=O.FLOOR,'actual retained disk-floor observations')
 vrraw=pin(out/'VIRTUAL_RECOVERY01.json',rec['virtual_recovery_sha256']);vr=json.loads(vrraw);m=json.loads(selected_body(q['manifest']));R.validate(m);ok(vr['virtual_manifest']==m and len(vr['flat_members'])==expectedfiles and q['expected_files']==expectedfiles,'fullvirtual manifest and regular denominator');idx=json.loads(selected_body(q['shard_index']));auth=json.loads(selected_body(q['union_auth']));ok(len(idx['shards'])==expectedshards and set(vr['shards'])==set(rec['actual_shards'])=={r['id'] for r in idx['shards']},'complete actual shard identities');prefix=str(Path(q['shard_index']['path']).parent);global_files={};shardraw={}
 for row in idx['shards']:
  ident=row['id'];dest=out/ident;record=rec['actual_shards'][ident];ar=row['archive'];mr=row['manifest'];raw=selected_body({'path':prefix+'/'+ar['path'],'bytes':ar['bytes'],'sha256':ar['sha256']});mmraw=selected_body({'path':prefix+'/'+mr['path'],'bytes':mr['bytes'],'sha256':mr['sha256']});mm=json.loads(mmraw);R.validate(mm);meta_raw=pin(dest/record['metadata_file'],record['metadata_sha256']);meta=json.loads(meta_raw);ok(meta['manifest']==mm and meta['archive']=={k:ar[k] for k in ('bytes','sha256','manifest_sha256')} and sha(R.encode(mm))==ar['manifest_sha256'],'actual flatmetadata/manifest/archive exactjoin');ok(vr['shards'][ident]==record and record['archive_sha256']==sha(raw) and record['manifest_sha256']==sha(mmraw),'actual shard record pins');ok(stat.S_IMODE(dest.lstat().st_mode)==448 and not dest.is_symlink(),'actual private shard directory');expected={r['path']:r for r in mm['members']};frame=list(R.framed_members(raw));ok(len(frame)==len(expected)==record['members'] and [n for n,t,b in frame]==[r['path'] for r in mm['members']],'full canonical header/order/footer framing')
  names=set()
  for name,t,body in frame:
   r=expected[name];ok(t.mode==r['mode'],'original archive literal mode')
   if r['kind']=='directory':ok(t.isdir() and not body and t.size==0,'archive directory semantics');continue
   ok(t.isfile() and len(body)==r['bytes'] and sha(body)==r['sha256'],'archive original opaque body semantics');leaf=meta['flat_members'][name];actual=R.read(dest,leaf);ok(actual==body and stat.S_IMODE((dest/leaf).lstat().st_mode)==384 and not (dest/leaf).is_symlink(),'EVERY fresh restored body bytes/hash/private mode');ok(name not in global_files and leaf not in names,'disjoint global and local filemembership');names.add(leaf);ref={'shard':ident,'file':leaf,'bytes':len(actual),'sha256':sha(actual)};global_files[name]=ref;ok(vr['flat_members'][name]==ref,'virtual actual body locator join')
  ok(set(os.listdir(dest))==names|{record['metadata_file']} and len(names)==record['regular_bodies'],'whole flat namespace no missing/extra');ok(stat.S_IMODE((dest/record['metadata_file']).lstat().st_mode)==384,'flat metadata private mode')
  # Exact full canonical gzip reconstruction from independently reread RESTORED bodies.
  sink=R.ExactSink(raw);gz=None;tar=None
  try:
   gz=gzip.GzipFile(filename='',mode='wb',fileobj=sink,mtime=0);tar=tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT)
   for r in mm['members']:
    t=tarfile.TarInfo(r['path']);t.mode=r['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0
    if r['kind']=='directory':t.type=tarfile.DIRTYPE;t.size=0;tar.addfile(t)
    else:b=R.read(dest,meta['flat_members'][r['path']]);t.size=len(b);tar.addfile(t,io.BytesIO(b))
  finally:R._cleanup((() if tar is None else (tar.close,))+(() if gz is None else (gz.close,)))
  ok(sink.count==len(raw) and sink.hash.hexdigest()==sha(raw),'all68 actual full canonical reencoding from recovered bytes');shardraw[ident]=raw
 ok(set(global_files)=={r['path'] for r in m['members'] if r['kind']=='file'}==set(vr['flat_members']),'complete global body set');ok(stat.S_IMODE(out.lstat().st_mode)==448,'whole root private mode');expectedtop={'request.json','intent.json','RECOVERY01.json','VIRTUAL_RECOVERY01.json'}|set(rec['actual_shards']);direct=None
 if label=='witness':
  expectedtop.add('direct-selected');d=vr['direct_body'];ok(d==rec['actual_direct_body'],'actual direct result identity');raw=selected_body(q['direct_body']);direct=R.read(out, d['file']);ok(direct==raw and len(raw)==2532973 and sha(raw)=='c47fcb6875375ecb8ea5c60926bae307955007751cdf52bec2473c44964e17e3','exact raw direct authentic recovered join');ok(stat.S_IMODE((out/d['file']).lstat().st_mode)==384 and stat.S_IMODE((out/'direct-selected').lstat().st_mode)==448 and set(os.listdir(out/'direct-selected'))=={'original.body'},'complete private direct namespace');ok(d['descriptor']==idx['direct_bodies'][0]==auth['direct_bodies'][0] and len(idx['direct_bodies'])==1,'sole direct metadata descriptor')
  for ident in ('shard-0035','shard-0049'):
   try:list(O.framed_members(shardraw[ident]))
   except ValueError as e:ok(str(e)=='noncanonical raw member slash/type','original b40 PAX refusal preserved')
   else:raise AssertionError('original b40 refusal disappeared')
 ok(set(os.listdir(out))==expectedtop,'complete final output root namespace');ok(all(vr[k] is False for k in ('links_followed','posix_tree_instantiated','research_authority','runtime_or_empirical_stores')),'original no-authority qualification')
 ref=global_files['ORIGINAL_TREES01.json'];mapping_raw=R.read(out/ref['shard'],ref['file']);mapping=json.loads(mapping_raw);ok(sha(mapping_raw)==auth['union_mapping_sha256'],'actual original full mapping pin');typed=files=links=0
 for tree in mapping['scope_trees']:
  root=Path(tree['original_root']);actual={'.'}
  for parent,dirs,leaves in os.walk(root,followlinks=False):
   for n in dirs+leaves:actual.add((Path(parent)/n).relative_to(root).as_posix())
  ok(actual=={r['path'] for r in tree['members']},'current full original scope membership')
  for r in tree['members']:
   p=root/r['path'];st=p.lstat();typed+=1;ok(stat.S_IMODE(st.st_mode)==r['mode'],'original literal mode metadata/current join')
   if r['kind']=='lexical-symlink':ok(stat.S_ISLNK(st.st_mode) and os.readlink(p)==r['target'],'original literal link exact nofollowing');links+=1
   elif r['kind']=='directory':ok(stat.S_ISDIR(st.st_mode) and not p.is_symlink(),'original empty/directory metadata')
   else:
    files+=1;body=read(p)
    if 'direct_source_path' in r:restored=direct;ok(label=='witness' and r['direct_source_path']==q['direct_body']['path'],'original direct pathmetadata')
    else:ref=global_files[r['union_path']];restored=R.read(out/ref['shard'],ref['file'])
    ok(body==restored and len(body)==r['bytes'] and sha(body)==r['sha256'],'EVERY actual original body recovered')
 expectedcounts=(20,1525,1185,50) if label=='final' else (5,2762,2302,59);ok((len(mapping['scope_trees']),typed,files,links)==expectedcounts,'full original exact cardinalities')
 outputs[label]={'output':str(out),'recovery_sha256':recovery_pin,'request_sha256':sha(read(caller/'REQUEST_FINAL03.json')),'terminal_sha256':sha(read(caller/'ACTUAL_TOOL_TERMINAL02.json')),'shards':expectedshards,'virtual_regular_bodies':len(global_files),'original_trees':len(mapping['scope_trees']),'original_typed_members':typed,'original_regular_bodies':files,'original_lexical_links':links,'actual_tool_exit':terminal['actual_tool']['exit_code'],'ticks_observed':False};mappings[label]=mapping;all_raw[label]=(out,global_files,m)
# Source339 entire original byte tree unchanged; no scientific imports or Git mutation.
source=B/'financial-genuine-wrapper-root-claimedrun-source339-capture01-2026-10-04';sm=json.loads(pin(source/'source-manifest.json','fdf77348b81a4d6df8b420b98530f5485900a0461636e1c201506106b036dfd8'));cap=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');O.same(cap,sm);ok(True,'actual whole Source339 unchanged');ok(O.read(cap,'.git/HEAD').strip()==b'0a2e7639b42b9423b90743feadcda4078aa21816','actual current design Source0a2 HEAD')
# Explicit current Parent/proof and generated verifier anchors are present among recovered20tree bytes.
anchors={('actual-parent','parent01.py'):'5d5cbdae455c62c3e66b53208b0f79e6e5bbc7ce05d3ded77126da5e0692deda',('actual-parent','REQUEST_FINAL03.json'):'529c9bf3c587e6160a217e8eb339882e59433b6fc0f759d0009d261f872b2bd8',('actual-parent','proofs/CUMULATIVE19_REVIEW01.json'):'3268b76971e4e721222707d16d25dfe84e94104779931e647fb4d7a2bf01202e',('actual-parent','proofs/INDEPENDENT_SOURCE_INPUT_RUNTIME01.json'):'059232d0f7fc8922cee526a1bd30fef2ecb51ee17103284bcaac18c77e77641c',('actual-parent','proofs/FULL_SOURCE_RECOVERY01.json'):'468dac2c06e570a89a30771c3f7e1b8e064e6f27e610acf01edcccf91c9a2825',('root-verifier-binding','generated-claimedrun01/verifier01.py'):'14089451a225aa541eb6faf30c78cb31c79b1380d7ef54d77e895575e3ce250c',('root-verifier-binding','generated-claimedrun01/BINDING01.json'):'57e3b72754668f3be5d1611475b9c29be3fabd91ffe71c5cad60792fa4881989',('actual-verifier-review','MANIFEST01.json'):'0c39988229162fd10b0d0df77f71163a4675a778251a8d75634283e40482bea2'}
out,global_files,manifest=all_raw['final']
for (scope,path),expectedpin in anchors.items():ref=global_files[scope+'/'+path];ok(sha(O.read(out/ref['shard'],ref['file']))==expectedpin,'exact recovered actual caller/proof/verifier anchor')
# Discharge FAILED original aggregate scope through identical virtual bodies plus ALL8 remote outside files.
requirements=js(B/'financial-genuine-wrapper-claimedrun-actual-final-capture-review02-2026-10-04/FAILED_SCOPE_RECOVERY_REQUIREMENTS01.json');oldroot=Path(requirements['old_root']);oldmanifest=js(oldroot/'union-manifest.json');ok(oldmanifest==manifest and sha(O.encode(oldmanifest))=='c72030b48f422bcfa52b1bbb2ca3202b9c8a8447387330f818edd20a58fb8b5d','FAILED original full1186 virtual identity')
for name,ref in global_files.items():ok(O.read(oldroot/'union-bytes01',name)==O.read(out/ref['shard'],ref['file']),'all1186 FAILED original union bodies recovered')
failed=[]
for row in requirements['must_select_exact_outside_union_files']:
 p=oldroot/row['path'];relative=p.relative_to(MAIN).as_posix();raw=selected_body({'path':relative,'bytes':row['bytes'],'sha256':row['sha256']});ok(raw==read(p) and stat.S_IMODE(p.lstat().st_mode)==row['mode'],'ALL8 actual failed outside rawselected bytes/mode');failed.append({'path':row['path'],'sha256':sha(raw),'bytes':len(raw)})
ok(len(failed)==8 and requirements['old_status']=='PERMANENT_FAILED','failed status never coerced');ok(any(r['sha256']=='fc7d4f78ae2db603aec2b84d14d9b98558ad9ea7d356df0983253eeab019972b' for r in failed),'partial fc7d retained opaque only')
ok(not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')),'no scientific imports')
evidence={'decision':'ACCEPTED_ACTUAL_FINAL11_AND_WITNESS57_PLUS_DIRECT_FULL_BYTE_RECOVERY','actual_remote_receipt_sha256':sha(receipt_raw),'actual_remote_commit':receipt['remote_commit'],'primary_selected_count':receipt['selected_count'],'outcomes':outputs,'failed_original_virtual_bodies_recovered':1186,'failed_outside_raw_files':failed,'failed_partial_archive_parsed':False,'source339_entire_tree_unchanged':True,'original_parent_intents_fields_unchanged':True,'process_start_ticks_observed':False,'runtime_or_empirical_bodies_recovered':False,'posix_original_tree_instantiated':False,'numerical_authority':False,'check_counts':dict(counts),'total_checks':sum(counts.values())}
(H/'READBACK01.json').write_text(json.dumps(evidence,sort_keys=True,indent=2)+'\n');print(json.dumps({'checks':sum(counts.values()),'decision':evidence['decision']}))
