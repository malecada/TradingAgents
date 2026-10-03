from pathlib import Path
import hashlib,json,os,stat,subprocess
H=Path(__file__).resolve().parent;F=H.parent;R=H.parents[3];C=F/'original-import-native-successor-preparation06-2026-10-03/capsule04';X=F/'original-import-native-successor-preparation06-2026-10-03/outcome-recovery01/recovered-terminal-capsule04';S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-04/source')
def read(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2;b=p.read_bytes();assert len(b)==s.st_size;return b
def sha(b):return hashlib.sha256(b).hexdigest()
def git(root,*a):return subprocess.check_output(['git','-C',str(root),*a],env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_OPTIONAL_LOCKS':'0'},timeout=15,stderr=subprocess.PIPE)
assert git(S,'rev-parse','HEAD').strip().decode()=='fa9712c36daf2896ef3f6a8a8a5d99ec696cfdf4'
objects={};trees={};requests=[];files=[];claims=[]
def obj(oid,kind):
 if oid not in objects:
  assert git(C,'cat-file','-t',oid).strip().decode()==kind
  n=int(git(C,'cat-file','-s',oid));assert 0<n<=4*1024**2
  b=git(C,'cat-file',kind,oid);assert len(b)==n and b==git(X,'cat-file',kind,oid);assert hashlib.sha1((kind+' '+str(n)+'\0').encode()+b).hexdigest()==oid
  objects[oid]={'object':oid,'type':kind,'bytes':len(b),'sha256':sha(b)};assert sum(x['bytes'] for x in objects.values())<=32*1024**2
  if kind in ('tree','commit'):trees[oid]=b
 return trees.get(oid)
def lookup(commit,path,pin):
 raw=obj(commit,'commit');oid=raw.splitlines()[0].split()[1].decode();parts=path.split('/')
 for i,name in enumerate(parts):
  raw=obj(oid,'tree');entries={};j=0
  while j<len(raw):
   end=raw.index(b'\0',j);mode,n=raw[j:end].split(b' ',1);value=raw[end+1:end+21].hex();entries[n.decode()]=(mode.decode(),value);j=end+21
  mode,oid=entries[name]
  if i<len(parts)-1:assert mode=='40000'
  else:assert mode in ('100644','100755');obj(oid,'blob');assert objects[oid]['sha256']==pin;requests.append({'commit':commit,'path':path,'git_mode':mode,'object':oid,'sha256':pin,'bytes':objects[oid]['bytes']})
 return git(C,'cat-file','blob',oid)
for i in range(1,5):
 name='original-import-native-success-20261003-%02d'%i;rel=Path('research_runs')/name;raw=read(C/rel/'claim.json');c=json.loads(raw);failed=read(C/rel/'failed.json');term=json.loads(failed)
 assert c['experiment_id']==name and c['source']==c['design_source'] and c['bindings'] is None and c['bindings_sha256'] is None and not any(v['sha256'] is None for v in c['inputs'].values());assert term['status']=='failed' and term['claim_sha256']==sha(raw)
 reg=json.loads(lookup(c['source'],c['registration'],c['registration_sha256']));assert reg['experiments'][name]==c['experiment'] and reg['families'][c['experiment']['family']]==c['family']
 exp=c['experiment'];pinned=dict(exp['source_files'])
 for key in ('charter','selection'):
  if exp.get(key):pinned[exp[key]['path']]=exp[key]['sha256']
 for commit in sorted({c['source'],c['design_source']}):
  for path,pin in pinned.items():lookup(commit,path,pin)
 ref=exp.get('cumulative_budget_extension')
 if ref:
  for k in ('extension','review'):lookup(c['source'],ref[k]['path'],ref[k]['sha256'])
 windows=[{**w,'identity':reg['datasets'][w['dataset']]['identity'],'state':'spent' if exp['stage']=='confirmation' else 'exposed'} for w in exp['windows']];exposures=[{**v,'identity':d['identity']} for d in reg['datasets'].values() for v in d['exposures']];assert c['windows']==windows and c['prior_exposures']==exposures and c['inputs']==exp['inputs']
 local=[]
 for p in sorted((C/rel).rglob('*')):
  assert not p.is_symlink()
  if p.is_file():
   b=read(p);relative=p.relative_to(C);assert b==read(X/relative);r={'path':relative.as_posix(),'bytes':len(b),'sha256':sha(b),'mode':stat.S_IMODE(p.lstat().st_mode),'source':str(p),'recovered_source':str(X/relative)};files.append(r);local.append(r['path']);assert len(files)<=128
 assert set(term['output_sha256'])=={p.name for p in (C/rel/'outputs').iterdir()}
 for out,pin in term['output_sha256'].items():assert sha(read(C/rel/'outputs'/out))==pin
 assert not os.path.lexists(C/rel/'complete.json') and not os.path.lexists(S/rel)
 claims.append({'identity':name,'source':c['source'],'design_source':c['design_source'],'registration':c['registration'],'registration_sha256':c['registration_sha256'],'claim_sha256':sha(raw),'terminal_sha256':sha(failed),'effective_budget':c['effective_attempt_budget'],'registered_source_count':len(exp['source_files']),'source_plus_charter_selection_count':len(pinned),'namespace_files':local})
# Query every precise expected object against fresh source without lazy fetching; no traversal.
missing=[];present=[]
for oid,row in sorted(objects.items()):
 try:
  kind=git(S,'cat-file','-t',oid).strip().decode();assert kind==row['type'];raw=git(S,'cat-file',kind,oid);assert len(raw)==row['bytes'] and sha(raw)==row['sha256'];present.append(oid)
 except subprocess.CalledProcessError:missing.append(oid)
unique={(r['commit'],r['path']):r for r in requests};plan={'status':'verified-history-copy-dependencies-not-installed','source_donor_git':str(C/'.git'),'recovered_donor_git':str(X/'.git'),'destination':str(S),'destination_head':git(S,'rev-parse','HEAD').decode().strip(),'claims':claims,'logical_committed_lookups':list(unique.values()),'objects':list(sorted(objects.values(),key=lambda x:x['object'])),'object_bytes':sum(x['bytes'] for x in objects.values()),'already_present_objects':present,'missing_objects':missing,'namespace_files':files,'namespace_bytes':sum(x['bytes'] for x in files),'limitations':'Only exact verify_claim commit:path object closure, not full original commit ancestry/tree or current admission release. No fetch or revision traversal.'}
(H/'COPY_PLAN01.json').write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n')
refs=[]
for p in [R/'tradingagents/research/admission.py',R/'tradingagents/research/verify.py',R/'tradingagents/research/budget_extensions.py']:
 b=read(p);refs.append({'path':str(p),'bytes':len(b),'sha256':sha(b)})
(H/'SOURCE_REFS01.json').write_text(json.dumps(refs,indent=2)+'\n')
print('PASS4claims exactoriginal/recovered/Git source joins;',len(unique),'uniquecommit:path lookups;',len(objects),'objects',plan['object_bytes'],'B;',len(missing),'missing;',len(files),'namespacefiles',plan['namespace_bytes'],'B;no admission/claims invoked')
