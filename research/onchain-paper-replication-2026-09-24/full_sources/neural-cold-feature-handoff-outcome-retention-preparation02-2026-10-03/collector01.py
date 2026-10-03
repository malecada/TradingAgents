"""Read-only original outcome authentication and separate complete byte retention.
No starts/admission, arrays/pickle deserialization, source changes or network.
"""
import argparse,hashlib,importlib.util,json,os,re,subprocess,sys,time
from pathlib import Path
import archive01 as store
import owned_io as io
from closed_comparison01 import authenticate_closed_comparison
IDS={'materialize':'compact-cold-inputs-20261003-01','compare':'compact-cold-comparison-20261003-01'}
OUTPUTS={'materialize':['proof-materialize.json'],'compare':['binding.json','journal.json','cold-handoff.json','proof-compare.json']}
INV='e8d8594d1c7aabe4076bf2b4bab7454cb0fad48ec8f46b754e06fc3f3ddb6773'
GIB=store.GIB;MAX=store.MAX;require=store.require

def digest(data):return hashlib.sha256(data).hexdigest()
def reference(v):
 require(type(v)is dict and set(v)=={'path','sha256'} and re.fullmatch('[0-9a-f]{64}',v['sha256']) is not None,'exact original reference required');b=store.read(v['path']);require(digest(b)==v['sha256'],'original reference changed');return b

def metadata(root,relative,limit=MAX):return json.loads(store.read(root/store.relative(relative),limit))
def load(name,path,expected):
 require(digest(store.read(path))==expected,'selected helper differs')
 if name in sys.modules:require(Path(sys.modules[name].__file__).resolve()==path,'existing helper origin differs');return sys.modules[name]
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def source_context(q):
 require(set(q)=={'schema_version','root','source','inventory','releases','wrappers','wrapper_waits','parent_sources','reservation_roots','destination'} and type(q['schema_version'])is int and q['schema_version']==2,'exact collection request required')
 require(set(q['releases'])==set(q['wrappers'])==set(q['wrapper_waits'])==set(q['parent_sources'])==set(q['reservation_roots'])==set(IDS),'both fixed phase denominator required')
 root=store.direct(q['root']);[reservation_paths(q,root,phase) for phase in IDS];require(Path.cwd()==root and (root/'.git').is_dir() and not os.path.lexists(root/'.git/objects/info/alternates'),'actual isolated capsule cwd required')
 require(re.fullmatch('[0-9a-f]{40}',q['source']) is not None,'source commit required');head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True,timeout=10).strip();require(head==q['source'],'current source freeze differs')
 raw=reference(q['inventory']);require(digest(raw)==INV,'selected composition04 inventory differs');inventory=json.loads(raw);rows=inventory['source_inventory'];require(len(rows)==195 and inventory['package_count']==147,'source195/package147 required');sources={}
 for row in rows:
  b=store.read(root/store.relative(row['target']));require(digest(b)==row['sha256'] and len(b)==row['bytes'],'selected source changed');sources[row['target']]=row['sha256']
 require(len(sources)==195 and sum(n.startswith('tradingagents/') for n in sources)==147,'source mapping duplicates or package mismatch')
 raw_api=load('proof_raw01',root/'proof_tools/proof_raw01.py',sources['proof_tools/proof_raw01.py']);api=load('proof_release01',root/'proof_tools/proof_release01.py',sources['proof_tools/proof_release01.py']);api.no_numerics()
 return root,sources,raw_api,api

AUTHORITY_NAMESPACES=('research_runs','proof_outer','proof_supervise','research_artifacts/compact-cold-engineering-20261003','research_artifacts/onchain-paper-replication-2026-09-24/runs')

# Exact selected compact_native_producer.NAMESPACES. Their presence is only
# conservative born-artifact evidence, never an attributed Owner or claim.
COMPACT_NAMESPACES=('onchain_representations','onchain_pair_workflows','onchain_compact_sampler','onchain_compact_samples','onchain_compact_dictionary','onchain_compact_mcm','onchain_compact_outputs','onchain_compact_graphs','onchain_compact_publications','onchain_compact_terminals')
def capsule_authority_paths(root,phase):
 return [root/ns/IDS[phase] for ns in AUTHORITY_NAMESPACES]+[root/'research_artifacts'/ns for ns in COMPACT_NAMESPACES]

