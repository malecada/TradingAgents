"""Small invented graph identity equality; no observation stores or model work."""
import importlib.util,json,hashlib,sys
from pathlib import Path
from unittest.mock import patch
from dataclasses import replace
import numpy as np
from tradingagents.research.onchain_replication import provenance
from tradingagents.research.onchain_replication.contracts import GraphSnapshot,graph_to_dict
D=Path(__file__).resolve().parent
mods=[]
for which in ('baseline','candidate'):
 spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication.hash_'+which,D/which/'neighborhoods.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);mods.append(m)
def graph(nodes,edges,width):
 ix=np.array([(i//nodes,i%nodes) for i in range(edges)],dtype=np.int64).reshape(-1,2).T
 agg=np.column_stack((np.ones(edges),np.arange(edges,dtype=float)/3))
 return GraphSnapshot('ETH','2024-01-01T00:00:00Z','2024-01-08T00:00:00Z','2024-01-09T00:00:00Z',('a'*64,),'b'*64,tuple('node-Č-\\-\n-'+str(i) for i in range(nodes)),np.resize(np.array([-0.,1e-300,-1e15,np.pi]),(nodes,width)),ix,np.log1p(agg),edges,edges,{},agg)
canonical=provenance.canonical_bytes;rows=[];real_sha=hashlib.sha256
for shape in [(0,0,4),(7,12,4),(1025,0,4),(40,1025,4),(2,1,1025),(3,0,0)]:
 g=graph(*shape);expected=hashlib.sha256(canonical(graph_to_dict(g))).hexdigest();counts=[]
 for m in mods:
  seen=[]
  def bounded(value):
   if isinstance(value,(list,tuple)):
    cells=sum(len(row) if isinstance(row,list) else 1 for row in value)
    assert cells<=1024,(shape,cells)
   seen.append(1);return canonical(value)
  class RecordedHash:
   def __init__(self,initial=b''):self.value=real_sha(initial);self.parts=[initial]
   def update(self,value):self.parts.append(bytes(value));self.value.update(value)
   def hexdigest(self):return self.value.hexdigest()
  recorded=[]
  def make_hash(initial=b''):
   value=RecordedHash(initial);recorded.append(value);return value
  with patch.object(provenance,'canonical_bytes',bounded),patch.object(hashlib,'sha256',make_hash):actual=m.graph_hash(g)
  assert len(recorded)==1 and b''.join(recorded[0].parts)==canonical(graph_to_dict(g))
  assert actual==expected;counts.append(len(seen))
 assert mods[1].graph_hash(replace(g,available_at='2024-01-10T00:00:00Z'))!=expected
 rows.append({'shape':shape,'hash_equal':True,'baseline_calls':counts[0],'candidate_calls':counts[1]})
for variant in ('strided','integer','nonfinite'):
 g=graph(7,12,4)
 if variant=='strided':g=replace(g,node_features=np.repeat(g.node_features,2,axis=0)[::2])
 if variant=='integer':g=replace(g,node_features=np.resize(np.array([-3,0,2],dtype=np.int64),g.node_features.shape))
 if variant=='nonfinite':
  corrupt=g.node_features.copy();corrupt[0,0]=np.nan;g=replace(g,node_features=corrupt)
  try:mods[1].graph_hash(g)
  except ValueError:continue
  else:raise AssertionError('nonfinite accepted')
 assert mods[0].graph_hash(g)==mods[1].graph_hash(g)==real_sha(canonical(graph_to_dict(g))).hexdigest()
g=graph(3,2,4);g=replace(g,edge_index=np.array([[0,0],[1,1]],dtype=np.int64))
try:mods[1].graph_hash(g)
except ValueError:pass
else:raise AssertionError('corrupt duplicate edges accepted')
print(json.dumps({'checks':rows,'duplicate_refused':True,'same_canonical_bytes':True,'bound_scalars':1024,'qualification':'small synthetic graphs; no measured whole-real-graph speed or30second admission'},indent=2))
