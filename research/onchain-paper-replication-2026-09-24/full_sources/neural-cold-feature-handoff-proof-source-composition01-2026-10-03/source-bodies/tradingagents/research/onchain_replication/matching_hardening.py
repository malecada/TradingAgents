"""Isolated ranked hardening with bounded scan checkpoints after atomic sorting.

Exclusive state ownership is required. Input identity is verified at creation;
callers must independently verify the frozen matrix identity after restoration.
The trusted outer hash binds the order body and metadata; structural checking
is not a replay of the greedy prefix. No production integration is implied.
"""
from pathlib import Path
import hashlib,json,os
from . import score_batches as io
import numpy as np
FIELDS={'version','safe','phase','shape','input_sha256','max_pair_entries','max_explicit_bytes','cursor','pairs','order'}
META_FIELDS=FIELDS-{'order'}|{'order_sha256','order_bytes'}
LIMIT=65536


def explicit_bytes(n,m):return 17*n*m+n+m+16*min(n,m)
def valid_hash(s):return isinstance(s,str) and len(s)==64 and all(c in '0123456789abcdef' for c in s)
def policy(n,m,pairs,buffer):
    if type(pairs) is not int or pairs<=0 or type(buffer) is not int or buffer<=0 or n*m>pairs or explicit_bytes(n,m)>buffer:
        raise ValueError('rank numeric capacity exceeded')
def sha(path):
    h=hashlib.sha256()
    with io._opened(Path(path),'rb') as f:
        while b:=f.read(1024**2):h.update(b)
    return h.hexdigest()
