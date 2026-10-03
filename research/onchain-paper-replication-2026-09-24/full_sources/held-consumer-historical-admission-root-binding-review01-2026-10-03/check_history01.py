"""Offline independent original history byte/object verification only."""
import hashlib,json,os,stat,subprocess,tarfile
from pathlib import Path
H=Path(__file__).resolve().parent;F=H.parent;MAIN=F.parents[2]
R=F/'held-consumer-historical-admission-root-binding01-2026-10-03'
sha=lambda b:hashlib.sha256(b).hexdigest()
raw=(R/'HISTORY_BINDING01.json').read_bytes();assert sha(raw)=='4d669b4cd53a314cc2e8fc169761da30f770f71b60ca0d3989d411b8c4d0ae23';doc=json.loads(raw)
planraw=(MAIN/doc['copy_plan']['path']).read_bytes();assert sha(planraw)==doc['copy_plan']['sha256'];plan=json.loads(planraw)
S=Path(doc['source_root']);HEAD='fa9712c36daf2896ef3f6a8a8a5d99ec696cfdf4'
ENV=os.environ|{'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0'}
def git(root,*args,data=None):
 r=subprocess.run(['git','-c','protocol.allow=never','-C',str(root),*args],input=data,env=ENV,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30);assert r.returncode==0,(args,r.stderr);return r.stdout
def batch(root,refs):
 b=git(root,'cat-file','--batch',data=('\n'.join(refs)+'\n').encode());i=0;out=[]
 for ref in refs:
  end=b.index(b'\n',i);oid,kind,size=b[i:end].split();size=int(size);i=end+1;body=b[i:i+size];i+=size;assert len(body)==size and b[i:i+1]==b'\n';i+=1
  assert hashlib.sha1(kind+b' '+str(size).encode()+b'\0'+body).hexdigest()==oid.decode();out.append((oid.decode(),kind.decode(),body))
 assert i==len(b);return out
assert git(S,'rev-parse','HEAD').decode().strip()==HEAD
assert not (S/'.git/objects/info/alternates').exists()
pack=(R/doc['pack']['path']).read_bytes();assert len(pack)==92437 and sha(pack)==doc['pack']['sha256']
bare=H/'independent-selected75.git';assert not bare.exists()
git(H,'init','--bare',str(bare));index=git(bare,'index-pack','--stdin',data=pack).decode().strip();assert index==doc['pack']['actual_index_pack_stdout']
oids=set(git(bare,'cat-file','--batch-all-objects','--batch-check=%(objectname)').decode().splitlines());assert oids==set(plan['missing_objects']) and len(oids)==75
allrows=plan['objects'];assert len(allrows)==222 and sum(r['bytes'] for r in allrows)==3696234
assert set(plan['already_present_objects']).isdisjoint(oids) and len(plan['already_present_objects'])==147
assert {r['object'] for r in allrows}==oids|set(plan['already_present_objects'])
roots=[S,Path(plan['source_donor_git']).parent,Path(plan['recovered_donor_git']).parent]
for root in roots:
 for row,(oid,kind,b) in zip(allrows,batch(root,[r['object'] for r in allrows])):
  assert oid==row['object'] and kind==row['type'] and len(b)==row['bytes'] and sha(b)==row['sha256']
lookups=plan['logical_committed_lookups'];assert len(lookups)==638
lookup_map={(r['commit'],r['path']):r for r in lookups};assert len(lookup_map)==638
for root in roots:
 for row,(oid,kind,b) in zip(lookups,batch(root,[r['commit']+':'+r['path'] for r in lookups])):
  assert oid==row['object'] and kind=='blob' and len(b)==row['bytes'] and sha(b)==row['sha256']
def checked(path,row):
 s=path.lstat();assert path.resolve()==path and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==row['mode']
 b=path.read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256'];return b
rows=doc['retained_namespace_files'];assert len(rows)==19 and sum(r['bytes'] for r in rows)==176184
for row in rows:
 assert checked(S/row['path'],row)==checked(Path(row['original_source']),row)==checked(Path(row['actual_recovered_source']),row)
