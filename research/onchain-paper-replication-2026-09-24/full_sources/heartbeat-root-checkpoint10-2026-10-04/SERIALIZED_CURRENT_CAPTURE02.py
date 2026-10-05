"""Current exact changed-byte capture; accepted CAP/Git object bodies stay reused."""
from pathlib import Path
import hashlib,json,os,resource,shutil,stat,sys,time
root=Path.cwd();F=root/'research/onchain-paper-replication-2026-09-24/full_sources';C=F/'heartbeat-root-checkpoint10-2026-10-04';parent=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-serialized-storage-root-launch-20261005-01');cap=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');identity='financial-wrapper-classification-eager-continue100-serialized-storage-successor-20261005-01';review=F/'financial-wrapper-serialized-storage-binding-review01-2026-10-05';out=F/'financial-wrapper-serialized-storage-current-capture01-2026-10-05'
assert hashlib.sha256((parent/'recovery04.py').read_bytes()).hexdigest()=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a';sys.path.insert(0,str(parent));import recovery04 as R
from bounded_git01 import git
resource.setrlimit(resource.RLIMIT_FSIZE,(R.FILE,R.FILE));assert not out.exists() and not (parent/'attempt').exists() and not os.path.lexists(cap/'research_runs'/identity) and shutil.disk_usage(cap).free>=10*1024**3
adoption=json.loads(R.read(C,'SERIALIZED_SOURCE_GATE_ADOPTION01.json'));source=git(cap,['rev-parse','HEAD'],cap=128).decode().strip();assert source==adoption['source']==adoption['design_source'] and adoption['tracked_count']==375 and adoption['selected_source_count']==374
q=json.loads(R.read(parent,'REQUEST_SOURCE_BOUND_DRAFT01.json'));assert q['source']==source and q['proofs']['full_recovery'] is None and q['final_review'] is None
for role,name in [('cumulative','CUMULATIVE_PROOF01.json'),('independent_source_input_runtime','SOURCE_INPUT_RUNTIME_PROOF01.json')]:
 raw=R.read(review,name);proof=json.loads(raw);assert proof['identity']==identity and proof['source']==source;q['proofs'][role]={'path':str(review/name),'sha256':R.digest(raw)}
with (parent/'REQUEST_PRESERVATION_DRAFT01.json').open('xb') as f:f.write((json.dumps(q,sort_keys=True,separators=(',',':'))+'\n').encode())
basis=F/'financial-wrapper-continuation-successor-outcome-review01-2026-10-05/FULL_TERMINAL_RECOVERY_PROOF01.json';assert R.digest(R.read(basis.parent,basis.name))=='2263ea2cd9f6e6b2fe6100498a917fb971328d9e4ae3478e4f544a07f93d908b'
raw=R.read(F/'financial-wrapper-continuation-successor-terminal-capture01-2026-10-05/snapshot','COMPOSITION01.json');assert R.digest(raw)=='6da636ed7f5de0bb93cff1556532fd7b9a63d776ca1e5094cf363ddc58c74e5c';old=json.loads(raw)
def metadata(base,omit_git=False):
 rows=[];deadline=time.monotonic()+10
 for current,dirs,files in os.walk(base):
  assert time.monotonic()<deadline and len(rows)<4096
  if Path(current)==base and omit_git:dirs[:]=[n for n in dirs if n!='.git']
  for name in sorted(dirs+files):
   p=Path(current)/name;s=p.lstat();assert p.resolve()==p and (stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode));row={'path':p.relative_to(base).as_posix(),'kind':'directory' if stat.S_ISDIR(s.st_mode) else 'file','mode':stat.S_IMODE(s.st_mode)}
   if row['kind']=='file':assert s.st_nlink==1 and s.st_size<=R.FILE;row['bytes']=s.st_size
   rows.append(row)
 return sorted(rows,key=lambda r:r['path'])
