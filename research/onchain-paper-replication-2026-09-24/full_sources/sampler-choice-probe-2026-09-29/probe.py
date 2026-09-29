"""Synthetic feasibility probe only; not a production sampler or research lease."""
from pathlib import Path
import hashlib,json,sys,time
import numpy as np


def run(directory):
    directory=Path(directory);directory.mkdir(exist_ok=False)
    if np.__version__!='2.3.0':raise ValueError('probe bound to pinned NumPy2.3.0')
    results=[]
    for n in (257,4097,131071):
        for seed in (11,23,37,53,71):
            case=directory/f'n{n}-s{seed}';case.mkdir()
            mapped=[np.memmap(case/(name+'.bin'),mode='w+',dtype=np.float64,shape=(n,)) for name in ('weights','probability','cdf')]
            weights,probability,cdf=mapped;weights[:]=1.
            oracle=np.ones(n,dtype=np.float64)
            eager_rng=np.random.Generator(np.random.PCG64(seed));mapped_rng=np.random.Generator(np.random.PCG64(seed))
            draws=min(n-1,512);transcript=hashlib.sha256();begin=time.monotonic()
            for step in range(draws):
                p=oracle/oracle.sum();expected=int(eager_rng.choice(n,p=p))
                # Keep original float64 NumPy reduction/scan order; no block sums.
                np.divide(weights,weights.sum(),out=probability)
                np.cumsum(probability,out=cdf);np.divide(cdf,cdf[-1],out=cdf)
                actual=int(cdf.searchsorted(mapped_rng.random(()),side='right'))
                if actual!=expected or probability[actual].tobytes()!=p[expected].tobytes():raise AssertionError((n,seed,step,'selection/probability differ'))
                if eager_rng.bit_generator.state!=mapped_rng.bit_generator.state:raise AssertionError('RNG state differs')
                transcript.update(np.array([actual],dtype=np.int64).tobytes());transcript.update(p[expected].tobytes())
                # Synthetic overlapping neighborhoods; zero chosen mass then halve.
                neighbors=np.unique((actual+np.arange(-31,33))%n)
                oracle[actual]=0;weights[actual]=0
                oracle[neighbors]*=.5;weights[neighbors]*=.5
            np.testing.assert_array_equal(weights,oracle)
            for a in mapped:a.flush()
            results.append({'candidates':n,'seed':seed,'draws':draws,'exact_chosen_probability_and_rng':True,
                'transcript_sha256':transcript.hexdigest(),'mapped_numeric_bytes':3*n*8,'elapsed_seconds':time.monotonic()-begin})
            del weights,probability,cdf,mapped,a
    result={'schema_version':1,'numpy':np.__version__,'scope':'synthetic weighted-draw feasibility only; no production implementation, graph admission, sampler integration or empirical data',
        'source':'https://github.com/numpy/numpy/blob/v2.3.0/numpy/random/_generator.pyx',
        'qualification':'Valid generated positive finite weights only. This is not a replacement for choice validation, exclusive retained workspaces, disk guards, checkpoints, graph-level manifest parity or registered policy integration.',
        'cases':results,'total_draws':sum(r['draws'] for r in results)}
    with (directory/'result.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({'cases':len(results),'exact_draws':result['total_draws'],'result':str(directory/'result.json')}))


if __name__=='__main__':run(sys.argv[1])
