from pathlib import Path
import types,os,time,json,hashlib
D=Path(__file__).resolve().parent;P=D.parent/'financial-wrapper-compatibility-coalesced-evidence-preparation03-2026-10-04';source=(P/'copy_layout01.py').read_bytes();assert hashlib.sha256(source).hexdigest()=='068147e5d5b20717b8ac54c5ac055c4826076e2b110fff9248a206fa49858b04';M=types.ModuleType('actual_copier');M.__file__=str(P/'copy_layout01.py');exec(compile(source,M.__file__,'exec'),M.__dict__)
root=D/'owned-empty-census';root.mkdir(mode=0o700);proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});closed=[]
class LateClose:
 def __init__(self,p):self.it=os.scandir(p)
 def __iter__(self):return self
 def __next__(self):return next(self.it)
 def close(self):self.it.close();closed.append(True);time.sleep(5.1)
proxy.scandir=LateClose;M.os=proxy;start=time.monotonic();result=M.namespace(root);elapsed=time.monotonic()-start
assert closed==[True] and result['members']=={} and elapsed>5
q={'source_sha256':hashlib.sha256(source).hexdigest(),'result':'RETURNED_SUCCESS_BEYOND_DECLARED_5_SECOND_CENSUS','elapsed_seconds':elapsed,'actual_iterator_closed_once':closed==[True],'real_sleep_seconds':5.1,'owned_root':str(root),'actual_namespace_result':result,'public_run_invoked':False,'fixed_Root_output_absent':not M.OUTPUT.exists()};(D/'CENSUS_DEADLINE_WITNESS01.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q))