def reservation_paths(q,root,phase):
 values=q['reservation_roots'][phase];require(type(values)is dict and set(values)=={'wrapper','parent'},'exact planned wrapper and parent roots required')
 paths={name:store.direct(path) for name,path in values.items()}
 require(paths['wrapper']!=paths['parent'] and all(not p.is_relative_to(root) and not root.is_relative_to(p) for p in paths.values()) and not paths['wrapper'].is_relative_to(paths['parent']) and not paths['parent'].is_relative_to(paths['wrapper']),'independent finite reservation roots required')
 if q.get('wrappers',{}).get(phase) is not None:require(store.direct(q['wrappers'][phase])==paths['wrapper'],'actual wrapper differs from planned root')
 if q.get('wrapper_waits',{}).get(phase) is not None:require(store.direct(q['wrapper_waits'][phase]['path']).parent==paths['parent'],'actual parent wait differs from planned root')
 return paths

def unattempted_observation(q,root,phase):
 paths=capsule_authority_paths(root,phase)+list(reservation_paths(q,root,phase).values())
 born=[str(p) for p in paths if os.path.lexists(p)]
 return {'all_absent':not born,'checked_paths':[str(p) for p in paths],'born_paths':born,'qualification':'fresh absence of all declared fixed authority and root reservations; not lifetime absence or admission'}

def observed_phase(root,phase,release):
 identity=IDS[phase];base=root/'research_runs'/identity;names=('claim.json','complete.json','failed.json');retained={}
 for name in names:
  p=base/name
  if p.exists():retained[name]={'path':str(p),'sha256':digest(store.read(p))}
 outputs=base/'outputs';actual=sorted(p.name for p in outputs.iterdir()) if outputs.is_dir() else None
 expected=None
 if release is not None:
  registration=metadata(root,release['registration']['path']);require(identity in registration['experiments'],'selected phase absent from original registration');expected=registration['experiments'][identity]['outputs']
 born=[str(path) for path in capsule_authority_paths(root,phase) if os.path.lexists(path)]
 status=('unclaimed_partial' if born else 'not_observed') if not retained else 'unclaimed_partial' if 'claim.json' not in retained else 'conflicting_original_terminals' if 'complete.json' in retained and 'failed.json' in retained else 'failed_terminal_present_unverified' if 'failed.json' in retained else 'complete_terminal_present_unverified' if 'complete.json' in retained else 'claimed_partial_no_terminal'
 return {'phase':phase,'identity':identity,'original_lifecycle_observation':status,'original_receipts':retained,'born_capsule_namespaces':born,'registered_outputs':expected,'protocol_outputs':OUTPUTS[phase],'present_output_names':actual,'absent_registered_outputs':None if expected is None else sorted(set(expected)-set(actual or [])),'unavailable_registered_output_names':None if expected is None else sorted(set(expected)-set(actual or [])),'scientific_authentication':None,'wrapper_authentication':None,'cleanup':None,'numerical_results_synthesized':False}