def sync(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally: io._release(lambda: os.close(fd))
def body(d):return (json.dumps(d,sort_keys=True,separators=(',',':'))+'\n').encode()


def create(x,*,max_pair_entries,max_explicit_bytes):
    if not isinstance(x,np.ndarray) or x.ndim!=2 or x.dtype!=np.float64 or not x.flags.c_contiguous or np.dtype(np.intp).itemsize!=8:
        raise ValueError('C-order float64 input and 64-bit platform required')
    n,m=x.shape;policy(n,m,max_pair_entries,max_explicit_bytes)
    key=x.copy().reshape(-1)
    if not np.isfinite(key).all():raise ValueError('nonfinite assignment')
    identity=hashlib.sha256(memoryview(x.reshape(-1)).cast('B')).hexdigest()
    np.negative(key,out=key);order=np.argsort(key,kind='stable');del key
    order.flags.writeable=False
    s=dict(version=1,safe=True,phase='scan' if min(n,m) else 'done',shape=[n,m],input_sha256=identity,max_pair_entries=max_pair_entries,max_explicit_bytes=max_explicit_bytes,cursor=0,pairs=[],order=order)
    check(s);return s


def _check_metadata(s):
    if not isinstance(s,dict) or set(s)!=FIELDS or type(s['version']) is not int or s['version']!=1 or s['safe'] is not True:raise ValueError('invalid or poisoned state')
    shape=s['shape']
    if not isinstance(shape,list) or len(shape)!=2 or any(type(v) is not int or v<0 for v in shape):raise ValueError('invalid shape')
    n,m=shape;policy(n,m,s['max_pair_entries'],s['max_explicit_bytes'])
    if not valid_hash(s['input_sha256']) or type(s['cursor']) is not int or not 0<=s['cursor']<=n*m:raise ValueError('identity or cursor differs')
    pairs=s['pairs']
    if not isinstance(pairs,list) or len(pairs)>min(n,m):raise ValueError('invalid pairs')
    rows=set();cols=set()
    for pair in pairs:
        if not isinstance(pair,list) or len(pair)!=2 or any(type(v) is not int for v in pair):raise ValueError('invalid pair')
        u,i=pair
        if not 0<=u<n or not 0<=i<m or u in rows or i in cols:raise ValueError('noninjective pair')
        rows.add(u);cols.add(i)
    if s['phase'] not in ('scan','done') or (s['phase']=='done')!=(len(pairs)==min(n,m)):raise ValueError('phase differs')
    if s['cursor']<len(pairs) or (s['cursor']>0 and not pairs) or (s['phase']=='scan' and s['cursor']==n*m):raise ValueError('unreachable cursor')


def check(s):
    _check_metadata(s)
    n,m=s['shape'];o=s['order']
    if not isinstance(o,np.ndarray) or o.dtype!=np.int64 or o.shape!=(n*m,) or not o.flags.c_contiguous or o.flags.writeable:raise ValueError('immutable order required')


def close(s):
    """Invalidate an exclusively owned state and close its successful mapping."""
    s['safe']=False
    order=s.get('order')
    mapping=getattr(order,'_mmap',None)
    s['order']=None
    if mapping is not None:io._cleanup((mapping.close,))


def _accept(s,index,rows,cols):
    n,m=s['shape'];u,i=divmod(int(index),m)
    if not 0<=u<n:raise ValueError('order entry out of bounds')
    if not rows[u] and not cols[i]:s['pairs'].append([u,i]);rows[u]=True;cols[i]=True


def advance(s,*,input_sha256,max_entries):
    check(s)
    if input_sha256!=s['input_sha256'] or type(max_entries) is not int or not 0<max_entries<=65536:raise ValueError('identity or scan allowance differs')
    if s['phase']=='done':return 0
    n,m=s['shape'];rows=np.zeros(n,dtype=np.bool_);cols=np.zeros(m,dtype=np.bool_)
    for u,i in s['pairs']:rows[u]=True;cols[i]=True
    s['safe']=False;used=0
    try:
        while used<max_entries and s['cursor']<n*m:
            _accept(s,s['order'][s['cursor']],rows,cols);s['cursor']+=1;used+=1
            if len(s['pairs'])==min(n,m):s['phase']='done';break
        s['safe']=True;check(s);return used
    except BaseException:s['safe']=False;raise


def save(s,directory,*,max_checkpoint_bytes):
    check(s)
    # 128-byte NPY header is asserted after writing; reserve a full manifest cap.
    if type(max_checkpoint_bytes) is not int or max_checkpoint_bytes<s['order'].nbytes+128+LIMIT:raise ValueError('checkpoint allowance exceeded')
    meta={k:v for k,v in s.items() if k!='order'}
    if len(body(meta|{'order_sha256':'0'*64,'order_bytes':s['order'].nbytes+128}))>LIMIT:raise ValueError('metadata allowance exceeded')
    directory=Path(directory);directory.mkdir(exist_ok=False);sync(directory.parent)
    path=directory/'order.npy'
    with io._opened(path,'xb') as f:np.save(f,s['order'],allow_pickle=False);f.flush();os.fsync(f.fileno())
    if path.stat().st_size!=s['order'].nbytes+128:raise ValueError('NPY extent differs')
    meta.update(order_sha256=sha(path),order_bytes=path.stat().st_size);raw=body(meta)
    with io._opened(directory/'manifest.json','xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    sync(directory);return hashlib.sha256(raw).hexdigest()


def load(directory,*,expected_sha256,input_sha256,max_pair_entries,max_explicit_bytes):
    directory=Path(directory);manifest=directory/'manifest.json';path=directory/'order.npy'
    if directory.is_symlink() or manifest.is_symlink() or not manifest.is_file() or manifest.stat().st_size>LIMIT or sha(manifest)!=expected_sha256:raise ValueError('manifest identity differs')
    d=json.loads(io._read_path(manifest,LIMIT))
    if not isinstance(d,dict) or set(d)!=META_FIELDS or d['input_sha256']!=input_sha256 or d['max_pair_entries']!=max_pair_entries or d['max_explicit_bytes']!=max_explicit_bytes:raise ValueError('schema, input or policy differs')
    shape=d['shape']
    if not isinstance(shape,list) or len(shape)!=2 or any(type(v) is not int or v<0 for v in shape):raise ValueError('invalid shape')
    n,m=shape;policy(n,m,max_pair_entries,max_explicit_bytes)
    if type(d['order_bytes']) is not int or d['order_bytes']!=8*n*m+128 or not valid_hash(d['order_sha256']) or path.is_symlink() or not path.is_file() or path.stat().st_size!=d['order_bytes'] or sha(path)!=d['order_sha256']:raise ValueError('order body differs')
    d.pop('order_bytes');d.pop('order_sha256');d['order']=None
    _check_metadata(d)  # Refuse malformed compact state before mapping the body.
    order=None
    try:
        order=np.load(path,mmap_mode='r',allow_pickle=False,max_header_size=128)
        d['order']=order;check(d);return d
    except BaseException as error:
        mapping=getattr(order,'_mmap',None)
        d['order']=None
        if mapping is not None:io._close_after_failure(mapping.close,error)
        raise
