import runpy,tempfile,json
from pathlib import Path
ns=runpy.run_path(str(Path(__file__).with_name('check_serialization01.py')));np=ns['np'];fast=ns['candidate']['_graph_chunk_bytes'];canonical=ns['canonical']
class Guarded(np.ndarray):
 @property
 def dtype(self):raise AssertionError('subclass dtype must not be inspected')
a=np.arange(4).view(Guarded);assert fast(a)==canonical(a.tolist())
with tempfile.TemporaryDirectory() as d:
 a=np.memmap(Path(d)/'synthetic.bin',dtype='f8',mode='w+',shape=(8,));a[:]=np.arange(8);assert fast(a)==canonical(a.tolist());before=fast(a);a[7]=.125;assert fast(a)==canonical(a.tolist())!=before
# NumPy expands subarray dtypes into shape; structured fields remain excluded.
a=np.zeros(2,dtype=np.dtype(('f8',(2,))));assert a.dtype.subdtype is None;assert fast(a)==canonical(a.tolist())
print(json.dumps({'status':'PASS','subclass_dtype_untouched':True,'synthetic_memmap_fallback_fresh':True,'normalized_subarray_equal':True}))
