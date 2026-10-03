"""Prospective genuine finite synthetic financial-wrapper fixture. No auto launch.
Numerical imports and synthetic tensor construction occur only after real admission.
"""
import hashlib,json,os,resource,stat,sys,time
from pathlib import Path
MODEL='20f451c08143dd81491b5c9fa0a90243ee6a9363df1fbbfcbd9c45b32f9b054d'
TRAINING='d5276b75491e130bd03d43de28120f72dd792e42af4446382a6c127d387b8ec0'
CANDIDATE='e16402d8625ed9b1c9fe5d308d18867b811b3acb2bb90b2e0bcb7132cd4a602e'
BACKEND='e8355dc4443dc40b64fe2fd0d22f764d47280c655f921e9f1705042e348ec21f'
PHASES=('agreement','interrupt1','complete100','continue100','predict')
F32={'atol':1e-6,'rtol':1e-5};EXACT={'atol':0.,'rtol':0.}
GIB=1024**3;FILE=4*1024**2
PREFIX='tradingagents/research/onchain_replication/'
OUTPUTS={'cell-ledger.json','wrapper-summary.json','artifact-index.json'}
RECIPE={'schema_version':1,'kind':'opaque-sha256-synthetic-16x28-distinct-v1','seed':11,'batch':16,'lookback':28,'nodes':4,'mcm_width':32,'empirical_inputs':False,'fitted_dictionary':False}
class Unavailable(ValueError):pass
class PlannedInterruption(RuntimeError):pass
def require(v,why):
 if not v:raise Unavailable(why)
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def validate_plan(p):
 keys={'schema_version','kind','phase','experiment','cell_id','task','execution','model_input','training_input','recipe_input','closure_input','runtime_input','prior_input','reference_input','namespace'}
 require(type(p)is dict and set(p)==keys and type(p['schema_version'])is int and p['schema_version']==1,'exact wrapper plan required')
 require(p['kind']=='genuine-financial-wrapper-synthetic-v1' and p['phase'] in PHASES,'finite wrapper phase required')
 for k in ('experiment','cell_id','model_input','training_input','recipe_input','closure_input','runtime_input','namespace'):require(type(p[k])is str and p[k] and '/' not in p[k] and '..' not in p[k],'unavailable genuine identity/input: '+k)
 require(p['task'] in ('classification','regression') and p['execution'] in ('eager','selected'),'fixed task/backend required')
 require((p['prior_input'] is not None)==(p['phase'] in ('continue100','predict')),'genuine prior phase input required exactly')
 require((p['reference_input'] is not None)==(p['phase']=='continue100'),'continuation requires registered uninterrupted100 reference')
 for k in ('prior_input','reference_input'):
  require(p[k] is None or type(p[k])is str and p[k] and '/' not in p[k],'invalid parent input reference')
 return p

def schema(job):
 require(type(job)is dict and set(job)=={'schema_version','kind','resources','environment_input','payload'} and job['schema_version']==1 and job['kind']=='financial_wrapper','explicit wrapper job required')
 require(type(job['payload'])is dict and set(job['payload'])=={'plan_input'} and type(job['payload']['plan_input'])is str and job['payload']['plan_input'],'registered plan route required')
 r=job['resources'];require(r.get('native_unit_limits')=={'file_size_bytes':FILE} and 'physical_policy' not in r,'native wrapper file route required')
 require(r['memory_high_bytes']==r['memory_max_bytes']==3*GIB and r['reserve_bytes']==3*GIB and r['start_reserve_bytes']==6*GIB and r['disk_floor_bytes']==10*GIB and r['wall_seconds']==1800,'frozen finite engineering resource envelope')
 b=r['storage_budget'];require(set(b)=={'root','limits'} and b['limits']=={'max_allocated_bytes':GIB,'max_logical_bytes':GIB,'max_entries':32768,'max_depth':32,'max_scan_seconds':5},'whole workspace sampled envelope required')

def worker_limits():
 resource.setrlimit(resource.RLIMIT_FSIZE,(FILE,FILE))
 require(resource.getrlimit(resource.RLIMIT_FSIZE)==(FILE,FILE),'actual inherited file limit required')
 return {'rlimit_fsize':FILE}

