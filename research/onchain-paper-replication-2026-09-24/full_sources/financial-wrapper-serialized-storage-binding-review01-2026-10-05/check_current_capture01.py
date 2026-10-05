from pathlib import Path
import json,hashlib,stat,tarfile,re,subprocess
M=Path.cwd();F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=Path(__file__).parent;C=F/'heartbeat-root-checkpoint10-2026-10-04';T=F/'financial-wrapper-serialized-storage-current-capture01-2026-10-05';CAP=M.parent/'onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source';H=lambda b:hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def ref(p):b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':H(b)}
x=read(T/'snapshot/COMPOSITION01.json');r=read(T/'CAPTURE01.json');root=read(T/'ACTUAL_ROOT_EXIT01.json');entry=read(D/'CURRENT_CAPTURE_ENTRY_RELEASE01.json');oldpath=F/'financial-wrapper-continuation-successor-terminal-capture01-2026-10-05/snapshot/COMPOSITION01.json';old=read(oldpath);assert ref(oldpath)['sha256']==entry['accepted_composition_sha256'];assert x['basis']['sha256']==entry['accepted_basis_sha256']=='2263ea2cd9f6e6b2fe6100498a917fb971328d9e4ae3478e4f544a07f93d908b'
assert x['source']==r['source']==entry['current_source']=='6b07c0f841e7d38102814aabb335751fd71fb7f7' and root['actual_root_exit']==0 and root['session_id'] is None and root['tool_chunk_id']=='8db87a'
assert ref(C/'SERIALIZED_CURRENT_CAPTURE02.py')['sha256']==entry['source_sha256']=='898639ccebe9abbcb1b4477bddfd219de715c7c73e854a8a73da077e8388d8fa'
prior={v['path']:v for v in old['capsule']['members']};now={v['path']:v for v in x['capsule']['members']};helper='tradingagents/research/onchain_replication/operational_source_compatibility.py';assert set(prior)<=set(now) and all(now[k]==v for k,v in prior.items() if k!=helper);assert len(now)==1088 and sum(v['kind']=='file' for v in now.values())==856
new=set(now)-set(prior);assert len(new)==9 and sum(now[k]['kind']=='file' for k in new)==8
mapped=x['materialized'];assert len(mapped)==93 and sum(v['bytes'] for v in mapped.values())==1871149
payload={};originmap={}
for name,row in mapped.items():
 label,rel=name.split('/',1);base=CAP if label=='CAP' else C if label=='Root' else Path(x['scopes'][label]['root']);p=base/rel;b=(T/'snapshot'/row['flat']).read_bytes();assert len(b)==row['bytes'] and H(b)==row['sha256'];assert p.read_bytes()==b;payload[name]=b;originmap[name]=p
assert {n[4:] for n in mapped if n.startswith('CAP/')}=={helper}|{n for n in new if now[n]['kind']=='file'}
gitold={v['path']:v for v in old['Git']['manifest']['members']};gitnow={v['path']:v for v in x['scopes']['Git']['manifest']['members']};assert set(gitold)<=set(gitnow);reused=[]
for name,row in gitnow.items():
 if row['kind']=='file':
  if 'Git/'+name in mapped:assert H(payload['Git/'+name])==row['sha256'] and len(payload['Git/'+name])==row['bytes']
  else:assert re.fullmatch(r'objects/[0-9a-f]{2}/[0-9a-f]{38}',name) and row==gitold[name];reused.append(name)
