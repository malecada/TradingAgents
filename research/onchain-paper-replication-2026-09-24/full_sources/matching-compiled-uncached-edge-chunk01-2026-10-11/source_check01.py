import ast,hashlib,json
from pathlib import Path
p=Path(__file__).resolve().parent;root=Path.cwd();base=root/'tradingagents/research/onchain_replication/matching_annealing.py'
a=base.read_text();b=(p/'matching_annealing.py').read_text()
assert hashlib.sha256(a.encode()).hexdigest()==json.loads((p/'BASELINE.json').read_text())['sha256']
x=ast.parse(a);y=ast.parse(b)
assert len(x.body)==len(y.body)
changed=[getattr(i,'name',type(i).__name__) for i,j in zip(x.body,y.body) if ast.dump(i)!=ast.dump(j)]
assert changed==['_advance_checked']
r=b.replace('edge_cache_policy=None,normalizer=None,edge_chunk_fill=None):','edge_cache_policy=None,normalizer=None):',1)
start=r.index('                            native_progress=None\n');stop=r.index('                            except BaseException:',start)
loopstart=r.index('                                    for offset in range(count):',start)
loop=r[loopstart:stop]
r=r[:start]+'                            try:\n'+''.join(line[4:]+'\n' for line in loop.splitlines())+r[stop:]
r=r.replace('                                if native_progress is not None and native_progress[0] is not None:\n                                    offset=native_progress[0]\n','',1)
assert r==a
scripts=[]
for q in sorted(p.glob('*.py')):ast.parse(q.read_bytes(),filename=str(q));scripts.append(q.name)
result={'status':'PASS_SOURCE_ONLY','changed_top_level':changed,'literal_inverse_equal':True,'syntax_parsed':scripts,'numeric_fixture_executed':False,'native_loaded':False}
(p/'SOURCE_RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