def cleanup_observation(root,phase,wrapper):
 identity=IDS[phase];base='research_artifacts/onchain-paper-replication-2026-09-24/runs/'+identity;required=[base+'/launch.json',base+'/owner.json',base+'/guard/final.json',base+'/guard/cpu_ready.json',base+'/guard/child_exit.json','proof_outer/'+identity+'/supervisor.json'];missing=[p for p in required if not (root/p).exists()]
 if missing:return {'status':'unresolved','missing_original_receipts':missing,'termination_attempted':False}
 launch=metadata(root,required[0],8192);owner=metadata(root,required[1],8192);guard=metadata(root,required[2],65536);ready=metadata(root,required[3],65536);child=metadata(root,required[4],65536);outer=metadata(root,required[5],8192)
 require(guard['owner_identity']==owner and all(owner[k]==v for k,v in launch.items()) and launch['supervisor_pid']==outer['pid'] and launch['experiment']==identity,'original cleanup owner/launch identity differs')
 pids={launch['supervisor_pid'],owner['monitor_pid'],ready['pid'],child['workload_pid']}
 starts={'monitor':{'pid':owner['monitor_pid'],'start_ticks':owner['monitor_start_ticks']},'job_launch':{'pid':outer['pid'],'start_ticks':outer['ticks']}}
 for ns in ('proof_supervise','proof_outer'):
  p=root/ns/identity/('child.json' if ns=='proof_supervise' else 'supervisor.json')
  if p.exists():v=json.loads(store.read(p,8192));pids.add(v['pid']);starts[ns]=v
 if wrapper is not None:
  p=wrapper/'child.json'
  if p.exists():v=json.loads(store.read(p,8192));pids.add(v['pid']);starts['root_wrapper_child']=v
  p=wrapper/'intent.json'
  if p.exists():pids.add(json.loads(store.read(p))['parent_pid'])
 require(all(type(p)is int and p>1 for p in pids),'original PID types differ');present=sorted(p for p in pids if Path('/proc',str(p)).exists());group=Path(guard['cgroup']);require(group.is_relative_to('/sys/fs/cgroup') and group.name==guard['unit'] and re.fullmatch(r'onchain-replication-[0-9a-f]{32}\.service',guard['unit']),'original cgroup path differs')
 absent=not group.exists();ok=guard['cleanup_verified'] is True and guard['cleanup_unit_properties']['ActiveState'] in ('inactive','failed') and guard['cleanup_unit_properties']['SubState'] in ('dead','failed') and not present and absent
 return {'status':'original-cleanup-observed' if ok else 'unresolved','recorded_pids':sorted(pids),'present_or_reused_pids':present,'original_start_receipts':starts,'original_cgroup':str(group),'cgroup_absent':absent,'original_guard_sha256':digest(store.read(root/required[2],65536)),'termination_attempted':False}

def wrapper_authentication(q,root,phase,wrapper,release):
 require(wrapper is not None and q['wrapper_waits'][phase] is not None,'actual root wrapper/wait evidence missing');wait=json.loads(reference(q['wrapper_waits'][phase]));intent=json.loads(store.read(wrapper/'intent.json'));seal=json.loads(store.read(wrapper/'tail-complete.json',8192));observation=json.loads(store.read(wrapper/'observation.json'));identity=IDS[phase]
 require(set(wait)=={'schema_version','identity','source','wrapper_pid','wrapper_exit_code','command','request','output_root'} and type(wait['schema_version'])is int and wait['schema_version']==1,'exact actual parent-wait record required')
 require(wait['identity']==identity and wait['source']==release['source'] and wait['wrapper_pid']==intent['parent_pid'] and type(wait['wrapper_exit_code'])is int and wait['wrapper_exit_code']==0 and not Path('/proc',str(wait['wrapper_pid'])).exists(),'actual wrapper wait/source/PID differs')
 parent=store.direct(q['wrapper_waits'][phase]['path']).parent;parent_intent=json.loads(store.read(parent/'intent.json'));parent_child=json.loads(store.read(parent/'child.json',8192))
 require(q['parent_sources'][phase] is not None,'reviewed actual parent source pin required');reference(q['parent_sources'][phase])
 require(not (parent/'failure.json').exists(),'original parent failure revokes whole-wrapper success')
 require(parent_intent['kind']=='actual-root-parent-intent-not-research-claim' and parent_intent['source']==wait['source'] and parent_intent['identity']==identity and parent_intent['command']==wait['command'] and parent_intent['request']==wait['request'] and parent_intent['cwd']==str(root) and parent_intent['python']==sys.executable and parent_intent['file_limit']==[MAX,MAX],'actual parent intent differs')
 require(parent_child['pid']==wait['wrapper_pid'] and parent_child['command']==wait['command'] and type(parent_child['start_ticks'])is str and parent_child['start_ticks'].isdigit() and int(parent_child['start_ticks'])>0,'actual parent child identity differs')
 require(type(parent_intent['parent_pid'])is int and parent_intent['parent_pid']>1 and not Path('/proc',str(parent_intent['parent_pid'])).exists(),'original parent PID absent/reused uncertainty')
 command_document=json.loads(reference(parent_intent['command_document']));require(command_document['argv']==wait['command'] and command_document['request']==wait['request'] and command_document['cwd']==str(root) and command_document['allowed_identity']==identity,'actual parent original command document differs')
 require(wait['request']==intent['request'] and wait['output_root']==str(wrapper),'wrapper original request/output differs');request=json.loads(reference(wait['request']));require(request['source']==release['source'] and request['phase']==phase and request['capsule']==str(root) and request['release']==q['releases'][phase],'actual root request release/phase differs')
 require(type(wait['command'])is list and len(wait['command'])==7 and wait['command'][0]==sys.executable and wait['command'][1]=='-B' and wait['command'][3:]==['--request',wait['request']['path'],'--request-sha256',wait['request']['sha256']],'actual wrapper command differs')
 require(digest(store.read(wait['command'][2]))=='3eb3c7f578c7b1308992cda0d8f3bea7ca98ed42ae97ad578590e7e993b4ad6a','accepted wrapper02 source differs')
 require(seal['kind']=='root-tail-complete-not-child-terminal' and seal['identity']==identity and seal['requires_actual_wrapper_exit0'] is True and seal['failure_markers_revoke_this_observation'] is True and observation['identity']==identity and observation['source']==release['source'] and observation['requires_root_tail_complete'] is True and observation['result'] is not None,'root success tail differs')
 require(not any((wrapper/n).exists() for n in ('failure.json','late-failure.json','tail-write-failure.json')),'root additive failure revokes success');return {'status':'original-wrapper-exit0-and-tail-authenticated','wait':q['wrapper_waits'][phase],'seal_sha256':digest(store.read(wrapper/'tail-complete.json',8192))}