def admitted(ad,job):
 schema(job);info=ad.inputs.get(job['payload']['plan_input']);require(info is not None,'wrapper plan not registered')
 raw=(ad.root/info['path']).read_bytes();require(sha(raw)==info['sha256'],'plan bytes differ');p=validate_plan(json.loads(raw))
 require(p['experiment']==ad.experiment_id and ad.experiment['cells']==[p['cell_id']] and set(ad.experiment['outputs'])==OUTPUTS,'exact separately registered engineering identity/cell/outputs required')
 require(ad.spec['program_id'].startswith('financial-wrapper-engineering-'),'financial research program cannot host this engineering fixture')
 require(job['resources']['disk_paths']==[str(ad.root)] and job['resources']['storage_budget']['root']==str(ad.root),'whole capsule resource coverage required')
 require((ad.root/'.git').is_dir() and (ad.root/'.git').resolve()==ad.root/'.git','genuine isolated Git root required')
 def registered(name):
  info=ad.inputs.get(name);require(info is not None,'unavailable registered prerequisite: '+str(name));path=ad.root/info['path']
  require(path.resolve()==path and path.is_file() and path.stat().st_size<=FILE,'registered prerequisite path/extent')
  raw=path.read_bytes();require(sha(raw)==info['sha256'],'registered prerequisite bytes changed');return raw
 require(sha(registered(p['model_input']))==MODEL and sha(registered(p['training_input']))==TRAINING and json.loads(registered(p['recipe_input']))==RECIPE,'pre-import original science/recipe closure differs')
 closure=json.loads(registered(p['closure_input']));require(type(closure)is dict and type(closure.get('installed'))is dict and closure.get('candidate02')==CANDIDATE,'pre-import source closure absent')
 source=closure['installed'];require(source.get(PREFIX+'financial_execution.py')==CANDIDATE and source.get(PREFIX+'streamed_gat.py')==BACKEND,'pre-import exact candidate pins differ')
 for name,pin in source.items():
  path=ad.root/name;require(not Path(name).is_absolute() and '..' not in Path(name).parts and path.resolve()==path and path.is_file() and path.stat().st_size<=FILE and ad.experiment['source_files'].get(name)==pin==sha(path.read_bytes()),'pre-import admitted source differs: '+name)
 runtime=json.loads(registered(p['runtime_input']));runtime_check(ad.root,runtime)
 return p

def runtime_check(root,value):
 import importlib.metadata,platform
 keys={'python','executable','resolved_executable','prefix','executable_sha256','lock_sha256','distribution_records'}
 require(type(value)is dict and set(value)==keys,'genuine locked runtime mapping unavailable')
 require(value['python']==platform.python_version()=='3.13.13' and value['executable']==sys.executable and value['prefix']==sys.prefix,'runtime interpreter mapping differs')
 exe=Path(sys.executable).resolve();require(str(exe)==value['resolved_executable'] and sha(exe.read_bytes())==value['executable_sha256'] and sha((root/'uv.lock').read_bytes())==value['lock_sha256'],'runtime interpreter/lock bytes differ')
 rows=value['distribution_records'];require(type(rows)is list and rows and {r['name'] for r in rows}>={'torch','numpy','scipy'},'runtime distribution closure absent')
 require(len({r['name'] for r in rows})==len(rows),'duplicate runtime distribution')
 for row in rows:
  require(set(row)=={'name','version','record','record_sha256'} and importlib.metadata.version(row['name'])==row['version'],'runtime distribution version differs')
  distribution=importlib.metadata.distribution(row['name']);matches=[f for f in distribution.files or () if str(f).endswith('.dist-info/RECORD')]
  require(len(matches)==1,'runtime installed RECORD unavailable')
  record=Path(distribution.locate_file(matches[0])).resolve();require(str(record)==row['record'] and sha(record.read_bytes())==row['record_sha256'],'runtime RECORD origin/hash differs')
 return {'qualification':'exact interpreter/lock/version/RECORD mapping; dependency bodies not fully rehashed'}