known={r['path']:r for r in old['capsule']['members']};before=metadata(cap,True);actual={r['path']:r for r in before};assert stat.S_IMODE(cap.lstat().st_mode)==old['capsule']['root_mode'];assert set(known)<=set(actual)
changed={'tradingagents/research/onchain_replication/operational_source_compatibility.py'};new=set(actual)-set(known);directory='fixture_inputs/financial_wrapper_serialized_storage01';assert new=={directory}|{directory+'/'+n for n in ('continue-plan.json','successor.json','source_closure.json','refusal.json','previous-recovery.json','successor-review.json','successor-recovery.json','gates.json')}
for n,row in known.items():
 assert actual[n]['kind']==row['kind'] and actual[n]['mode']==row['mode']
 if n not in changed:assert actual[n]=={k:v for k,v in row.items() if k!='sha256'}
saved={};current=[]
for row in before:
 n=row['path']
 if row['kind']=='file' and (n in changed or n in new):
  b=R.read(cap,n);assert len(b)==row['bytes'] and R.digest(b)==(q['registration_sha256'] if n==q['registration'] else q['source_files'][n]);saved['CAP/'+n]=b;current.append(dict(row,sha256=R.digest(b)))
 else:current.append(known.get(n,row))
assert len(current)==1088 and sum(r['kind']=='file' for r in current)==856 and len(saved)==9
old_git=old['Git'];git_known={r['path']:r for r in old_git['manifest']['members']};git_before=metadata(cap/'.git');git_actual={r['path']:r for r in git_before};assert set(git_known)<=set(git_actual);git_current=[];git_reused=0
for row in git_before:
 n=row['path'];prior=git_known.get(n)
 if row['kind']=='file' and (prior is None or not (len(Path(n).parts)==3 and Path(n).parts[0]=='objects' and len(Path(n).parts[1])==2 and len(Path(n).parts[2])==38 and all(c in '0123456789abcdef' for c in ''.join(Path(n).parts[1:])))):
  b=R.read(cap/'.git',n);assert len(b)==row['bytes'];saved['Git/'+n]=b;git_current.append(dict(row,sha256=R.digest(b)))
 elif prior is not None:
  assert row=={k:v for k,v in prior.items() if k!='sha256'};git_current.append(prior);git_reused+=row['kind']=='file'
 else:git_current.append(row)
git_manifest={'schema_version':old_git['manifest']['schema_version'],'root_mode':old_git['manifest']['root_mode'],'members':git_current};assert stat.S_IMODE((cap/'.git').lstat().st_mode)==git_manifest['root_mode']
scopes={'Git':{'root':str(cap/'.git'),'manifest':git_manifest,'accepted_unchanged_object_basis':old_git}}
# Review fields are explicitly frozen now; later release/outcome files are a separate increment.
review_names=('SOURCE_REVIEW_PROOF01.json','SOURCE_RECOVERY_PROOF01.json','SOURCE_CHECK01.json','SOURCE_REMOTE03_SOURCE_CHECK01.json','SOURCE_REMOTE03_ENTRY_RELEASE01.json','WATCH_SOURCE_CHECK01.json','WATCH_FINDING01.json','SOURCE_REMOTE_FAILURE_CHECK01.json','FAILED_RECEIVER_CAPTURE_CHECK01.json','FAILED_FLAT_SOURCE_CHECK01.json','FAILED_FLAT_ENTRY_RELEASE01.json','FAILED_FLAT_CHECK01.json','SOURCE_REMOTE_CHECK01.json','ADOPTION_SOURCE_CHECK01.json','CUMULATIVE_PROOF01.json','SOURCE_INPUT_RUNTIME_PROOF01.json','CURRENT_GATE_CHECK01.json','ADMISSION_PHASE_REPORT01.md')
review_pins={n:R.digest(R.read(review,n)) for n in review_names}
for n in review_names:saved['review-phase/'+n]=R.read(review,n)
scopes['review-phase']={'root':str(review),'exact_files':review_pins}
manifest=R.scan(parent);scopes['Parent']={'root':str(parent),'manifest':manifest}
for row in manifest['members']:
 if row['kind']=='file':saved['Parent/'+row['path']]=R.read(parent,row['path'])
