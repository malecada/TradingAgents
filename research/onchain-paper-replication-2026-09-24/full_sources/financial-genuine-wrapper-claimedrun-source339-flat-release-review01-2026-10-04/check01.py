import copy,hashlib,importlib.util,json,os,shutil,stat,sys
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;D=F/'financial-genuine-wrapper-root-claimedrun-source339-flat01-2026-10-04';H=F/'financial-genuine-wrapper-claimedrun-source339-flat-20261004-01';A=F/'financial-genuine-wrapper-claimedrun-source-recovery-preparation03-2026-10-04';V=F/'financial-genuine-wrapper-claimedrun-source-recovery-review03-2026-10-04';REMOTE=F/'financial-genuine-wrapper-root-claimedrun-source339-remote02-2026-10-04';RV=F/'financial-genuine-wrapper-claimedrun-source339-actual-remote-review01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):assert v,m;checks.append(m)
qraw=(D/'REQUEST_PROPOSAL02.json').read_bytes();ck(sha(qraw)=='3e56dfac4d7a666097d6a70e57685cafe42e0abac87f476fa249c6ef46b8b149','actual exact Root proposal');q=json.loads(qraw);ck(q['release'] is None,'actual proposal release null');ck(sha((V/'MANIFEST01.json').read_bytes())=='dacd234b5c16579039d0da8d1654b4a982260873904b15bf91fc126507977980','genuine strict03 review seal');vr=json.loads((V/'READBACK01.json').read_bytes());ck(vr['decision']=='ACCEPTED_SOURCE_ONLY_STRICT1024_CORRECTION' and vr['new1025_refused_before_extra_state'] is True,'genuine strict bound/source acceptance')
files=['restore01.py','git_objects01.py','recovery04.py','owned_io.py','bounded_git01.py','CAPTURE_PINS01.json'];ck({p.name for p in H.iterdir()}==set(files),'exact installed sixbody fresh namespace');pins={}
for n in files:
 p=H/n;s=p.lstat();b=p.read_bytes();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and b==(A/n).read_bytes(),'entire installed accepted closure '+n);pins[n]=sha(b)
ck(pins['restore01.py'].startswith('9e21e92c') and pins['git_objects01.py']=='c364269be9c112dbc9501a41c8f9cf21def9a95b33cf2b9054f4384ae3888a4a','exact strictadapter/Githelper');ck(sha((RV/'READBACK01.json').read_bytes())==q['review']['sha256']=='6dcb03cfed84ff48132710e548aeaead0015c97df1b8885f55e8ad7ea0cbe13d' and Path(q['review']['path'])==RV/'READBACK01.json','genuine remote review reference');ck(sha((RV/'MANIFEST01.json').read_bytes())=='a747c2ad4eda66c44605690029c3d697fc663b8e8ea5b7385f7c9562c35dde15','full actual remote review seal');proof=json.loads((RV/'READBACK01.json').read_bytes());ck(proof['decision']=='ACCEPTED_ACTUAL_SOURCE339_SELECTED_REMOTE_RECOVERY','actual accepted remoteproof')
ck(q['remote_root']==str(REMOTE) and sha((REMOTE/'REMOTE_RECOVERY01.json').read_bytes())==q['remote_receipt_sha256']==proof['remote_receipt_sha256']=='9e6d7dd7e0260aa955f6aeff72abbf6fbaf7c85bd5b308d1c527c6b69ce472b2','actual remote exact binding');sys.path.insert(0,str(H));spec=importlib.util.spec_from_file_location('exact_installed_adapter_source_only',H/'restore01.py');P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
def refuse(fn,label):
 try:fn()
 except (ValueError,KeyError,TypeError,FileNotFoundError) as e:checks.append(label);return {'case':label,'type':type(e).__name__,'reason':str(e)}
 raise AssertionError('unexpectedacceptance '+label)
refusals=[refuse(lambda:P.validate_request(q),'original real null release refuses')]
for k in q:
 bad=copy.deepcopy(q);del bad[k];refusals.append(refuse(lambda:P.validate_request(bad),'missing exact request field '+k))
