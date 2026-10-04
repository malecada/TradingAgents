"""Opaque byte framing only. No numerical conversion, live authority or transport.

Source.read(n), sink(name, bytes), reader(name), and provisional(raw) are bounded
callbacks. A decoder callback must quarantine bytes until final success. Callback
blocking/resource enforcement belongs to an outer supervisor; sampled deadlines
are not preemption. No callback return is a remote preservation receipt.
"""
import hashlib,json,math,struct,time
FILE=4*1024**2
CHUNK=1024**2
META=65536
PAGE=64
MAX_BYTES=9239969792
MAX_CHUNKS=16384
SECONDS=1800
SCOPE={'graph','node_order','dictionary','ordered_motifs','matching','workflow'}
DTYPES={'<f8':8,'<f4':4}
HEADER=struct.Struct('<8sQQQ32s32s')
MAGIC=b'MCMBYTE1'

def require(v,m):
 if not v:raise ValueError(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(v):
 b=(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
 require(len(b)<=META,'metadata cap');return b
def pin(v):require(type(v)is str and len(v)==64 and all(c in '0123456789abcdef' for c in v),'SHA256 required')
def parse(raw):
 require(type(raw)is bytes and len(raw)<=META,'metadata byte bound')
 value=json.loads(raw);require(canonical(value)==raw,'canonical metadata required');return value

def descriptor(d):
 require(type(d)is dict and set(d)=={'schema_version','kind','role','dtype','shape','order','scope','motifs','spent_samples'},'descriptor schema')
 require(type(d['schema_version'])is int and d['schema_version']==1 and d['kind']=='mcm-batch-output-bytes','descriptor version')
 require(d['role'] in ('score-batches','mcm-output') and d['dtype']==({'score-batches':'<f8','mcm-output':'<f4'}[d['role']]),'original role/dtype; no cast')
 require(d['order']=='C' and type(d['shape'])is list and len(d['shape'])==2 and all(type(x)is int and x>0 for x in d['shape']),'positive matrix shape and C order')
 require(type(d['motifs'])is int and d['motifs']==32 and d['shape'][1]==32 and type(d['spent_samples'])is int and d['spent_samples']==512,'original dictionary cardinality')
 require(type(d['scope'])is dict and set(d['scope'])==SCOPE,'complete original scientific scope')
 for v in d['scope'].values():pin(v)
 size=math.prod(d['shape'])*DTYPES[d['dtype']];require(size<=MAX_BYTES,'finite logical payload bound')
 canonical(d);return size

def deadline(start):require(time.monotonic()-start<=SECONDS,'codec sampled deadline')
def _read(source,n):
 result=bytearray()
 while len(result)<n:
  b=source.read(n-len(result));require(type(b)is bytes and len(b)<=n-len(result),'source bounded bytes contract')
  if not b:break
  result.extend(b)
 require(len(result)==n,'truncated raw payload');return bytes(result)

def encode_stream(source,d,sink,*,chunk_bytes=CHUNK):
 total=descriptor(d);d=parse(canonical(d));start=time.monotonic()
 require(type(chunk_bytes)is int and 0<chunk_bytes<=CHUNK and chunk_bytes%DTYPES[d['dtype']]==0,'aligned finite chunk size')
 count=(total+chunk_bytes-1)//chunk_bytes;require(count<=MAX_CHUNKS,'finite chunk cardinality')
 spec={'schema_version':1,'descriptor':d,'logical_bytes':total,'chunk_bytes':chunk_bytes,'chunks':count,'page_rows':PAGE}
 spec_raw=canonical(spec);head=spec_pin=sha(spec_raw);sink('start.json',spec_raw)
 whole=hashlib.sha256();rows=[];pages=[];offset=0
 for i in range(count):
  deadline(start);raw=_read(source,min(chunk_bytes,total-offset));whole.update(raw)
  frame=HEADER.pack(MAGIC,i,offset,len(raw),bytes.fromhex(spec_pin),bytes.fromhex(head))+raw
  frame+=hashlib.sha256(frame).digest();require(len(frame)<=FILE,'framed file cap')
  name=f'chunk-{i:05d}.bin';head=sha(frame);sink(name,frame)
  rows.append({'index':i,'offset':offset,'bytes':len(raw),'name':name,'frame_sha256':head,'raw_sha256':sha(raw)})
  offset+=len(raw)
  if len(rows)==PAGE or i==count-1:
   page={'schema_version':1,'start_sha256':spec_pin,'index':len(pages),'rows':rows};body=canonical(page);name=f'page-{len(pages):04d}.json';sink(name,body)
   pages.append({'name':name,'sha256':sha(body)});rows=[]
 require(source.read(1)==b'','extra raw payload');deadline(start)
 terminal={'schema_version':1,'kind':'complete-byte-proof-only','start_sha256':spec_pin,'logical_bytes':total,'chunks':count,'head':head,'raw_sha256':whole.hexdigest(),'pages':pages}
 body=canonical(terminal);sink('terminal.json',body);deadline(start)
 return sha(body)

def verify_stream(reader,terminal_pin,expected,provisional=lambda raw:None):
 """Failing verification can have delivered a prefix; never publish it as complete."""
 start=time.monotonic();total=descriptor(expected);expected=parse(canonical(expected));pin(terminal_pin)
 terminal_raw=reader('terminal.json');require(sha(terminal_raw)==terminal_pin,'terminal external pin');t=parse(terminal_raw)
 require(set(t)=={'schema_version','kind','start_sha256','logical_bytes','chunks','head','raw_sha256','pages'} and type(t['schema_version'])is int and t['schema_version']==1 and t['kind']=='complete-byte-proof-only','terminal schema')
 for k in ('start_sha256','head','raw_sha256'):pin(t[k])
 raw=reader('start.json');require(sha(raw)==t['start_sha256'],'start pin');s=parse(raw)
 require(set(s)=={'schema_version','descriptor','logical_bytes','chunk_bytes','chunks','page_rows'} and type(s['schema_version'])is int and s['schema_version']==1 and canonical(s['descriptor'])==canonical(expected),'exact descriptor')
 descriptor(s['descriptor']);chunk=s['chunk_bytes'];require(type(chunk)is int and 0<chunk<=CHUNK and chunk%DTYPES[expected['dtype']]==0,'chunk alignment/bound')
 count=(total+chunk-1)//chunk;require(count<=MAX_CHUNKS and type(s['chunks'])is int and type(t['chunks'])is int and s['chunks']==t['chunks']==count and type(s['logical_bytes'])is int and type(t['logical_bytes'])is int and s['logical_bytes']==t['logical_bytes']==total and type(s['page_rows'])is int and s['page_rows']==PAGE,'full denominator')
 require(type(t['pages'])is list and len(t['pages'])==(count+PAGE-1)//PAGE,'page count')
 head=t['start_sha256'];whole=hashlib.sha256();index=offset=0;names=['start.json','terminal.json']
 for pnum,ref in enumerate(t['pages']):
  deadline(start);require(type(ref)is dict and set(ref)=={'name','sha256'} and ref['name']==f'page-{pnum:04d}.json','page order/path');pin(ref['sha256'])
  body=reader(ref['name']);require(sha(body)==ref['sha256'],'page pin');p=parse(body);names.append(ref['name'])
  require(set(p)=={'schema_version','start_sha256','index','rows'} and type(p['schema_version'])is int and p['schema_version']==1 and p['start_sha256']==t['start_sha256'] and type(p['index'])is int and p['index']==pnum and type(p['rows'])is list and len(p['rows'])==min(PAGE,count-index),'page schema/count')
  for row in p['rows']:
   require(type(row)is dict and set(row)=={'index','offset','bytes','name','frame_sha256','raw_sha256'},'row schema')
   length=min(chunk,total-offset);name=f'chunk-{index:05d}.bin'
   require(all(type(row[k])is int for k in ('index','offset','bytes')) and (row['index'],row['offset'],row['bytes'],row['name'])==(index,offset,length,name),'ordered exact chunk coverage')
   pin(row['frame_sha256']);pin(row['raw_sha256']);frame=reader(name)
   require(type(frame)is bytes and len(frame)==HEADER.size+length+32<=FILE and sha(frame)==row['frame_sha256'],'frame length/hash')
   require(HEADER.unpack(frame[:HEADER.size])==(MAGIC,index,offset,length,bytes.fromhex(t['start_sha256']),bytes.fromhex(head)),'frame header/chain')
   require(hashlib.sha256(frame[:-32]).digest()==frame[-32:],'frame footer')
   data=frame[HEADER.size:-32];require(sha(data)==row['raw_sha256'],'raw chunk hash')
   whole.update(data);head=row['frame_sha256'];index+=1;offset+=length;names.append(name);provisional(data);deadline(start)
 require(index==count and offset==total and head==t['head'] and whole.hexdigest()==t['raw_sha256'],'whole payload footer')
 return {'status':'complete-byte-proof-only','logical_bytes':total,'raw_sha256':whole.hexdigest(),'members':sorted(names),'authority':None,'representation_complete':False}

def publish_live(owner,binding,target,*args,**kwargs):
 raise ValueError('UNAVAILABLE: genuine Owner/Binding/Target codec integration, registered production ancestry, transport, recovery and resource release have not been implemented/admitted; metadata is not authority')
