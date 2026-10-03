"""Lossless non-tail member planning; metadata/codec only, never authority.

The future genuine held adapter must derive every input field from admitted
original artifacts and retain all source/Owner/lease checks. These dictionaries
are plans, not archival/recovery receipts. No file, array, transport or owner IO.
"""
import hashlib,json,re
from pathlib import PurePosixPath
SCOPES=('graph','node_order','dictionary','ordered_motifs','matching','workflow')
FIELDS={'schema_version','kind','role','owner','stage_sha256','container_sha256','scope','path','dtype','order','rows','motifs','start_cell','cells','header_bytes','bytes','sha256','chunk_bytes'}
MAX_PART=1048576;MAX_PARTS=65536

def require(v,m):
 if not v:raise ValueError(m)
def sha(v):return type(v) is str and re.fullmatch('[0-9a-f]{64}',v) is not None
def validate(value):
 require(type(value) is dict and set(value)==FIELDS,'exact member fields required')
 require(type(value['schema_version']) is int and value['schema_version']==1 and value['kind']=='non-tail-exact-member-plan-v1','member schema differs')
 require(all(sha(value[k]) for k in ('owner','stage_sha256','container_sha256','sha256')),'original reference hashes required')
 require(type(value['scope']) is dict and set(value['scope'])==set(SCOPES) and all(sha(x) for x in value['scope'].values()),'exact scientific scope required')
 p=value['path'];require(type(p) is str and p and not PurePosixPath(p).is_absolute() and str(PurePosixPath(p))==p and '..' not in PurePosixPath(p).parts and '\\' not in p and '\x00' not in p,'relative member path required')
 for k in ('rows','motifs','start_cell','cells','header_bytes','bytes','chunk_bytes'):require(type(value[k]) is int and 0<=value[k]<2**63,'strict finite integer required')
 n=value['rows']*value['motifs'];require(value['rows']>0 and value['motifs']==32 and 0<value['cells']<=n and value['start_cell']+value['cells']<=n,'original32 cell extent differs')
 require(value['order']=='row-major' and 0<value['chunk_bytes']<=MAX_PART,'original order/part bound differs')
 role=value['role'];require(role in ('score-batch','mcm-output','graph-artifact-mcm'),'non-tail role differs')
 if role=='score-batch':require(value['dtype']=='<f8' and value['header_bytes']==0,'original float64 batch required');width=8
 else:
  width=4;require(value['dtype']=='<f4' and value['start_cell']==0 and value['cells']==n,'full original float32 matrix required')
  if role=='mcm-output':require(value['header_bytes']==0,'raw output must have no NPY header')
  else:require(0<value['header_bytes']<=65536,'exact original NPY header extent required')
 require(value['bytes']==width*value['cells']+value['header_bytes'],'member byte algebra differs')
 require((value['bytes']+value['chunk_bytes']-1)//value['chunk_bytes']<=MAX_PARTS,'finite member part denominator exceeded')
 raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode();require(len(raw)<=8192,'member metadata bound exceeded')
 return json.loads(raw)
def ranges(value):
 spec=validate(value)
 for offset in range(0,spec['bytes'],spec['chunk_bytes']):yield offset,min(spec['chunk_bytes'],spec['bytes']-offset)
def verify_parts(value,parts):
 """Hash one exact ordered byte stream; output is expressly not a capability."""
 spec=validate(value);expected=spec['sha256'];digest=hashlib.sha256();seen=0;iterator=iter(parts)
 for offset,count in ranges(spec):
  try:raw=next(iterator)
  except StopIteration:raise ValueError('missing exact member part') from None
  require(type(raw) is bytes and len(raw)==count,'part order/extent differs');digest.update(raw);seen+=len(raw)
 try:next(iterator)
 except StopIteration:pass
 else:raise ValueError('extra member part')
 require(seen==spec['bytes'] and digest.hexdigest()==expected,'full original member hash differs')
 return {'kind':'unadmitted-byte-stream-observation','sha256':expected,'bytes':seen,'execution_admitted':False,'recovery_authority':False}
def activate(*args,**kwargs):
 raise RuntimeError('genuine held Owner/Target, original transport Context and reviewed disposition/recovery integration required')
