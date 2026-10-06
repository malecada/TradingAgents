"""Bounded header boundary and real get-method storage-domain witness; synthetic only."""
import ast,hashlib,importlib.util,json,os,struct,tempfile
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parent;ROOT=H.parents[3]
S=H.parent/'real-data-pilot-graph-count-header-preparation01-2026-10-06'
spec=importlib.util.spec_from_file_location('header_review',S/'header_counts01.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
with tempfile.TemporaryDirectory(dir=H) as t:
 p=Path(t)/'header.fixture';head=b"{'descr': '<f8', 'fortran_order': False, 'shape': (2, 4)}\n";prefix=b'\x93NUMPY\x02\x00'+struct.pack('<I',len(head));raw=prefix+head+b'X'*64;p.write_bytes(raw)
 with p.open('rb') as f:
  result=h.header(f.fileno(),len(raw),'node_features');assert result['shape']==[2,4] and os.lseek(f.fileno(),0,os.SEEK_CUR)==len(prefix+head)
 with p.open('rb') as f:
  try:h.header(f.fileno(),len(raw)-1,'node_features')
  except ValueError as error:assert 'extent differs' in str(error)
  else:raise AssertionError('shape extent mismatch accepted')
 source=ROOT/'tradingagents/research/onchain_replication/archive_transport.py';tree=ast.parse(source.read_text());cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='Transport');fn=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='get')
 def receive(command,destination,**kwargs):
  destination.write_bytes(b'Z'*kwargs['expected_bytes']);Path(str(destination)+'.transport.json').write_text('{}')
 ns={'Path':Path,'os':os,'BLOCK_BYTES':65536,'archive':SimpleNamespace(MAX_BYTES=4*1024**2),'receive_diagnostic':receive,'sync_directory':lambda path:None}
 exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),ns)
 diagnostics=Path(t)/'diagnostics';diagnostics.mkdir();index=0;reserved=[]
 def next_path(kind):
  global index
  index+=1;return diagnostics/f'{kind}-{index:04d}.bin'
 obj=SimpleNamespace(remote_path=lambda x:x,reserve=reserved.append,next=next_path,live=lambda:None,ssh=['synthetic'],max_seconds=1,rate_bytes=1,diagnostics=diagnostics)
 for i in range(3):ns['get'](obj,'synthetic',Path(t)/f'destination-{i}',expected_bytes=1024)
 assert not list(diagnostics.glob('*.bin')) and len(list(diagnostics.glob('*.transport.json')))==3
 assert sum(x.stat().st_size for x in diagnostics.iterdir())==6 and sum(reserved)==3*65536
 print(json.dumps({'passed':True,'header_v2_exact_boundary':True,'payload_bytes_read':0,'extent_mismatch_refused':True,'successful_gets':3,'retained_diagnostic_body_bytes':0,'retained_diagnostic_metadata_bytes':6,'cumulative_reserved_payload_bytes':sum(reserved),'native_network_or_genuine_authority':False},indent=2))
