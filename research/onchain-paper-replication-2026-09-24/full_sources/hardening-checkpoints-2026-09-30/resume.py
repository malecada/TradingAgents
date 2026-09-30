"""Isolated exact greedy hardening, resumable at bounded scan-chunk boundaries.

Caller must verify and freeze the matrix named by input_sha256 for the entire
operation. This component compares that external identity; it does not hash the
matrix itself. Numeric scratch allowance excludes input/Python/JSON residency.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import numpy as np

FIELDS={'version','input_sha256','shape','dtype','chunk_entries','max_buffer_bytes',
        'phase','cursor','pairs','best_index','best_value','safe'}


def check(s):
 if set(s)!=FIELDS or type(s['version']) is not int or s['version']!=1 or s['safe'] is not True:raise ValueError('unsafe or invalid state')
 if not isinstance(s['input_sha256'],str) or not re.fullmatch('[0-9a-f]{64}',s['input_sha256']):raise ValueError('external input identity required')
 if not isinstance(s['shape'],list) or len(s['shape'])!=2 or any(type(x) is not int or x<0 for x in s['shape']):raise ValueError('shape differs')
 dtype=np.dtype(s['dtype'])
 if dtype.kind not in 'biuf' or dtype.itemsize>8:raise ValueError('real matrix required')
 n,m=s['shape'];entries=n*m;matches=min(n,m)
 for name in ('chunk_entries','max_buffer_bytes'):
  if type(s[name]) is not int or s[name]<=0:raise ValueError('positive resource bounds required')
 if s['chunk_entries']>65536 or 48*matches+64*min(s['chunk_entries'],entries)>s['max_buffer_bytes']:raise ValueError('numeric scratch allowance exceeded')
 pairs=s['pairs']
 if not isinstance(pairs,list) or len(pairs)>matches or any(not isinstance(p,list) or len(p)!=2 or any(type(x) is not int for x in p) or not 0<=p[0]<n or not 0<=p[1]<m for p in pairs):raise ValueError('invalid pairs')
 if len({p[0] for p in pairs})!=len(pairs) or len({p[1] for p in pairs})!=len(pairs):raise ValueError('noninjective pairs')
 phase=s['phase'];cursor=s['cursor']
 if phase not in ('validate','scan','done') or type(cursor) is not int or cursor<0 or cursor%s['chunk_entries']:raise ValueError('invalid phase/cursor')
 if phase=='done':
  if len(pairs)!=matches or cursor or s['best_index'] is not None or s['best_value'] is not None:raise ValueError('unreachable completion')
 elif not entries or cursor>=entries or len(pairs)>=matches:raise ValueError('unreachable progress')
 if phase=='validate' and (pairs or s['best_index'] is not None or s['best_value'] is not None):raise ValueError('selection before validation')
 if (s['best_index'] is None)!=(s['best_value'] is None):raise ValueError('incomplete best entry')
 if s['best_index'] is not None:
  index=s['best_index'];value=s['best_value']
  if phase!='scan' or type(index) is not int or not 0<=index<cursor or type(value) not in (int,float) or not math.isfinite(value):raise ValueError('invalid best entry')
  row,col=divmod(index,m)
  if row in {p[0] for p in pairs} or col in {p[1] for p in pairs}:raise ValueError('ineligible best entry')


def create(matrix,*,input_sha256,max_buffer_bytes,chunk_entries=65536):
 if not isinstance(matrix,np.ndarray) or matrix.ndim!=2:raise ValueError('two dimensional ndarray required')
 s={'version':1,'input_sha256':input_sha256,'shape':list(matrix.shape),'dtype':matrix.dtype.str,
    'chunk_entries':chunk_entries,'max_buffer_bytes':max_buffer_bytes,'phase':'validate' if matrix.size else 'done',
    'cursor':0,'pairs':[],'best_index':None,'best_value':None,'safe':True}
 check(s);return s


def advance(s,matrix,*,input_sha256,max_chunks):
 check(s)
 if type(max_chunks) is not int or max_chunks<=0:raise ValueError('positive chunk budget required')
 if not isinstance(matrix,np.ndarray) or list(matrix.shape)!=s['shape'] or matrix.dtype.str!=s['dtype'] or input_sha256!=s['input_sha256']:raise ValueError('external input binding differs')
 s['safe']=False
 try:
  n,m=s['shape'];entries=n*m;used=0
  while used<max_chunks and s['phase']!='done':
   start=s['cursor'];stop=min(entries,start+s['chunk_entries'])
   values=np.asarray(matrix.flat[start:stop],dtype=np.float64)
   if s['phase']=='validate':
    if not np.isfinite(values).all():raise ValueError('nonfinite soft assignment')
    s['cursor']=stop
    if stop==entries:s.update(phase='scan',cursor=0)
   else:
    indexes=np.arange(start,stop,dtype=np.int64);rows=indexes//m;cols=indexes%m
    if s['pairs']:
     taken=np.asarray(s['pairs'],dtype=np.int64);used_rows=np.sort(taken[:,0]);used_cols=np.sort(taken[:,1]);step=len(taken)
     positions=np.searchsorted(used_rows,rows);np.minimum(positions,step-1,out=positions);values[used_rows[positions]==rows]=-np.inf
     positions=np.searchsorted(used_cols,cols);np.minimum(positions,step-1,out=positions);values[used_cols[positions]==cols]=-np.inf
     del taken,used_rows,used_cols,positions
    offset=int(np.argmax(values));value=float(values[offset])
    if value!=-np.inf and (s['best_value'] is None or value>s['best_value']):s.update(best_value=value,best_index=start+offset)
    s['cursor']=stop
    if stop==entries:
     if s['best_index'] is None:raise ValueError('no feasible entry')
     s['pairs'].append(list(divmod(s['best_index'],m)))
     s.update(cursor=0,best_index=None,best_value=None,phase='done' if len(s['pairs'])==min(n,m) else 'scan')
    del indexes,rows,cols
   del values
   used+=1
  s['safe']=True
  return used
 except BaseException:
  s['safe']=False
  raise


def save(s,path,*,max_checkpoint_bytes):
 check(s)
 if type(max_checkpoint_bytes) is not int or max_checkpoint_bytes<=0:raise ValueError('positive checkpoint bound required')
 raw=(json.dumps(s,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
 if len(raw)>max_checkpoint_bytes:raise ValueError('checkpoint bound exceeded')
 path=Path(path)
 with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 fd=os.open(path.parent,os.O_DIRECTORY|os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
 return hashlib.sha256(raw).hexdigest()


def load(path,*,expected_sha256,max_checkpoint_bytes):
 path=Path(path)
 if type(max_checkpoint_bytes) is not int or max_checkpoint_bytes<=0 or path.is_symlink() or path.stat().st_size>max_checkpoint_bytes:raise ValueError('checkpoint bound or path differs')
 raw=path.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=expected_sha256:raise ValueError('checkpoint hash differs')
 s=json.loads(raw);check(s);return s