def authorize(run,args,plan_input):
 # No duck-typed Run, Owner, Binding or fixture bypass is accepted.
 from ..lifecycle import ResearchRun
 from . import job,resources
 require(type(run)is ResearchRun,'genuine admitted ResearchRun unavailable')
 run._active();run._check_source();run._check_inputs()
 ad,j=job._admitted(args);p=admitted(ad,j)
 require(ad.experiment_id==run.admission.experiment_id and ad.source==run.admission.source and ad.registration_sha256==run.admission.registration_sha256 and j['payload']['plan_input']==plan_input,'actual job/Run/plan join differs')
 r=j['resources'];base=job._base(args)
 live=resources.assert_guarded_worker(base/'guard',job._command(args,'worker'),required_paths=[ad.root],wall_seconds=r['wall_seconds'],memory_max_bytes=r['memory_max_bytes'],memory_high_bytes=r['memory_high_bytes'],disk_floor_bytes=r['disk_floor_bytes'])
 owner=json.loads((base/'owner.json').read_bytes())
 require(live['owner_identity']==owner and owner['experiment']==ad.experiment_id and owner['source_commit']==ad.source and live['native_unit_limits']==r['native_unit_limits'],'genuine native process owner missing')
 require(resource.getrlimit(resource.RLIMIT_FSIZE)==(FILE,FILE) and len(os.sched_getaffinity(0))==2,'actual file/CPU envelope differs')
 require(all(live[k]==v for k,v in r.items()),'registered guard policy differs')
 raw_model=run.read_input(p['model_input']);raw_training=run.read_input(p['training_input']);raw_recipe=run.read_input(p['recipe_input']);closure=json.loads(run.read_input(p['closure_input']))
 require(sha(raw_model)==MODEL and sha(raw_training)==TRAINING and json.loads(raw_recipe)==RECIPE,'frozen science or synthetic recipe differs')
 require(type(closure)is dict and set(closure)=={'schema_version','installed','scientific_model','scientific_training','candidate02'} and closure['schema_version']==1,'complete source closure schema unavailable')
 require(closure['scientific_model']==MODEL and closure['scientific_training']==TRAINING and closure['candidate02']==CANDIDATE,'source/science pins differ')
 source=closure['installed'];require(type(source)is dict and job.required_sources()<=set(source),'complete conservative source closure unavailable')
 require(source.get(PREFIX+'financial_execution.py')==CANDIDATE and source.get(PREFIX+'streamed_gat.py')==BACKEND,'exact candidate02/backend required')
 for name,pin in source.items():
  path=ad.root/name;require(type(name)is str and not Path(name).is_absolute() and '..' not in Path(name).parts and path.resolve()==path and path.is_file() and not path.is_symlink() and path.stat().st_size<=FILE,'source path/extent differs')
  require(ad.experiment['source_files'].get(name)==pin==sha(path.read_bytes()),'installed registered source body differs: '+name)
 require(Path(__file__).resolve()==ad.root/(PREFIX+'financial_wrapper_fixture.py'),'fixture imported outside admitted package')
 require(source.get(PREFIX+'financial_wrapper_fixture.py')==sha(Path(__file__).read_bytes()),'fixture itself unregistered')
 # The job worker already compared the full frozen runtime inventory inside its
 # genuine native boundary. Repeat that comparison before tensor construction.
 from .environment import inventory
 require(inventory(ad.root,include_torch=True)==json.loads(run.read_input(j['environment_input'])),'actual runtime closure differs')
 return p,json.loads(raw_model),json.loads(raw_training),source,sha(raw_recipe)

def watch(run,directory,deadline):
 run._active();require(time.monotonic()<deadline,'finite wrapper cooperative deadline')
 total=allocated=count=0
 if directory.exists():
  for p in directory.rglob('*'):
   s=p.lstat();count+=1;require(count<=512 and len(p.relative_to(directory).parts)<=12 and not stat.S_ISLNK(s.st_mode),'wrapper namespace bound')
   if stat.S_ISREG(s.st_mode):require(s.st_size<=FILE,'retained member exceeds native file bound');total+=s.st_size;allocated+=s.st_blocks*512
   else:require(stat.S_ISDIR(s.st_mode),'wrapper special file refused')
 require(total<=64*1024**2 and allocated<=80*1024**2,'wrapper retained byte bound')
 return {'files_and_directories':count,'logical_bytes':total,'allocated_bytes':allocated}