counts=[];required=set();closures=[]
assert doc['actual_old_claims']==plan['claims']
for row in doc['actual_old_claims']:
 d=S/'research_runs'/row['identity'];claimraw=(d/'claim.json').read_bytes();claim=json.loads(claimraw);terminalraw=(d/'failed.json').read_bytes();terminal=json.loads(terminalraw)
 assert sha(claimraw)==row['claim_sha256'] and sha(terminalraw)==row['terminal_sha256']
 assert claim['experiment_id']==terminal['experiment_id']==row['identity'] and terminal['claim_sha256']==sha(claimraw) and terminal['status']=='failed'
 assert claim['source']==row['source'] and claim['design_source']==row['design_source'] and claim['effective_attempt_budget']==row['effective_budget']
 assert claim['family']['attempt_budget']==2 and claim['family']['prior_attempts']==0
 assert not (d/'complete.json').exists()
 files=claim['experiment']['source_files'];assert len(files)==row['registered_source_count']
 selection=dict(files);selection[claim['experiment']['charter']['path']]=claim['experiment']['charter']['sha256']
 assert len(selection)==row['source_plus_charter_selection_count']
 for name,pin in selection.items():assert lookup_map[(claim['source'],name)]['sha256']==pin;required.add((claim['source'],name))
 for commit in [claim['source'],claim['design_source']]:
  regrow=lookup_map[(commit,claim['registration'])];assert regrow['sha256']==claim['registration_sha256'];required.add((commit,claim['registration']))
  reg=json.loads(batch(S,[commit+':'+claim['registration']])[0][2]);assert reg['program_id']==claim['program_id'] and reg['experiments'][row['identity']]==claim['experiment']
 outputs={p.name for p in (d/'outputs').iterdir()};assert outputs==set(terminal['output_sha256'])
 for name,pin in terminal['output_sha256'].items():assert sha((d/'outputs'/name).read_bytes())==pin
 counts.append(len(outputs));closures.append({'identity':row['identity'],'status':'failed','effective_budget':row['effective_budget'],'actual_outputs':sorted(outputs),'missing_registered_outputs':sorted(set(claim['experiment']['outputs'])-outputs),'claim_sha256':sha(claimraw),'terminal_sha256':sha(terminalraw)})
assert counts==[4,4,2,1] and required==set(lookup_map)
assert {p.name for p in (S/'research_runs').iterdir()}=={r['identity'] for r in doc['actual_old_claims']}
# Rejoin every previous227 body from composition rather than trusting current count.
composition=json.loads((F/'held-consumer-root-source-composition04-2026-10-03/SOURCE_COMPOSITION04.json').read_bytes())
old=S.parent.parent/'held-score-consumer-native-20261003-03/source'
expected={r['path'] for r in rows}
for row in composition['source_entries']:
 path=row['target'];b=(S/path).read_bytes();assert sha(b)==row['sha256'] and len(b)==row['bytes'];assert b==batch(S,[HEAD+':'+path])[0][2];expected.add(path)
 if path!='tradingagents/research/onchain_replication/resource_fixture.py':assert b==(old/path).read_bytes()
for row in composition['retained_auxiliary_tracked_bodies']:
 b=(S/row['path']).read_bytes();assert sha(b)==row['sha256'] and len(b)==row['bytes'] and b==(old/row['path']).read_bytes();expected.add(row['path'])
for row in composition['opaque_prior_inputs']+[composition['runtime_role']]:checked(S/row['path'],row);expected.add(row['path'])
assert (old/'tradingagents/research/onchain_replication/resource_fixture.py').read_bytes()==batch(old,['903488c49ad25e8026ec849a1c8b30ca5f90bcff:tradingagents/research/onchain_replication/resource_fixture.py'])[0][2]
actual=set()
def scan(root):
 for e in os.scandir(root):
  p=Path(e.path);rel=p.relative_to(S).as_posix()
  if rel=='.git':continue
  info=e.stat(follow_symlinks=False)
  if stat.S_ISDIR(info.st_mode):assert any(n.startswith(rel+'/') for n in expected);scan(p)
  else:assert stat.S_ISREG(info.st_mode) and info.st_nlink==1;actual.add(rel)
scan(S);assert len(actual)==246 and actual==expected
assert git(S,'rev-parse','HEAD').decode().strip()==HEAD and not git(S,'diff','--name-only') and not git(S,'diff','--cached','--name-only')
assert git(old,'rev-parse','HEAD').decode().strip()=='903488c49ad25e8026ec849a1c8b30ca5f90bcff'
result={'scope':'read-only actual historical object/byte binding; no verify_claim/admission/start','head':HEAD,'pack_objects':75,'working_and_two_donor_objects':222,'object_payload_bytes':3696234,'exact_commit_path_lookups_per_store':638,'copied_run_files':19,'copied_run_bytes':176184,'actual_output_counts':counts,'closures':closures,'non_git_files':246,'new_claims':0,'network':False,'numeric_imports':False,'full_history_or_external_recovery_claim':False}
(H/'READBACK01.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS exact75-object independent bare pack,222 objects and638 named paths in Source04 and BOTH donor stores;19 files176184B/modes identical;four FAILED output counts4/4/2/1;246 exactfiles/unchangedHEAD')
# Preserve the entire reviewer-created bare evidence without modifying it.
inventory=[]
for p in sorted(bare.rglob('*')):
 s=p.lstat();row={'path':p.relative_to(H).as_posix(),'mode':stat.S_IMODE(s.st_mode),'type':'directory' if p.is_dir() else 'file'}
 if p.is_file():b=p.read_bytes();row.update(bytes=len(b),sha256=sha(b))
 inventory.append(row)
(H/'BARE_INVENTORY01.json').write_text(json.dumps(inventory,indent=2)+'\n')
with tarfile.open(H/'independent-selected75.tar.gz','w:gz',dereference=False) as archive:archive.add(bare,arcname=bare.name)