def authenticate_lifecycle(root,sources,phase,release):
 require(release is not None,'original release required for lifecycle join');identity=IDS[phase];directory=root/'research_runs'/identity
 verifier=load('retention_structural_verifier',root/'tradingagents/research/verify.py',sources['tradingagents/research/verify.py']);actual=verifier.verify_run(directory);claim=json.loads(store.read(directory/'claim.json'))
 require(claim['source']==release['source'] and claim['registration']==release['registration']['path'] and claim['registration_sha256']==release['registration']['sha256'],'original lifecycle release differs')
 require(claim['experiment']['source_files']==sources and claim['family']['attempt_budget']==2 and claim['family']['prior_attempts']==0,'original lifecycle source/family differs')
 terminal='complete.json' if actual['status']=='complete' else 'failed.json'
 return {'status':actual['status'],'verification':'actual pinned verify_run structural hashes only; no scientific completion inferred','claim_sha256':digest(store.read(directory/'claim.json')),'terminal_sha256':digest(store.read(directory/terminal)),'actual_output_count':actual['output_count'],'registered_cells':claim['experiment']['cells'],'unavailable_cell_count':actual['unavailable_count'] if actual['status']=='complete' else None,'failed_cell_count_not_synthesized':True}

def authenticate_phase(q,root,sources,raw_api,api,phase,release):
 require(release is not None,'actual phase release missing');identity=IDS[phase]
 if phase=='materialize':
  retained=api.authenticated_materialization(root,raw_api.ref(root,'proof_outer/'+identity+'/accepted.json',kind='metadata'),raw_api.ref(root,'proof_supervise/'+identity+'/exit.json',kind='metadata'));ctx=retained['context'];require(ctx['release']==release,'original materialization release differs');result=retained['observed']
 else:
  retained=authenticate_closed_comparison(root,release,raw_api.ref(root,'proof_outer/'+identity+'/accepted.json',kind='metadata'),raw_api.ref(root,'proof_supervise/'+identity+'/exit.json',kind='metadata'),api);ctx=retained['context'];result=retained['observed']
 require(ctx['sources']==sources,'original exact195 source map differs');runtime=api.module('retention_runtime_'+phase,root/'proof_tools/runtime_gate01.py',sources['proof_tools/runtime_gate01.py']);runtime.check(root,ctx['runtime']);return result

