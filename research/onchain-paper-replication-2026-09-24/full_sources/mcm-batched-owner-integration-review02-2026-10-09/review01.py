import ast,hashlib,json,os,stat,types,importlib.util,resource,signal
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
H=Path(__file__).resolve().parent;R=H.parents[3];C=H.parent/'mcm-batched-owner-integration02-2026-10-09';O=H.parent/'mcm-batched-owner-integration01-2026-10-09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def extract(path,names,ns):
 t=ast.parse(path.read_text());nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
ns={'json':json,'hashlib':hashlib,'META_LIMIT':8192};extract(R/'tradingagents/research/onchain_replication/score_batches.py',{'_signature','_json','_require'},ns)
io=types.SimpleNamespace(**{k:ns[k] for k in ('_signature','_json','_require')})
base={'os':os,'stat':stat,'hashlib':hashlib,'io':io,'require':io._require}
a=dict(base);b=dict(base);extract(O/'compact_mcm_batched.py',{'_checkpoint_inventory'},a);extract(C/'compact_mcm_batched.py',{'_checkpoint_inventory'},b)
p=H/'inventory';p.mkdir();(p/'body').write_bytes(b'tiny opaque fixture');old=a['_checkpoint_inventory'](p);new=b['_checkpoint_inventory'](p);(p/'empty').mkdir();assert old==a['_checkpoint_inventory'](p);assert new!=b['_checkpoint_inventory'](p)
refusals=[]
(p/'symlink').symlink_to(p/'body')
try:b['_checkpoint_inventory'](p)
except ValueError:refusals.append('symlink')
else:raise AssertionError('symlink accepted')
# Preserve this refused tree; separate clean resource-failure fixture.
manifest=json.loads((C/'MANIFEST.json').read_text());joins={}
for name,row in manifest['sources'].items():
 assert sha(C/name)==row['source_sha256'];assert sha(R/row['baseline'])==row['baseline_sha256'];joins[name]=row['source_sha256']
spec=importlib.util.spec_from_file_location('review_journal',C/'batched_journal.py');journal=importlib.util.module_from_spec(spec);spec.loader.exec_module(journal)
created=[]
def make_journal(*args,**kwargs):
 j=journal.BatchJournal(*args,**kwargs);created.append(j);return j
primary=OSError('synthetic token open failure')
def opening(path,*args,**kwargs):
 if str(path).endswith('/closure-tokens.bin'):raise primary
 return os.open(path,*args,**kwargs)
proxy=types.SimpleNamespace(**{k:getattr(os,k) for k in dir(os)});proxy.open=opening
ns=dict(b,os=proxy,thaw=lambda x:x,FORMAT='ordered-mcm-batch-closure-v2')
extract(C/'compact_mcm_batched.py',{'selected','validate','_compute'},ns)
root=H/'failure-stage';root.mkdir();stage=types.SimpleNamespace(root=root);target=types.SimpleNamespace(owner=types.SimpleNamespace(policy={'pair':{},'schedule':{}},matching={}))
policy={'schema_version':4,'max_entries':32,'max_workflow_metadata_bytes':65536,'numeric':{},'batched':{'format':ns['FORMAT'],'authority_boundaries':'entry-batch-checkpoint-final','batch_cells':32,'max_journal_bytes':100000,'max_body_bytes':1024,'max_closure_token_bytes':168,'max_checkpoint_bytes':100000,'retention':'local-v2','max_spool_bytes':128,'max_offload_metadata_bytes':1000,'max_offload_entries':100,'max_offload_anchor_bytes':0}}
mods={'journal':types.SimpleNamespace(BatchJournal=make_journal),'executor':types.SimpleNamespace(PairExecutor=lambda *a:None)}
try:ns['_compute'](target,stage,None,policy,{'cells':32},mods,lambda:None)
except OSError as e:assert e is primary
else:raise AssertionError('failure did not propagate')
assert len(created)==1;j=created[0];os.fstat(j.fd);assert not j.closed
finding={'primary_preserved':True,'journal_closed':j.closed,'journal_fd_still_open':True,'numerical_calls':0,'genuine_authority_constructed':False}
j.close() # reviewer closes leaked synthetic descriptor after recording evidence
out={'decision':'withheld','manifest_sha256':sha(C/'MANIFEST.json'),'sources':joins,'original_inventory_red_reproduced':True,'successor_inventory_detects_empty_directory':True,'refusals':refusals,'blocking_failure':finding,'qualification':'AST actual _compute with metadata-only doubles; actual frozen BatchJournal; injected token-open OSError. No Owner/Target/View/transport constructed.'}
(H/'RESULT01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
