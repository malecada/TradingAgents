"""Bounded expected native NPY descriptors before graph-feature writing."""
import hashlib
import io
import numpy as np

def require(value,message):
    if not value:raise ValueError(message)

def descriptors(feature,chunk):
    require(type(chunk) is int and 0<chunk<=65536,'encoded feature chunk differs')
    require(type(feature) is dict and set(feature)=={'mcm','edge_index'},'encoded feature keys differ')
    a=feature['mcm'];e=feature['edge_index']
    require(type(a) is np.ndarray and a.dtype==np.dtype('float32') and a.ndim==2 and all(n>0 for n in a.shape)
        and type(e) is np.ndarray and e.dtype==np.dtype('int64') and e.ndim==2 and e.shape[0]==2,'encoded feature types differ')
    result={}
    for array in (a,e):
        header=io.BytesIO();info=np.lib.format.header_data_from_array_1_0(array)
        np.lib.format.write_array_header_1_0(header,info);raw=header.getvalue();h=hashlib.sha256(raw)
        order='F' if info['fortran_order'] else 'C'
        with np.nditer(array,flags=['external_loop','buffered','zerosize_ok'],op_flags=[['readonly','contig']],
                order=order,buffersize=chunk) as iterator:
            for block in iterator:
                require(block.size<=chunk,'encoded feature chunk exceeded')
                h.update(memoryview(block).cast('B'));del block
        del iterator
        result[f'array-{len(result):06d}.npy']={'sha256':h.hexdigest(),'bytes':len(raw)+array.nbytes,
            'shape':list(array.shape),'dtype':str(array.dtype)}
    return result