def capture_external(q,directory):
 """Finite referenced metadata closure; never recursively reads arbitrary paths."""
 directory.mkdir(exist_ok=False);pending=[q];seen={};records=[];total=0
 while pending:
  value=pending.pop()
  if type(value)is list:
   require(len(value)<=32768,'metadata list bound');pending.extend(value);continue
  if type(value)is not dict:continue
  if set(value)=={'path','sha256'} and type(value['path'])is str and Path(value['path']).is_absolute():
   key=(value['path'],value['sha256'])
   if key in seen:continue
   require(len(records)<1024,'external metadata reference bound');raw=reference(value);total+=len(raw);require(total<=32*1024**2,'external metadata aggregate bound')
   name=f"reference-{len(records):04d}";source=Path(value['path']);row={'signature':store.sig(source.lstat()),'mode':source.stat().st_mode&0o777,'bytes':len(raw)}
   got=store.copy_file(source,directory/name,row,time.monotonic()+10);require(got==value['sha256'],'external reference changed during copy');seen[key]=name;records.append({'original':value,'retained':name,'sha256':got,'bytes':len(raw)})
   try:decoded=json.loads(raw)
   except (ValueError,UnicodeDecodeError):decoded=None
   if decoded is not None:pending.append(decoded)
  else:pending.extend(value.values())
 store.write(directory,'reference-index.json',{'schema_version':1,'references':records,'scope':'all bounded absolute path/SHA metadata refs recursively reachable from request; complete recovery trees are separately retained inputs, not duplicated here'})
 return records

def failure_observation(phase,error):
 return {'phase':phase,'identity':IDS[phase],'original_lifecycle_observation':'unverified','observation_error_type':type(error).__name__,'original_receipts':None,'registered_outputs':None,'protocol_outputs':OUTPUTS[phase],'present_output_names':None,'absent_registered_outputs':None,'unavailable_registered_output_names':None,'scientific_authentication':None,'wrapper_authentication':None,'cleanup':None,'numerical_results_synthesized':False}

def retain_unverified(q,error):
 """Independent byte retention after an ordinary source/authentication refusal.
 No selected capsule helper is imported here and no positive authority emitted.
 """
 root=store.direct(q['root']);destination=store.direct(q['destination']);require(not destination.is_relative_to(root) and not root.is_relative_to(destination),'independent retention root required');destination.mkdir(exist_ok=False);data=destination/'data';data.mkdir();members=destination/'members';members.mkdir();indexes={};absent=[]
 try:
  trees={'capsule':(root,GIB)}
  for phase in IDS:
   if 'reservation_roots' in q:
    paths=reservation_paths(q,root,phase)
   else:
    paths={'wrapper':None if q['wrappers'][phase] is None else store.direct(q['wrappers'][phase]),'parent':None if q['wrapper_waits'][phase] is None else store.direct(q['wrapper_waits'][phase]['path']).parent}
   for role,path in paths.items():
    if path is not None and os.path.lexists(path):trees[role+'-'+phase]=(path,(32 if role=='wrapper' else 16)*1024**2)
    else:absent.append(role+'-'+phase)
  for name,(path,limit) in trees.items():indexes[name]=store.pages(members/name,store.snapshot(path,data/name,limit=limit))
  outcomes={phase:{'identity':identity,'strict_scientific_disposition':'FAILED_OR_UNVERIFIED','source_authentication':'refused','error_type':type(error).__name__,'numerical_results_synthesized':False} for phase,identity in IDS.items()}
  report={'schema_version':1,'source':q.get('source'),'root':str(root),'outcomes':outcomes,'byte_retention_status':'complete-original-byte-copy','source_authentication':'refused','external_reference_authentication':'not_performed','absent_roots':absent,'member_pages':indexes,'tree_root_modes':{name:(data/name).stat().st_mode&0o777 for name in indexes},'paper_financial_completion':False,'numerical_arrays_decoded':False,'original_receipts_modified':False,'remote_recovery_proved':False}
  store.write(destination,'request.json',q);store.write(destination,'collection.json',report);return report
 except BaseException as primary:
  try:store.write(destination,'collection-failed.json',{'schema_version':1,'error_type':type(primary).__name__,'partial_archive_retained':True,'no_retry_same_destination':True})
  except BaseException as later:io._cleanup((lambda:(_ for _ in ()).throw(later),),primary=primary)
  raise

