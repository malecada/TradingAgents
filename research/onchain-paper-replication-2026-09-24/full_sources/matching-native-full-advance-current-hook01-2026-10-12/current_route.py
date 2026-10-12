"""Root-only CURRENT selected-route qualification; never a real pilot or grant.

No compilation API. The author has not imported/executed this file.
Candidate02 and original fd... numerical harness remain unchanged.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import math
import struct
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
HARNESS_DIR = BASE/'pilot-matching-weight-cache-candidate-2026-10-12'
NATIVE_DIR = BASE/'matching-native-full-advance-candidate02-2026-10-12'
CONFIG_SHA = 'b3b8d88424a56a6009a4baa447e00b971d769930299c769414f6d33d9a4e873e'
NORMALIZER_SHA = '648654607c166911bfec4b0b276cf7f8c148ff7bf9f62621faf12b1ef1b5a8f6'
PINS = {
    HARNESS_DIR/'numeric_harness.py':'fdc0940ca0b18d75cb933bbaa58c4a0fd38824b638f6ed09d0d1adc3ad3729e8',
    HARNESS_DIR/'phase_timing.py':'013e3384395e3ae6a95596df17e9dbf95b903ff8babcfd06d72befc663eb01dd',
    HARNESS_DIR/'matching_numeric_policy.py':'1402729793c6e32a6eb7948af36701f61b953f11790607c7cf1e8b86328e577f',
    HARNESS_DIR/'matching_immutable_session.py':'9ec80833156fb8f649a076778260d0da666486e25c98d9d4681092fcf65a144c',
    NATIVE_DIR/'native_full.c':'c76737a37682dbd932896ba1d836a54a6fce1dec1db5ec95dcd7ea8af151432d',
    NATIVE_DIR/'wrapper.py':'c587393f81b649087f9d42f4b4948f8adfb34dee5073f89ab074b6db0740cc1a',
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module)
    return module


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root-reviewed-offline-qualification', action='store_true', required=True)
    parser.add_argument('--native-library', type=Path, required=True)
    parser.add_argument('--native-sha256', required=True)
    parser.add_argument('--normalization-policy', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args()
    for path,expected in PINS.items():
        if digest(path)!=expected:raise ValueError('frozen input differs: '+str(path))
    if digest(args.native_library)!=args.native_sha256:raise ValueError('Root-built native artifact hash differs')
    if digest(args.normalization_policy)!=NORMALIZER_SHA:raise ValueError('exact current compiled normalization selection required')
    if digest(args.config)!=CONFIG_SHA:raise ValueError('exact original48 config required')
    args.output.mkdir(exist_ok=False)
    # Only Root execution reaches the numerical imports below.
    h=load(HARNESS_DIR/'numeric_harness.py','native_current_harness')
    baseline=h.ann._advance_checked;original_session=h.Session
    for module,expected in ((h.ann,'b77d6ee6093047715024b9f1cd8033b02f24f06bb1461b854a659e0a336f8f91'),
                            (h.engine,'eebc1cd361f884259beb2dd0bd11fa31322440fb5eaa0f153c37051364ecd693')):
        if digest(module.__file__)!=expected:raise ValueError('current source baseline differs')
    wrapper=load(NATIVE_DIR/'wrapper.py','native_current_wrapper')
    native=load(args.native_library,'_native_full')
    candidate=wrapper.Candidate(native,args.native_sha256)
    config=h.config(args.config,CONFIG_SHA)
    selection=json.loads(args.normalization_policy.read_bytes())
    from tradingagents.research.onchain_replication.compiled_normalization_policy import BackendOwner
    owners={};owner_close={};rows=[];primary=None;stats=None

    def seam(state,a,b,c,*,max_operations,edge_cache_policy=None,normalizer=None,edge_chunk_fill=None):
        nonlocal stats
        stats['attempted']+=1
        started=time.perf_counter()
        try:used=candidate.try_advance(state,a,b,c,max_operations=max_operations)
        except BaseException:
            stats['failed']+=1;raise
        finally:stats['candidate_boundary_seconds']+=time.perf_counter()-started
        if used is not None:
            stats['selected']+=1;stats['selected_operations']+=used
            return used
        stats['fallback']+=1
        return baseline(state,a,b,c,max_operations=max_operations,
                        edge_cache_policy=edge_cache_policy,normalizer=normalizer,
                        edge_chunk_fill=edge_chunk_fill)

    def graph(n,edges,offset):
        np=h.np
        nodes=(np.arange(n*4,dtype=np.float64).reshape(n,4)%29)*.017+offset
        z=np.arange(edges,dtype=np.int64)
        index=np.asarray((z//n,z%n),dtype=np.int64).reshape(2,edges)
        features=(np.arange(edges*2,dtype=np.float64).reshape(edges,2)%97)*.013+offset
        return h.AttributedGraph(tuple(map(str,range(n))),nodes,index,features,'a'*64,'0')

    def diagnostic_validation(a,b):
        # Independent fresh-validation sample, NEVER subtracted from solver time.
        # Full checks remain inside Candidate.try_advance; no trusted boolean.
        state=h.engine.create(a,b,config,max_state_bytes=16*1024**2,hardening_buffer_bytes=4*1024**2)
        try:
            t=time.perf_counter();h.ann.check(state['annealing'],a,b,config);check=time.perf_counter()-t
            t=time.perf_counter();candidate.current();body=time.perf_counter()-t
            return dict(fresh_ann_check_seconds=check,candidate_library_current_seconds=body,
                        qualification='independent diagnostic sample; not an exclusive decomposition of solver time')
        finally:h.engine.close(state)

    def solve(a,b,budget,selected,checkpoint):
        nonlocal stats
        route='native' if selected else 'current'
        owner=owners[route]
        h.ann._advance_checked=seam if selected else baseline
        h.Session=lambda *values,**kw:original_session(*values,
            compiled_normalization_policy_value=selection,_normalization_owner=owner,**kw)
        stats=dict(attempted=0,selected=0,fallback=0,failed=0,selected_operations=0,candidate_boundary_seconds=0.)
        try:
            if checkpoint:
                with tempfile.TemporaryDirectory(dir=args.output) as temp:
                    result=h.solve(a,b,config,2,budget=budget,checkpoint=Path(temp)/'checkpoint')
            else:result=h.solve(a,b,config,2,budget=budget)
            result[2]['candidate_route']=dict(stats)
            result[2]['normalization_policy_sha256']=NORMALIZER_SHA
            result[2]['backend_owner_lifetime']='one shared real engineering owner per route across fixtures and checkpoint sessions'
            return result
        finally:h.Session=original_session;h.ann._advance_checked=baseline

    try:
        owners['current']=BackendOwner(selection)
        owners['native']=BackendOwner(selection)
        fixtures=[('1x1',1,1,1,1),('2x2',2,2,2,2),('3x4',3,4,4,6),
                  ('8x8',8,8,16,16),('16x16',16,16,32,32),
                  ('32x32',32,32,32,32),('zero',3,4,0,0)]
        jobs=[(*row,1000000,False) for row in fixtures]
        needed=3*4+48*(4*6+5)
        jobs += [('exact',3,4,4,6,needed,False),('plus_one',3,4,4,6,needed+1,False),
                 ('partial_checkpoint',8,8,16,16,1024,True)]
        for label,n,m,ea,eb,budget,checkpoint in jobs:
            a,b=graph(n,ea,0.),graph(m,eb,.031)
            validation=diagnostic_validation(a,b)
            old=solve(a,b,budget,False,checkpoint)
            new=solve(a,b,budget,True,checkpoint)
            x,y=old[0],new[0];np=h.np
            history_equal=old[1]==new[1]
            soft_layout_equal=(x.soft_assignment.shape==y.soft_assignment.shape and x.soft_assignment.dtype==y.soft_assignment.dtype)
            assignments_equal=bool(np.array_equal(x.assignment,y.assignment))
            soft_close=bool(np.allclose(x.soft_assignment,y.soft_assignment,atol=1e-8,rtol=1e-6))
            score_close=math.isclose(x.score,y.score,abs_tol=1e-8,rel_tol=1e-6)
            expected_hit=ea*eb>0 and not checkpoint
            selected=new[2]['candidate_route']['selected']
            row=dict(case=label,shape=[n,m],edges=[ea,eb],budget=budget,
                checkpoint_requested=checkpoint,history_equal=history_equal,
                baseline_history=old[1],candidate_history=new[1],
                assignments_equal=assignments_equal,soft_layout_equal=soft_layout_equal,soft_close=soft_close,
                soft_bitwise=x.soft_assignment.tobytes()==y.soft_assignment.tobytes(),
                soft_max_abs=float(np.max(np.abs(x.soft_assignment-y.soft_assignment))),
                score_close=score_close,score_abs=abs(x.score-y.score),
                score_bitwise=struct.pack('!d',x.score)==struct.pack('!d',y.score),
                baseline_iterations=x.iterations,candidate_iterations=y.iterations,
                selected_expected=expected_hit,selected_calls=selected,
                baseline=old[2],candidate=new[2],validation_diagnostic=validation)
            row['passed']=all((history_equal,assignments_equal,soft_layout_equal,soft_close,score_close,
                x.convergence==y.convergence,
                x.iterations==y.iterations==48,(selected>0)==expected_hit,
                not checkpoint or old[2]['checkpoint_reloaded'] and new[2]['checkpoint_reloaded']))
            rows.append(row)
            (args.output/'COMPARISON_PARTIAL01.json').write_text(json.dumps(rows,indent=2)+'\n')
    except BaseException as error:
        primary=error
        try:
            (args.output/'FAILURE01.json').write_text(json.dumps({'type':type(error).__name__,'message':str(error),'completed_cases':len(rows)},indent=2)+'\n')
        except BaseException:pass  # diagnostic failure cannot replace primary
        raise
    finally:
        h.ann._advance_checked=baseline;h.Session=original_session
        cleanup_error=None
        for name,owner in owners.items():
            started=time.perf_counter()
            try:owner.close()
            except BaseException as error:
                if primary is not None:
                    try:BaseException.add_note(primary,'hook owner cleanup failed: '+repr(error))
                    except BaseException:pass
                elif cleanup_error is None:cleanup_error=error
                else:
                    try:BaseException.add_note(cleanup_error,'additional owner cleanup failed: '+repr(error))
                    except BaseException:pass
            finally:owner_close[name]=time.perf_counter()-started
        if cleanup_error is not None:raise cleanup_error
    report=dict(scope='finite synthetic current C05v2 Session/shared owned normalizer/production score_only comparison; no pilot/authority/capacity proof',
        native_sha256=args.native_sha256,config_sha256=CONFIG_SHA,
        normalization_policy_sha256=NORMALIZER_SHA,atol=1e-8,rtol=1e-6,
        candidate_preserves_compiled_normalizer_dispatch=False,
        tiny_edgeproduct_agreements='candidate02 recomputes1..7 edge products every iteration; original production telemetry still absent',
        qualification='native selected loop holds GIL; omits original per-normalization BackendOwner dispatch and per-temperature runtime rechecks; unchanged synthetic domain only',
        owner_cleanup_seconds=owner_close,cases=rows,passed=all(r['passed'] for r in rows))
    (args.output/'COMPARISON01.json').write_text(json.dumps(report,indent=2)+'\n')
    if not report['passed']:raise SystemExit(1)


if __name__=='__main__':main()
