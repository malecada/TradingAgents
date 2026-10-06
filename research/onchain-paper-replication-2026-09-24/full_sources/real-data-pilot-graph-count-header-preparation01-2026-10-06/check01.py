import importlib.util,json,os,struct,sys
from pathlib import Path
H=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('counts',H/'header_counts01.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
def body(descr='<f8',shape=(3,4)):
 value=repr({'descr':descr,'fortran_order':False,'shape':shape}).encode();value+=b' '*((64-(10+len(value)+1)%64)%64)+b'\n'
 return b'\x93NUMPY\x01\x00'+struct.pack('<H',len(value))+value
fixture=H/'parser-fixture.npy';raw=body();fixture.write_bytes(raw+b'\0'*(3*4*8))
fd=os.open(fixture,os.O_RDONLY)
try:
 out=c.header(fd,fixture.stat().st_size,'node_features');assert out['shape']==[3,4] and os.lseek(fd,0,os.SEEK_CUR)==len(raw) and out['payload_bytes_read']==0
finally:os.close(fd)
refusals=[]
for name,raw,extent in [('object',body('|O',(3,)),152),('extent',body(),999),('huge',b'\x93NUMPY\x01\x00'+struct.pack('<H',10001),20000),('duplicate',b"\x93NUMPY\x01\x00"+struct.pack('<H',80)+b"{'descr':'<f8','descr':'<f8','shape':(1,1),'fortran_order':False}".ljust(79)+b'\n',98)]:
 p=H/(name+'.fixture');p.write_bytes(raw);fd=os.open(p,os.O_RDONLY)
 try:
  try:c.header(fd,extent,'node_features')
  except (ValueError,SyntaxError):refusals.append(name)
  else:raise AssertionError('accepted '+name)
 finally:os.close(fd)
assert len(refusals)==4 and not {'numpy','torch','networkx','scipy'} & sys.modules.keys()
(H/'CHECK01.json').write_text(json.dumps({'decision':'passed','valid_header_without_payload_read':True,'refusals':refusals,'scope':'Tiny synthetic NPY header bytes only; no real arrays/numeric imports/authority.'},indent=2)+'\n')
print('passed: header-only read and four finite refusals')