bundle,body,receipt=P.remote_bodies(REMOTE,q['remote_receipt_sha256']);m,unused,t=P.joins(body);ck(len(m['members'])==1029 and sum(r['kind']=='file' for r in m['members'])==747,'actual required full source scope');S=Path(t['source_root']);P.R.same(S,m);ck(q['source']==t['current_equals_design']==P.SOURCE,'currentSource exact0a2');ck(len(receipt['selected_blobs'])==195 and receipt['selected_count']==195,'actual genuine remote denominator');free=shutil.disk_usage(H).free;ck(free>=10*1024**3,'fresh actual10GiB floor')
# Pure pin/denominator refusal controls on opaque in-memory metadata; no restore or claimed history construction.
for name in body:
 altered=dict(body);altered[name]=body[name]+b' '
 if name=='source-manifest.json':refusals.append(refuse(lambda:P.joins(altered),'noncanonical manifest tail refuses'))
for field,value in [('tracked',338),('original_spent_claims',0),('new_claim_started',True),('parent_or_final_review_captured',True)]:
 altered=dict(body);z=json.loads(body['CAPTURE01.json']);z[field]=value;altered['CAPTURE01.json']=P.R.encode(z);refusals.append(refuse(lambda:P.joins(altered),'altered capture '+field+' refuses'))
refusals.append(refuse(lambda:P.remote_bodies(REMOTE,'0'*64),'wrong actual remote receipt hash refuses'))
contract=sha(P.R.encode({k:v for k,v in q.items() if k!='release'}));release={'decision':'accepted-exact-claimedrun-source339-flat-recovery','source':q['source'],'helper_sha256':pins['restore01.py'],'request_sha256':contract,'review_sha256':q['review']['sha256']}
# Genuine reviewer release after all actual inputs joined, only owned output. Not a Root request mutation.
path=O/'RELEASE01.json';fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
try:
 raw=P.R.encode(release);offset=0
 while offset<len(raw):offset+=os.write(fd,raw[offset:])
 os.fsync(fd)
finally:os.close(fd)
released=copy.deepcopy(q);released['release']={'path':str(path),'sha256':sha(raw)};ck(P.validate_request(released)==REMOTE,'genuine exact release accepted by original pure validator')
for k,value in [('source','0'*40),('remote_receipt_sha256','0'*64),('remote_root',str(D))]:
 bad=copy.deepcopy(released);bad[k]=value;refusals.append(refuse(lambda:P.validate_request(bad),'exact released contract tamper '+k+' refuses'))
bad=copy.deepcopy(released);bad['review']['sha256']='0'*64;refusals.append(refuse(lambda:P.validate_request(bad),'tampered genuine review refuses'));bad=copy.deepcopy(released);bad['release']['sha256']='0'*64;refusals.append(refuse(lambda:P.validate_request(bad),'tampered release ref refuses'))
ck({p.name for p in H.iterdir()}==set(files),'installed output remains sixbodies nointent/recovery');ck((D/'REQUEST_PROPOSAL02.json').read_bytes()==qraw,'Root proposal remains original null');P.R.same(S,m);ck(not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules),'no research numeric import')
x={'schema_version':1,'decision':'ACCEPTED_EXACT_REQUEST_RELEASE_FOR_ONE_SOURCE339_FLAT_ONLY','proposal_sha256':sha(qraw),'request_contract_sha256':contract,'release_sha256':sha(raw),'release_path':str(path),'review_sha256':q['review']['sha256'],'source':q['source'],'installed_helper_pins':pins,'checks':len(checks),'refusals':refusals,'observed_free_bytes':free,'required_original_members':1029,'required_regular_bodies':747,'required_private_flat_files_with_metadata':748,'required_tracked_source':339,'required_selected_source_pins':338,'required_input_roles':8,'required_implementation':194,'required_package':149,'actual_source_restore_executed':False,'actual_recovered_ancestry_observed':False,'actual_Root_request_mutated':False,'fresh_research_claims_created':0,'POSIX_runtime_empirical_caller_native_authority':False};(O/'READBACK01.json').write_bytes(P.R.encode(x));print(json.dumps({'checks':len(checks),'contract':contract,'release':sha(raw)}))
