from pathlib import Path
import hashlib,json,stat,io,gzip,tarfile,zlib,os
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=Path(__file__).parent;R=F/'financial-wrapper-serialized-prediction-current-remote01-2026-10-05';O=F/'financial-wrapper-serialized-prediction-current-flat01-2026-10-05';prefix='research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-current-capture01-2026-10-05';S=R/'selected'/prefix;sha=lambda b:hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes())}
def load(p):return json.loads(p.read_bytes())
def save(n,v):
 with (D/n).open('x') as h:h.write(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n')
 os.chmod(D/n,0o444);return ref(D/n)
raw=(O/'RECOVERY01.json').read_bytes();assert sha(raw)=='c1044170db742f5cf7ce7e4be43fa0ddd6c0a701c4f7b020cef920fecc455d8e';receipt=json.loads(raw);assert sha((O/'ACTUAL_ROOT_EXIT01.json').read_bytes())=='e845c1adb519d7293563ac0344d7bf87701484f37ae0471ef959a0a550bbe39e' and load(O/'ACTUAL_ROOT_EXIT01.json')['actual_exit']==0
assert receipt['receiver_receipt_sha256']==sha((R/'REMOTE_RECOVERY01.json').read_bytes())=='dd8d8265be9b810ccc0a296b7d32f385ef52d83b32277cf4fe524fbceb8237f7';assert receipt['primitive']['regular_bodies']==110
metadata_raw=(O/'flat'/receipt['primitive']['metadata_file']).read_bytes();assert sha(metadata_raw)==receipt['primitive']['metadata_sha256'];meta=json.loads(metadata_raw);manifest=load(S/'archive-manifest.json');assert meta['manifest']==manifest and sha((S/'archive-manifest.json').read_bytes())==receipt['manifest_sha256'];rows={r['path']:r for r in manifest['members']};flatmap=meta['flat_members'];assert set(flatmap)==set(rows) and len(flatmap)==len(set(flatmap.values()))==110
assert {p.name for p in (O/'flat').iterdir()}==set(flatmap.values())|{receipt['primitive']['metadata_file']}
bodies={}
for name,filename in flatmap.items():
 p=O/'flat'/filename;s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304;body=p.read_bytes();assert len(body)==rows[name]['bytes'] and sha(body)==rows[name]['sha256'];bodies[name]=body
# Re-encode only restored new bodies using the accepted R4 deterministic PAX framing.
sink=io.BytesIO()
with gzip.GzipFile(filename='',mode='wb',fileobj=sink,mtime=0) as gz:
 with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
  for row in manifest['members']:
   t=tarfile.TarInfo(row['path']);t.mode=row['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0;t.size=row['bytes'];tf.addfile(t,io.BytesIO(bodies[row['path']]))
encoded=sink.getvalue();assert len(encoded)==683272 and sha(encoded)==receipt['archive_sha256']=='e22abea2dd16f158e9536e1f90609894e04a2037cd31a69971875fa41043c106' and encoded==(S/'increment.tar.gz').read_bytes()
c=json.loads(bodies['COMPOSITION01.json']);capturecheck=load(D/'CURRENT_CAPTURE_CHECK01.json');assert sha(bodies['COMPOSITION01.json'])==capturecheck['composition']['sha256'];mapped=c['materialized'];assert len(mapped)==109
originals={name:bodies[row['flat']] for name,row in mapped.items()}
for name,row in mapped.items():assert len(originals[name])==row['bytes'] and sha(originals[name])==row['sha256']
caprows={r['path']:r for r in c['capsule']['members']};gitrows={r['path']:r for r in c['Git']['manifest']['members']};parentrows={r['path']:r for r in c['Parent']['manifest']['members']};reviewrows={r['path']:r for r in c['review-phase']['manifest']['members']}
for label,index in [('CAP',caprows),('Git',gitrows),('Parent',parentrows),('review-phase',reviewrows)]:
 for name,body in originals.items():
  if name.startswith(label+'/'):
   r=index[name[len(label)+1:]];assert r['kind']=='file' and r['bytes']==len(body) and r['sha256']==sha(body) and isinstance(r['mode'],int)
q=json.loads(originals['Parent/REQUEST_PRESERVATION_DRAFT01.json']);assert q['source']==q['design_source']==c['source']=='4c66c404fd61ccdbb62c39cd91e16878df74a232';assert q['status']=='DRAFT_NOT_RELEASED' and q['final_review'] is None and q['proofs']['full_recovery'] is None
for role,name in [('cumulative','CUMULATIVE_PROOF01.json'),('independent_source_input_runtime','SOURCE_INPUT_RUNTIME_PROOF01.json')]:assert q['proofs'][role]['sha256']==sha(originals['review-phase/'+name])
gateraw=originals['CAP/'+q['registration']];gate=json.loads(gateraw);exp=gate['experiments'][q['identity']];assert sha(gateraw)==q['registration_sha256'] and exp['source_files']==q['source_files'] and {k:v['sha256'] for k,v in exp['inputs'].items()}==q['input_hashes'];assert len(q['source_files'])==381 and len(exp['inputs'])==29
assert sha(originals['Parent/parent01.py'])==q['caller_sha256']
for name,pin in q['helper_hashes'].items():assert sha(originals['Parent/'+name])==pin
cum=json.loads(originals['review-phase/CUMULATIVE_PROOF01.json']);assert cum['spent_claims']==5 and cum['complete']==2 and cum['failed']==3 and cum['remaining']==15
# Authenticate recovered new loose Git objects, then resolve all changed file paths from the actual recovered commit tree.
objects={}
for name,raw in originals.items():
 if not name.startswith('Git/objects/'):continue
 parts=Path(name).parts
 if len(parts)==4 and len(parts[2])==2 and len(parts[3])==38:
  inflated=zlib.decompress(raw);assert len(inflated)<=4194304;head,content=inflated.split(b'\0',1);kind,size=head.split();assert int(size)==len(content);oid=parts[2]+parts[3];assert hashlib.sha1(inflated).hexdigest()==oid;objects[oid]=(kind,content)
assert len(objects)==19
kind,commit=objects[q['source']];assert kind==b'commit' and b'parent 6b07c0f841e7d38102814aabb335751fd71fb7f7\n' in commit;tree=commit.splitlines()[0].split()[1].decode()
def entries(oid):
 kind,b=objects[oid];assert kind==b'tree';out={};offset=0
 while offset<len(b):
  nul=b.index(b'\0',offset);mode,name=b[offset:nul].split(b' ',1);oid2=b[nul+1:nul+21].hex();out[name.decode()]=(mode,oid2);offset=nul+21
 return out
for name,body in originals.items():
 if not name.startswith('CAP/'):continue
 oid=tree;parts=Path(name[4:]).parts
 for part in parts:mode,oid=entries(oid)[part]
 assert mode==b'100644' and objects[oid]==(b'blob',body)
prior=load(F/'financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/new-bodies/COMPOSITION01.json');oldcap={r['path']:r for r in prior['capsule']['members']};oldgit={r['path']:r for r in prior['Git']['manifest']['members']};assert sum(r['kind']=='file' for r in caprows.values())==1188 and len(caprows)==1530
for n,r in caprows.items():
 if 'CAP/'+n not in originals and n in oldcap:assert r==oldcap[n]
reused=[n for n,r in gitrows.items() if r['kind']=='file' and 'Git/'+n not in originals];assert len(reused)==454 and all(gitrows[n]==oldgit[n] for n in reused)
assert len(parentrows)==11 and sum(r['kind']=='file' for r in gitrows.values())==498 and c['Git_logical_objects']==473
for n in ['Root/SERIALIZED_PREDICTION_CURRENT_CAPTURE01.py','Root/SERIALIZED_PREDICTION_CURRENT_CAPTURE01_WITHHELD.json','review-phase/CURRENT_CAPTURE_FINDING01.json']:assert n in originals
check={'schema_version':1,'decision':'accepted-actual-complete-current-prediction-flat-byte-recovery','source':q['source'],'identity':q['identity'],'actual_flat_receipt':ref(O/'RECOVERY01.json'),'actual_flat_root_exit':ref(O/'ACTUAL_ROOT_EXIT01.json'),'actual_remote_check':ref(D/'CURRENT_REMOTE_CHECK01.json'),'capture_review':ref(D/'CURRENT_CAPTURE_CHECK01.json'),'archive_sha256':sha(encoded),'archive_bytes':len(encoded),'restored_metadata_sha256':sha(metadata_raw),'composition_sha256':sha(bodies['COMPOSITION01.json']),'fresh_bodies':110,'original_mappings':109,'new_original_bytes':1580043,'all_restored_bytes_and_path_modes_joined':True,'deterministic_R4_archive_reencoding_identical':True,'new_Git_objects_hash_checked':19,'actual_recovered_commit_tree_changed_files_joined':11,'CAP_regular':1188,'CAP_typed':1530,'CAP_reused_regular':1177,'Git_regular':498,'Git_logical_objects':473,'Git_reused_loose_regular':454,'Parent_regular':11,'review_phase_regular':24,'accepted_basis':c['basis'],'caller_source_input_runtime_and_accounting_joined':True,'withheld_source01_preserved':True,'original_parent_exit':None,'native_PID_history_complete':False,'POSIX_reconstruction':False,'runtime_body_recovery':False,'immutable_writer_exclusion':False,'final_envelope_supplement_pending':True,'numerical_authority':False,'qualification':'All110 fresh bodies read once. All109 origin mappings and typed mode/name manifests joined to actual capture and received archive. New19 Git objects independently decoded as opaque Git storage, actual recovered source commit/tree resolves all11 changed/new CAP files. Old1177 CAP and454 Git loose bodies reused through actual6bbe/9fc; no historical body reread, tensors, numerical packages or economic inference.'}
cp=save('CURRENT_FLAT_CHECK01.json',check)
proof={'schema_version':1,'kind':'full_recovery','decision':'accepted-actual-complete-current-serialized-prediction-byte-recovery','identity':q['identity'],'source':q['source'],'design_source':q['source'],'accepted_baseline':c['basis'],'actual_flat_receipt':ref(O/'RECOVERY01.json'),'actual_flat_Root_exit':ref(O/'ACTUAL_ROOT_EXIT01.json'),'capture_review':ref(D/'CURRENT_CAPTURE_CHECK01.json'),'review':cp,'scope':{'CAP_regular':1188,'CAP_typed':1530,'Git_regular':498,'Git_logical_objects':473,'Parent_regular':11,'accepted_unchanged_CAP_regular':1177,'accepted_unchanged_Git_objects':454,'fresh_flat_bodies':110,'new_original_bodies':109},'final_envelope_supplement_pending':True,'final_envelope_scope':'Actual source-bound caller/helpers, preservation draft and genuine current cumulative/runtime metadata proofs recovered. Final released request/review, recovery proof and post-capture review tail require separate direct byte recovery. Detailed review pins complete original path/mode mappings and independently reconstructed actual Git commit/tree.','original_parent_exit':None,'native_PID_history_complete':False,'POSIX_reconstruction':False,'installed_runtime_body_recovery':False,'immutable_writer_exclusion':False,'namespace_reuse_authority':False,'paper_fit_credit':0,'numerical_authority':False}
print(json.dumps({'check':cp,'proof':save('FULL_CURRENT_RECOVERY_PROOF01.json',proof)}))
