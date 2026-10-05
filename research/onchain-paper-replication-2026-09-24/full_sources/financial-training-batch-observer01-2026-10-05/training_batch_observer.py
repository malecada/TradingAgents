"""Opt-in native TRAINING metadata observation; never reads tensor values or labels.

Only the genuine resident compact feature route is supported. Events contain
scalar identities, not strong/weak references to graph/tensor/parent objects.
Pointer equality has meaning inside one event only; no lifetime/saving claim.
"""
import hashlib, json, re, shutil, threading
from datetime import datetime, timedelta
from pathlib import Path
ROLE='training_batch_observer'
FILE=4*1024**2
def require(v,m):
 if not v:raise ValueError(m)
def encode(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def utc(v):
 require(type(v)is str,'date string');d=datetime.fromisoformat(v.replace('Z','+00:00'));require(d.tzinfo is not None and d.utcoffset()==timedelta(0),'UTC required');return d
def week(day):
 d=utc(day+'T00:00:00Z');end=(d-timedelta(days=d.weekday())).replace(hour=0,minute=0,second=0,microsecond=0)
 return (end-timedelta(days=7)).isoformat().replace('+00:00','Z')
def project(row):
 # Explicit whitelist: never asdict(), vars(), prices, labels, targets or test rows.
 return {'decision_at':row.decision_at,'input_dates':list(row.input_dates),'graph_hashes':list(row.graph_hashes),'graph_available_at':list(row.graph_available_at)}
def excluded(examples):
 return [{'decision_at':x['decision_at'],'reason':x['reason'],'partition':'train'} for x in examples.exclusions if x['partition']=='train']
def tensor_metadata(t):
 # Called only after genuine native authority; imports never occur in scalar controls.
 import torch
 storage=None
 try:
  require(type(t)is torch.Tensor,'exact tensor required');storage=t.untyped_storage()
  return {'tensor_object_id':id(t),'storage_pointer':storage.data_ptr(),'storage_bytes':storage.nbytes(),'device':str(t.device),'dtype':str(t.dtype),'shape':list(t.shape),'stride':list(t.stride()),'storage_offset':t.storage_offset()}
 finally:t=None;storage=None
def snapshot(indices,rows,inputs,*,tensor_reader=tensor_metadata):
 """Pure finite mechanics, not admission. Objects are borrowed only for this call."""
 graph=None;sequence=None;row=None;value=None;selected=None
 try:
  require(type(indices)is list and 0<len(indices)<=16 and all(type(i)is int for i in indices),'batch16 index bound')
  require(indices==list(range(indices[0],indices[0]+len(indices))) and 0<=indices[0] and indices[-1]<len(rows),'consecutive eligible rows')
  require(type(inputs)is dict and set(inputs)=={'prices','graph_sequences'},'unmasked graph training path only')
  selected=inputs['graph_sequences'];require(len(selected)==len(indices),'batch row count')
  projections=[];uses=[];objects={};hash_objects={};weeks=[];prior=None
  for ordinal,(index,sequence) in enumerate(zip(indices,selected,strict=True)):
   row=rows[index];meta=project(row);decision=utc(meta['decision_at'])
   require(prior is None or prior<decision,'chronological training rows');prior=decision
   require(len(sequence)==len(meta['input_dates'])==len(meta['graph_hashes'])==len(meta['graph_available_at'])==28,'original28 lookback')
   expected=[(decision-timedelta(days=i)).date().isoformat() for i in range(28,0,-1)]
   require(meta['input_dates']==expected,'original complete daily lookback')
   projections.append({'eligible_index':index,**meta})
   for step,(graph,day,h,available) in enumerate(zip(sequence,meta['input_dates'],meta['graph_hashes'],meta['graph_available_at'],strict=True)):
    require(type(h)is str and re.fullmatch('[0-9a-f]{64}',h)is not None,'graph hash')
    require(utc(available)<=utc(day+'T00:00:00Z')+timedelta(days=1),'late selected week')
    require(type(graph)is dict and set(graph)=={'mcm','edge_index'},'exact graph dictionary; no missing/masked step')
    identity=id(graph);hash_objects.setdefault(h,set()).add(identity)
    if identity not in objects:
     objects[identity]={'graph_object_id':identity,'mcm':tensor_reader(graph['mcm']),'edge_index':tensor_reader(graph['edge_index'])}
    w=week(day)
    if w not in weeks:weeks.append(w)
    uses.append({'row':ordinal,'step':step,'graph_hash':h,'week':w,'graph_object_id':identity})
  gaps=[]
  for left,right in zip(projections,projections[1:]):
   n=(utc(right['decision_at'])-utc(left['decision_at'])).days-1
   if n>0:gaps.append({'after':left['decision_at'],'before':right['decision_at'],'calendar_days_missing':n})
  return {'training_rows':projections,'uses':uses,'unique_graph_objects':list(objects.values()),'hash_to_object_ids':{h:sorted(v) for h,v in hash_objects.items()},'ordered_week_union':weeks,'eligible_row_calendar_gaps':gaps,'epoch_cursor':None,'identity_scope':'single event; addresses may be recycled after return','values_or_labels_read':False}
 finally:
  graph=None;sequence=None;row=None;value=None;selected=None;inputs=None;rows=None;tensor_reader=None
def authority(run,features):
 from ..lifecycle import ResearchRun
 require(type(run)is ResearchRun,'genuine existing ResearchRun required')
 source=Path(__file__).resolve();require(source.is_relative_to(run.admission.root),'observer must load from actual admitted source root')
 name=source.relative_to(run.admission.root).as_posix();require(name in run.admission.experiment['source_files'],'observer source must be in genuine source map')
 from .compact_native_features import _Features
 from .compact_terminal import Receipt
 from .compact_owner import Owner
 from .matching_owner import Binding
 from .provenance import thaw
 terminal=owner=bound=None
 try:
  require(type(run)is ResearchRun and type(features)is _Features,'genuine resident native financial route required; cold/detached unsupported')
  terminal=features._terminal;require(type(terminal)is Receipt,'genuine compact terminal')
  owner=terminal._owner;require(type(owner)is Owner,'genuine compact Owner')
  bound=owner.bound;require(type(bound)is Binding and bound._run is run and owner._run is run,'genuine same-run Binding')
  terminal.check();bound._guard();run._active();run._check_source()
  require(terminal.record['resident_originals_retained'] is True,'resident-parent declaration changed')
  return {'owner_id':owner.identity,'binding_sha256':owner._binding_sha256,'terminal_record_sha256':sha(encode(thaw(terminal.record))),'resident_originals_retained':True,'parent_population_object_census':None,'parent_retention_basis':'genuine checked resident terminal; no heap/alias census'}
 finally:terminal=None;owner=None;bound=None;features=None;run=None
def prepare(run,cell,provenance,examples,feature_binding,training_config,features):
 """Called after existing evaluate_cell admission and component-byte validation."""
 if ROLE not in run.admission.inputs:return None
 from .provenance import thaw
 from .workflow_storage import StorageWatch
 require(training_config['batch_size']==16 and training_config['shuffle'] is False,'original batch16 chronological training')
 authority(run,features)
 raw=run.read_input(ROLE);require(len(raw)<=65536,'observer policy bound');p=json.loads(raw)
 require(set(p)=={'schema_version','cell_id','source_commit','train_hash','fold_hash','metadata_input','call_ordinals','outputs','max_event_bytes','max_total_bytes'} and p['schema_version']==1,'observer policy schema')
 require(p['cell_id']==cell==provenance['cell_id'] and p['source_commit']==run.admission.source and p['train_hash']==examples.train_hash and p['fold_hash']==examples.fold_hash,'observer exact current cell/population')
 calls=p['call_ordinals'];outputs=p['outputs'];require(type(calls)is list and 0<len(calls)<=32 and all(type(x)is int and 0<=x<1000000 for x in calls) and calls==sorted(set(calls)),'finite fixed selected training calls')
 require(type(outputs)is list and len(outputs)==len(calls) and len(set(outputs))==len(outputs) and all(type(x)is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',x) for x in outputs) and set(outputs)<=set(run.admission.experiment['outputs']),'exact registered output names')
 require(type(p['max_event_bytes'])is int and 0<p['max_event_bytes']<=256*1024 and type(p['max_total_bytes'])is int and 0<p['max_total_bytes']<=FILE and len(calls)*p['max_event_bytes']<=p['max_total_bytes'],'finite event/total reservation')
 require(type(p['metadata_input'])is str and p['metadata_input'] in run.admission.inputs,'registered training-only metadata projection')
 rawmeta=run.read_input(p['metadata_input']);require(len(rawmeta)<=FILE,'projection4MiB');projection=json.loads(rawmeta)
 require(len(examples.train)<=2048 and len(examples.exclusions)<=8192,'finite metadata population')
 actual={'schema_version':1,'train_hash':examples.train_hash,'fold_hash':examples.fold_hash,'source_hashes':list(examples.source_hashes),'rows':[project(row) for row in examples.train],'exclusions':excluded(examples)}
 require(projection==actual,'actual training metadata/exclusions differ from admitted projection')
 require(len(encode(actual))<=FILE,'bounded training projection');job=json.loads(run.read_input('execution_job'));storage=job['resources']['storage_budget'];require(storage['root']==str(run.admission.root),'existing whole owned storage root')
 StorageWatch(run.admission.root,storage['limits']).check();require(shutil.disk_usage(run.admission.root).free>=10*1024**3,'10GiB floor')
 # Only scalars/JSON metadata and a lock survive. No graph/feature/tensor/parent references.
 return {'policy':p,'policy_sha256':run.admission.inputs[ROLE]['sha256'],'projection_sha256':run.admission.inputs[p['metadata_input']]['sha256'],'feature_binding_sha256':sha(encode(thaw(feature_binding))),'claim_sha256':run._claim_sha256,'source':run.admission.source,'identity':run.admission.experiment_id,'exclusions':actual['exclusions'],'storage':storage,'call':0,'bytes':0,'poisoned':False,'lock':threading.Lock()}
def observe(run,state,indices,rows,inputs,features):
 if state is None:return
 require(state['lock'].acquire(blocking=False),'concurrent observer')
 try:
  require(not state['poisoned'],'observer poisoned; no retry');call=state['call'];state['call']+=1;require(call<1000000,'finite observer calls')
  p=state['policy']
  if call not in p['call_ordinals']:return
  from .workflow_storage import StorageWatch
  from ..lifecycle import _encode
  require(run._claim_sha256==state['claim_sha256'] and run.admission.source==state['source'] and run.admission.experiment_id==state['identity'],'observer current claim/source')
  policy_raw=run.read_input(ROLE);projection_raw=run.read_input(p['metadata_input']);projection=json.loads(projection_raw)
  require(sha(policy_raw)==state['policy_sha256'] and json.loads(policy_raw)==p and sha(projection_raw)==state['projection_sha256'],'observer policy/projection current')
  require(json.loads(run.read_input('execution_job'))['resources']['storage_budget']==state['storage'],'original whole-storage policy current')
  watch=StorageWatch(run.admission.root,state['storage']['limits']);watch.check()
  context=authority(run,features);event=snapshot(indices,rows,inputs)
  require(event['training_rows']==[{'eligible_index':i,**projection['rows'][i]} for i in indices] and state['exclusions']==projection['exclusions'],'actual selected metadata still matches registered projection')
  event.update(schema_version=1,kind='training-batch-metadata-only',call_ordinal=call,source=state['source'],experiment=state['identity'],cell_id=p['cell_id'],train_hash=p['train_hash'],fold_hash=p['fold_hash'],policy_sha256=state['policy_sha256'],projection_sha256=state['projection_sha256'],feature_binding_sha256=state['feature_binding_sha256'],claim_sha256=state['claim_sha256'],authority=context,training_exclusions=state['exclusions'],sampled_calls=p['call_ordinals'],complete_population_census=False,capacity_or_saving_claim=False)
  raw=_encode(event);require(len(raw)<=p['max_event_bytes'] and state['bytes']+len(raw)<=p['max_total_bytes'],'metadata output reservation');state['bytes']+=len(raw)
  authority(run,features);require(shutil.disk_usage(run.admission.root).free>=10*1024**3,'prewrite10GiB floor');watch.check()
  run.write_json(p['outputs'][p['call_ordinals'].index(call)],event)
  watch.check();require(shutil.disk_usage(run.admission.root).free>=10*1024**3,'postwrite10GiB floor');authority(run,features)
 except BaseException:
  state['poisoned']=True
  raise
 finally:
  inputs=None;features=None;rows=None;run=None;state['lock'].release()
