"""Independent malformed framing and real concurrent source-change refusal."""
import copy,hashlib,importlib.util,json,shutil,sys,threading,time
from pathlib import Path
B=Path(__file__).resolve().parent;P=B.parent/'financial-outcome-chunked-preservation-preparation01-2026-10-04';sys.path.insert(0,str(P));spec=importlib.util.spec_from_file_location('review_framing_chunk',P/'chunk_archive01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);checks=[];cases=[]
def ok(v,label):
 if not v:raise AssertionError(label)
 checks.append(label)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
original=B/'owned01/archive-retained';index=json.loads((original/'index.json').read_bytes());root=B/'framing03';root.mkdir()
for case in ('missing','duplicate','swapped','extent','overlap','member-order','missing-parent','extra-root'):
 archive=root/case;shutil.copytree(original,archive);idx=copy.deepcopy(index);pages=[json.loads((archive[p['name']).read_bytes()) for p in idx['pages']];allrows=[r for p in pages for r in p];row=next(r for r in allrows if r['path']=='multi-chunk.bin')
 if case=='missing':row['chunks'].pop()
 elif case=='duplicate':row['chunks'].append(copy.deepcopy(row['chunks'][-1]))
 elif case=='swapped':row['chunks'].reverse()
 elif case=='extent':row['chunks'][0]['bytes']-=1
 elif case=='overlap':row['chunks'][1]=copy.deepcopy(row['chunks'][0])
 elif case=='member-order':pages[0].reverse()
 elif case=='missing-parent':next(r for r in allrows if r['path']=='hidden')['path']='hidden-renamed'
 elif case=='extra-root':row['root']='undeclared'
 for record,rows in zip(idx['pages'],pages,strict=True):
  raw=m.encode(rows);(archive/record['name']).write_bytes(raw);record.update(bytes=len(raw),sha256=m.sha(raw))
 # Deliberately new hash pin for a self-consistent envelope containing invalid framing.
 raw=m.encode(idx);(archive/'index.json').write_bytes(raw);pin=m.sha(raw)
 try:m.validate_archive(archive,pin,m.Bounds())
 except (ValueError,KeyError,FileNotFoundError) as e:cases.append({'case':case,'status':'refused','error_type':type(e).__name__,'reason':str(e)});checks.append(case+' invalid framing refused')
 else:raise AssertionError('accepted '+case)
# Natural whole-capture failure: thread adds one opaque source file after durable intent.
source=root/'mutable-source';source.mkdir()
for i in range(256):(source/('%04d'%i)).write_bytes(b'opaque control body\n')
(source/'z-chunk').write_bytes(b'x'*(1024*1024+17));dest=root/'failed-capture';observations={};ready=threading.Event()
def mutate():
 ready.set();deadline=time.monotonic()+5
 while time.monotonic()<deadline:
  if (dest/'intent.json').exists():
   (source/'changed-after-intent').write_bytes(b'actual owned source addition\n');observations['mutated']=True;return
  time.sleep(.0001)
 observations['mutated']=False
thread=threading.Thread(target=mutate);thread.start();ready.wait();error=None
try:m.capture({'opaque':str(source)},dest)
except BaseException as e:error=e
finally:thread.join(timeout=6)
ok(not thread.is_alive() and observations.get('mutated') is True,'owned concurrent mutation completed')
ok(isinstance(error,ValueError),'whole capture refused changed source')
ok((dest/'intent.json').exists() and (dest/'capture-failure.json').exists(),'actual partial intent/failure evidence retained')
receipt=json.loads((dest/'capture-failure.json').read_bytes());ok(receipt['status']=='failed' and receipt['error_type']=='ValueError','actual capture failure disposition')
ok((source/'changed-after-intent').read_bytes()==b'actual owned source addition\n','source failure bytes not deleted')
try:m.validate_archive(dest,'0'*64,m.Bounds())
except (ValueError,FileNotFoundError):checks.append('failed capture cannot validate complete')
else:raise AssertionError('partial accepted')
(B/'FRAMING_CHECKS03.json').write_text(json.dumps({'status':'passed','checks':len(checks),'labels':checks,'framing_cases':cases,'actual_failure':{'error_type':type(error).__name__,'error':str(error),'receipt':receipt,'partial_paths':sorted(p.name for p in dest.iterdir()),'thread_joined':not thread.is_alive()},'scope':'No monkeypatch; actual owned source changed concurrently after intent; no live source/Git/arrays/native jobs.'},sort_keys=True,indent=2)+'\n');print(json.dumps({'checks':len(checks),'actual_failure':str(error),'partial_members':len(list(dest.iterdir()))}))
