"""UNINSTALLED C05 candidate; explicit Root qualification only, no authority.

None means unsupported without state writes. Exceptions mean fatal candidate
failure; caller must retain the original composite poisoning/cleanup envelope.
This checked entry deliberately keeps original graph/state validation. A future
private checked-body integration requires separate source/Owner review.
"""
import hashlib
import sys
import types
from pathlib import Path
import numpy as np
from tradingagents.research.onchain_replication import matching_annealing as ann
from tradingagents.research.onchain_replication.contracts import AttributedGraph

SCRATCH_BOUND = 65536  # all explicit candidate payload; original state excluded
ATOL = 1e-8
RTOL = 1e-6
_ARRAY = np.ndarray
_OPS = tuple((name, getattr(np, name)) for name in
             ('dtype', 'isfinite', 'abs', 'all', 'shares_memory', 'geterr'))
_CHECK = (ann.check, ann.check.__code__)
_IDENTITY = (ann.identity, ann.identity.__code__)
_RUNTIME = (ann._reuse_runtime, ann._reuse_runtime.__code__)
_AGREEMENT = (ann.agreement, ann.agreement.__code__)


def _immutable(x, dtype):
    if (type(x) is not _ARRAY or x.dtype != np.dtype(dtype) or
            x.dtype.metadata is not None or x.ndim != 2 or
            not x.flags.c_contiguous or not x.flags.aligned or x.flags.writeable):
        return False
    current = x
    for _ in range(4):
        if type(current) is bytes:
            return True
        if type(current) is not _ARRAY or current.flags.writeable:
            return False
        current = current.base
    return False


def _runtime():
    return (sys.platform == 'linux' and sys.byteorder == 'little' and
            np.ndarray is _ARRAY and
            all(getattr(np, name) is value for name, value in _OPS) and
            (ann.check, ann.check.__code__) == _CHECK and
            (ann.identity, ann.identity.__code__) == _IDENTITY and
            (ann._reuse_runtime, ann._reuse_runtime.__code__) == _RUNTIME and
            (ann.agreement, ann.agreement.__code__) == _AGREEMENT and
            ann._reuse_runtime() and
            np.geterr() == dict(divide='warn', over='warn', under='ignore', invalid='warn'))


class Candidate:
    """Local body/function pin, explicitly NOT a native execution capability."""
    def __init__(self, module, library_sha256):
        if type(module) is not types.ModuleType or type(module.run) is not types.BuiltinFunctionType:
            raise ValueError('loaded prototype extension required')
        self.path = Path(module.__file__).resolve()
        if hashlib.sha256(self.path.read_bytes()).hexdigest() != library_sha256:
            raise ValueError('qualification library body differs')
        self.module = module
        self.run = module.run
        self.library_sha256 = library_sha256

    def current(self):
        if (self.module.run is not self.run or
                Path(self.module.__file__).resolve() != self.path or
                hashlib.sha256(self.path.read_bytes()).hexdigest() != self.library_sha256):
            raise ValueError('qualification extension replaced')

    def try_advance(self, inner, a, b, config, *, max_operations):
        self.current()
        if not _runtime():
            return None
        if (type(inner) is not dict or type(config) is not dict or
                type(a) is not AttributedGraph or type(b) is not AttributedGraph or
                type(max_operations) is not int or max_operations <= 0):
            return None
        fixed = dict(alpha=1, beta0=1, beta_final=30, beta_rate=.075,
                     max_iterations=50, normalization_iterations=1)
        if any(config.get(k) != v or isinstance(config.get(k), bool) for k, v in fixed.items()):
            return None
        if (inner.get('phase') != 'nodes' or inner.get('cursor') != 0 or
                inner.get('iterations') != 0 or inner.get('safe') is not True or
                inner.get('beta') != config['beta0']):
            return None
        n, m = len(a.node_ids), len(b.node_ids)
        if not 1 <= n <= 32 or not 1 <= m <= 32:
            return None
        for graph in (a, b):
            if not (_immutable(graph.node_features, 'float64') and
                    _immutable(graph.edge_features, 'float64') and
                    _immutable(graph.edge_index, 'int64')):
                return None
            for x in (graph.node_features, graph.edge_features):
                if not 1 <= x.shape[1] <= 4:
                    return None
                # <=256*4 float64 abs temporary8192B + finite mask1024B.
                for start in range(0, len(x), 256):
                    part = x[start:start+256]
                    if not np.all(np.isfinite(part)) or not np.all(np.abs(part) <= 256):
                        return None
        ea, eb = a.edge_index.shape[1], b.edge_index.shape[1]
        if not 0 < ea*eb <= 1024:
            return None
        if (a.node_features.shape != (n, b.node_features.shape[1]) or
                b.node_features.shape[0] != m or
                a.edge_features.shape != (ea, b.edge_features.shape[1]) or
                b.edge_features.shape[0] != eb or
                a.edge_index.shape[0] != 2 or b.edge_index.shape[0] != 2):
            return None
        if inner.get('max_chunk_entries', 0) < n*m:
            return None  # exactly one operation per normalization phase
        beta = config['beta0']; iterations = 0
        while beta <= config['beta_final'] and iterations < config['max_iterations']:
            beta *= 1 + config['beta_rate']; iterations += 1
        needed = n*m + iterations*(1 + ea*eb + 4)
        if iterations != 48 or max_operations < needed:
            return None
        arrays = tuple(inner.get(name) for name in ('V', 'M', 'Q'))
        if any(type(x) is not _ARRAY or x.shape != (n, m) or
               x.dtype != np.dtype('float64') or x.dtype.metadata is not None or
               not x.flags.c_contiguous or not x.flags.aligned or not x.flags.writeable for x in arrays):
            return None
        sources = (a.node_features, b.node_features, a.edge_features,
                   b.edge_features, a.edge_index, b.edge_index)
        if any(np.shares_memory(x, y) for k, x in enumerate(arrays)
               for y in arrays[k+1:]+sources):
            return None
        # Original checked boundary, not an invented state-validity capability.
        ann.check(inner, a, b, config)
        if not _runtime():
            return None
        try:
            used = self.run(inner, a.node_features, b.node_features,
                            a.edge_features, b.edge_features, a.edge_index,
                            b.edge_index, _AGREEMENT[0], max_operations,
                            float(config['alpha']), float(config['beta0']),
                            float(config['beta_rate']), float(config['beta_final']),
                            config['max_iterations'])
            if type(used) is not int or used != needed:
                raise ValueError('native operation accounting differs')
            return used
        except BaseException:
            inner['safe'] = False
            raise
