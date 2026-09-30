"""Synthetic reduction-order probe; not a solver or empirical resource trial."""
from pathlib import Path
import hashlib
import inspect
import json
import numpy as np
import scipy
from scipy.special import logsumexp, _logsumexp

HERE=Path(__file__).resolve().parent
rows=[]
for n,m in ((1,1),(1,7),(7,1),(7,3),(17,6),(257,6),(513,17),(1025,33)):
    for seed in (11,23,37):
        rng=np.random.default_rng(seed)
        for scale in (1.,100.):
            q=rng.standard_normal((n,m))*scale
            row_ref=logsumexp(q,axis=1,keepdims=True)
            normalized=q-row_ref
            col_ref=logsumexp(normalized,axis=0,keepdims=True)
            expected=np.exp(normalized-col_ref)
            for width in (1,2,4,7,16,64):
                row_got=np.concatenate([logsumexp(q[i:i+width],axis=1,keepdims=True) for i in range(0,n,width)],axis=0)
                col_got=np.concatenate([logsumexp(normalized[:,j:j+width],axis=0,keepdims=True) for j in range(0,m,width)],axis=1)
                actual=np.exp(normalized-col_got)
                rows.append({'shape':[n,m],'seed':seed,'scale':scale,'chunk':width,
                             'row_reduction_bitwise':bool(np.array_equal(row_ref,row_got)),
                             'column_reduction_bitwise':bool(np.array_equal(col_ref,col_got)),
                             'normalized_bitwise':bool(np.array_equal(expected,actual)),
                             'column_max_abs_difference':float(np.max(np.abs(col_ref-col_got))),
                             'normalized_max_abs_difference':float(np.max(np.abs(expected-actual)))})
result={'qualification':'Synthetic random inputs only; a counterexample suffices to reject unconditional bitwise parity. Passing examples are not a general equivalence proof or wall/RSS measurement. No solver, scientific configuration, cache or empirical source changed.',
        'numpy':np.__version__,'scipy':scipy.__version__,
        'scipy_reduction_source_sha256':hashlib.sha256(inspect.getsource(_logsumexp._logsumexp).encode()).hexdigest(),
        'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'cases':len(rows), 'row_mismatches':sum(not r['row_reduction_bitwise'] for r in rows),
        'column_mismatches':sum(not r['column_reduction_bitwise'] for r in rows),
        'normalized_mismatches':sum(not r['normalized_bitwise'] for r in rows), 'rows':rows}
with (HERE/'result.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
