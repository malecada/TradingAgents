import ast,hashlib,importlib.util,json,os,stat,sys,types
from pathlib import Path
HERE=Path(__file__).resolve().parent;PREP=HERE.parent/'financial-genuine-wrapper-claimedrun-source-handoff-preparation01-2026-10-04';raw=(PREP/'generate01.py').read_bytes();assert hashlib.sha256(raw).hexdigest()=='efcba9d1f36f2a472812ff5582a4d706c52f6a0360c7868cf2cfab34d5b072b7';(HERE/'generate01.py').write_bytes(raw);tree=ast.parse(raw)
sys.path.insert(0,str(PREP));spec=importlib.util.spec_from_file_location('witness_owned_io',PREP/'owned_io.py');oi=importlib.util.module_from_spec(spec);spec.loader.exec_module(oi)
def require(v,m):
 if not v:raise ValueError(m)
# Exact reader with one controlled owned-directory substitution during first read.
root=HERE/'owned-reader';root.mkdir();folder=root/'original';folder.mkdir();leaf=folder/'body';leaf.write_bytes(b'opaque owned metadata\n');moved=root/'retained-original';done=[]
def read(fd,n):
 b=os.read(fd,n)
 if not done:
  done.append(True);folder.rename(moved);folder.symlink_to(moved,target_is_directory=True)
 return b
proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in ('open','close','fstat','O_RDONLY','O_NOFOLLOW','O_NONBLOCK')},read=read)
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='read');ns={'FILE':4*1024**2,'os':proxy,'stat':stat,'require':require,'_cleanup':oi._cleanup};exec(compile(ast.Module(body=[node],type_ignores=[]),'<exact reader>','exec'),ns);result=ns['read'](leaf);assert result==b'opaque owned metadata\n' and folder.is_symlink() and leaf.resolve()!=leaf
# Exact output loop using an owned concrete buffered file subclass to inject a
# first-fatal write error; builtin context-manager close yields real EBADF.
import io
first=MemoryError('controlled original write fatal');ownedfd=[]
class Stream(io.BufferedWriter):
 def write(self,b):
  ownedfd.append(self.raw.fileno());os.close(self.raw.fileno());raise first
class Leaf:
 def open(self,mode):
  assert mode=='xb';return Stream(io.FileIO(HERE/'owned-writer','xb'))
class Output:
 def __truediv__(self,n):assert n=='tiny';return Leaf()
main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');loop=next(n for n in main.body if isinstance(n,ast.For));ns={'output':Output(),'bodies':{'tiny':b'opaque'}}
try:exec(compile(ast.Module(body=[loop],type_ignores=[]),'<exact main writer loop>','exec'),ns)
except BaseException as e:writer={'raised_type':type(e).__name__,'errno':getattr(e,'errno',None),'primary_preserved':e is first,'context_is_primary':e.__context__ is first,'fd_absent':not Path('/proc/self/fd/'+str(ownedfd[0])).exists()}
else:raise AssertionError('writer witness failed')
assert writer['raised_type']=='OSError' and writer['errno']==9 and writer['context_is_primary'] and not writer['primary_preserved'] and writer['fd_absent']
out={'reader':{'accepted_after_parent_redirect':True,'lexical_requested_path':str(leaf),'actual_resolved_path':str(leaf.resolve()),'opaque_sha256':hashlib.sha256(result).hexdigest(),'qualification':'Exact extracted reader; controlled read callback renames only owned directory and replaces it with a symlink; real file signatures and actual reads.'},'writer':writer,'writer_qualification':'Exact extracted main output loop; owned io.BufferedWriter subclass injects the write fatal, while real FileIO context-manager close supplies EBADF. This is source exception-order evidence, not an actual production write failure.','source_sha256':hashlib.sha256(raw).hexdigest(),'actual_capsule_created':False}
(HERE/'WITNESSES01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out))
