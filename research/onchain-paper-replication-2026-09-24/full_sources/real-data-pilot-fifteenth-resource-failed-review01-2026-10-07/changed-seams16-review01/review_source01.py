"""Independent header/formula/policy/source checks only; no arrays or native launch."""
from pathlib import Path
import ast,hashlib,json,math,os,stat,struct,subprocess,types
R=Path.cwd();F=Path('research/onchain-paper-replication-2026-09-24/full_sources')
H=F/'real-data-pilot-fifteenth-resource-failed-review01-2026-10-07/changed-seams16-review01'
I=F/'real-data-pilot-index-capacity01-2026-10-07';M=F/'real-data-pilot-ram-candidate01-2026-10-07'
SOURCE='1f0894a2c15a1d544ba3ac6c35893dfe53068b6a';cache={}
def raw(p):
 p=Path(p)
 if p not in cache:
  q=R/p;s=q.lstat();assert q.resolve(strict=True)==q and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4*1024**2
  b=q.read_bytes();z=q.lstat();assert len(b)==s.st_size and (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns);cache[p]=b
 return cache[p]
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p)}
def read(p):return json.loads(raw(p))
def joined(r):assert sha(r['path'])==r['sha256'];return read(r['path'])
def write(n,v):
 p=H/n
 with p.open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
 return p
manifest=read(M/'MANIFEST01.json')
for n,r in manifest.items():assert sha(M/n)==r['sha256'] and len(raw(M/n))==r['bytes']
index_manifest=read(I/'SOURCE01.json')
for r in index_manifest['files']:assert sha(r['path'])==r['sha256'] and len(raw(r['path']))==r['bytes']
capacity=read(I/'CAPACITY01.json');g=joined(capacity['gate_ref']);inputs=next(iter(g['experiments'].values()))['inputs']
job=joined(inputs['execution_job']);desc=job['payload']['representation_jobs']['original32']['descriptor'];old=joined(inputs['mcm_policy']);new=read(I/'mcm_policy01.json')
assert desc['configs']['dictionary']['maximum_neighborhood_nodes']==capacity['maximum_neighborhood_nodes']==10000
assert desc['configs']['dictionary']['size']==32 and desc['configs']['dictionary']['hop_depth']==1
assert new['numeric']['edge_chunk']==old['numeric']['edge_chunk']==capacity['edge_chunk']==4096
assert old['numeric']['max_buffer_bytes']==1048576 and old['numeric']['max_numeric_bytes']==291030144
inverse=json.loads(json.dumps(new))
for k in ('max_buffer_bytes','max_numeric_bytes'):inverse['numeric'][k]=old['numeric'][k]
assert inverse==old
assert len(capacity['graphs'])==len(desc['resource_graph_inputs'])==7
count_joins={r['role']:r for r in capacity['count_joins']};independent=[];header_bytes=0
for row in capacity['graphs']:
 assert desc['resource_graph_inputs'][row['graph_hash']]==row['role'] and inputs[row['role']]==row['manifest']
 manifest=joined(row['manifest']);assert manifest['graph_hash']==row['graph_hash'] and manifest['metadata']['asset']=='ETH'
 shapes={}
 for name in ('node_features','edge_index','edge_features'):
  member=manifest['arrays'][name];p=R/Path(row['manifest']['path']).parent/member['path'];s=p.lstat()
  assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==member['bytes']
  with p.open('rb') as f:
   magic=f.read(8);assert magic[:6]==b'\x93NUMPY' and magic[6:] in (b'\x01\x00',b'\x02\x00')
   width=2 if magic[6:]==b'\x01\x00' else 4;sizebytes=f.read(width);length=int.from_bytes(sizebytes,'little');assert 0<length<=10000
   header=f.read(length);assert len(header)==length;observed=magic+sizebytes+header
   assert f.tell()==len(observed)
  z=p.lstat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
  h=ast.literal_eval(header.decode('latin1'));saved=row['headers'][name]
  assert set(h)=={'descr','shape','fortran_order'} and h['fortran_order'] is False
  assert h['descr']==('<i8' if name=='edge_index' else '<f8')
  assert list(h['shape'])==saved['shape'] and hashlib.sha256(observed).hexdigest()==saved['header_sha256']
  assert len(observed)==saved['header_bytes'] and len(observed)+math.prod(h['shape'])*8==member['bytes']==saved['member_bytes']
  assert member['sha256']==saved['member_sha256'];shapes[name]=h['shape'];header_bytes+=len(observed)
 n,nw=shapes['node_features'];ew,e=shapes['edge_index'];assert nw==4 and ew==2 and shapes['edge_features']==(e,2)
 count=joined(count_joins[row['role']]['count_ref']);joined(count_joins[row['role']]['evidence_ref'])
 assert count['rows']==n==row['nodes'] and row['edges']==e and count['graph_manifest_sha256']==row['manifest']['sha256']
 assert count['node_features_sha256']==manifest['arrays']['node_features']['sha256']
 # Algebraically simplified independent reconstruction of existing A + 2O.
 retained=16*e+16*n+16;additive=32*e+60*n+56+4096*160
 output=32*min(n,10000)+32*e;buffer=additive+2*output;mcm=128*n
 assert retained==row['retained_index_bytes'] and additive==row['index_additive_bytes'] and output==row['maximum_single_neighborhood_array_bytes'] and buffer==row['output_inclusive_buffer_bytes'] and mcm==row['mcm_output_bytes']
 independent.append({'graph_hash':row['graph_hash'],'nodes':n,'edges':e,'retained_index_bytes':retained,'index_additive_bytes':additive,'output_inclusive_buffer_bytes':buffer,'mcm_output_bytes':mcm})
