"""Root-only finite offline compile/comparison hook. NOT executed by author.

No datasets, claims, Owner, registration, network or external native backend.
Root must supply its reviewed CPU/memory/wall/offline process envelope.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig
import time


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root-reviewed-offline-qualification', action='store_true', required=True)
    parser.add_argument('--compile-only', action='store_true')
    parser.add_argument('--cc', default='/usr/bin/cc')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--config-sha256', required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    args.output.mkdir(exist_ok=False)
    body = args.config.read_bytes()
    if hashlib.sha256(body).hexdigest() != args.config_sha256:
        raise ValueError('original matching config hash differs')
    library = args.output / ('_native_full' + sysconfig.get_config_var('EXT_SUFFIX'))
    command = [args.cc, '-shared', '-fPIC', '-O3', '-std=c11',
               '-fno-fast-math', '-ffp-contract=off', '-fno-associative-math',
               '-fno-unsafe-math-optimizations', '-frounding-math',
               '-I' + sysconfig.get_paths()['include'], str(here/'native_full.c'),
               '-o', str(library), '-lm']
    # No shell, runtime compiler flags or arbitrary linker inputs are inherited.
    result = subprocess.run(command, capture_output=True, text=True, timeout=30,
                            env={k: os.environ[k] for k in ('PATH', 'TMPDIR') if k in os.environ})
    record = dict(command=command, exit=result.returncode, stdout=result.stdout,
                  stderr=result.stderr, source_sha256=hashlib.sha256((here/'native_full.c').read_bytes()).hexdigest())
    (args.output/'COMPILE01.json').write_text(json.dumps(record, indent=2)+'\n')
    if result.returncode:
        raise SystemExit(result.returncode)
    if args.compile_only:
        return
    import numpy as np
    from tradingagents.research.onchain_replication import matching_checkpoint as engine
    from tradingagents.research.onchain_replication.contracts import AttributedGraph
    module = load('_native_full', library)
    wrapper = load('finite_native_wrapper', here/'wrapper.py')
    candidate = wrapper.Candidate(module, hashlib.sha256(library.read_bytes()).hexdigest())
    config = json.loads(body)

    def frozen(x, dtype):
        x = np.asarray(x, dtype=dtype)
        return np.frombuffer(x.tobytes(), dtype=dtype).reshape(x.shape)

    def graph(n, edges, shift=0., tied=False):
        nodes = np.zeros((n,4)) if tied else np.arange(n*4).reshape(n,4)*.013+shift
        index = np.array([(k//n, k%n) for k in range(edges)], dtype=np.int64).reshape(-1,2).T
        features = np.zeros((edges,2)) if tied else np.arange(edges*2).reshape(edges,2)*.007+shift
        return AttributedGraph(tuple(map(str, range(n))), frozen(nodes,np.float64),
                               frozen(index,np.int64), frozen(features,np.float64),'a'*64,'0')

    def advance(state, a, b, budget, selected):
        if not selected or state['phase'] != 'annealing':
            return engine.advance(state,a,b,config,max_operations=budget), False
        engine.check(state,a,b,config)
        try:
            used = candidate.try_advance(state['annealing'],a,b,config,max_operations=budget)
            if used is None:
                return engine.advance(state,a,b,config,max_operations=budget), False
            state['safe'] = False
            if state['annealing']['phase'] == 'done':
                # Original zero-operation annealing completion + ranking handoff.
                assert engine._advance_owned(state,a,b,config,max_operations=1) == 0
            else:
                state['safe'] = True
            return used, True
        except BaseException:
            state['safe'] = False
            raise

    def solve(a,b,budget,selected):
        start=time.perf_counter();state=engine.create(a,b,config,max_state_bytes=4*1024**2)
        history=[];hits=0
        try:
            for _ in range(6):
                used,accepted=advance(state,a,b,budget,selected);hits+=accepted
                inner=state['annealing']
                history.append((used,state['phase'],inner['phase'],inner['cursor'],inner['iterations'],inner['beta']))
                if state['phase']=='done':break
            if state['phase']!='done':raise RuntimeError('finite hook failed to complete')
            answer=engine.result(state,a,b,config)
            return answer,history,hits,time.perf_counter()-start
        finally:engine.close(state)

    rows=[]
    cases=[(1,1,1,1,False),(3,4,4,6,False),(8,8,16,32,False),
           (16,16,32,32,False),(32,32,32,32,False),(8,8,16,32,True),(3,4,0,0,False)]
    for n,m,ea,eb,tied in cases:
        a,b=graph(n,ea,tied=tied),graph(m,eb,.03,tied)
        needed=n*m+48*(1+ea*eb+4)
        for budget in (needed-1,needed,1000000):
            baseline,h0,_,t0=solve(a,b,budget,False)
            actual,h1,hits,t1=solve(a,b,budget,True)
            soft0,soft1=baseline.soft_assignment,actual.soft_assignment
            rows.append(dict(shape=[n,m],edges=[ea,eb],tied=tied,budget=budget,
                selected_calls=hits,history_equal=h0==h1,history=h1,
                soft_max_abs=float(np.max(np.abs(soft0-soft1))),
                soft_allclose=bool(np.allclose(soft0,soft1,atol=1e-8,rtol=1e-6)),
                soft_bitwise=soft0.tobytes()==soft1.tobytes(),
                assignment_equal=bool(np.array_equal(baseline.assignment,actual.assignment)),
                score_abs=abs(baseline.score-actual.score),
                score_close=bool(np.isclose(baseline.score,actual.score,atol=1e-8,rtol=1e-6)),
                score_bitwise=float(baseline.score).hex()==float(actual.score).hex(),
                iterations=actual.iterations,baseline_seconds=t0,candidate_seconds=t1))
    report=dict(scope='finite synthetic engineering only; cold checks/create/hardening/result included; no release',
                atol=1e-8,rtol=1e-6,scratch_bound=wrapper.SCRATCH_BOUND,
                normalization='native max-exclusion/reduction/libm, not universal bitwise SciPy',
                cases=rows)
    report['passed']=all(r['history_equal'] and r['soft_allclose'] and
                         r['assignment_equal'] and r['score_close'] and r['iterations']==48 for r in rows)
    (args.output/'COMPARISON01.json').write_text(json.dumps(report,indent=2)+'\n')
    if not report['passed']:raise SystemExit(1)


if __name__ == '__main__':main()
