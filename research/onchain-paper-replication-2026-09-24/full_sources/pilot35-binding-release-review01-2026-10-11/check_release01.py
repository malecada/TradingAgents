"""Final binding/admission changed joins only; no entry or scientific execution."""
import pathlib,json,hashlib,os,resource,signal,ast,copy
os.sched_setaffinity(0,{3});os.nice(10);resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(20)
F=pathlib.Path('research/onchain-paper-replication-2026-09-24/full_sources');E=F/'real-data-pilot-full35-entry-preparation01-2026-10-11';B=F/'pilot35-actual-binding-review01-2026-10-11';D=F/'pilot35-binding-release-review01-2026-10-11';NAME='eth-paper-real-data-end-to-end-resource-20261011-35';SOURCE='5fb09399632508b04bc44253ffaf6d08bddd7d54';checked={};checks=[];evidence={}
def need(v,label):
 assert v,label
 checks.append(label)
def read(p,h=None):
 p=pathlib.Path(p);assert not p.is_absolute() and '..'not in p.parts and not str(p).startswith(('research_artifacts/','research_runs/'))
 assert not set(p.parts)&{'.git','.venv','keys','apis','node_modules','.env','connection.json','hf_token.txt'}
 b=p.read_bytes();r={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};checked[str(p)]=r
 if h is not None:need(r['sha256']==h,'actual body '+str(p))
 return b
def load(p,h=None):return json.loads(read(p,h))
def add(p,h):
 need(p not in evidence or evidence[p]==h,'consistent evidence ref '+p);evidence[p]=h
review=load(B/'BINDING_REVIEW01.json','838cba49a58c31005f1a749da08fb9097ef3d7f4c15729910d527f0973cca45c');manifest=load(B/'MANIFEST01.json','77cdfdc69ad9f6b5b9ccf9bee3436ae3c667d3b700df3ad4d724fbc60898a9ba')
need(review['decision']=='accepted' and review['identity']==NAME,'accepted actual binding review')
final=load(E/'BINDING01.json','ed639540d5486a658f7376d9699a91d4db9b4d6cc00aaf5ea37ebeb85395fe70');draft=load(E/'BINDING_DRAFT01.json','e8ef96244e9944c5f8c6e0d1bcc6aca61cf50395681e82126a3b7cdc2dd0bdcf');expected=copy.deepcopy(draft);expected['status']='BOUND_NOT_RELEASED';expected['binding_review']=checked[str(B/'BINDING_REVIEW01.json')];need(final==expected,'only final status and genuine review ref changed')
gate=load(E/'gate01.json','4c784743a457344bddc8cb0f4af8aaa64577835a847291f8fa8296f0e5da0799');n=gate['experiments'][NAME];actual={k:{x:v[x]for x in ('path','sha256')}for k,v in n['inputs'].items()};need(actual==final['input_refs']==review['input_refs'] and len(actual)==72 and len(n['source_files'])==806,'exact reviewed806 source and72 input closure')
# Reuse immutable source/binding proof; no old payload/body replay.
for p,h in n['source_files'].items():add(p,h)
for r in actual.values():add(r['path'],r['sha256'])
for p,h in review['evidence'].items():add(p,h)
for role,r in final.items():
 if isinstance(r,dict)and {'path','sha256'}<=r.keys():
  add(r['path'],r['sha256'])
  if role!='binding_review':need(review['evidence'][r['path']]==r['sha256'],'binding ref previously authenticated '+role)
  if role=='transport':need(r==draft['transport'],'sole opaque ref metadata unchanged')
need([k for k,r in actual.items()if r['path']==final['transport']['path']]==['archive_transport'],'sole opaque input exception')
need(final['transport']['path']not in n['source_files'],'no opaque source exception')
for name in ('preflight35_01.py','root_io35_01.py'):
 p=str(E/name);read(p,review['references'][p]['sha256']);ast.parse(read(p));add(p,checked[p]['sha256'])
# Literal public helper references required by existing preflight; never execute it.
for node in ast.parse(read(E/'preflight35_01.py')).body:
 if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('BINDER','INDEX_CAPACITY'):
  r=ast.literal_eval(node.value);read(r['path'],r['sha256']);add(r['path'],r['sha256'])
adm=load(E/'ADMISSION01.json','f0f2e1c74edbe8fc54e9363fc703146b1818490d2f8482971dcb2d7c5d8373c9');need(adm['actual_returncode']==0 and adm['source']==SOURCE and adm['claim']is False and adm['metadata_only']is True,'actual metadata admission disposition')
need(adm['argv']==['.venv/bin/python','-B','-m','tradingagents.research','check','--root','.','--registration',str(E/'gate01.json'),'--experiment',NAME,'--source',SOURCE],'actual genuine CLI argv')
for name,r in adm['outputs'].items():
 b=read(r['path'],r['sha256']);need(len(b)==r['bytes'],'raw admission output length')
 if name=='admission-stderr01.txt':need(b==b'','actual empty stderr')
 else:
  out=json.loads(b);need(out['experiment']==NAME and out['ready']is True and out['status']=='metadata_admitted'and out['empirical_inputs_opened']is False and out['run_started']is False,'actual ready metadata stdout only')
