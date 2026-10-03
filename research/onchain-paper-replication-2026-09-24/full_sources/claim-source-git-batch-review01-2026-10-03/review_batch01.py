"""Independent isolated Git, framing and cleanup checks. No research claims."""
import ast,hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;S=P.with_name('claim-source-git-batch-candidate01-2026-10-03');R=P.parents[3]
def h(b):return hashlib.sha256(b).hexdigest()
def j(p):return json.loads(p.read_bytes())
m=j(S/'MANIFEST01.json');assert h((S/'MANIFEST01.json').read_bytes())=='c048da8c0c5242dab43b1e72a985b76565d8dd1a52f993c7277d18eac12ced03'
for row in m['files']:
 b=(S/row['path']).read_bytes();assert len(b)==row['bytes'] and h(b)==row['sha256']
base=(S/'baseline.py').read_bytes();candidate=(S/'candidate01.py').read_bytes()
for row in j(S/'origins01.json')['origins']:assert (R/row['path']).read_bytes()==base
bt=ast.parse(base);nt=ast.parse(candidate);baseline_names={n.name for n in bt.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
nt.body=[n for n in nt.body if not((isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name not in baseline_names) or (isinstance(n,ast.Assign) and all(isinstance(x,ast.Name) and x.id.startswith('_GIT_') for x in n.targets)))]
bf=next(n for n in bt.body if isinstance(n,ast.FunctionDef) and n.name=='verify_claim');nf=next(n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name=='verify_claim');i=next(i for i,n in enumerate(bf.body) if isinstance(n,ast.For) and ast.unparse(n.target)=='(path, expected)');assert ast.unparse(nf.body[i])=="_verify_sources(root, pinned, {claim['source'], claim['design_source']})";nf.body[i]=bf.body[i];assert ast.dump(bt)==ast.dump(nt)
spec=importlib.util.spec_from_file_location('reviewed_verifier',S/'candidate01.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
# Isolated fresh local Git store only; no hooks, credentials, lazy fetching or network.
env={'GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_COUNT':'2','GIT_CONFIG_KEY_0':'protocol.allow','GIT_CONFIG_VALUE_0':'never','GIT_CONFIG_KEY_1':'core.hooksPath','GIT_CONFIG_VALUE_1':'/dev/null'}
os.environ.update(env);G=P/'tiny-git01';G.mkdir()
def git(*args):return subprocess.check_output(['git',*args],cwd=G,stderr=subprocess.PIPE)
git('init','-q');names=['plain','space name','line\nname','cr\rname',os.fsdecode(b'nonutf-\xff'),'empty'];pins={}
for i,n in enumerate(names):
 b=b'' if n=='empty' else bytes([i,0,10,13,255])+n.encode(errors='surrogateescape');(G/n).write_bytes(b);pins[n]=h(b)
git('add','-A');git('-c','user.name=Review','-c','user.email=review@example.invalid','commit','-qm','tiny source one');c1=git('rev-parse','HEAD').decode().strip()
v._verify_sources(G,pins,{c1});(G/'plain').write_bytes(b'new content');git('add','plain');git('-c','user.name=Review','-c','user.email=review@example.invalid','commit','-qm','tiny source two');c2=git('rev-parse','HEAD').decode().strip()
v._verify_sources(G,pins,{c1})
try:v._verify_sources(G,pins,{c2})
except ValueError as e:assert 'hash mismatch' in str(e)
else:raise AssertionError('stale pin accepted on fresh invocation')
newpins=dict(pins,plain=h(b'new content'));v._verify_sources(G,newpins,{c2});v._verify_sources(G,{'empty':pins['empty']},{c1,c2})
for p in ['missing','/bad','../bad','keys/x','x/.env.y']:
 try:v._verify_sources(G,{p:'0'*64},{c1})
 except ValueError:pass
 else:raise AssertionError('invalid path/object accepted')
try:v._verify_sources(G,{'plain':'0'*64,'../bad':'0'*64},{c1})
except ValueError as e:assert str(e)=='registered source/charter/selection hash mismatch'
else:raise AssertionError('hash order')
# Actual retained framing function with tiny synthetic response bodies.
frame=b'a'*40+b' blob 1\nx\n';row=[('x',c1,h(b'x'))];v._verify_batch(frame,row)
for raw in [frame[:-1],frame+b'x',b'a'*40+b' tree 1\nx\n',b'x missing\n',frame.replace(b' 1\n',b' 01\n',1),frame.replace(b'x\n',b'y\n')]:
 try:v._verify_batch(raw,row)
 except ValueError:pass
 else:raise AssertionError('bad frame accepted')
# Actual subprocess plus read fatal and independently failing close operations.
real_spawn=subprocess.Popen;real_read=os.read;cases=[]
class Pipe:
 def __init__(self,f):self.f=f;self.closes=0
 def fileno(self):return self.f.fileno()
 def close(self):self.closes+=1;self.f.close();raise OSError('synthetic close uncertainty')
for fatal in [MemoryError('first'),KeyboardInterrupt('first'),SystemExit(19)]:
 made=[]
 def spawn(command,**kwargs):
  p=real_spawn([sys.executable,'-B','-c','import sys,time;sys.stdout.buffer.write(b"x");sys.stdout.flush();time.sleep(1)'],**kwargs)
  p.stdin=Pipe(p.stdin);p.stdout=Pipe(p.stdout);p.stderr=Pipe(p.stderr);made.append(p);return p
 def fail(fd,n):
  if made and fd==made[0].stdout.fileno():raise fatal
  return real_read(fd,n)
 # Keep stdin open long enough for output read: inject primary independently at select output.
 # A nonempty pending input would still close normally, so suppress uncertainty only for stdin.
 original_close=Pipe.close
 def selected_close(self):
  self.closes+=1;self.f.close()
  if made and self is not made[0].stdin:raise OSError('synthetic close uncertainty')
 with patch.object(Pipe,'close',selected_close),patch.object(v.subprocess,'Popen',side_effect=spawn),patch.object(os,'read',side_effect=fail):
  try:v._git_transport(G,b'')
  except BaseException as e:assert e is fatal
  else:raise AssertionError('fatal lost')
 p=made[0];assert p.poll() is not None and all(f.closes==1 and f.f.closed for f in [p.stdin,p.stdout,p.stderr]);cases.append(type(fatal).__name__)
# Existing uncertainty must not mask a later real fatal; all independent actions run.
first=MemoryError('later actual');seen=[]
def raise_first():seen.append(1);raise first
try:v._git_cleanup((raise_first,lambda:seen.append(2)),v._GitCleanupFailure('old uncertainty'))
except MemoryError as e:assert e is first and seen==[1,2]
else:raise AssertionError('fatal suppression')
assert not {'numpy','torch','scipy'}&set(sys.modules)
print(json.dumps({'manifest_files':len(m['files']),'inverse_whole_AST_parity':True,'tiny_actual_Git_names':len(names),'actual_commits':2,'fresh_committed_hash_checks':True,'valid_LF_CR_nonUTF8_empty':True,'ordered_hash_before_invalid_path':True,'framing_refusals':6,'actual_read_fatal_plus_two_close_failures':cases,'each_pipe_close_once_child_reaped':True,'original_claims_or_numerics_or_network':False},indent=2))
