"""Changed actual E35 metadata joins only; never executes builders or runtime."""
import os,resource,signal,pathlib,json,hashlib,copy,ast,collections
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(30)
F=pathlib.Path('research/onchain-paper-replication-2026-09-24/full_sources');D=F/'pilot35-actual-binding-review01-2026-10-11';E=F/'real-data-pilot-full35-entry-preparation01-2026-10-11';O=F/'real-data-pilot-full34-entry-preparation01-2026-10-11';T=F/'real-data-pilot-full35-binding-preparation01-2026-10-11';NAME='eth-paper-real-data-end-to-end-resource-20261011-35';OLD=NAME[:-2]+'34'
refs={};checks=collections.Counter()
def need(x,category):
 assert x,category
 checks[category]+=1
def raw(p):
 p=pathlib.Path(p);s=str(p)
 assert not p.is_absolute() and '..' not in p.parts and not s.startswith(('research_artifacts/','research_runs/'))
 assert not set(p.parts)&{'.git','.venv','keys','apis','node_modules','.env','connection.json','hf_token.txt'}
 b=p.read_bytes();refs[s]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
def load(p):return json.loads(raw(p))
def pin(p,h):
 b=raw(p);need(hashlib.sha256(b).hexdigest()==h,'public body hash');return b
def refcheck(r):
 b=pin(r['path'],r['sha256'])
 if 'bytes' in r:need(len(b)==r['bytes'],'public body length')
 return b
p=load(D/'BINDING_CHECK01.json');need(refs[str(D/'BINDING_CHECK01.json')]['sha256']=='ace4427be875f8cb8da13a8584f897e6ec05fdd783137a181cd82122824dd476','frozen preliminary actual72 proof')
b=json.loads(pin(E/'BINDING_DRAFT01.json','e8ef96244e9944c5f8c6e0d1bcc6aca61cf50395681e82126a3b7cdc2dd0bdcf'))
g=json.loads(pin(E/'gate01.json','4c784743a457344bddc8cb0f4af8aaa64577835a847291f8fa8296f0e5da0799'));old=load(O/'gate01.json');n=g['experiments'][NAME];on=old['experiments'][OLD]
need({k:v for k,v in g.items()if k!='experiments'}=={k:v for k,v in old.items()if k!='experiments'},'old gate metadata preserved')
need({k:v for k,v in g['experiments'].items()if k!=NAME}==old['experiments'],'all original experiments preserved')
need(n['parent']==OLD and n['family']==on['family'],'fresh child identity')
for k in ('cells','outputs','windows','stage','selection','reuse'):need(n[k]==on[k],'original method selection')
actual={k:{x:v[x]for x in ('path','sha256')}for k,v in n['inputs'].items()}
need(len(actual)==72 and actual==b['input_refs'],'strict72 gate binding input closure')
need(all(set(v)=={'path','sha256'}for v in actual.values()),'strict ref schema')
need({k for k in actual if actual[k]!=p['input_refs'][k]}=={'matching_ordered_edge_scratch'},'sole fresh scratch delta')
scratch=json.loads(refcheck(actual['matching_ordered_edge_scratch']));base=load(O/'MATCHING_SCRATCH_RESERVATION01.json');base['experiment']=NAME;base['installed_source']['sha256']='86ccc3a471827bdce7784145914240d04416d2cc0023e8acb77fb26ae473df57';need(scratch==base,'scratch literal JSON inverse')
evidence={}
for role,r in b.items():
 if isinstance(r,dict) and {'path','sha256'}<=r.keys():
  if role=='transport':need(r==p['opaque_reference_metadata'],'opaque reference metadata only')
  else:refcheck(r)
  evidence[r['path']]=r['sha256']
need(b['identity']==NAME and b['status']=='DRAFT_NOT_RELEASED' and b['binding_review'] is None,'actual draft disposition')
reviewpath=F/'pilot35-entry-source-review01-2026-10-11/REVIEW01.json';sr=json.loads(pin(reviewpath,'9c637f38fd925c3ceeab8a8b62d8242825210cb955e7ecdd88d57a68f1857472'));need(sr['decision']=='accepted','different author builder source acceptance')
for kind,filename in [('source','prepare_source01.py'),('registration','prepare_registration01.py')]:
 need(raw(E/filename)==refcheck(sr['commands'][kind]['source']),'exact independently reviewed builder copy')