ops=load(E/'ROOT_ADMISSION_OPERATIONS01.json');need(ops['metadata_admission']['receipt']==checked[str(E/'ADMISSION01.json')],'Root receipt join');need(ops['metadata_admission']['exit_code']==0 and ops['metadata_admission']['session_id']==9556 and ops['metadata_admission']['terminal_tool']=='648196','actual Root terminal provenance');need(ops['source_commit']['source']==SOURCE and ops['source_commit']['exit_code']==0 and ops['run_started']is False and ops['empirical_inputs_opened']is False,'Root source commit and no run provenance')
# Different-author builder source acceptance and actual public preparation acceptance retained.
for folder,h in [('pilot35-entry-source-review01-2026-10-11','9c637f38fd925c3ceeab8a8b62d8242825210cb955e7ecdd88d57a68f1857472'),('pilot35-generated-public-review01-2026-10-11','5d6a18d3cb1b1fc28d7875a596bf08d062314dd1092cd41f1952ff8466977cd6')]:
 r=load(F/folder/'REVIEW01.json',h);need(r['decision']=='accepted','reused independent acceptance '+folder)
for p,r in checked.items():add(p,r['sha256'])
need(all(evidence[p]==h for p,h in n['source_files'].items()),'complete806 release source denominator');need(all(evidence[r['path']]==r['sha256']for r in actual.values()),'complete72 release input denominator')
limits=['Opaque archive_transport is the sole uncommitted reference exception and is authenticated here only through unchanged public metadata; no private body/connection/key read, stat or hash.','Unchanged historical source/input bodies are covered by accepted prior evidence and current metadata admission; no old scientific payload or historical review matrix was replayed.','Builder semantics rely on different-author review9c637f38; this reviewer authored builders and reviews actual output/admission joins rather than claiming independent source self-review.','Metadata admission ready=true does not start a run, adopt proposed106 or establish genuine Owner/caller execution, numerical equivalence, throughput, PnL or model validity.','Capacity is a prospective conditional Root declaration with sampled aggregate storage/floor checks, not a hard quota or measured full-population capacity.','No native/scientific import, preflight, runtime inventory, launch, claim, Git/network/recovery action or ledger mutation by this review; Root operation provenance is trusted recorded observation, not cryptographic execution attestation.']
conditions=['Root copies these exact RELEASE_REVIEW01 bytes to E35/RELEASE_REVIEW01.json and commits the complete final public source, binding, release and evidence. Fresh genuine preflight must authenticate all evidence against the actual new HEAD; earlier source5fb093 admission is not a substitute for final commit authentication.','After final freeze, Root preserves the complete declared current preparation increment30 externally, obtains a fresh actual recovery receipt and independent complete returned-scope acceptance. Accepted failed34/native03 recoveries are dependencies, not substitutes for this current preparation recovery.','Exactly one opaque archive_transport exception may remain outside committed public evidence; Root genuine whole preflight must validate its fixed reference/permissions and exact selected route without printing credentials. Every other source/input/evidence body must match the released digest.','Fresh genuine whole preflight must require proposed106 exact review/extension, unused fixed35 namespace, no active program claim/native unit, current committed source/input/runtime inventory, unchanged kernel/resource controls and actual RAM/disk/writable-union headroom. Frozen scientific cells, models/training and60-second scheduler lease remain unchanged.','Root alone may run the exact Root I/O command for one unused fixed35 attempt only after all prior conditions pass. Keep original exclusive attempt outputs, failure dispositions and raw operation logs. Freeze source until actual terminal closure; no retry or spent identity reuse.']
r={'schema_version':1,'decision':'accepted','reviewer':'independent outcome16_release_review; actual output/caller joins with different-author builder semantics reused','identity':NAME,'scope':'Conditional exact pilot35 binding, gate806/source/72input and Root caller release after actual metadata admission; fresh current preparation recovery and whole preflight required.','binding':checked[str(E/'BINDING01.json')],'binding_review':checked[str(B/'BINDING_REVIEW01.json')],'gate':checked[str(E/'gate01.json')],'admission':checked[str(E/'ADMISSION01.json')],'source_count':806,'input_count':72,'evidence':evidence,'exact_read_only_preflight_command':['.venv/bin/python','-B',str(E/'preflight35_01.py')],'exact_root_command':['.venv/bin/python','-B',str(E/'root_io35_01.py')],'command_cwd':str(pathlib.Path.cwd()),'limits':limits,'required_root_before_launch_conditions':conditions,'checks':{'total':len(checks),'final_binding_inverse':True,'source_denominator':806,'input_denominator':72,'evidence_paths':len(evidence),'raw_admission_exit':0,'empirical_inputs_opened':False,'run_started':False,'unchanged_binding_checks_replayed':False},'checked_actual_references':checked}
with(D/'RELEASE_REVIEW01.json').open('x')as f:json.dump(r,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'decision':r['decision'],'checks':r['checks']}))