def synthetic(torch):
 """448 distinct graph objects/tensors; no data file, empirical graph or reuse."""
 def values(tag,n):
  return [(int.from_bytes(hashlib.sha256((tag+':'+str(i)).encode()).digest()[:2],'big')/65535-.5)/8 for i in range(n)]
 graphs=[]
 for i in range(16*28):
  mcm=torch.tensor(values('opaque-graph-'+str(i),4*32),dtype=torch.float32).reshape(4,32).requires_grad_()
  edges=torch.tensor([[0,1,2,3,1],[1,2,3,0,0]],dtype=torch.long)
  graphs.append({'mcm':mcm,'edge_index':edges})
 require(len({id(g) for g in graphs})==448 and len({g['mcm'].data_ptr() for g in graphs})==448,'distinct synthetic object/storage denominator')
 prices=torch.tensor(values('opaque-prices',448),dtype=torch.float32).reshape(16,28,1).requires_grad_()
 return {'graph_sequences':[graphs[i*28:(i+1)*28] for i in range(16)],'prices':prices},graphs

def targets(torch,task):
 return torch.tensor([i%2 for i in range(16)],dtype=torch.long) if task=='classification' else torch.tensor([(i-8)/32 for i in range(16)],dtype=torch.float32).reshape(16,1)

def compare(torch,a,b,tol=F32,path='root',records=None):
 require(type(a)is type(b) or isinstance(a,dict) and isinstance(b,dict),'comparison type: '+path)
 if isinstance(a,torch.Tensor):
  require(a.shape==b.shape and a.dtype==b.dtype,'tensor shape/dtype: '+path)
  if a.dtype.is_floating_point:
   require(bool(torch.isfinite(a).all()) and bool(torch.isfinite(b).all()),'nonfinite comparison: '+path)
   torch.testing.assert_close(a,b,**tol)
   if records is not None:records.append({'path':path,'shape':list(a.shape),'max_abs':float((a-b).abs().max()) if a.numel() else 0.})
  else:require(torch.equal(a,b),'exact tensor differs: '+path)
 elif isinstance(a,dict):
  require(a.keys()==b.keys(),'comparison keys: '+path)
  for k in a:compare(torch,a[k],b[k],tol,path+'/'+str(k),records)
 elif isinstance(a,(list,tuple)):
  require(len(a)==len(b),'comparison length: '+path)
  for i,(x,y) in enumerate(zip(a,b,strict=True)):compare(torch,x,y,tol,path+'/'+str(i),records)
 else:require(a==b,'exact scalar differs: '+path)

def selected(financial):
 policy={'schema_version':1,'backend':'streamed-gat-mulsum-v1','block_edges':65536}
 return financial.identity({'policy':policy,'policy_sha256':sha(canonical(policy)),'source_path':financial.SOURCE,'source_sha256':BACKEND,'candidate_sha256':BACKEND})

def optimizer(torch,model,t):
 return torch.optim.Adam(model.parameters(),lr=t['learning_rate'],betas=tuple(t['betas']),eps=t['epsilon'],weight_decay=t['weight_decay'])

def provenance(run,p,model,training,sources,recipe_hash,execution):
 value={'source_hashes':sorted(set(sources.values())),'config_hash':sha(canonical({'model':model,'training':training,'task':p['task'],'recipe':RECIPE})),'input_hash':recipe_hash,'dictionary_hash':sha(b'synthetic opaque MCM; no empirical dictionary fitted or recovered'),'fold_id':'synthetic-16x28-distinct','cell_id':p['cell_id'],'source_commit':run.admission.source}
 if execution is not None:value['model_execution']=execution
 return value

def frozen(torch,value):
 import copy
 if isinstance(value,torch.Tensor):return value.detach().cpu().clone()
 if isinstance(value,dict):return {k:frozen(torch,v) for k,v in value.items()}
 if isinstance(value,list):return [frozen(torch,v) for v in value]
 if isinstance(value,tuple):return tuple(frozen(torch,v) for v in value)
 return copy.deepcopy(value)

