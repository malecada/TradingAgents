"""Synthetic-only baseline/candidate byte, error and validated graph controls."""
import ast,dataclasses,hashlib,itertools,json,runpy,sys,tempfile,types
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent;R=P.parents[3];S=R/'tradingagents/research/onchain_replication'
prov=runpy.run_path(str(S/'provenance.py'));canonical=prov['current_canonical_bytes']
def extract(path,names,env):
 class Imports(ast.NodeTransformer):
  def visit_ImportFrom(self,n):return ast.Pass() if n.level else n
 tree=ast.parse(path.read_text());nodes=[Imports().visit(n) for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
 exec(compile(ast.fix_missing_locations(ast.Module(nodes,[])),str(path),'exec'),env);return env
ctx={'__name__':__name__,'np':np,'dataclass':dataclasses.dataclass,'Mapping':__import__('collections.abc',fromlist=['Mapping']).Mapping,'MappingProxyType':types.MappingProxyType,'utc':prov['utc'],'require_hash':prov['require_hash'],'pairwise':itertools.pairwise}
extract(S/'contracts.py',{'GraphSnapshot','validate_graph','_duplicate_edges'},ctx)
def hashes(path):return extract(path,{'graph_hash','_graph_chunk_bytes'},{'np':np,'validate_graph':ctx['validate_graph'],'canonical_bytes':canonical,'current_canonical_bytes':canonical})
base=hashes(P/'BASELINE_neighborhoods.py');candidate=hashes(P/'neighborhoods.py')
def cases():
 for dtype in ['i1','u1','<i2','>i2','<u2','>u2','<i4','>i4','<u4','>u4','<i8','>i8','<u8','>u8','<f2','>f2','<f4','>f4','<f8','>f8']:
  for shape in ((0,),(0,4),(4,0),(1023,),(1024,),(1025,),(257,4),(2,1025)):
   count=int(np.prod(shape));arr=(np.arange(count,dtype=np.int64)%111).astype(dtype).reshape(shape);yield dtype+str(shape),arr
 for dtype in ('f2','f4','f8'):
  values=np.array([0.,-0.,1.,-1.,np.finfo(dtype).tiny,np.finfo(dtype).max,np.nextafter(np.array(0,dtype=dtype),np.array(1,dtype=dtype)),.1,1.0000000000000002],dtype=dtype)
  yield 'hard-'+dtype,values
 for value in (np.nan,np.inf,-np.inf):yield 'nonfinite-'+str(value),np.array([value])
 for kind,arr in [('unicode',np.array(['žluťoučký','𐍈','\n','"','\\'])),('bool',np.array([True,False])),('object',np.array([1,'雪',None],dtype=object)),('structured',np.array([(1,2.)],dtype=[('a','i4'),('b','f8')])),('complex',np.array([1+2j])),('datetime',np.array(['2026-01-01'],dtype='datetime64[D]')),('longfloat',np.array([1],dtype=np.longdouble)),('metadata',np.array([1],dtype=np.dtype('i4',metadata={'tag':'x'})))]:yield kind,arr
 class Sub(np.ndarray):
  def tolist(self):return ['subclass',super().tolist()]
 yield 'subclass',np.array([1,2]).view(Sub)
 yield 'nested',np.arange(8).reshape(2,2,2)
 yield 'strided',np.arange(2048,dtype='f8')[::2]
 for dtype in ('i8','u8'):
  yield 'integer-extremes-'+dtype,np.array([np.iinfo(dtype).min,np.iinfo(dtype).max],dtype=dtype)
def outcome(fn):
 try:
  b=fn();return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)},b
 except Exception as e:return {'error':type(e).__name__,'message':str(e)},None
def graph(n,width=4,dtype='f8'):
 e=max(0,n-1);return ctx['GraphSnapshot']('ETH','2026-01-01T00:00:00Z','2026-01-02T00:00:00Z','2026-01-02T00:00:00Z',('a'*64,),'b'*64,tuple('雪'+str(i) for i in range(n)),np.zeros((n,width),dtype=dtype),np.array([np.arange(e),np.arange(1,e+1)],dtype='i8'),np.zeros((e,2),dtype=dtype),e,e,{})
def main(mode):
 records={};count=0
 for name,arr in cases():
  expected,body=outcome(lambda:canonical(arr.tolist()));records[name]=expected
  if mode!='baseline':
   actual,got=outcome(lambda:candidate['_graph_chunk_bytes'](arr));assert actual==expected,(name,actual,expected);assert got==body,name
  count+=1
 for n,width in ((0,4),(1,0),(1,1025),(1023,4),(1024,4),(1025,4),(2049,4)):
  g=graph(n,width);h=base['graph_hash'](g);records['graph'+str((n,width))]={'digest':h}
  if mode!='baseline':assert candidate['graph_hash'](g)==h
 for bad in ('nan','endpoint'):
  g=graph(4)
  if bad=='nan':object.__setattr__(g,'node_features',np.full((4,4),np.nan))
  else:object.__setattr__(g,'edge_index',np.array([[0],[99]]));object.__setattr__(g,'edge_features',np.zeros((1,2)))
  old,_=outcome(lambda:base['graph_hash'](g));records['invalid-'+bad]=old
  if mode!='baseline':assert outcome(lambda:candidate['graph_hash'](g))[0]==old
 if mode!='baseline':
  g=graph(1025);before=candidate['graph_hash'](g);a=np.array(g.node_features);a[1024,3]=.125;object.__setattr__(g,'node_features',a);assert candidate['graph_hash'](g)==base['graph_hash'](g)!=before
  assert records==json.loads((P/'BASELINE_RESULTS01.json').read_bytes())
 path=P/('BASELINE_RESULTS01.json' if mode=='baseline' else 'COMPATIBILITY_RESULTS02.json')
 with path.open('x') as f:json.dump(records,f,indent=2,ensure_ascii=False);f.write('\n')
 print(json.dumps({'mode':mode,'chunk_cases':count,'validated_graph_cases':9,'fresh_mutation':mode!='baseline','status':'PASS'}))
if __name__=='__main__':main(sys.argv[1])