for n in ('SERIALIZED_SOURCE_GATE_ADOPT03.py','SERIALIZED_ADOPTION_INTENT01.json','SERIALIZED_SOURCE_GATE_ADOPTION01.json','SERIALIZED_READONLY_ADMISSION01.py','SERIALIZED_READONLY_ADMISSION01.json','SERIALIZED_READONLY_ADMISSION01.stdout','SERIALIZED_READONLY_ADMISSION01.stderr','SERIALIZED_READONLY_ADMISSION_ROOT_EXIT01.json','SERIALIZED_CURRENT_CAPTURE02.py'):saved['Root/'+n]=R.read(C,n)
for label,base,names in [('source-recovery',F/'financial-wrapper-serialized-storage-source-remote03-2026-10-05',('SELECTED_BODIES01.json','REMOTE_RECOVERY01.json','ACTUAL_ROOT_EXIT01.json')),('failed-flat-recovery',F/'financial-wrapper-serialized-storage-source-failed-flat01-2026-10-05',('RECOVERY01.json','ACTUAL_ROOT_EXIT01.json'))]:
 pins={n:R.digest(R.read(base,n)) for n in names};scopes[label]={'root':str(base),'exact_files':pins}
 for n in names:saved[label+'/'+n]=R.read(base,n)
objects=git(cap,['cat-file','--batch-all-objects','--batch-check=%(objectname) %(objecttype) %(objectsize)']).decode().splitlines();assert old['Git_logical_objects']==438 and len(objects)>438
assert sum(map(len,saved.values()))<8*1024**2;out.mkdir(mode=0o700);snapshot=out/'snapshot';snapshot.mkdir(mode=0o700);mapped={}
for i,(name,b) in enumerate(sorted(saved.items())):
 leaf='body-%04d'%i
 with R.new_file(snapshot/leaf) as fd:
  with os.fdopen(os.dup(fd),'wb') as f:f.write(b)
 mapped[name]={'flat':leaf,'bytes':len(b),'sha256':R.digest(b)}
composition={'schema_version':1,'kind':'current-serialized-storage-byte-increment','identity':identity,'source':source,'basis':{'path':str(basis),'sha256':R.digest(R.read(basis.parent,basis.name))},'capsule':{'schema_version':old['capsule']['schema_version'],'root_mode':old['capsule']['root_mode'],'members':current},'scopes':scopes,'Git_logical_objects':len(objects),'Git_object_inventory':objects,'materialized':mapped,'accepted_unchanged_CAP_bodies_reused':847,'accepted_unchanged_Git_object_bodies_reused':git_reused,'immutable_current_writer_exclusion':False,'runtime_package_bodies_recovered':False,'POSIX_reconstruction':False,'numerical_claim':False,'external_recovery':None,'qualification':'Complete current CAP/Git byte scope through accepted immutable recovery basis plus exact nine changed CAP regular bodies, actual new Git objects/all current mutable Git metadata, whole new Parent and fixed genuine review/Root files. No unchanged historical body recopy. Released envelope remains a separate genuine supplement.'}
R.put(snapshot/'COMPOSITION01.json',composition);manifest=R.scan(snapshot);R.put(out/'archive-manifest.json',manifest);archive=R.pack(snapshot,manifest,out/'increment.tar.gz');R.same(parent,scopes['Parent']['manifest']);assert all(R.digest(R.read(review,n))==pin for n,pin in review_pins.items());assert before==metadata(cap,True) and git_before==metadata(cap/'.git');R.same(snapshot,manifest)
R.put(out/'CAPTURE01.json',{'schema_version':1,'source':source,'identity':identity,'archive':archive,'basis':composition['basis'],'new_original_bodies':len(mapped),'new_original_bytes':sum(r['bytes'] for r in mapped.values()),'CAP_regular':856,'CAP_typed':1088,'new_or_changed_CAP_regular':9,'Git_logical_objects':len(objects),'Git_regular':sum(r['kind']=='file' for r in git_current),'Git_unchanged_object_bodies_reused':git_reused,'Parent_regular':sum(r['kind']=='file' for r in scopes['Parent']['manifest']['members']),'external_recovery':False,'scope':composition['qualification']})
print(json.dumps({'status':'CAPTURED_ONCE','original_bodies':len(mapped),'logical_bytes':sum(r['bytes'] for r in mapped.values()),'archive':archive,'Git_objects':len(objects),'reused_Git_objects':git_reused}))
