"""Changed metadata composition checks. Fake transport conveys no authority."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
s=importlib.util.spec_from_file_location('successor',HERE/'continue01.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
review_name=h.STUDY+'/full_sources/real-data-pilot-second-graph-storage-outcome-review01-2026-10-06/FAILED_REVIEW02.json'
review_ref={'path':review_name,'sha256':'7516cd31e3218d8d3ae22130db9968dc6a61175f0716fe3bf8893ae2ff69c687'}
review=h.doc(ROOT,review_ref);binding={'review':review_ref,'metadata':review['metadata_check'],'outcome':review['outcome_check']};m=h.doc(ROOT,binding['metadata'])
protected={ROOT/r[k] for r in m['rows'] for k in ('original_path','recovered_path')}
original_open=Path.open
opens=[]
def bounded_open(p,*args,**kwargs):
 assert p not in protected,'payload body was opened';opens.append(str(p));return original_open(p,*args,**kwargs)
# h.raw uses os.open for compact receipts; also forbid those against bodies.
original_osopen=h.os.open
def bounded_osopen(p,*args,**kwargs):
 assert Path(p) not in protected,'payload body was opened through os.open';return original_osopen(p,*args,**kwargs)
Path.open=bounded_open;h.os.open=bounded_osopen
try:
 actual=h.select(ROOT,binding);parent=h.parent_state(ROOT,binding)
 bad=copy.deepcopy(binding);bad['review']['sha256']='0'*64
 try:h.parent_state(ROOT,bad)
 except ValueError as e:assert 'hash/currentness' in str(e)
 else:raise AssertionError('unanchored proof accepted')
finally:Path.open=original_open;h.os.open=original_osopen
assert actual['body_transfer_count']==0 and actual['missing_rows']==[35] and actual['original_count']==36
primitives=h.bind_primitives(ROOT)
# Exact source inversion of entry; imports/launch/native paths are not executed.
c=json.loads((HERE/'ENTRY_CHANGE01.json').read_bytes());entry=(HERE/'entry01.py').read_text()
for change in reversed(c['literal_edits']):assert entry.count(change['after'])==1;entry=entry.replace(change['after'],change['before'])
assert hashlib.sha256(entry.encode()).hexdigest()==c['before_sha256']
# Synthetic file currentness refusal; no genuine inherited evidence modified.
f=HERE/'synthetic-stat.bin';f.write_bytes(b'x');pin=h.identity(f.stat());mode=f.stat().st_mode&0o7777;f.write_bytes(b'y')
try:h.current(HERE,f.name,pin,mode)
except ValueError as e:assert 'stat/mode differs' in str(e)
else:raise AssertionError('changed inherited file accepted')
# Worker sequencing only: synthetic parent boundary and local byte transport.
# These stubs are deliberately not Admission/Owner/native or external evidence.
h.parent_state=lambda root,binding:copy.deepcopy(parent)
h.bind_primitives=lambda root:primitives
class Fake:
 def __init__(self,corrupt=False):self.remaining=8*h.GIB;self.objects={};self.calls=[];self.corrupt=corrupt
 def available(self):return 16*1024**2
 def mkdir(self,name):self.calls.append(('mkdir',name))
 def put(self,p,name):
  assert Path(p).parent.name==h.ID and Path(p).suffix=='.json';b=Path(p).read_bytes();assert len(b)<=h.LIMIT;self.objects[name]=b;self.calls.append(('put',name))
 def get(self,name,p):
  b=self.objects[name];Path(p).write_bytes(b'bad' if self.corrupt else b);Path(str(p)+'.transport.json').write_text(json.dumps({'status':'complete','returncode':0,'expected_bytes':len(b),'received_bytes':len(b)}));self.calls.append(('get',name))
records=[]
for label,corrupt in [('synthetic-success',False),('synthetic-corrupt',True)]:
 root=HERE/label;dest=root/h.DEST;dest.mkdir(parents=True);selection=h.select(root,binding);t=Fake(corrupt)
 try:result=h.preserve_selected(root,dest,selection,t,lambda:None)
 except ValueError as e:
  assert corrupt and 'recovery differs' in str(e);assert (dest/'failed.json').exists() and not (dest/'complete.json').exists()
 else:
  assert not corrupt and result['count']==36 and result['parent_status']=='FAILED' and result['fresh_body_transfers']==0
  assert len([c for c in t.calls if c[0]=='put'])==2 and len([c for c in t.calls if c[0]=='get'])==2
  assert json.loads((dest/'complete.json').read_bytes())==json.loads((dest/'recovered-complete.json').read_bytes())
  previous=len(t.calls)
  try:h.preserve_selected(root,dest,selection,t,lambda:None)
  except FileExistsError:pass
  else:raise AssertionError('one-use identity retried')
  assert len(t.calls)==previous
 records.append({'synthetic_case':label,'calls':t.calls})
assert 'numpy' not in sys.modules and 'torch' not in sys.modules
record={'actual_inherited_body_stat_checks':36,'actual_body_opens':0,'actual_missing_metadata_rows':[35],'actual_parent_reclassified':False,'wrong_proof_refused':True,'changed_stat_refused':True,'entry_exact_inverse':True,'synthetic_metadata_only_cases':records,'scope':'actual compact metadata/stat joins plus synthetic transport sequencing; no external/native operation or authority'}
(HERE/'CHECK01.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