def collect(q):
 try:root,sources,raw_api,api=source_context(q)
 except Exception as error:
  if isinstance(error,(MemoryError,RecursionError)):raise
  return retain_unverified(q,error)
 destination=store.direct(q['destination']);require(not destination.is_relative_to(root) and not root.is_relative_to(destination),'independent collection root required');destination.mkdir(exist_ok=False);store.fsync_dir(destination.parent);data=destination/'data';data.mkdir();outcomes={};primary=None;copies={};absent=[]
 try:
  observed_roots={'capsule':(root,GIB)}
  for phase in IDS:
   for role,path in reservation_paths(q,root,phase).items():
    if os.path.lexists(path):observed_roots[role+'-'+phase]=(path,(32 if role=='wrapper' else 16)*1024**2)
  before={name:(store.sig(path.stat()),store.census(path,limit,time.monotonic()+120)) for name,(path,limit) in observed_roots.items()}
  for phase in IDS:
   release=None;wrapper=None
   try:
    release=None if q['releases'][phase] is None else json.loads(reference(q['releases'][phase]));wrapper=None if q['wrappers'][phase] is None else store.direct(q['wrappers'][phase]);value=observed_phase(root,phase,release)
   except Exception as error:
    if isinstance(error,(MemoryError,RecursionError)):raise
    value=failure_observation(phase,error)
   outcomes[phase]=value;value['reservation_observation']=unattempted_observation(q,root,phase)
   for key,fn in [('lifecycle_authentication',lambda:authenticate_lifecycle(root,sources,phase,release)),('scientific_authentication',lambda:authenticate_phase(q,root,sources,raw_api,api,phase,release)),('wrapper_authentication',lambda:wrapper_authentication(q,root,phase,wrapper,release)),('cleanup',lambda:cleanup_observation(root,phase,wrapper))]:
    try:value[key]=fn()
    except Exception as e:
     if isinstance(e,(MemoryError,RecursionError)):raise
     value[key]={'status':'unverified','error_type':type(e).__name__,'missing_or_failed_original_evidence':True}
   value['strict_scientific_disposition']=('MATERIALIZATION_COMPLETE_SCIENCE_PENDING' if phase=='materialize' else 'SCIENTIFIC_COMPARISON_COMPLETE') if 'observation_error_type' not in value and value['scientific_authentication'].get('status')=='authenticated' and value['wrapper_authentication'].get('status')=='original-wrapper-exit0-and-tail-authenticated' and value['cleanup'].get('status')=='original-cleanup-observed' else ('FAILED_AUTHENTICATED_TERMINAL' if value['cleanup'].get('status')=='original-cleanup-observed' else 'FAILED_AUTHENTICATED_TERMINAL_CLEANUP_UNRESOLVED') if value['lifecycle_authentication'].get('status')=='failed' else 'UNAVAILABLE_OR_INCOMPLETE_TERMINAL' if value['lifecycle_authentication'].get('unavailable_cell_count') else 'NOT_ATTEMPTED_OBSERVED' if value['original_lifecycle_observation']=='not_observed' and wrapper is None and unattempted_observation(q,root,phase)['all_absent'] else 'FAILED_OR_UNVERIFIED'
  external=capture_external(q,data/'external-evidence');copies['external-evidence']=store.census(data/'external-evidence',32*1024**2,time.monotonic()+120)
  copies['external-evidence']=[{k:v for k,v in row.items() if k!='signature'}|({'sha256':store.hash_file(data/'external-evidence'/row['path'],row,time.monotonic()+10)} if row['kind']=='file' else {}) for row in copies['external-evidence']]
  copies['capsule']=store.snapshot(root,data/'capsule',limit=GIB)
  for phase in IDS:
   for role,path in reservation_paths(q,root,phase).items():
    name=role+'-'+phase
    if not os.path.lexists(path):absent.append(name)
    else:copies[name]=store.snapshot(path,data/name,limit=(32 if role=='wrapper' else 16)*1024**2)
  for name,(path,limit) in observed_roots.items():require(before[name]==(store.sig(path.stat()),store.census(path,limit,time.monotonic()+120)),'original evidence changed across authentication/retention')
  require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True,timeout=10).strip()==q['source'],'source freeze changed while collecting')
  for path,h in sources.items():require(digest(store.read(root/path))==h,'source changed while collecting')
  page_root=destination/'members';page_root.mkdir();indexes={name:store.pages(page_root/name,rows) for name,rows in copies.items()}
  report={'schema_version':1,'source':q['source'],'root':str(root),'outcomes':outcomes,'byte_retention_status':'complete-original-byte-copy','absent_roots':absent,'member_pages':indexes,'tree_root_modes':{name:(data/name).stat().st_mode&0o777 for name in indexes},'external_evidence_count':len(external),'paper_financial_completion':False,'numerical_arrays_decoded':False,'original_receipts_modified':False,'remote_recovery_proved':False}
  store.write(destination,'collection.json',report);store.write(destination,'request.json',q);return report
 except BaseException as e:
  primary=e
  try:store.write(destination,'collection-failed.json',{'schema_version':1,'error_type':type(e).__name__,'partial_archive_retained':True,'remote_recovery_proved':False,'no_retry_same_destination':True})
  except BaseException as later:io._cleanup((lambda:(_ for _ in ()).throw(later),),primary=primary)
  raise