assert header_bytes==2688
max_buffer=max(r['output_inclusive_buffer_bytes'] for r in independent);max_output=max(r['mcm_output_bytes'] for r in independent)
assert max_buffer==capacity['max_buffer_required']==new['numeric']['max_buffer_bytes']==439582708
assert max_output==capacity['max_output_required']==new['numeric']['max_output_bytes']==289981568
assert new['numeric']['max_numeric_bytes']==max_buffer+max_output==729564276
helper=types.ModuleType('independent_capacity');exec(compile(raw(I/'candidate/index_capacity.py'),str(I/'candidate/index_capacity.py'),'exec'),vars(helper))
assert helper.demand(1768268,2518332,32,16,4096,10000)['index_additive_bytes']==187338120>1048576
assert helper.demand(3,3,32,16,2,3)['output_inclusive_buffer_bytes']==1036
changes={};allowed={'job.py':{'resource_policy','worker'},'resources.py':{'assert_guarded_worker'},'matching_owner.py':{'_guard'},'real_pilot_import_caller.py':{'_amended_host_reserve','_finite_resources','execute'}}
for name,expected in allowed.items():
 oldbytes=raw(M/'baseline'/name);newbytes=raw(M/name)
 assert subprocess.run(['git','show',SOURCE+':tradingagents/research/onchain_replication/'+name],capture_output=True,check=True).stdout==oldbytes
 oldast=ast.parse(oldbytes);newast=ast.parse(newbytes)
 def by_name(tree):return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
 a,b=by_name(oldast),by_name(newast);changed={k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)};assert changed==expected
 def other(tree):return [ast.dump(n,include_attributes=False) for n in tree.body if not isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
 assert other(oldast)==other(newast);changes[name]={'baseline':ref(M/'baseline'/name),'candidate':ref(M/name),'changed_functions':sorted(changed)}
assert 'pilot_context=(admitted,job)' in raw(M/'job.py').decode() and 'pilot_context=(run.admission,job)' in raw(M/'real_pilot_import_caller.py').decode()
assert "if p['reserve_bytes']<3*resources.GIB else None" in raw(M/'matching_owner.py').decode()
assert "ad.ready or _read(ad,'execution_job')!=execution" in raw(M/'job.py').decode()
assert "live.get('memory_swap_max_bytes')!=0" in raw(M/'resources.py').decode()
rp=write('SOURCE_REVIEW01.json',{'schema_version':1,'decision':'accepted_source_candidates_only','scope':'Exact index reservation/helper and four RAM candidate deltas. Entry integration/final concrete source registration/release are separate.','evidence':{str(p):hashlib.sha256(b).hexdigest() for p,b in sorted(cache.items())},'ram_changed_functions':changes,'capacity':{'graphs':independent,'bounded_header_bytes_observed':header_bytes,'array_payload_bytes_read':0,'max_buffer_required':max_buffer,'max_output_required':max_output,'max_numeric_required':max_buffer+max_output,'old_first_graph_constructor_required':187338120,'old_allowed':1048576,'policy_changes':['numeric.max_buffer_bytes','numeric.max_numeric_bytes'],'qualification':'Observed bounded NPY headers joined to admitted manifests and retained node-count receipts; no new full-body authentication, atomic snapshot, actual peak or whole-capacity proof.'},'method_preservation':'No numerical algorithm source change. Existing 32 motifs, original512 samples, full seven graphs, directed edge ordering, complete induced neighborhoods, 10000-node scientific refusal, chunk4096 and matching/model/training contracts retained. Buffer bound includes all possible graph edges; it does not truncate high-degree nodes.','ram_policy':{'startup':9126805504,'hard_cap':6442450944,'high':5368709120,'host_reserve':2684354560,'disk_floor':10737418240,'swap':0,'scope':'Exact authenticated schema2 pilot only; default legacy reserve remains3GiB. Native startup/runtime/cleanup implementations unchanged.'},'focused_verification':[{'case_set':'index candidate cases only','passed':9,'seconds':0.33,'exit_code':0,'tool_chunk':'076f0e'},{'case_set':'RAM candidate cases only','passed':25,'seconds':1.06,'exit_code':0,'tool_chunk':'759081','session':82140}],'findings':[],'not_tested':['No new genuine Admission/claim, RootIO, preflight, native launch or financial experiment.','Matching-owner consumer wiring inspected as source; no fabricated Owner/Binding or numerical library execution.','No payload/body/label/price/raw/runtime/private data review or scientific result.','No full7 simultaneous live RAM proof, Python ID/metadata/model/optimizer/retained outputs capacity or future throughput.','Existing complete-array regression suite reused from candidate receipt, not rerun.','Final16 concrete source/metadata/entry pins and recovery pending separate review.']})
mp=write('SOURCE_MANIFEST01.json',{'schema_version':1,'decision':'accepted_source_candidates_only','files':[ref(H/'review_source01.py'),ref(rp)]})
print(json.dumps({'review':ref(rp),'manifest':ref(mp)},sort_keys=True))
