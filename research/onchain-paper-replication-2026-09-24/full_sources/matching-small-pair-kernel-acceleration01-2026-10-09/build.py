from pathlib import Path
import difflib
D=Path(__file__).resolve().parent;R=D.parents[3]
s=(R/'tradingagents/research/onchain_replication/matching_annealing.py').read_text()
helper='''
# Specialization of the pinned SciPy public wrapper for this kernel's real,
# nonempty float64 matrices. All floating operations remain in original order.
from scipy._lib.array_api_compat import numpy as _normalization_xp
_NORMALIZATION_INNER = logsumexp.__globals__['_logsumexp']
_NORMALIZATION_INNER_CODE = _NORMALIZATION_INNER.__code__

def _matrix_logsumexp(a, *, axis, keepdims):
    if (type(a) is not np.ndarray or a.dtype != np.float64 or a.ndim != 2
            or not a.size or axis not in (0, 1) or keepdims is not True
            or logsumexp is not _NORMALIZATION_ORIGINAL
            or logsumexp.__code__ is not _NORMALIZATION_CODE
            or logsumexp.__globals__.get('_logsumexp') is not _NORMALIZATION_INNER
            or _NORMALIZATION_INNER.__code__ is not _NORMALIZATION_INNER_CODE):
        return logsumexp(a, axis=axis, keepdims=keepdims)
    xp = _normalization_xp
    with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
        b_exp_a = xp.exp(a)
        sum_ = xp.sum(b_exp_a, axis=axis, keepdims=True)
        out_inf = xp.log(sum_)
    with np.errstate(divide='ignore', invalid='ignore'):
        out, sgn = _NORMALIZATION_INNER(a, None, axis=axis, return_sign=False, xp=xp)
    out_finite = xp.isfinite(out)
    return xp.where(out_finite, out, out_inf)

'''
s2=s.replace('\ndef _immutable_edges(graph):', '\n'+helper+'def _immutable_edges(graph):')
s2=s2.replace('block-=logsumexp(', 'block-=_matrix_logsumexp(')
(D/'matching_annealing.py').write_text(s2)
(D/'candidate.diff').write_text(''.join(difflib.unified_diff(s.splitlines(True),s2.splitlines(True),fromfile='installed/matching_annealing.py',tofile='candidate/matching_annealing.py')))