source=load(E/'SOURCE_PREPARATION01.json');need(source['source_anchor']=='53b8890630765d06f8a44e3e8fbaee1f4b00bdfb' and source['capacity_source_bodies']==423 and source['numerical_source_bodies']==200 and len(source['changed_source'])==13 and len(source['added_source_paths'])==2,'actual source counts and anchor')
for k in ('claim','launch','admission','numerical_imports'):need(source[k] is False,'source metadata only')
pins=n['source_files'];oldpins=on['source_files'];need(len(pins)==806 and oldpins.keys()<=pins.keys(),'complete prior source roster retained')
changed={k for k in oldpins if oldpins[k]!=pins[k]};need(changed=={r['path']for r in source['changed_source']},'only accepted13 old source updates')
for path in sorted((pins.keys()-oldpins.keys())|changed):pin(path,pins[path])
mapping=load(E/'CAPACITY_SOURCE_MAP01.json');mp=mapping['source_files'];need(len(mp)==423 and all(pins[k]==h for k,h in mp.items()),'423 capacity bodies joined to gate')
# Source-review current423 body proof and Root actual committed joins reused; verify each fresh actual body now without imports.
for path,h in mp.items():pin(path,h)
for name,h in n['runtime_hashes'].items():pin(pathlib.Path('tradingagents/research')/name,h)
cap=load(E/'CAPACITY_DECLARATION_ROOT01.json');oldcap=load(O/'CAPACITY_DECLARATION_ROOT01.json');need(cap['source_body_pins']==mp,'capacity source map join')
for k in ('new_logical_growth_bytes','new_allocated_growth_bytes','non_directory_new_allocated_growth_bytes','new_entries','directory_allocated_bound_bytes','other_writer_reserved_bytes','allocation_semantics','directory_and_other_writers_included','runtime_residuals_included'):need(cap[k]==oldcap[k],'unchanged conditional capacity bound')
need(cap['owned_paths']==[x.replace('20261011-34','20261011-35')for x in oldcap['owned_paths']],'fresh writable union identity')
core=load(E/'CORE_MANIFEST01.json');oldcore=load(O/'CORE_MANIFEST01.json')
for role,r in core['inputs'].items():
 curr=json.loads(refcheck(r));prior=json.loads(refcheck(oldcore['inputs'][role]))
 if role=='mcm_policy':
  ex=curr['batched']['execution'];ep=ex.pop('compiled_edge_policy');ei=ex.pop('compiled_edge_inputs')
  for kind,rol in ei.items():need(actual[rol]['sha256']==ep[kind+'_sha256'] and str(pathlib.Path.cwd()/actual[rol]['path'])==ep[kind+'_path'],'five native role policy joins')
 need(curr==prior,'four scientific core JSON inverse')
for path,h in core['source'].items():need(pins[path]==h,'core current source join')
br=json.loads(refcheck(b['budget_review']));need(set(b['budget_review'])=={'path','sha256'} and br['decision']=='accepted','strict106 accepted machine review')
need(n['cumulative_budget_extension']['review']==b['budget_review'] and n['cumulative_budget_extension']['extension']['sha256']==br['extension_sha256'],'106 extension review exact join')
refcheck(n['cumulative_budget_extension']['extension']);refcheck(n['charter'])
pub=load(E/'PUBLIC_MANIFEST01.json');need(pub['experiment']==NAME and pub['all_input_roles']==72,'public role manifest')
# Authenticate generated helper files against actual source manifest and exact diff reconstruction.
manifest=load(E/'SOURCE_MANIFEST01.json')
for name in ('preflight35_01.py','root_io35_01.py'):refcheck(manifest['files'][name]);ast.parse(raw(E/name))
need(raw(E/'root_io35_01.py')==raw(O/'root_io34_01.py').replace(b'from preflight34_01 import check',b'from preflight35_01 import check'),'Root IO exact import-only inverse')
ops=load(E/'ROOT_PREPARATION_OPERATIONS01.json');need(ops['source_anchor']==source['source_anchor'],'Root actual source anchor')
# Original actual receipts are provenance, not cryptographic execution attestation.
limits=['Actual public binding and generated metadata joins only; no private transport/connection bytes read, statted or hashed.','Builder source semantics rely on different-author review9c637f38; this reviewer authored candidate builders and does not self-review their semantics.','Unchanged historical source/evidence rows and raw scientific payloads rely on accepted predecessor reviews; no historical matrices or payload reads repeated.','Root prospective capacity declaration is not measured full workload capacity; finite native qualification does not prove genuine Owner, full caller workload equivalence or speed.','No empirical claim, Owner, native/scientific execution, Git operation, registration mutation or ledger write by this review. Financial accounting106 is proposed only; fresh no-active/single-launch/resource eligibility and current source freeze remain Root preflight obligations.','Final BINDING01, exact committed-source metadata admission, final release, current preparation external recovery and fresh whole preflight remain separate.']
result={'schema_version':1,'decision':'accepted','identity':NAME,'scope':'Actual offline bound72 plus generated E35 source/gate/core/capacity reference joins; permits Root final binding publication only.','input_refs':actual,'evidence':evidence,'checks':dict(checks),'counts':{'source_pins':len(pins),'prior_source_pins':len(oldpins),'new_source_paths':len(pins.keys()-oldpins.keys()),'changed_source_paths':len(changed),'capacity_current_bodies':423,'input_roles':72,'opaque_bodies_read':0},'references':refs,'limits':limits,'root_next_action':'Publish BINDING01 from exact BINDING_DRAFT01 changing only status to BOUND_NOT_RELEASED and binding_review to this actual review path/SHA/bytes. Final release is a separate review after authentic final binding and committed-source metadata admission; no launch authority here.'}
with (D/'BINDING_REVIEW01.json').open('x')as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'decision':result['decision'],'checks':sum(checks.values()),'counts':result['counts']}))
