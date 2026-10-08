from pathlib import Path
exec(compile((Path(__file__).parent/'reproduce01.py').read_text().split('results={}')[0],__file__,'exec'))
import difflib
comparisons=0;fast_lines=0

def equal(x,y):
 global comparisons
 for k in x:
  assert x[k].tobytes()==y[k].tobytes() if isinstance(x[k],np.ndarray) else x[k]==y[k],k
 comparisons+=1
# Exactly one insertion and full literal inversion.
x=(A/'baseline.py').read_text().splitlines(True);y=(A/'matching_annealing.py').read_text().splitlines(True)
ops=[z for z in difflib.SequenceMatcher(a=x,b=y,autojunk=False).get_opcodes() if z[0]!='equal'];assert len(ops)==1 and ops[0][0]=='insert';_,_,_,lo,hi=ops[0];assert y[:lo]+y[hi:]==x
line=next(i+1 for i,t in enumerate(y) if 'np.add.at' in t)
def trace(frame,event,arg):
 global fast_lines
 if event=='line' and frame.f_code.co_filename==str(A/'matching_annealing.py') and frame.f_lineno==line:fast_lines+=1
 return trace
# Valid repeated destinations, signed zero, finite subnormal M; warning-error fast path.
for dtype in (np.float64,np.float32):
 aa=AttributedGraph(('a','b'),np.array([[0.],[-0.]],dtype=dtype),edges,np.zeros((3,1),dtype=dtype),'a'*64,'a')
 for schedule in ([1,7,8,9],[8],[1023,1024,1025]):
  x=B.create(aa,b,config,max_state_bytes=1024,max_chunk_entries=8);y=C.create(aa,b,config,max_state_bytes=1024,max_chunk_entries=8);step=0
  while x['phase']!='done':
   budget=schedule[step%len(schedule)];step+=1
   with warnings.catch_warnings(),np.errstate(under='ignore',over='warn',invalid='warn'):
    warnings.simplefilter('error',RuntimeWarning)
    bx=B.advance(x,aa,b,config,max_operations=budget)
    sys.settrace(trace)
    try:cy=C.advance(y,aa,b,config,max_operations=budget)
    finally:sys.settrace(None)
   assert bx==cy;equal(x,y)
  rx=B.result(x,aa,b,config);ry=C.result(y,aa,b,config)
  assert rx.score.hex()==ry.score.hex() and rx.assignment.tobytes()==ry.assignment.tobytes() and rx.soft_assignment.tobytes()==ry.soft_assignment.tobytes() and (rx.iterations,rx.convergence)==(ry.iterations,ry.convergence)
  for src,dst,tag in [(B,C,'bc'),(C,B,'cb')]:
   path=P/(tag+'-'+str(dtype.__name__)+'-'+str(schedule[0]));sha=src.save(x,path,aa,b,config,max_checkpoint_bytes=100000)
   z=dst.load(path,aa,b,config,expected_sha256=sha,max_state_bytes=1024,max_chunk_entries=8);equal(x,z)
assert fast_lines>0
# Fourth-product overflow with literal scalar prefix preserved.
ae=np.array([[0],[1]],dtype=np.int64);be=np.array([[0]*9,list(range(1,10))],dtype=np.int64)
aa=AttributedGraph(('a','b'),np.zeros((2,1)),ae,np.zeros((1,1)),'a'*64,'a');bb=AttributedGraph(tuple(map(str,range(10))),np.zeros((10,1)),be,np.zeros((9,1)),'b'*64,'0')
z=B.create(aa,bb,config,max_state_bytes=4096,max_chunk_entries=32);B.advance(z,aa,bb,config,max_operations=21);z['Q'].fill(np.finfo(float).max);z['M'].fill(0.);z['M'][1,4]=np.finfo(float).max
for mode in ['warn','raise','call','log']:
 states=[];errs=[];old=np.geterrcall()
 class Log:
  def write(self,*args):raise RuntimeError('logger')
 def callback(*args):raise RuntimeError('callback')
 try:
  np.seterrcall(Log() if mode=='log' else callback)
  for mod in [B,C]:
   state=copy.deepcopy(z)
   with warnings.catch_warnings(),np.errstate(over=mode):
    warnings.simplefilter('error',RuntimeWarning)
    try:mod.advance(state,aa,bb,config,max_operations=9)
    except Exception as e:errs.append((type(e).__name__,str(e)))
   states.append(state)
 finally:np.seterrcall(old)
 assert len(errs)==2 and errs[0]==errs[1];equal(*states);assert states[0]['cursor']==3
# Agreement overflow after three scalar calls: no duplicated prefix agreements.
f=bb.edge_features.copy();f[3,0]=1e308;bad=AttributedGraph(bb.node_ids,bb.node_features,bb.edge_index,f,bb.parent_hash,bb.center_id)
z=B.create(aa,bad,config,max_state_bytes=4096,max_chunk_entries=32);B.advance(z,aa,bad,config,max_operations=21)
counts=[];states=[]
for mod in [B,C]:
 original=mod.agreement;calls=[]
 def observed(a,b):calls.append((a.tobytes(),b.tobytes()));return original(a,b)
 mod.agreement=observed;x=copy.deepcopy(z)
 try:
  try:mod.advance(x,aa,bad,config,max_operations=9)
  except OverflowError:pass
 finally:mod.agreement=original
 counts.append(calls);states.append(x)
assert counts[0]==counts[1] and len(counts[0])==4;equal(*states)
print(json.dumps({'status':'PASS','state_comparisons':comparisons,'fast_path_line_hits':fast_lines,'inverse_inserted_lines':hi-lo,'agreement_calls_on_failure':4,'checkpoint_directions':2,'scope':'synthetic only; tracer observes execution, does not mutate numerical inputs'}))
