"""Read-only actual CLOSED02 inventory and synthetic scalar metadata limits."""
import ast,copy,hashlib,importlib.util,json,os,stat,time,sys
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3];W=P.parent/'original-import-native-refusal-worker-preparation02-2026-10-03';C=P.parent/'original-import-native-successor-preparation04-2026-10-03/capsule02'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
rows={r['target']:r for r in read(W/'source_inventory02.json')['source_inventory']}
source=W/'refusal_outer01.py';assert sha(source.read_bytes())=='eed4786a2383cb99f426facdd00431d1bae85b1f1e5ad63f2fd3c1922eff2535'
row=rows['fixture_tools/raw_receipts01.py'];path=R/row['origin'];assert sha(path.read_bytes())==row['sha256'];spec=importlib.util.spec_from_file_location('review_raw_only',path);raw=importlib.util.module_from_spec(spec);spec.loader.exec_module(raw)
tree=ast.parse(source.read_bytes())
def fn(t,name):return next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name)
ns=dict(Path=Path,time=time,stat=stat,hashlib=hashlib,body=raw.body,require=raw.require,FILE=4194304,GIB=1073741824)
exec(compile(ast.Module(body=[fn(tree,'inventory')],type_ignores=[]),'actual inventory','exec'),ns)
actual=ns['inventory'](C)
ret=read(C.parent/'RETAINED_PRIMARY01.json');assert len(actual['members'])==len(ret['members'])-1==816
retrows={r['path']:r for r in ret['members']}
for r in actual['members']:
 old=retrows[r['path']];assert r['kind']==old['kind'] and r['allocated']==old['allocated_bytes']
 if r['kind']=='file':assert r['sha256']==old['sha256'] and r['bytes']==old['bytes']
run=fn(tree,'run');savefn=next(n for n in run.body if isinstance(n,ast.FunctionDef) and n.name=='save')
g=next(n for n in run.body if isinstance(n,ast.Try) and n.finalbody);block=next(n for n in g.finalbody if isinstance(n,ast.Try) and any(isinstance(x,ast.Assign) and 'index' in ast.unparse(x) and 'inventory(root)' in ast.unparse(x) for x in n.body));nodes=block.body
encoded=lambda v:(json.dumps(v,sort_keys=True,allow_nan=False)+'\n').encode()
class Sink:
 def __init__(self):self.files={};self.attempts=[]
 def _native_receipt(self,outer,name,value):
  b=encoded(value);self.attempts.append((name,len(b)));assert len(b)<=65536
  if name in self.files:raise FileExistsError(name)
  self.files[name]=b

def measure(index):
 sink=Sink();env={'json':json,'require':raw.require,'resources':sink,'outer':C/'fixture_outer/synthetic-no-birth','root':C,'hashlib':hashlib,'inventory':lambda _:copy.deepcopy(index)}
 env['body']=lambda root,name:sink.files[Path(name).name]
 exec(compile(ast.Module(body=[savefn],type_ignores=[]),'actual save','exec'),env)
 error=None
 try:exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual paging','exec'),env)
 except Exception as e:error={'type':type(e).__name__,'message':str(e)}
 return {'error':error,'pages_published':len([n for n in sink.files if n.startswith('inventory-')]),'max_page_bytes':max([len(b) for n,b in sink.files.items() if n.startswith('inventory-')],default=0),'index_bytes':len(sink.files['inventory.json']) if 'inventory.json' in sink.files else None,'prospective_index_bytes':len(encoded(env['index']|{'pages':env.get('references',[])})),'compact_aggregate_bytes':env.get('total'),'rows':len(index['members'])}
baseline=measure(actual);assert baseline['error'] is None
# Exactly use actual resulting index envelope and page-reference syntax.
envelope={k:v for k,v in actual.items() if k!='members'}
def index_extent(n):return len(encoded(envelope|{'pages':[{'path':'inventory-'+str(i).zfill(3)+'.json','sha256':'0'*64} for i in range(n)]}))
limit=max(n for n in range(769) if index_extent(n)<=8192)
# Synthetic metadata only: no actual file, authority, native job or future tree.
# Each row obeys declared path/file/extents and represents singly-linked regular files.
def synthetic(n,path='research_artifacts/synthetic-closed-metadata'):
 return dict(envelope,members=[{'path':path+'/'+str(i).zfill(5)+'.json','bytes':1,'allocated':4096,'kind':'file','sha256':'0'*64} for i in range(n)])
lo=0;hi=32768
while lo+1<hi:
 mid=(lo+hi)//2
 if measure(synthetic(mid))['error'] is None:lo=mid
 else:hi=mid
boundary={'last_passing':measure(synthetic(lo)),'first_refused':measure(synthetic(hi))}
# Feasible character/component/depth scalar path demonstrates byte-encoding gap;
# no such filesystem tree is created or asserted to exist in registered outputs.
emoji='/'.join(['\U0001f600'*32]*27)
es=synthetic(1,emoji);unicode=measure(es)
assert len(es['members'][0]['path'])<=2048 and unicode['error'] is not None
# Synthetic 32768-row short-name inventory: tests finite representation ceilings,
# not actual suite storage or a completed directory scan.
maximum=measure(synthetic(32768,'s'))
assert not {'numpy','torch','scipy','tradingagents'}&set(sys.modules)
print(json.dumps({'source_sha256':sha(source.read_bytes()),'closed_tree':str(C),'closed_tree_retention_sha256':sha((C.parent/'RETAINED_PRIMARY01.json').read_bytes()),'actual_closed_baseline':baseline,'actual_inventory_rows_excluding_root':816,'index_envelope_bytes_with_zero_pages':index_extent(0),'maximum_reference_pages_fitting8192':limit,'index_bytes_at_maximum':index_extent(limit),'index_bytes_at_next':index_extent(limit+1),'index_bytes_at_declared768':index_extent(768),'synthetic_ASCII_count_boundary':boundary,'synthetic_declared32768_short_rows':maximum,'synthetic_escaped_path':{'characters':len(es['members'][0]['path']),'utf8_bytes':len(es['members'][0]['path'].encode()),'max_component_utf8_bytes':max(len(s.encode()) for s in es['members'][0]['path'].split('/')),'components':len(es['members'][0]['path'].split('/')),'result':unicode},'actual_suite_attempts':0,'numeric_imports':False},indent=2))
