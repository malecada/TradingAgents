"""Bounded read-only consistency verification of the closed census artifacts.

No source graph reconstruction or census rerun. Checks retained hash bindings,
counts/histogram/maxima and sorted-key invariants. Not an independent raw-source
transaction audit or proof of every source-edge-to-count mapping.
"""
from pathlib import Path
import hashlib
import json
import time
import os
import subprocess
import numpy as np

ROOT=Path.cwd()
NAME='eth-paper-neighborhood-census-20260930-01'
SOURCE=ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/NAME
HERE=Path(__file__).resolve().parent

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
    return h.hexdigest()


def main():
    start=time.monotonic()
    binding=json.loads((HERE/'bindings.json').read_text())
    assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==binding['head']
    required={str((SOURCE/name).relative_to(ROOT)) for name in ('result.json','census/summary.json','census/checkpoints/03-summary.json')}
    assert required<=set(binding['files']) and binding['plan'] in binding['files']
    for name,expected in binding['files'].items():
        path=ROOT/name
        assert path.resolve().is_relative_to(ROOT) and path.is_file() and not path.is_symlink()
        assert digest(path)==expected
    plan=json.loads((ROOT/binding['plan']).read_text())
    assert (plan['expected_nodes'],plan['expected_edges'])==(2764221,3504159)

    terminal=json.loads((ROOT/'research_runs'/NAME/'complete.json').read_text())
    assert terminal['status']=='complete' and terminal['unavailable_count']==0
    run=ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/NAME
    guard=json.loads((run/'guard/final.json').read_text())
    assert guard['phase']=='complete' and guard['cleanup_verified'] and guard['child_exit_code']==0
    assert not Path(guard['cgroup']).exists()
    result=json.loads((SOURCE/'result.json').read_text());s=result['result']
    assert result['status']=='complete'
    claim_path=ROOT/'research_runs'/NAME/'claim.json'
    claim=json.loads(claim_path.read_text())
    assert terminal['claim_sha256']==digest(claim_path)==s['identity']['claim_sha256']
    assert claim['source']==binding['head'] and claim['experiment_id']==NAME
    assert digest(ROOT/claim['registration'])==claim['registration_sha256']
    assert s['identity']['plan_sha256']==digest(ROOT/binding['plan'])
    outputs=ROOT/'research_runs'/NAME/'outputs'
    assert set(terminal['output_sha256'])=={'artifact-index.json','cell-ledger.json','source-summary.json'}
    for name,want in terminal['output_sha256'].items():assert digest(outputs/name)==want
    index=json.loads((outputs/'artifact-index.json').read_text())
    for name,info in index.items():
        p=ROOT/name
        assert p.resolve().is_relative_to(SOURCE.resolve()) and not p.is_symlink()
        assert str(p.relative_to(ROOT)) in binding['files']
        assert p.stat().st_size==info['bytes'] and digest(p)==info['sha256']

    assert s==json.loads((SOURCE/'census/summary.json').read_text())
    assert s['nodes']==plan['expected_nodes'] and s['directed_edges']==plan['expected_edges']
    for key in ('graph_hash','graph_config_hash','node_order_sha256'):
        assert s['identity'][key]==plan[key]
    names={'cardinalities.npy','sorted_pairs.npy','histogram.npy','maxima_indices.npy'}
    assert set(s['files'])==names
    assert sum(v['bytes'] for v in s['files'].values())<=128*1024**2
    final_checkpoint=json.loads((SOURCE/'census/checkpoints/03-summary.json').read_text())
    assert final_checkpoint['identity']==s['identity']
    assert set(final_checkpoint['files'])==names|{'summary.json'}
    for name,info in final_checkpoint['files'].items():
        path=SOURCE/'census'/name
        assert path.stat().st_size==info['bytes'] and digest(path)==info['sha256']
        if name in names:assert info==s['files'][name]
    # Validate every exact-format NPY header and extent before any mapping.
    for name in sorted(names):
        path=SOURCE/'census'/name
        with path.open('rb') as stream:
            assert np.lib.format.read_magic(stream)==(1,0)
            shape,fortran,dtype=np.lib.format.read_array_header_1_0(stream,max_header_size=10000)
            assert dtype==np.dtype(np.int64) and not fortran
            if name=='cardinalities.npy':assert shape==(s['nodes'],)
            elif name=='sorted_pairs.npy':assert shape==(s['directed_edges'],)
            elif name=='maxima_indices.npy':assert len(shape)==1 and 1<=shape[0]<=s['nodes']
            else:assert len(shape)==2 and shape[1]==2 and 1<=shape[0]<=s['nodes']
            assert path.stat().st_size==stream.tell()+int(np.prod(shape))*8
    arrays={};primary=None;receipt=None
    try:
        for name,info in s['files'].items():
            p=SOURCE/'census'/name
            assert p.stat().st_size==info['bytes'] and digest(p)==info['sha256']
            arrays[name]=np.load(p,mmap_mode='r',allow_pickle=False)
        counts=arrays['cardinalities.npy'];keys=arrays['sorted_pairs.npy']
        maxima=arrays['maxima_indices.npy'];hist=arrays['histogram.npy']
        n=s['nodes'];e=s['directed_edges'];chunk=65536
        assert all(a.dtype==np.int64 for a in arrays.values())
        assert counts.shape==(n,) and keys.shape==(e,) and maxima.ndim==1 and hist.ndim==2 and hist.shape[1]==2
        # Histogram bins, nonzero indices and a gathered histogram column can each
        # occupy O(N) numeric space; plus bounded chunks, no adjacency materialization.
        bins=np.zeros(n+1,dtype=np.int64)
        low=n;high=0;total=0;above=0
        for first in range(0,n,chunk):
            c=counts[first:first+chunk]
            assert c.min()>=1 and c.max()<=n
            np.add.at(bins,c,1);total+=int(c.sum());above+=int(np.count_nonzero(c>10000))
            low=min(low,int(c.min()));high=max(high,int(c.max()))
        assert (low,high,above)==(s['minimum'],s['maximum'],s['above_10000'])
        nonzero=np.flatnonzero(bins)
        assert hist.shape==(len(nonzero),2)
        assert np.array_equal(hist[:,0],nonzero) and np.array_equal(hist[:,1],bins[nonzero])
        assert int(hist[:,1].sum())==n
        cursor=0
        for first in range(0,n,chunk):
            expected=np.flatnonzero(counts[first:first+chunk]==high)+first
            assert np.array_equal(maxima[cursor:cursor+len(expected)],expected)
            cursor+=len(expected)
        assert cursor==len(maxima)
        previous=-1;unique=0
        for first in range(0,e,chunk):
            k=keys[first:first+chunk]
            assert int(k.min())>=-1 and int(k.max())<n*n
            assert int(k[0])>=previous and np.all(k[1:]>=k[:-1])
            valid=k[k>=0]
            assert np.all(valid//n<valid%n)
            distinct=np.empty(len(k),dtype=bool);distinct[0]=k[0]!=previous;distinct[1:]=k[1:]!=k[:-1]
            distinct &= k>=0;unique+=int(distinct.sum());previous=int(k[-1])
        assert unique==s['unique_nonself_pairs'] and total==n+2*unique
        receipt={'status':'complete','experiment':NAME,'nodes':n,'edges':e,'minimum':low,'maximum':high,'above_10000':above,'maxima_count':len(maxima),'unique_nonself_pairs':unique,'histogram_sum':int(hist[:,1].sum()),'sum_cardinalities':total,'identity':s['identity'],'array_sha256':{k:v['sha256'] for k,v in s['files'].items()},'elapsed_seconds':time.monotonic()-start,'qualification':__doc__}
    except BaseException as error:
        primary=error
        raise
    finally:
        errors=[]
        for a in arrays.values():
            if isinstance(a,np.memmap):
                try:a._mmap.close()
                except BaseException as error:errors.append(error)
        if errors:
            if primary is not None:
                for error in errors:primary.add_note('verification map close error: '+repr(error))
            else:raise RuntimeError('verification mapping cleanup failed') from errors[0]
    assert receipt is not None
    with (HERE/'verification01.json').open('x') as f:
        json.dump(receipt,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    fd=os.open(HERE,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
    print(json.dumps(receipt),flush=True)

if __name__=='__main__':main()
