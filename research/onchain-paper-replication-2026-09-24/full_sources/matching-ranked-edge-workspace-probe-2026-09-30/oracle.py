"""Independent Eq1 arithmetic for full bijections of equal constant chains."""
import math

def chain_score(pairs,n,alpha):
    if type(n) is not int or n<2 or not math.isfinite(alpha) or alpha<0:raise ValueError('invalid constant-chain domain')
    if len(pairs)!=n or any(len(p)!=2 or any(type(i) is not int for i in p) for p in pairs):raise ValueError('full integer bijection required')
    if {u for u,i in pairs}!=set(range(n)) or {i for u,i in pairs}!=set(range(n)):raise ValueError('full bijection required')
    mapping=dict(pairs)
    hits=sum(mapping[u+1]==mapping[u]+1 for u in range(n-1))
    # Unit node agreement yields node term1; equal edge counts yield2*(n-1).
    return hits,(hits/(2*(n-1))+alpha)/(1+alpha)
