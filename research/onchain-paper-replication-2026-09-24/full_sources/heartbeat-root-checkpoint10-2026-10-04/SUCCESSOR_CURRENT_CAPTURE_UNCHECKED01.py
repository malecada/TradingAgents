"""One complete current changed-byte capture with immutable accepted CAP basis."""
from pathlib import Path
import hashlib,json,os,shutil,stat,sys,time
root=Path.cwd();f=root/'research/onchain-paper-replication-2026-09-24/full_sources';c=f/'heartbeat-root-checkpoint10-2026-10-04';p=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-resource-successor-root-launch-20261005-01');cap=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');r=f/'financial-wrapper-continuation-successor-review01-2026-10-05';out=f/'financial-wrapper-continuation-successor-current-capture01-2026-10-05';identity='financial-wrapper-classification-eager-continue100-resource-successor-20261005-01'
assert hashlib.sha256((p/'recovery04.py').read_bytes()).hexdigest()=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a';sys.path.insert(0,str(p));import recovery04 as R
from bounded_git01 import git
source=git(cap,['rev-parse','HEAD'],cap=128).decode().strip();assert source=='a5bcc943167ad035b45e12ddf9864d46e685b124'
assert not out.exists() and not (p/'attempt').exists() and not (cap/'research_runs'/identity).exists() and shutil.disk_usage(cap).free>=10*1024**3
q=json.loads(R.read(p,'REQUEST_SOURCE_BOUND_DRAFT01.json'));assert q['source']==source and q['proofs']['full_recovery'] is None and q['final_review'] is None
for role,name,pin in [('cumulative','CUMULATIVE_PROOF01.json','74d0bfe2ef63fc00df67cccc725382dcfde9b2bf9dfaec48aa02b467c4f548a4'),('independent_source_input_runtime','SOURCE_INPUT_RUNTIME_PROOF01.json','56366c03ef32b89d9b375242233f0911fa2d06012f4de5ba2d82151205827ecb')]:
 raw=R.read(r,name);assert R.digest(raw)==pin;q['proofs'][role]={'path':str(r/name),'sha256':pin}
R.put(p/'REQUEST_PRESERVATION_DRAFT01.json',q)
basis=f/'financial-wrapper-continuation-outcome-review01-2026-10-05/FULL_REFUSAL_RECOVERY_PROOF01.json';assert R.digest(R.read(basis.parent,basis.name))=='a5357602f130838bbf52fd6fe54288401e91bfd045c96aac73fa128f4be41a42'
old=json.loads(R.read(f/'financial-wrapper-continuation-refused-outcome-capture01-2026-10-05/snapshot','COMPOSITION01.json'))['capsule'];known={x['path']:x for x in old['members']}
def metadata():
 rows=[];deadline=time.monotonic()+10
 for current,dirs,files in os.walk(cap):
  assert time.monotonic()<deadline and len(rows)<4096
  if Path(current)==cap:dirs[:]=[n for n in dirs if n!='.git']
  for name in sorted(dirs+files):
   path=Path(current)/name;s=path.lstat();assert path.resolve()==path and (stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode));row={'path':path.relative_to(cap).as_posix(),'kind':'directory' if stat.S_ISDIR(s.st_mode) else 'file','mode':stat.S_IMODE(s.st_mode)}
   if row['kind']=='file':row['bytes']=s.st_size
   rows.append(row)
 return sorted(rows,key=lambda x:x['path'])
before=metadata();actual={x['path']:x for x in before};assert set(known)<=set(actual)
changed={'tradingagents/research/onchain_replication/operational_source_compatibility.py','tradingagents/research/onchain_replication/financial_wrapper_fixture.py'}
new=set(actual)-set(known);expected={'fixture_inputs/financial_wrapper_continuation_successor01'}|{'fixture_inputs/financial_wrapper_continuation_successor01/'+x for x in ('successor.json','source_closure.json','continue-plan.json','refusal.json','successor-review.json','successor-recovery.json','gates.json')};assert new==expected
for name,row in known.items():
 assert actual[name]['mode']==row['mode'] and actual[name]['kind']==row['kind']
 if name not in changed:assert all(actual[name][k]==v for k,v in row.items() if k!='sha256')
