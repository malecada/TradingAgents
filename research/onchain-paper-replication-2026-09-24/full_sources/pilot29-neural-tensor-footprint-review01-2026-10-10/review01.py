"""Independent finite header/source arithmetic; no payload/scientific imports."""
import ast,builtins,collections,hashlib,json,math,os,resource,signal,stat,struct,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=P.parents[3];C=F/'pilot29-neural-tensor-footprint01-2026-10-10'
resource.setrlimit(resource.RLIMIT_AS,(384*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(15,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(20);assert os.sched_getaffinity(0)=={3}
start=time.perf_counter_ns();checks=[];refs={};observations=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def ok(n,v=True):assert v,n;checks.append(n)
def read(p,limit=1048576):
 p=Path(p);fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:
  st=os.fstat(fd);assert stat.S_ISREG(st.st_mode) and 0<st.st_size<=limit
  b=os.read(fd,st.st_size+1);assert len(b)==st.st_size
 finally:os.close(fd)
 refs[str(p.relative_to(R))]={'sha256':sha(b),'bytes':len(b)};return b
original_import=builtins.__import__
def guarded(name,*a,**kw):
 assert name.split('.')[0] not in {'numpy','torch','scipy','ctypes','array','tradingagents'},name
 return original_import(name,*a,**kw)
builtins.__import__=guarded
manifest=read(C/'MANIFEST01.json');ok('exact author manifest',sha(manifest)=='c9ae2cf222af485585f28421f026f0fdae0297245fe74470d3dcacf7d6e7fac3')
for n,v in json.loads(manifest)['files'].items():
 b=read(C/n);ok('author body '+n,len(b)==v['bytes'] and sha(b)==v['sha256'])
ok('exact report',sha((C/'REPORT.md').read_bytes())=='fdb8923a86aee755b5f35b257d132807aed2099388469215f89191ba5d12657a')
i=json.loads((C/'INPUTS01.json').read_bytes());h=json.loads((C/'GRAPH_HEADERS01.json').read_bytes());a=json.loads((C/'ARITHMETIC01.json').read_bytes())
def join(ref):
 b=read(R/ref['path']);ok('actual reference '+ref['path'],sha(b)==ref['sha256'] and len(b)==ref['bytes']);return b
for name in ('gate','binding','population'):join(i[name])
gate=json.loads((R/i['gate']['path']).read_bytes());exp=gate['experiments']['eth-paper-real-data-end-to-end-resource-20261009-29']
sourcepins=exp['source_files']
if isinstance(sourcepins,list):sourcepins={r['path']:r['sha256'] for r in sourcepins}
source_text={}
for ref in i['sources']:
 b=join(ref);entry=sourcepins[ref['path']];pin=entry['sha256'] if isinstance(entry,dict) else entry
 ok('actual29 source pin '+ref['path'],sha(b)==pin);source_text[Path(ref['path']).name]=b.decode()
for name,ref in i['inputs'].items():
 b=join(ref);ok('actual29 input '+name,any(v['path']==ref['path'] and v['sha256']==sha(b) for v in exp['inputs'].values()))
join(i['torch_from_numpy_documentation'])
pilot=json.loads((R/i['inputs']['pilot']['path']).read_bytes());pop=json.loads((R/i['population']['path']).read_bytes());binding=json.loads((R/i['binding']['path']).read_bytes());model=json.loads((R/i['inputs']['model']['path']).read_bytes());training=json.loads((R/i['inputs']['training']['path']).read_bytes())
ok('exact selected model execution',pilot['model_execution']==i['model_execution']=={'backend':'streamed-gat-mulsum-v1','block_edges':65536,'graph_activation_checkpointing':True,'schema_version':2})
ok('exact model/training metadata',model==i['model'] and training==i['training'])
canonical=json.dumps(pop,sort_keys=True,separators=(',',':')).encode();ok('canonical population binding',sha(canonical)==i['population_canonical_sha256']==binding['pilot_population_sha256'])
sequences=[r['graph_hashes'] for r in pop['resource_rows']];count=collections.Counter(x for row in sequences for x in row)
ok('population exact selected sequences',sequences==pilot['graph_sequences'] and len(sequences)==16 and all(len(r)==28 for r in sequences))
ok('448 references seven actual graph objects',dict(count)==i['graph_reference_counts'] and sum(count.values())==448 and len(count)==7 and set(count)==set(pilot['graph_inputs']))
ok('population plan and manifest binding',binding['plan_sha256']==i['inputs']['resource_population_plan']['sha256'] and pop['graph_manifest_hashes']==binding['graph_manifest_hashes'])
rows={r['graph_hash']:r for r in a['graphs']};totals=collections.Counter();largest=0
for graph in h['graphs']:
 key=graph['graph_hash'];n=graph['N'];e=graph['E'];role=pilot['graph_inputs'][key];mref=graph['manifest'];mbytes=join(mref);gm=json.loads(mbytes)
 ok('registered manifest '+key,role==graph['role'] and exp['inputs'][role]['path']==mref['path'] and exp['inputs'][role]['sha256']==sha(mbytes)==binding['graph_manifest_hashes'][graph['week']])
 ok('graph identity and week '+key,gm['graph_hash']==key and gm['metadata']['start_utc']==graph['week'])
 for name,shape in {'node_features':[n,4],'edge_index':[2,e],'edge_features':[e,2],'edge_aggregates':[e,2]}.items():
  rec=graph['headers'][name];path=R/rec['path'];fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
  try:
   before=os.fstat(fd);magic=os.read(fd,8);assert magic[:6]==b'\x93NUMPY' and magic[6:] in (b'\x01\x00',b'\x02\x00');width=2 if magic[6:]==b'\x01\x00' else 4
   prefix=os.read(fd,width);length=int.from_bytes(prefix,'little');assert 0<length<=10000
   header=os.read(fd,length);after=os.fstat(fd);raw=magic+prefix+header;parsed=ast.literal_eval(header.decode('latin1').strip())
  finally:os.close(fd)
  signature=lambda st:[getattr(st,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')]
  ok('header snapshot stable '+key+name,signature(before)==signature(after)==rec['file_stat_signature'])
  ok('only exact captured header '+key+name,len(raw)==rec['header_bytes'] and raw.hex()==rec['header_raw_hex'] and sha(raw)==rec['header_sha256'])
  ok('actual finite dtype/shape '+key+name,set(parsed)=={'descr','fortran_order','shape'} and list(parsed['shape'])==shape and parsed['fortran_order'] is False and parsed['descr']==('<i8' if name=='edge_index' else '<f8'))
  data=math.prod(shape)*8;registered=gm['arrays'][name]
  ok('registered extent/body reference only '+key+name,registered['path']==path.name and path.parent==R/Path(mref['path']).parent and registered['bytes']==before.st_size==len(raw)+data and data==rec['data_bytes_from_header'] and registered['sha256']==rec['registered_full_body_sha256'] and rec['full_body_sha256_verified_here'] is False)
  observations.append({'graph_hash':key,'member':name,'path':rec['path'],'bytes_read':len(raw),'header_sha256':sha(raw),'data_extent_from_header':data,'payload_read':False,'registered_full_body_sha256_unverified':registered['sha256']})
 row=rows[key];ok('graph row and U bounds '+key,(row['N'],row['E'])==(n,e) and row['U_range']==[e,e+n])
 vals={'mcm_float32_N32_mapped_bytes':128*n,'original_edge_index_int64_2E_bytes':16*e,'raw_numeric_graph_arrays_bytes':32*n+48*e,'mlp_N64_each_bytes':256*n,'mlp_N32_each_bytes':128*n}
 ok('independent graph arithmetic '+key,all(row[k]==v for k,v in vals.items()))
 for layer,heads,width,inputwidth in zip(row['layers'],(4,1),(16,32),(32,64),strict=True):
  expected={'heads':heads,'head_width':width,'input_width':inputwidth,'clean_NF_bytes':4*n*inputwidth,'h_NHD_bytes':4*n*heads*width,'out_NHD_bytes':4*n*heads*width,'source_score_target_score_maximum_denom_each_NH_bytes':4*n*heads,'e_numer_attention_each_UH_bytes_range':[4*v*heads for v in (e,e+n)],'source_target_each_int64_U_bytes_range':[8*v for v in (e,e+n)],'one_full_block_message_BHD_bytes':4*65536*heads*width,'proven_h_out_one_block_coexist_bytes':8*n*heads*width+4*65536*heads*width}
  ok('independent full layer arithmetic '+key+str(heads),layer==expected);largest=max(largest,expected['proven_h_out_one_block_coexist_bytes'])
 totals.update(N=n,E=e,raw_numeric_retained_bytes=vals['raw_numeric_graph_arrays_bytes'],mcm_mapped_payload_bytes=128*n,original_edge_index_bytes_included_in_raw=16*e)
ok('complete seven graph denominator',len(h['graphs'])==len(rows)==7 and set(rows)==set(count))
ok('independent totals',dict(totals)==a['totals'] and totals['N']==12999004 and totals['E']==18683284)
bound=totals['raw_numeric_retained_bytes']+largest
ok('conditional simultaneous lower bound',largest==1176703488 and bound==a['conservative_proven_simultaneous_storage_bytes']==2489469248 and a['bound_exceeds_6GiB'] is False and a['bound_exceeds_nominal_16GB'] is False)
# Additional live-source contract only, authenticated with selected gate; no
# graph loader or actual tensor is imported or called.
contractpath='tradingagents/research/onchain_replication/contracts.py';cb=read(R/contractpath);entry=sourcepins[contractpath];ok('selected GraphSnapshot contract',sha(cb)==(entry['sha256'] if isinstance(entry,dict) else entry));ct=cb.decode()
ok('retained immutable numeric bodies and duplicate-free contract',"np.frombuffer(array.tobytes(), dtype=array.dtype).reshape(array.shape)" in ct and "if _duplicate_edges(g.edge_index):" in ct)
sg=source_text['streamed_gat.py'];mo=source_text['model.py'];caller=source_text['real_pilot_import_caller.py'];loader=source_text['graph_store.py'];tr=source_text['real_pilot_training.py'];mm=source_text['compact_mcm_batched.py']
ok('distinct local simultaneous allocations',all(x in sg for x in ('out = torch.zeros_like(h)','messages = h.index_select(0, source[start:stop]) * attention[start:stop, :, None]','out.index_add_(0, target[start:stop], messages)','del messages')))
ok('normalized edge vectors and expanded view',all(x in sg for x in ('source,target=edge_index','source=source[keep];target=target[keep]','source=torch.cat([source,nodes]);target=torch.cat([target,nodes])','index=target[:,None].expand_as(e)')))
ok('retained whole graph raw arrays through neural call',all(x in caller for x in ('graphs = {}','resident=True','graphs[key] = graph','for (key,g), result in zip(graphs.items(),targets,strict=True):','edges = torch.from_numpy(g.edge_index)','mcm = torch.from_numpy(result.matrix)','training_helper.run_one_update(')))
ok('resident storage allocated and unicode converted',"value=np.empty(shape,dtype=dtype" in loader and "arrays['node_ids']=tuple(arrays['node_ids'].tolist())" in loader)
ok('read-only mapped MCM reused',"mmap.mmap(matrix_fd,0,access=mmap.ACCESS_READ)" in mm and "np.ndarray((start['rows'],32),dtype='<f4',buffer=mapped)" in mm)
ok('within-forward identity cache and checkpoint',all(x in mo for x in ('rows=[];encoded_graphs={}','key=id(graph)','if key not in encoded_graphs:','use_reentrant=False,preserve_rng_state=True')))
ok('CPUf32 no fixed-input gradients',all(x in tr for x in ('not tensor.requires_grad','mcm.dtype == torch.float32','edges.dtype == torch.int64',"p.dtype == torch.float32","selected_checkpointing")))
ok('resource update not100epochs and checkpoint file cap',"steps = 1" in tr and "'financial_fit_complete':False" in tr and pilot['max_checkpoint_bytes']==4194304 and training['epochs']==100)
ok('no prohibited imports',not {'numpy','torch','scipy','ctypes','array','tradingagents'}&set(sys.modules))
ok('author manifest unchanged',read(C/'MANIFEST01.json')==manifest)
r={'disposition':'ACCEPT_BOUNDED_SOURCE_HEADER_ARITHMETIC_ONLY','checks':checks,'check_count':len(checks),'body_references':refs,'actual_header_observations':observations,'header_files':len(observations),'header_bytes_read':sum(x['bytes_read'] for x in observations),'totals':dict(totals),'largest_local_coexistence_bytes':largest,'conditional_storage_lower_bound_bytes':bound,'payload_integrity_verified':False,'rss_measured':False,'complete_peak_estimated':False,'actual_fit_established':False,'numerical_native_execution':False,'elapsed_ns':time.perf_counter_ns()-start,'peak_reviewer_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(P/'RESULT01.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ('disposition','check_count','header_files','header_bytes_read','conditional_storage_lower_bound_bytes','elapsed_ns')}))