def one_step(torch,registry,financial,checkpoints,config,training,task,execution):
 rng=checkpoints.seed_all(11);model=registry.build_model('proposed',task,config,execution=execution);financial.check_model(model,execution)
 initial=frozen(torch,model.state_dict());initial_rng=frozen(torch,checkpoints.capture_rng(rng));opt=optimizer(torch,model,training);inputs,graphs=synthetic(torch);target=targets(torch,task);model.train();out=model(**inputs)
 loss=torch.nn.functional.cross_entropy(out,target) if task=='classification' else torch.nn.functional.mse_loss(out,target)
 require(bool(torch.isfinite(loss)),'nonfinite one-step loss');loss.backward()
 grads={}
 for name,param in model.named_parameters():
  require(param.requires_grad and param.grad is not None and bool(torch.isfinite(param.grad).all()),'missing/nonfinite trainable gradient: '+name);grads[name]=frozen(torch,param.grad)
 input_grads={'mcm':[frozen(torch,g['mcm'].grad) for g in graphs],'prices':frozen(torch,inputs['prices'].grad)}
 require(all(x is not None for x in input_grads['mcm']) and input_grads['prices'] is not None,'missing input gradients')
 torch.nn.utils.clip_grad_norm_(model.parameters(),training['gradient_clip_norm'],error_if_nonfinite=True);opt.step();financial.check_model(model,execution)
 evidence={'initial':initial,'initial_rng':initial_rng,'output':frozen(torch,out),'loss':frozen(torch,loss),'parameter_gradients':grads,'input_gradients':input_grads,'updated':frozen(torch,model.state_dict()),'optimizer':frozen(torch,opt.state_dict()),'rng':frozen(torch,checkpoints.capture_rng(rng))}
 return model,opt,rng,evidence

def persist_tensors(torch,path,value):
 import io
 class Bounded(io.BytesIO):
  def write(self,b):require(self.tell()+len(b)<=FILE,'evidence serialization bound');return super().write(b)
 with Bounded() as stream:
  torch.save(value,stream);body=stream.getvalue()
 with path.open('xb') as f:f.write(body);f.flush();os.fsync(f.fileno())
 return {'bytes':len(body),'sha256':sha(body)}

def _parent(run,p,prov):
 from ..verify import verify_claim
 from .provenance import file_hash
 value=json.loads(run.read_input(p['prior_input']));require(set(value)=={'parent','claim_input','terminal_input','checkpoint_input','completion_input','provenance'},'exact genuine prior descriptor required')
 parent=value['parent'];require(parent==run.admission.experiment['parent'] and parent!=run.admission.experiment_id,'registered prior identity required')
 directory=run.admission.root/'research_runs'/parent;claim=verify_claim(directory);claim_raw=run.read_input(value['claim_input']);terminal_raw=run.read_input(value['terminal_input']);terminal=json.loads(terminal_raw)
 require(claim_raw==(directory/'claim.json').read_bytes() and terminal['claim_sha256']==sha(claim_raw) and terminal['experiment_id']==parent,'genuine prior claim/terminal join')
 status='failed' if p['phase']=='continue100' else 'complete'
 require(terminal_raw==(directory/(status+'.json')).read_bytes() and not (directory/('complete.json' if status=='failed' else 'failed.json')).exists(),'actual prior lifecycle status differs')
 require({k:v for k,v in value['provenance'].items() if k!='source_commit'}=={k:v for k,v in prov.items() if k!='source_commit'},'prior scientific provenance differs')
 info=run.admission.inputs[value['checkpoint_input']];run.read_input(value['checkpoint_input']);checkpoint=run.admission.root/info['path']
 manifest=json.loads(checkpoint.read_bytes())
 require(manifest['provenance']==value['provenance'],'prior artifact provenance differs')
 for name,item in manifest['members'].items():
  path=checkpoint.parent/name;relative=str(path.relative_to(run.admission.root))
  require(Path(name).name==name and any(x['path']==relative and x['sha256']==item['sha256'] for x in run.admission.inputs.values()),'every checkpoint body must be a genuine registered input')
  require(path.stat().st_size==item['size']<=FILE and file_hash(path)==item['sha256'],'prior checkpoint member differs')
 return value,checkpoint

