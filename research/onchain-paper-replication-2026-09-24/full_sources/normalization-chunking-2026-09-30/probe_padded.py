"""Synthetic candidate: preserve C-order reduction layout for singleton tails."""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.special import logsumexp
HERE=Path(__file__).resolve().parent
rows=[]
for n,m in ((1,1),(1,7),(7,1),(7,3),(17,6),(257,6),(513,17),(1025,33)):
    for seed in (11,23,37):
        rng=np.random.default_rng(seed)
        normal=rng.standard_normal((n,m))
        for mode,q in (('normal',normal),('wide',normal*1000),('ties',np.round(normal)),('zeros',np.zeros((n,m)))):
            for order in ('C','F'):
                q=np.array(q,order=order)
                row_ref=logsumexp(q,axis=1,keepdims=True)
                normalized=q-row_ref
                col_ref=logsumexp(normalized,axis=0,keepdims=True)
                expected=np.exp(normalized-col_ref)
                for width in (1,2,4,7,16,64):
                    row_got=np.concatenate([logsumexp(q[i:i+width],axis=1,keepdims=True) for i in range(0,n,width)],axis=0)
                    blocks=[]
                    for j in range(0,m,width):
                        block=normalized[:,j:j+width]
                        if block.shape[1]==1 and m>1:
                            # Make the reduction axis non-contiguous just as in
                            # a C-order reference with more than one column.
                            padded=np.repeat(block,2,axis=1)
                            value=logsumexp(padded,axis=0,keepdims=True)[:,:1]
                        else:
                            value=logsumexp(block,axis=0,keepdims=True)
                        blocks.append(value)
                    col_got=np.concatenate(blocks,axis=1)
                    actual=np.exp(normalized-col_got)
                    rows.append({'shape':[n,m],'seed':seed,'mode':mode,'order':order,'chunk':width,
                                 'row_bitwise':bool(np.array_equal(row_ref,row_got)),
                                 'column_bitwise':bool(np.array_equal(col_ref,col_got)),
                                 'normalized_bitwise':bool(np.array_equal(expected,actual)),
                                 'column_max_abs_difference':float(np.max(np.abs(col_ref-col_got)))})
result={'qualification':'Synthetic diagnostic of singleton padding only, not a general equivalence proof. C/F cases expose layout assumptions; production annealing creates C-order matrices. Neither implementation nor source/config/cache changed.',
        'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'cases':len(rows),'summary':{},'rows':rows}
for order in ('C','F'):
    selection=[r for r in rows if r['order']==order]
    result['summary'][order]={k:sum(not r[k] for r in selection) for k in ('row_bitwise','column_bitwise','normalized_bitwise')}
with (HERE/'padded-result.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
