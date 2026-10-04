from pathlib import Path
import ast,atexit,copy,hashlib,importlib.util,json,os,stat,subprocess,sys
H=Path(__file__).resolve().parent;B=H.parent;P=B/'financial-wrapper-compatibility-root-policy01-2026-10-04';S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');A=B/'financial-wrapper-compatibility-actual-source-adoption-review01-2026-10-04';V=B/'financial-wrapper-operational-provenance-compatibility-review02-2026-10-04'
sha=lambda b:hashlib.sha256(b).hexdigest();canon=lambda o:json.dumps(o,sort_keys=True,separators=(',',':'),allow_nan=False).encode();rows=[]
def save(n,v):(H/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def ck(n,v):rows.append({'case':n,'passed':bool(v)});assert v,n
atexit.register(lambda:save('CHECK_PROGRESS02.json',rows))
def refusal(n,fn):
 try:fn()
 except (ValueError,TypeError,KeyError):ck(n,True)
 else:ck(n,False)
def git(*args):return subprocess.run(['git','--no-replace-objects',*args],cwd=S,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0'}).stdout
# Authenticate independently authored source-adoption and source-candidate reviews.
for directory,pin in ((A,'e0a39ef23d7b3624249e769b7f0bc2bec6a6c20028a48a393780e5f6ca19a915'),(V,'6d61d65f528a1db42fead75f70062acff1599aa571af1d1f09746302c3538e5e')):
 ck('review manifest '+directory.name,sha((directory/'MANIFEST01.json').read_bytes())==pin)
 for row in json.loads((directory/'MANIFEST01.json').read_bytes())['members']:
  q=directory/row['path'];st=q.lstat();good=stat.S_IMODE(st.st_mode)==row['mode']
  if row['kind']=='file':good=good and stat.S_ISREG(st.st_mode) and st.st_size==row['bytes'] and sha(q.read_bytes())==row['sha256']
  elif row['kind']=='directory':good=good and stat.S_ISDIR(st.st_mode)
  else:good=good and stat.S_ISLNK(st.st_mode) and os.readlink(q)==row['target']
  ck('review member '+directory.name+'/'+row['path'],good)
 snap=H/('source-adoption-review' if directory==A else 'source-candidate-review');snap.mkdir()
 for f in ('MACHINE01.json','REPORT01.md','MANIFEST01.json'):(snap/f).write_bytes((directory/f).read_bytes())
rootpins={}
for name in ('POLICY01.json','SOURCE_CLOSURE01.json','HISTORICAL_ROLE_MAP01.json','SOURCE_POLICY_BINDING01.json','root_policy04.py'):
 raw=(P/name).read_bytes();rootpins[name]=sha(raw);(H/name).write_bytes(raw)
ck('exact concrete policy requested',rootpins['POLICY01.json']=='ae8fbdc9d13e75fc453b70b5ee633c89fb4577e9b68a35b4147cf1bbd58c6887')
policy=json.loads((H/'POLICY01.json').read_bytes());closure=json.loads((H/'SOURCE_CLOSURE01.json').read_bytes());roles=json.loads((H/'HISTORICAL_ROLE_MAP01.json').read_bytes());binding=json.loads((H/'SOURCE_POLICY_BINDING01.json').read_bytes());hist=policy['historical'];target=policy['target']['installed'];old=hist['installed']
helperrel='tradingagents/research/onchain_replication/operational_source_compatibility.py';helperraw=(S/helperrel).read_bytes();helperpin=sha(helperraw);ck('actual installed helper exact accepted source',helperpin=='d0d770b45def89e8e00e81fa1bbb35416034eaace5ecab0f15193fd43b7a32d8');(H/'operational_source_compatibility.py').write_bytes(helperraw)
spec=importlib.util.spec_from_file_location('independent_concrete_policy',H/'operational_source_compatibility.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.validate_contract(policy,helperpin);ck('authentic full concrete contract predicate',True)
ck('source current adopted commit',git('rev-parse','HEAD').decode().strip()==binding['actual_source_design']=='7b056a574e3e7b3c7ba209a39ee6a615e649d60c')
ck('source adoption direct parent',git('rev-parse',binding['actual_source_design']+'^').decode().strip()=='9dc5c79f738920b52947b4e63fed0397f1b5b207')
oldsource='0a2e7639b42b9423b90743feadcda4078aa21816';ck('exact original historical source',hist['source']==m.HISTORICAL_SOURCE==oldsource)
# Every historical body from its historical Git commit; current bodies also
# match the independently accepted installed target and actual adopted commit.
source_rows=[]
for label,mapping,commit in (('old',old,oldsource),('target',target,binding['actual_source_design'])):
 for rel,pin in mapping.items():
  ck('canonical nonsecret source path '+label+rel,not Path(rel).is_absolute() and '..' not in Path(rel).parts and not any(x in {'keys','apis','.env','hf_token.txt'} for x in Path(rel).parts))
  raw=git('show',commit+':'+rel);ck('committed body '+label+rel,len(raw)<=4*1024**2 and sha(raw)==pin)
  if label=='target':
   q=S/rel;st=q.lstat();ck('installed target '+rel,stat.S_ISREG(st.st_mode) and not q.is_symlink() and sha(q.read_bytes())==pin)
  dest=H/('source-'+label)/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);source_rows.append({'scope':label,'path':rel,'sha256':pin,'bytes':len(raw)})
ck('full194→195 and191 preserved',len(old)==194 and len(set(old.values()))==193 and len(target)==195 and len(set(target.values()))==194 and sum(target.get(k)==v for k,v in old.items())==191)
ck('canonical map binding hashes',sha(canon(old))==binding['old_map_sha256'] and sha(canon(target))==binding['target_map_sha256'])
ck('closure complete and unchanged science',closure['installed']==target and closure['scientific_model']==m.MODEL and closure['scientific_training']==m.TRAINING and rootpins['SOURCE_CLOSURE01.json']==binding['closure_sha256'])
ck('binding exact policy/helper',binding['policy_sha256']==rootpins['POLICY01.json'] and binding['helper_sha256']==helperpin)
# Root aliases must all describe actual original bytes under the same root.
expected_aliases={'closure_input':'historical_source_closure','claim_input':'historical_claim','failed_input':'historical_failed','checkpoint_input':'historical_checkpoint','plan_input':'historical_plan','job_input':'historical_execution_job'}
ck('exact historical alias domain',set(roles)==set(expected_aliases.values()) and all(hist[k]==v for k,v in expected_aliases.items()) and policy['target']['closure_input']=='source_closure')
data={};paths={}
for role,info in roles.items():
 p=S/info['path'];ck('canonical actual role '+role,p.resolve(strict=True)==p and p.is_relative_to(S) and not p.is_symlink());raw=p.read_bytes();ck('exact actual role bytes '+role,len(raw)==info['bytes'] and sha(raw)==info['sha256'] and info['dataset']=='synthetic');data[role]=json.loads(raw);paths[role]=p
 dest=H/'historical-metadata'/(role+'.json');dest.parent.mkdir(exist_ok=True);dest.write_bytes(raw)
claim=data['historical_claim'];failed=data['historical_failed'];cp=data['historical_checkpoint'];plan=data['historical_plan'];job=data['historical_execution_job'];histclosure=data['historical_source_closure'];identity=hist['identity']
ck('exact actual immutable identity hashes',roles['historical_claim']['sha256']==hist['claim_sha256']==m.HISTORICAL_CLAIM_SHA256 and roles['historical_failed']['sha256']==hist['failed_sha256']==m.HISTORICAL_FAILED_SHA256 and roles['historical_checkpoint']['sha256']==hist['checkpoint_sha256']==m.HISTORICAL_CHECKPOINT_SHA256)
ck('old claim identity/protocol',claim['experiment_id']==identity==m.HISTORICAL_ID and claim['source']==claim['design_source']==oldsource and claim['experiment']['charter']['sha256']==hist['protocol_sha256']==m.HISTORICAL_PROTOCOL_SHA256)
ck('permanent original FAILED',failed['status']=='failed' and failed['experiment_id']==identity and failed['claim_sha256']==hist['claim_sha256'] and not (paths['historical_claim'].parent/'complete.json').exists())
ck('exact original provenance and pathmap retained',cp['provenance']==hist['provenance'] and hist['provenance']['source_commit']==oldsource and hist['provenance']['source_hashes']==sorted(set(old.values())) and histclosure['installed']==old and all(claim['experiment']['source_files'].get(k)==v for k,v in old.items()))
ck('old job/plan/closure original input identities',claim['inputs']['execution_job']['path']==roles['historical_execution_job']['path'] and claim['inputs']['execution_job']['sha256']==roles['historical_execution_job']['sha256'] and claim['inputs'][job['payload']['plan_input']]['path']==roles['historical_plan']['path'] and claim['inputs'][job['payload']['plan_input']]['sha256']==roles['historical_plan']['sha256'] and claim['inputs'][plan['closure_input']]['sha256']==roles['historical_source_closure']['sha256'])
ck('opaque state declaration unchanged',cp['members']=={'state.pt':{'size':493424,'sha256':m.HISTORICAL_STATE_SHA256}})
member=paths['historical_checkpoint'].parent/'state.pt';ck('actual opaque state hash only',member.stat().st_size==493424 and sha(member.read_bytes())==m.HISTORICAL_STATE_SHA256)
# Original scientific configuration and stable numerical/tolerance AST.
science={}
for key,pin in (('model_input',m.MODEL),('training_input',m.TRAINING),('recipe_input',hist['provenance']['input_hash'])):
 role=plan[key];info=claim['inputs'][role];raw=(S/info['path']).read_bytes();ck('science raw '+key,sha(raw)==info['sha256']==pin);science[key]=json.loads(raw);(H/'historical-metadata'/(key+'.json')).write_bytes(raw)
ck('original schedule100/16',science['training_input']['epochs']==100 and science['training_input']['batch_size']==16)
prefix=m.PREFIX
for filename,allowed in (('financial_wrapper_fixture.py',{'authorize','_parent','_reference_state'}),('training.py',{'_reserve'})):
 a=ast.parse((H/'source-old'/prefix/filename).read_bytes());b=ast.parse((H/'source-target'/prefix/filename).read_bytes());a.body=[n for n in a.body if getattr(n,'name',None) not in allowed];b.body=[n for n in b.body if getattr(n,'name',None) not in allowed];ck('all scientific/tolerance AST unchanged '+filename,ast.dump(a)==ast.dump(b))
for filename in ('checkpoints.py','cache.py','financial_execution.py','evaluation.py'):ck('generic scientific body unchanged '+filename,old[prefix+filename]==target[prefix+filename])
# Concrete fixed identities; shared continuation cell is intentionally historical,
# not falsely presented as unused. Each new identity namespace must be absent.
cell=hist['provenance']['cell_id'];expected={'complete100':{'experiment':'financial-wrapper-classification-eager-complete100-compatibility-20261004-01','cell_id':'financial-wrapper-classification-eager-reference-compatibility-20261004-01'},'continue100':{'experiment':'financial-wrapper-classification-eager-continue100-compatibility-20261004-01','cell_id':cell},'predict':{'experiment':'financial-wrapper-classification-eager-predict-compatibility-20261004-01','cell_id':cell}}
ck('all three exact fixed consumers',policy['consumers']==binding['consumers']==expected and len(set(v['experiment'] for v in expected.values()))==3)
namespace_rows=[]
jobtree=ast.parse((S/prefix/'job.py').read_bytes());jobprefix=next(ast.literal_eval(n.value) for n in jobtree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PREFIX' for t in n.targets))
for phase,c in expected.items():
 for root in (S,M):
  pathscheck=[root/'research_runs'/c['experiment'],root/jobprefix/'runs'/c['experiment'],root/'research_artifacts/financial_wrapper_engineering'/c['experiment'],root/'research_artifacts/onchain_fit_cells'/sha(c['cell_id'].encode())/c['experiment']]
  for p in pathscheck:ck('unused consumer namespace '+str(p),not p.exists() and not p.is_symlink());namespace_rows.append({'path':str(p),'absent':True})
refdir=S/'research_artifacts/onchain_fit_cells'/sha(expected['complete100']['cell_id'].encode());ck('new reference cell absent',not refdir.exists())
shared=S/'research_artifacts/onchain_fit_cells'/sha(cell.encode());ck('shared continued cell contains only original failed parent',sorted(p.name for p in shared.iterdir())==[identity] and (shared/identity/'failed.json').exists() and not (shared/identity/'complete.json').exists())
# Exact helper source guards remain strict and policy roles remain pending.
ht=ast.parse(helperraw);functions={n.name:n for n in ht.body if isinstance(n,ast.FunctionDef)};context=ast.unparse(functions['_context']);prediction=ast.unparse(functions['validate_prediction_parent']);relation=ast.unparse(functions['validate_relation'])
for frag in ("ad.design_source == ad.source", "ad.experiment['source_files'].get(ad.inputs[ROLE]['path']) == sha(raw)", "closure['installed'] == target['installed']", "ad.experiment['source_files'].get(path) == pin", "proof['policy_sha256'] == sha(raw)"):
 ck('strict source predicate '+frag,frag in context)
ck('exact prediction policy/fullmap/cell guards',"parent_inputs.get(ROLE, {}).get('sha256') == policy_sha256" in prediction and "parent_cells == [expected['cell_id']]" in prediction and "parent_sources.get(p) == h" in prediction)
ck('no non-source provenance relaxation',"if k not in ('source_commit', 'source_hashes')" in relation and "old['source_commit'] == HISTORICAL_SOURCE" in relation)
# Concrete policy negative controls. Pure metadata only, never API authority.
for name,alter in [('oldclaim',lambda p:p['historical'].update(claim_sha256='0'*64)),('oldsource',lambda p:p['historical'].update(source=binding['actual_source_design'])),('oldmapmissing',lambda p:p['historical']['installed'].pop(next(iter(old)))),('targetmapmissing',lambda p:p['target']['installed'].pop(next(iter(target)))),('deltaomitted',lambda p:p['allowed_delta'].pop()),('proofroleomitted',lambda p:p['proof_roles'].pop()),('consumerunresolved',lambda p:p['consumers']['predict'].update(experiment=None)),('consumerhistorical',lambda p:p['consumers']['predict'].update(experiment=identity))]:
 bad=copy.deepcopy(policy);alter(bad);refusal('concrete policy refuses '+name,lambda bad=bad:m.validate_contract(bad,helperpin))
# Correct exact old/current relation with a prospective provenance value only.
newprov=copy.deepcopy(hist['provenance']);newprov.update(source_commit=binding['actual_source_design'],source_hashes=sorted(set(target.values())));m.validate_relation(old,target,hist['provenance'],newprov);ck('actual old/target directional pure relation',True)
for name,bad in [('sameoldsource',newprov|{'source_commit':oldsource}),('launderedoldhashes',newprov|{'source_hashes':hist['provenance']['source_hashes']}),('differentcell',newprov|{'cell_id':'wrong'})]:refusal('concrete relation refuses '+name,lambda bad=bad:m.validate_relation(old,target,hist['provenance'],bad))
ck('binding still has no recovery/gate/budget/numerical release',all(binding[k] is None for k in ('actual_recovery_proof','actual_review_proof','gate','budget20_adoption','numerical_release')))
ck('stdlib only/no numerical imports',not any(n in sys.modules for n in ('numpy','torch','pandas')))
save('ROOT_PINS01.json',rootpins);save('SOURCE_MAP_READBACK01.json',source_rows);save('NAMESPACE_READBACK01.json',namespace_rows)
save('CHECKS01.json',{'checks':len(rows),'rows':rows,'historical_member_hashed_only':True,'new_source_policy_installed':False,'new_Run_or_Admission_created':False,'numerical_packages_imported':False,'future_reference_UNAVAILABLE':True,'continuation_cell_reuse':'exact original failed parent required; future identity namespaces absent'})
print(json.dumps({'status':'PASS_CONCRETE_POLICY_ONLY','checks':len(rows),'policy_sha256':rootpins['POLICY01.json'],'helper_sha256':helperpin,'historical_map_sha256':sha(canon(old)),'target_map_sha256':sha(canon(target))}))