def replay_package(torch,directory,model,checkpoint,prov,config,replay):
 from ..lifecycle import _immutable
 from .provenance import file_hash
 directory.mkdir();inputs,graphs=synthetic(torch);model.eval()
 with torch.no_grad():expected=model(**inputs).tolist()
 raw={'data_kind':'synthetic_neural_inputs','graphs':[{'mcm':g['mcm'].detach().tolist(),'edge_index':g['edge_index'].tolist()} for g in graphs],'sequences':[list(range(i*28,(i+1)*28)) for i in range(16)],'prices':inputs['prices'].detach().tolist()}
 _immutable(directory/'inputs.json',raw);_immutable(directory/'model.json',config);_immutable(directory/'expected.json',expected)
 # Copy every immutable checkpoint byte inside the replay namespace; the source
 # checkpoint remains intact. This does not mint fit completion or run authority.
 local=directory/'checkpoint'/checkpoint.parent.name;local.mkdir(parents=True)
 for source in sorted(checkpoint.parent.iterdir()):
  require(source.is_file() and not source.is_symlink() and source.stat().st_size<=FILE,'checkpoint replay member bound')
  with (local/source.name).open('xb') as f:f.write(source.read_bytes());f.flush();os.fsync(f.fileno())
 package=Path(replay.__file__).resolve().parent
 manifest={'data_kind':raw['data_kind'],'task':model.task,'provenance':prov,'checkpoint':str((local/checkpoint.name).relative_to(directory)),'files':{str(x.relative_to(directory)):file_hash(x) for x in directory.rglob('*') if x.is_file()},'source_files':{name:file_hash(package/name) for name in (replay.SELECTED_CODE if 'model_execution' in prov else replay.CODE)},'qualification':'448 distinct tiny synthetic graphs,16x28; no paper result'}
 _immutable(directory/'manifest.json',manifest);return replay.replay(directory)