saved={};current=[]
for row in before:
 name=row['path']
 if row['kind']=='file' and (name in changed or name in new):
  raw=R.read(cap,name);assert len(raw)==row['bytes'];saved['CAP/'+name]=raw;current.append({**row,'sha256':R.digest(raw)})
 else:current.append(known.get(name,row))
assert len(saved)==9 and len(current)==1068 and sum(x['kind']=='file' for x in current)==839
scopes={}
for label,base in [('Git',cap/'.git'),('Parent',p),('review-phase',r)]:
 manifest=R.scan(base);scopes[label]={'root':str(base),'manifest':manifest}
 for row in manifest['members']:
  if row['kind']=='file':saved[label+'/'+row['path']]=R.read(base,row['path'])
for name in ('SUCCESSOR_GATE_ADOPTION01.json','SUCCESSOR_READONLY_ADMISSION01.py','SUCCESSOR_READONLY_ADMISSION01.json','SUCCESSOR_READONLY_ADMISSION01.stdout','SUCCESSOR_READONLY_ADMISSION01.stderr','SUCCESSOR_SOURCE_ADOPTION01.json','SUCCESSOR_CURRENT_CAPTURE01.py'):
 saved['Root/'+name]=R.read(c,name)
assert sum(map(len,saved.values()))<16*1024**2
objects=git(cap,['cat-file','--batch-all-objects','--batch-check=%(objectname) %(objecttype) %(objectsize)']).decode().splitlines();assert len(objects)>=422
out.mkdir(mode=0o700);snapshot=out/'snapshot';snapshot.mkdir(mode=0o700);mapped={}
for i,(name,raw) in enumerate(sorted(saved.items())):
 leaf='body-%04d'%i
 with R.new_file(snapshot/leaf) as fd:
  with os.fdopen(os.dup(fd),'wb') as w:w.write(raw)
 mapped[name]={'flat':leaf,'bytes':len(raw),'sha256':R.digest(raw)}
composition={'schema_version':1,'kind':'current-successor-complete-byte-scope-with-accepted-basis','identity':identity,'source':source,'basis':{'path':str(basis),'sha256':R.digest(R.read(basis.parent,basis.name))},'capsule':{'schema_version':old['schema_version'],'root_mode':old['root_mode'],'members':current},'Git_logical_objects':len(objects),'Git_object_inventory':objects,'scopes':scopes,'materialized':mapped,'old830_unchanged_CAP_bodies_not_reread':True,'runtime251_package_bodies_recovered':False,'POSIX_reconstruction':False,'envelope_qualification':'complete actual caller/helpers and source/input/runtime-bound preservation draft; actual full recovery proof/final release references are prospective and require separately preserved final supplement','numerical_claim':False,'external_recovery':None}
R.put(snapshot/'COMPOSITION01.json',composition);manifest=R.scan(snapshot);R.put(out/'archive-manifest.json',manifest);archive=R.pack(snapshot,manifest,out/'increment.tar.gz')
for label,scope in scopes.items():R.same(Path(scope['root']),scope['manifest'])
assert before==metadata() and not (p/'attempt').exists() and not (cap/'research_runs'/identity).exists();R.same(snapshot,manifest)
R.put(out/'CAPTURE01.json',{'schema_version':1,'identity':identity,'source':source,'archive':archive,'new_original_bodies':len(mapped),'new_original_bytes':sum(x['bytes'] for x in mapped.values()),'CAP_regular':839,'CAP_typed':1068,'changed_CAP_regular':9,'Git_logical_objects':len(objects),'Parent_regular':sum(x['kind']=='file' for x in scopes['Parent']['manifest']['members']),'basis':composition['basis'],'scope':'complete current CAP by accepted unchanged basis plus actual nine changed/added regulars, actual complete physical Git tree, current Parent/caller/helpers/preservation draft, frozen review-phase and Root records; final released envelope supplement pending','external_recovery':False})
print(json.dumps({'status':'CAPTURED_ONCE','archive_bytes':archive['bytes'],'archive_sha256':archive['sha256'],'original_bodies':len(mapped),'logical_bytes':sum(x['bytes'] for x in mapped.values()),'Git_objects':len(objects)}))
