from pathlib import Path
import types,os,json
D=Path(__file__).resolve().parent;P=D.parent/'financial-wrapper-compatibility-coalesced-evidence-preparation03-2026-10-04';M=types.ModuleType('copier');M.__file__=str(P/'copy_layout01.py');exec(compile((P/'copy_layout01.py').read_bytes(),M.__file__,'exec'),M.__dict__);root=D/'owned-iterator-controls';root.mkdir(mode=0o700);rows=[]
classes=[ValueError,OSError,MemoryError,KeyboardInterrupt,SystemExit];fatal=lambda e:isinstance(e,MemoryError) or not isinstance(e,Exception)
for pc in classes:
 for sc in classes:
  primary=pc('first actual scan failure');secondary=sc('actual closed iterator failure');closed=[]
  class Iterator:
   def __init__(self,p):self.it=os.scandir(p)
   def __iter__(self):return self
   def __next__(self):next(self.it,None);raise primary
   def close(self):self.it.close();closed.append(True);raise secondary
  proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});proxy.scandir=Iterator;original=M.os;M.os=proxy
  try:
   try:M.namespace(root)
   except BaseException as actual:
    expected=primary if fatal(primary) else secondary if fatal(secondary) else None
    assert actual is expected if expected is not None else isinstance(actual,M.IO.CleanupFailure)
    state=BaseException.__dict__['__dict__'].__get__(actual);assert actual is secondary or secondary in state.get('layout_cleanup_errors',()) or secondary in state.get('failures',())
    assert closed==[True];rows.append({'body':pc.__name__,'close':sc.__name__,'selected':type(actual).__name__,'closed_once':True,'secondary_preserved':True})
   else:raise AssertionError('failure accepted')
  finally:M.os=original
(D/'ITERATOR_CONTROLS01.json').write_text(json.dumps({'actual_iterator_pairs':rows,'count':len(rows),'public_entry':False},indent=2)+'\n');print(len(rows))