def verify_recovery(original,recovered,expected_collection_sha):
 original=store.direct(original);recovered=store.direct(recovered);require(original!=recovered and not original.is_relative_to(recovered) and not recovered.is_relative_to(original),'distinct actual recovery roots required');require(not (original/'collection-failed.json').exists() and not (recovered/'collection-failed.json').exists(),'failed collection cannot prove complete recovery');a=store.read(original/'collection.json');b=store.read(recovered/'collection.json');require(a==b and digest(a)==expected_collection_sha,'actual original/recovered collection differs');report=json.loads(a);require(report['byte_retention_status']=='complete-original-byte-copy','partial collection not recovery-complete');results={}
 for name,refs in report['member_pages'].items():
  rows=[]
  for ref in refs:
   path='members/'+name+'/'+ref['path'];left=store.read(original/path,8192);right=store.read(recovered/path,8192);require(left==right and len(left)==ref['bytes'] and digest(left)==ref['sha256'],'actual recovered member page differs');rows.extend(json.loads(left))
  limit=GIB if name=='capsule' else 32*1024**2
  require((original/'data'/name).stat().st_mode&0o777==report['tree_root_modes'][name]==(recovered/'data'/name).stat().st_mode&0o777,'recovered root mode differs')
  results[name]={'original':store.verify_tree(original/'data'/name,rows,limit=limit),'recovered':store.verify_tree(recovered/'data'/name,rows,limit=limit)}
 # Whole archive metadata membership is also exact; no later/omitted receipt can
 # hide behind a verified data-only subset. Network provenance is root supplied.
 deadline=time.monotonic()+120
 full=store.census(original,2*GIB,deadline)
 full=[{k:v for k,v in r.items() if k!='signature'}|({'sha256':store.hash_file(original/r['path'],r,deadline)} if r['kind']=='file' else {}) for r in full]
 store.verify_tree(recovered,full,limit=2*GIB)
 return {'schema_version':1,'status':'complete-actual-recovered-byte-equality','collection_sha256':expected_collection_sha,'roots':results,'network_transfer_performed':False,'external_provider_provenance_requires_root_evidence':True,'scientific_dispositions':{k:v['strict_scientific_disposition'] for k,v in report['outcomes'].items()}}

def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True);c=sub.add_parser('collect');c.add_argument('--request',required=True);c.add_argument('--request-sha256',required=True);v=sub.add_parser('verify-recovery');v.add_argument('--original',required=True);v.add_argument('--recovered',required=True);v.add_argument('--collection-sha256',required=True);a=p.parse_args()
 if a.mode=='collect':result=collect(json.loads(reference({'path':a.request,'sha256':a.request_sha256})))
 else:result=verify_recovery(a.original,a.recovered,a.collection_sha256)
 print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
