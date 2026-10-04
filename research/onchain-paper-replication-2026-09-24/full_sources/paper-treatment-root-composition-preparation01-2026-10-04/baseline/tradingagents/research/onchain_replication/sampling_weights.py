"""Optional retained mapped weight scratch, preserving pinned NumPy choices.

This component does not admit empirical work or resume a sampling attempt.
Callers still require a resource guard covering page cache and this filesystem.
"""
import os
from pathlib import Path
import shutil

import numpy as np

from .provenance import canonical_bytes, sync_directory


class MappedWeights:
    def __init__(self, directory, count, max_bytes, binding):
        if np.__version__ != '2.3.0':
            raise ValueError('mapped choice requires validated NumPy 2.3.0')
        if type(count) is not int or count <= 0:
            raise ValueError('weight count must be positive')
        if type(max_bytes) is not int or max_bytes <= 0:
            raise ValueError('explicit weight scratch budget required')
        self.directory = Path(directory)
        if self.directory.exists() or self.directory.is_symlink():
            raise FileExistsError('weight workspace is already reserved')
        block = os.statvfs(self.directory.parent).f_frsize
        if block <= 0:
            raise ValueError('unknown weight workspace allocation granularity')
        self.numeric_bytes = 3 * count * 8
        # Intent and terminal each have a 32KiB encoded-content ceiling, plus
        # newline; reserve separate rounded blocks and one directory block.
        metadata_bytes = 2 * ((32769 + block - 1) // block * block) + block
        self.reserved_bytes = 3 * ((count * 8 + block - 1) // block * block) + metadata_bytes
        if self.reserved_bytes > max_bytes:
            raise ValueError('weight scratch budget insufficient')
        self.intent = {'schema_version':1, 'count':count, 'dtype':'float64',
                       'numpy':np.__version__, 'numeric_bytes':self.numeric_bytes,
                       'reserved_bytes':self.reserved_bytes, 'max_weight_bytes':max_bytes,
                       'binding':binding, 'resumable':False}
        if len(canonical_bytes(self.intent)) > 32768:
            raise ValueError('weight scratch metadata budget exceeded')
        if shutil.disk_usage(self.directory.parent).free < 20 * 2**30 + self.reserved_bytes:
            raise ValueError('weight workspace breaches disk reserve')
        self.count = count
        self.arrays = []
        self.sample_identity = None

    def _write(self, name, value):
        data = canonical_bytes(value)
        if len(data) > 32768:
            raise ValueError('weight receipt metadata budget exceeded')
        with (self.directory/name).open('xb') as stream:
            stream.write(data+b'\n')
            stream.flush(); os.fsync(stream.fileno())
        sync_directory(self.directory)

    def __enter__(self):
        self.directory.mkdir()
        sync_directory(self.directory.parent)
        try:
            self._write('intent.json', self.intent)
            for name in ('weights','probability','cdf'):
                path = self.directory/(name+'.bin')
                with path.open('xb') as stream:
                    os.posix_fallocate(stream.fileno(), 0, self.count*8)
                    stream.flush(); os.fsync(stream.fileno())
                self.arrays.append(np.memmap(path,mode='r+',dtype=np.float64,shape=(self.count,)))
            self.weights,self.probability,self.cdf = self.arrays
            self.weights[:] = 1.
            sync_directory(self.directory)
            return self
        except BaseException as error:
            self.__exit__(type(error), error, error.__traceback__)
            raise

    def draw(self, rng):
        if type(rng.bit_generator) is not np.random.PCG64:
            raise ValueError('mapped weights require PCG64')
        for start in range(0,self.count,65536):
            block = self.weights[start:start+65536]
            if not np.isfinite(block).all() or (block < 0).any():
                raise ValueError('invalid sampling weights')
        # Do not replace these global NumPy reductions/scans by block sums.
        total = self.weights.sum()
        if not np.isfinite(total) or total <= 0:
            raise ValueError('invalid sampling weight mass')
        np.divide(self.weights,total,out=self.probability)
        np.cumsum(self.probability,out=self.cdf)
        np.divide(self.cdf,self.cdf[-1],out=self.cdf)
        chosen = int(self.cdf.searchsorted(rng.random(()),side='right'))
        return chosen,float(self.probability[chosen])

    def __exit__(self, kind, error, traceback):
        cleanup_error = None
        for array in self.arrays:
            try:
                array.flush()
            except BaseException as failure:
                cleanup_error = cleanup_error or failure
            try:
                array._mmap.close()
            except BaseException as failure:
                cleanup_error = cleanup_error or failure
            try:
                with Path(array.filename).open('rb') as stream:
                    os.fsync(stream.fileno())
            except BaseException as failure:
                cleanup_error = cleanup_error or failure
        failure = error or cleanup_error
        result = {'schema_version':1,'numeric_bytes':self.numeric_bytes,
                  'reserved_bytes':self.reserved_bytes,'resumable':False,
                  'sample_identity':self.sample_identity}
        if failure is not None:
            result['reason'] = (type(failure).__name__+': '+str(failure))[:2048]
        if cleanup_error is not None:
            result['cleanup_error'] = (type(cleanup_error).__name__+': '+str(cleanup_error))[:2048]
        self._write('failed.json' if failure is not None else 'complete.json', result)
        if cleanup_error is not None and error is None:
            raise cleanup_error
        return False
