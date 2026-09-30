"""Isolated scalar score-only finalization of accepted composite checkpoints.

No production dispatch, dense result construction, or scientific capacity change.
The sparse objective deliberately retains its conservative agreement domain.
"""
from pathlib import Path
import importlib.util
import numpy as np
from tradingagents.research.onchain_replication.matching import MatchScore
HERE=Path(__file__).resolve().parent

def component(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

combined=component('score_only_composite',HERE.with_name('matching-composite-checkpoints-2026-09-30')/'combined.py')
sparse=component('score_only_sparse',HERE.with_name('bounded-hardening-2026-09-30')/'sparse_objective.py')

def score_only(state,left,right,config,*,max_buffer_bytes,chunk_edges=65536):
    # Admit the newly allocated int64 pairs plus sparse numeric scratch first.
    # Graphs, issued states, validation scans, Python/runtime overhead excluded.
    if (type(max_buffer_bytes) is not int or max_buffer_bytes<=0
            or type(chunk_edges) is not int or not 0<chunk_edges<=65536):
        raise ValueError('positive bounded scoring policy required')
    count=min(len(left.node_ids),len(right.node_ids))
    if 80*count+32*min(chunk_edges,right.edge_index.shape[1])>max_buffer_bytes:
        raise ValueError('score-only numeric allowance exceeded')
    combined.check(state,left,right,config)
    if state['phase']!='done':raise ValueError('composite matching is incomplete')
    pairs=np.asarray(state['hardening']['pairs'],dtype=np.int64).reshape(-1,2)
    score=sparse.score_indices(left,right,pairs,config,
                               max_buffer_bytes=max_buffer_bytes-16*count,
                               chunk_edges=chunk_edges)
    inner=state['annealing']
    return MatchScore(score,'temperature_complete' if inner['beta']>config['beta_final'] else 'iteration_cap',inner['iterations'])
