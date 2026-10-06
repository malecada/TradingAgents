"""Independent exact canonical-byte recorder for small invented graph arrays."""
from pathlib import Path
from dataclasses import replace
import hashlib,importlib.util,json,sys
from unittest.mock import patch
import numpy as np
from tradingagents.research.onchain_replication.contracts import GraphSnapshot,graph_to_dict
from tradingagents.research.onchain_replication.provenance import canonical_bytes
HERE=Path(__file__).resolve().parent;W=HERE.parent/'real-data-pilot-authority-gap-fix01-2026-10-06';p=W/'candidate/neighborhoods.py'
spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication.review_byte_candidate',p);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
realsha=hashlib.sha256
class Recorder:
 def __init__(self,body=b''):self.parts=[body];self.inner=realsha(body)
 def update(self,body):self.parts.append(body);self.inner.update(body)
 def hexdigest(self):return self.inner.hexdigest()
records=[]
def factory(body=b''):
 r=Recorder(body);records.append(r);return r
rows=[]
for n,width in [(257,4),(3,1024),(3,1025),(0,0),(3,0)]:
 backing=np.resize(np.array([-0.0,1e-300,-1e15,np.pi]),(n,max(1,width)*2));features=backing[:,:width*2:2]
 e=0 if n<2 else 1;ix=np.array([[0],[1]],dtype=np.int64) if e else np.empty((2,0),dtype=np.int64);agg=np.ones((e,2))
 g=GraphSnapshot('ETH','2024-01-01T00:00:00Z','2024-01-08T00:00:00Z','2024-01-09T00:00:00Z',('a'*64,),'b'*64,tuple('Č\n\\'+str(i) for i in range(n)),features,ix,np.log1p(agg),e,e,{},agg)
 expected=canonical_bytes(graph_to_dict(g));records.clear()
 with patch.object(hashlib,'sha256',factory):digest=m.graph_hash(g)
 assert len(records)==1 and b''.join(records[0].parts)==expected
 assert digest==realsha(expected).hexdigest()
 rows.append({'nodes':n,'width':width,'exact_bytes':len(expected),'sha256':digest,'strided':not features.flags.c_contiguous})
result={'decision':'passed','candidate_sha256':realsha(p.read_bytes()).hexdigest(),'cases':rows,'scope':'Exact recorded hash update byte stream equals independent complete canonical graph_to_dict serialization, including strided/signed-zero/subnormal/Unicode/empty and wide-row boundaries; small invented graphs only. No real observation data/performance claim.'}
(HERE/'BYTE_STREAM_REVIEW01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