def execute(run,args,plan_input):
 p,config,t,sources,recipe_hash=authorize(run,args,plan_input)
 # The original training.json is retained, including100 epochs. These are tiny
 # synthetic engineering fits; no empirical fit or completed one-step shortcut.
 require(t['epochs']==100 and t['batch_size']==16 and config['lookback_days']==28,'fixed original training/config dimensions')
 import torch
 from . import financial_execution as financial,model_registry as registry,checkpoints,training,evaluation,replay
 from ..lifecycle import _immutable
 from .provenance import file_hash
 torch.set_num_threads(2);require(not torch.cuda.is_available(),'CPU-only fixture runtime required')
 execution=financial.for_run(run,selected(financial)) if p['execution']=='selected' else None
 prov=provenance(run,p,config,t,sources,recipe_hash,execution)
 directory=run.admission.root/'research_artifacts'/'financial_wrapper_engineering'/p['namespace'];directory.parent.mkdir(parents=True,exist_ok=True);directory.mkdir(exist_ok=False)
 require(directory.resolve()==directory,'canonical engineering output required');deadline=time.monotonic()+1700
 lease=lambda:watch(run,directory,deadline)
 lease();_immutable(directory/'intent.json',{'plan':p,'provenance':prov,'kind':'synthetic engineering only','scientific_epochs':100,'paper_financial_fits':0})
 try:
  if p['phase']=='agreement':
   records=[];states=[]
   for policy in (None,financial.for_run(run,selected(financial))):
    lease();model,opt,rng,evidence=one_step(torch,registry,financial,checkpoints,config,t,p['task'],policy);cp_prov=provenance(run,p,config,t,sources,recipe_hash,policy)
    cp=checkpoints.save_checkpoint(directory/('selected' if policy else 'eager'),model,opt,rng,cp_prov,epoch=1,batch=0,logs=[{'kind':'one-step engineering; not completed fit'}])
    fresh=registry.build_model('proposed',p['task'],config,execution=policy);freshopt=optimizer(torch,fresh,t);fresh_rng=checkpoints.seed_all(901)
    restored=checkpoints.load_checkpoint(cp,fresh,freshopt,fresh_rng,cp_prov)
    compare(torch,evidence['updated'],fresh.state_dict(),EXACT);compare(torch,evidence['optimizer'],freshopt.state_dict(),EXACT);compare(torch,evidence['rng'],checkpoints.capture_rng(fresh_rng),EXACT)
    replay_result=replay_package(torch,directory/('selected-replay' if policy else 'eager-replay'),fresh,cp,cp_prov,config,replay)
    persist_tensors(torch,directory/('selected-evidence.pt' if policy else 'eager-evidence.pt'),evidence)
    states.append(evidence);records.append({'backend':'selected' if policy else 'eager','checkpoint':str(cp.relative_to(run.admission.root)),'checkpoint_sha256':file_hash(cp),'replay':replay_result})
    if policy is not None:
     # Genuine selected constructor mutations must refuse before restore. No
     # public attach route or fake model is used; mutated models are discarded.
     altered=registry.build_model('proposed',p['task'],config,execution=policy);altered.graph.gat[0].slope+=.1
     try:checkpoints.load_checkpoint(cp,altered,optimizer(torch,altered,t),fresh_rng,cp_prov)
     except ValueError:pass
     else:raise AssertionError('changed selected contract accepted')
     missing=dict(restored);missing.pop('model_contract')
     try:financial.check_state_model(missing,fresh,cp_prov)
     except ValueError:pass
     else:raise AssertionError('missing selected state contract accepted')
   comparisons=[];compare(torch,states[0],states[1],F32,records=comparisons);compare(torch,states[0]['initial'],states[1]['initial'],EXACT);compare(torch,states[0]['rng'],states[1]['rng'],EXACT)
   result={'phase':p['phase'],'comparisons':comparisons,'backends':records,'full_batch':16,'lookback':28,'distinct_graphs':448,'one_step_is_fit_completion':False}
  else:
   factory=lambda:registry.build_model('proposed',p['task'],config,execution=execution)
   def batches(indices):
    require(indices==list(range(16)),'fixture cannot shorten configured16 batch');lease();data,_=synthetic(torch);return data,targets(torch,p['task'])
   if p['phase']=='predict':
    prior,cp=_parent(run,p,prov)
    recovery={'provenance':prior['provenance'],'checkpoint_input':prior['checkpoint_input'],'completion_input':prior['completion_input']}
    model,cp_hash=evaluation.recover_completed_model(run,p['cell_id'],prov,recovery,factory,'proposed')
    require(json.loads(run.read_input(prior['completion_input']))['epochs']==100,'genuine completed100 fit required')
    predictions=training.predict_cell(model,batches,16,16);persist_tensors(torch,directory/'predictions.pt',predictions)
    result={'phase':'predict','checkpoint_sha256':cp_hash,'replay':replay_package(torch,directory/'replay',model,cp,prior['provenance'],config,replay),'optimizer_updates':0}
   else:
    continuation=None
    if p['phase']=='continue100':
     prior,cp=_parent(run,p,prov);continuation={'checkpoint':str(cp),'provenance':prior['provenance']}
    def after(epoch,batch,checkpoint):
     lease()
     if p['phase']=='interrupt1':
      require(epoch==1 and batch==0 and checkpoint is not None,'first genuine epoch checkpoint unavailable')
      _immutable(directory/'interrupted-checkpoint.json',{'checkpoint':str(checkpoint),'sha256':file_hash(checkpoint),'provenance':prov,'epochs_completed':epoch,'requires_genuine_failed_parent':True})
      raise PlannedInterruption('prospective engineering failed-parent fixture after one real update; no fit completion')
    fitted=training.fit_cell(run,p['cell_id'],prov,factory,batches,16,p['task'],11,t,continuation=continuation,after_batch=after)
    require(len(fitted.logs)==100,'original100-epoch completion required')
    if p['phase']=='continue100':
     from ..verify import verify_claim
     ref=json.loads(run.read_input(p['reference_input']));require(set(ref)=={'checkpoint_input','provenance','completion_input','claim_input','terminal_input'},'uninterrupted reference schema')
     terminal=json.loads(run.read_input(ref['terminal_input']));claim_raw=run.read_input(ref['claim_input']);claim=json.loads(claim_raw);require(terminal['status']=='complete' and terminal['claim_sha256']==sha(claim_raw) and terminal['experiment_id']==claim['experiment_id'],'genuine uninterrupted complete reference')
     refdir=run.admission.root/'research_runs'/claim['experiment_id'];verified=verify_claim(refdir)
     require(verified==claim and claim_raw==(refdir/'claim.json').read_bytes() and run.read_input(ref['terminal_input'])==(refdir/'complete.json').read_bytes() and not (refdir/'failed.json').exists(),'uninterrupted reference actual lifecycle join')
     require({k:v for k,v in ref['provenance'].items() if k not in ('source_commit','cell_id')}=={k:v for k,v in prov.items() if k not in ('source_commit','cell_id')},'reference scientific provenance differs')
     complete=json.loads(run.read_input(ref['completion_input']));require(complete['epochs']==100,'uninterrupted reference incomplete')
     refcp=run.admission.root/run.admission.inputs[ref['checkpoint_input']]['path'];run.read_input(ref['checkpoint_input']);require(complete['sha256']==file_hash(refcp),'reference checkpoint completion join')
     expected_fit=run.admission.root/'research_artifacts/onchain_fit_cells'/sha(ref['provenance']['cell_id'].encode())/claim['experiment_id']
     require(refcp.resolve().is_relative_to(expected_fit.resolve()) and (run.admission.root/run.admission.inputs[ref['completion_input']]['path']).resolve()==(expected_fit/'complete.json').resolve() and Path(complete['checkpoint']).resolve()==refcp.resolve(),'reference completed fit location differs')
     refmanifest=json.loads(refcp.read_bytes())
     for name,item in refmanifest['members'].items():
      member=refcp.parent/name;require(Path(name).name==name and any(x['path']==str(member.relative_to(run.admission.root)) and x['sha256']==item['sha256'] for x in run.admission.inputs.values()) and member.stat().st_size==item['size']<=FILE and file_hash(member)==item['sha256'],'reference checkpoint body not registered')
     reference=factory();op=optimizer(torch,reference,t);rng=checkpoints.seed_all(11);state=checkpoints.load_checkpoint(refcp,reference,op,rng,ref['provenance'])
     require(state['epoch']==100 and state['batch']==0,'reference cursor incomplete')
     current=factory();op2=optimizer(torch,current,t);rng2=checkpoints.seed_all(11);actual=checkpoints.load_checkpoint(fitted.checkpoint,current,op2,rng2,prov)
     compare(torch,state['model'],actual['model'],EXACT);compare(torch,state['optimizer'],actual['optimizer'],EXACT);compare(torch,state['rng'],actual['rng'],EXACT);compare(torch,state['logs'],actual['logs'],EXACT)
    result={'phase':p['phase'],'checkpoint':str(fitted.checkpoint),'checkpoint_sha256':fitted.checkpoint_hash,'epochs':len(fitted.logs),'replay':replay_package(torch,directory/'replay',fitted.model,fitted.checkpoint,prov,config,replay)}
  result.update(scope='genuine synthetic financial wrapper only',paper_financial_fits=0,full_size_capacity=False,resources=lease())
  _immutable(directory/'result.json',result)
  cells=[{'id':p['cell_id'],'status':'complete','kind':'finite synthetic engineering'}]
  run.write_json('cell-ledger.json',cells);run.write_json('wrapper-summary.json',result);run.write_json('artifact-index.json',{str(x.relative_to(run.admission.root)):{'sha256':file_hash(x),'bytes':x.stat().st_size} for x in directory.rglob('*') if x.is_file()})
  return cells
 except BaseException as error:
  # Genuine ResearchRun/job owns FAILED and native descendant shutdown. Never
  # coerce a100-epoch completion, delete partials, retry or manufacture an Owner.
  try:_immutable(directory/'failure.json',{'type':type(error).__name__,'reason':str(error),'success':False,'retry':False})
  except BaseException as later:
   error.add_note('failure evidence publication unresolved: '+repr(later))
   if not isinstance(later,Exception) or isinstance(later,MemoryError):raise later from error
  raise
