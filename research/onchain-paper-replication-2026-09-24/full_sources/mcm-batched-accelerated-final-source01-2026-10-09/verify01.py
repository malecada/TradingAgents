"""Synthetic callable composition; no Owner/Target/Run capabilities instantiated."""
import ast,hashlib,importlib.util,json,os,resource,signal,sys
from pathlib import Path
from types import SimpleNamespace,ModuleType
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]));os.nice(10);signal.alarm(60)
R=Path.cwd();H=Path(__file__).resolve().parent;F=H.parent;sys.path.insert(0,str(R));package='tradingagents.research.onchain_replication'
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
from tradingagents.research.onchain_replication import score_batches as io
m=ModuleType(package+'.compact_mcm_batched');m.__package__=package;m.__file__=str(F/'mcm-batched-accelerated-integration01-2026-10-09/compact_mcm_batched.py');sys.modules[m.__name__]=m
source=ast.parse((F/'mcm-batched-accelerated-integration01-2026-10-09/compact_mcm_batched.py').read_text());source.body=[n for n in source.body if not (isinstance(n,ast.ImportFrom) and n.module is None and any(x.name in ('compact_owner','compact_mcm_publication') for x in n.names))];m.io=io;exec(compile(source,m.__file__,'exec'),m.__dict__)
def actual(file,name,namespace):
 node=next(n for n in ast.parse(file.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name);exec(compile(ast.Module(body=[node],type_ignores=[]),str(file),'exec'),namespace);return namespace[name]
m.owners=SimpleNamespace(entries=actual(R/'tradingagents/research/onchain_replication/compact_owner.py','entries',{'io':io,'os':os,'require':io._require}));m.producer=SimpleNamespace(ROOT=R)
paths={'batched_journal':F/'mcm-batched-owner-integration03-2026-10-09/batched_journal.py','batched_driver':F/'mcm-batched-owner-integration02-2026-10-09/batched_driver.py','batched_pair_executor':F/'mcm-immutable-pair-executor02-2026-10-09/pair_executor.py','batched_numeric_reuse':F/'matching-exact-numeric-reuse03-2026-10-09/numeric_reuse.py','batched_numeric_execution':F/'mcm-batched-numeric-execution03-2026-10-09/numeric_execution.py'}
for name,path in paths.items():load(package+'.'+name,path)
# _modules additionally checks genuine installed role paths only with Admission;
# this test supplies actual helper objects directly and never fabricates Admission.
mods={k:sys.modules[package+'.'+v] for k,v in m.MODULES.items()}
import numpy as np
from tradingagents.research.onchain_replication.contracts import GraphSnapshot,AttributedGraph
from tradingagents.research.onchain_replication.neighborhoods import graph_hash,node_order_hash
c=dict(beta0=.2,beta_final=.5,beta_rate=.1,max_iterations=3,alpha=.7,max_pair_entries=10000,normalization_iterations=1,solver='algorithm1_literal')
p=dict(max_state_bytes=65536,normalization_chunk_entries=8,hardening_chunk_entries=8,hardening_buffer_bytes=65536,max_score_buffer_bytes=65536,chunk_edges=8,max_checkpoint_bytes=262144,max_publications=100,total_checkpoint_bytes=1048576)
s=dict(max_checkpoints=100,calls_per_checkpoint=2,operations_per_call=10000,max_total_checkpoints=1000,max_total_checkpoint_bytes=500000000)
g=GraphSnapshot('ETH','2022-01-03T00:00:00Z','2022-01-10T00:00:00Z','2022-01-10T00:00:00Z',('a'*64,),'b'*64,('a','b'),np.ones((2,4)),np.array([[0],[1]],dtype=np.int64),np.ones((1,2)),1,1,{})
motifs=tuple(AttributedGraph(('m',),np.ones((1,4)),np.empty((2,0),dtype=np.int64),np.empty((0,2)),'c'*64,'m') for _ in range(32));dictionary=SimpleNamespace(representatives=motifs,config={'hop_depth':1,'maximum_neighborhood_nodes':2})
root=H/'tiny-stage';root.mkdir();(root/'intent.json').write_text('{}\n');st=root.stat();stage=SimpleNamespace(root=root,inode=(st.st_dev,st.st_ino));target=SimpleNamespace(dictionary=dictionary,owner=SimpleNamespace(policy={'pair':p,'schedule':s},matching=c))
scope={'graph':graph_hash(g),'node_order':node_order_hash(g.node_ids),'dictionary':'a'*64,'ordered_motifs':'b'*64,'matching':'c'*64,'workflow':'d'*64}
execution=dict(route='immutable-input-session+exact-byte-reuse-v1',max_entries=8,max_retained_bytes=16384,max_key_bytes=4096,max_origin_bytes=576,max_summary_bytes=16384)
policy={'schema_version':5,'max_entries':64,'max_workflow_metadata_bytes':65536,'numeric':{'max_buffer_bytes':100000,'edge_chunk':2,'extraction_limit':3},'batched':{'format':m.FORMAT,'authority_boundaries':'entry-batch-checkpoint-final','batch_cells':48,'max_journal_bytes':200000,'max_body_bytes':1024,'max_closure_token_bytes':336,'max_checkpoint_bytes':1000000,'retention':'local-v2','max_spool_bytes':256,'max_offload_metadata_bytes':100000,'max_offload_entries':1000,'max_offload_anchor_bytes':64,'execution':execution}}
start={'rows':2,'cells':64,'motifs':32,'graph_hash':graph_hash(g),'scope':scope}
binding=m._compute(target,stage,g,policy,start,mods,lambda:None)
contract={'owner':'e'*64,'scope':{},'policy':{},'kind':'mcm','pairs':64,'batched':binding};raw=io._json(contract);(root/'stage-complete.json').write_bytes(raw);reference=hashlib.sha256(raw).hexdigest();result=m.verify_content(root,contract,reference,mods)
assert result['completed_pairs']==64 and binding['numeric_execution']['computed']+binding['numeric_execution']['reused']==64 and binding['numeric_execution']['reused']>0
assert (root/'stream/numeric-origins.bin').stat().st_size==576 and (root/'stream/scores.f32').stat().st_size==256
checks=['actual_index_journal_session_cache_spool_composition','complete64cell_two_batch_coverage','durable_origin_and_summary_verification','no_owner_or_admission_fabricated']
# Concrete downstream numerical consumer must reject mutated retained origins.
origin=root/'stream/numeric-origins.bin';saved=origin.read_bytes();damaged=bytearray(saved);damaged[-1]^=1;origin.write_bytes(damaged)
try:m.verify_content(root,contract,reference,mods)
except ValueError:checks.append('tampered_provenance_refuses_completed_stage')
else:raise AssertionError('provenance corruption accepted')
# Retain corrupted fixture as evidence; do not restore or reopen its closure.
(H/'RESULT01.json').write_text(json.dumps({'decision':'PASS','checks':checks,'numeric_binding':binding['numeric_execution'],'scientific_arrays':False,'genuine_authority':False,'benchmark':False},indent=2)+'\n');print(json.dumps({'decision':'PASS','checks':len(checks),'computed':binding['numeric_execution']['computed'],'reused':binding['numeric_execution']['reused']}))