assert len(reused)==438 and sum(v['kind']=='file' for v in gitnow.values())==479 and sum(n.startswith('Git/') for n in mapped)==41
assert x['Git_logical_objects']==454 and len(x['Git_object_inventory'])==454
inventory=subprocess.run(['git','cat-file','--batch-all-objects','--batch-check=%(objectname) %(objecttype) %(objectsize)'],cwd=CAP,capture_output=True,check=True).stdout.decode().splitlines();assert inventory==x['Git_object_inventory']
for label,scope in x['scopes'].items():
 if label=='Git':continue
 if 'manifest' in scope:
  rows=scope['manifest']['members'];expected={label+'/'+v['path'] for v in rows if v['kind']=='file'}
  for v in rows:
   p=Path(scope['root'])/v['path'];assert stat.S_IMODE(p.lstat().st_mode)==v['mode']
   if v['kind']=='file':assert H(payload[label+'/'+v['path']])==v['sha256'] and len(payload[label+'/'+v['path']])==v['bytes']
 else:
  expected={label+'/'+n for n in scope['exact_files']}
  for n,pin in scope['exact_files'].items():assert H(payload[label+'/'+n])==pin
 assert expected=={n for n in mapped if n.startswith(label+'/')}
assert x['scopes']['review-phase']['exact_files']==entry['preserved_review_files']
q=json.loads(payload['Parent/REQUEST_PRESERVATION_DRAFT01.json']);assert q['proofs']['full_recovery'] is None and q['final_review'] is None and q['status']=='DRAFT_NOT_RELEASED'
for role,name in [('cumulative','CUMULATIVE_PROOF01.json'),('independent_source_input_runtime','SOURCE_INPUT_RUNTIME_PROOF01.json')]:assert q['proofs'][role]['sha256']==H(payload['review-phase/'+name])
manifest=read(T/'archive-manifest.json');expected={v['path']:v for v in manifest['members']};assert len(expected)==94 and all(v['kind']=='file' for v in expected.values());assert ref(T/'archive-manifest.json')['sha256']==r['archive']['manifest_sha256']=='945c0f480cd2fef0ca5d563d51ad93b19da84dc70382819d30de5d790d4f5799';assert ref(T/'increment.tar.gz')['sha256']==r['archive']['sha256']=='61365ba16c8561b4ebbe17e1b8ac23e9b31261e9e87cda775019ff09ce625995' and (T/'increment.tar.gz').stat().st_size==619705
with tarfile.open(T/'increment.tar.gz','r:gz') as tar:
 members=tar.getmembers();assert len(members)==94 and {v.name for v in members}==set(expected)
 for item in members:
  assert item.isfile();b=tar.extractfile(item).read();v=expected[item.name];assert H(b)==v['sha256'] and len(b)==v['bytes'] and item.mode==v['mode']
result={'schema_version':1,'decision':'accepted-actual-current-serialized-capture','capture':ref(T/'CAPTURE01.json'),'actual_root_exit':ref(T/'ACTUAL_ROOT_EXIT01.json'),'composition':ref(T/'snapshot/COMPOSITION01.json'),'archive':ref(T/'increment.tar.gz'),'archive_manifest':ref(T/'archive-manifest.json'),'source':x['source'],'identity':x['identity'],'new_original_bodies':93,'new_original_bytes':1871149,'archive_bodies':94,'CAP_regular':856,'CAP_typed':1088,'CAP_accepted_unchanged_regular':847,'CAP_changed_or_new_regular':9,'Git_regular':479,'Git_accepted_unchanged_loose_objects':438,'Git_new_objects_and_mutable_files_read':41,'Git_logical_objects':454,'Parent_regular':11,'review_phase_regular':18,'Root_regular':9,'source_recovery_regular':3,'failed_flat_recovery_regular':2,'all93_actual_origin_and_snapshot_joins':True,'final_release_envelope_pending':True,'external_current_recovery':False,'numerical_authority':False,'qualification':'Accepted current composition and actual changed bytes; old847 CAP and438 loose Git-object bodies reused by exact accepted basis and metadata, not rescanned. Mutable Git/newobjects and complete new Parent captured. No immutable writer/POSIX/runtime-body or final-release claim.'};p=D/'CURRENT_CAPTURE_CHECK01.json';assert not p.exists();p.write_text(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n');p.chmod(0o444);print(ref(p))
