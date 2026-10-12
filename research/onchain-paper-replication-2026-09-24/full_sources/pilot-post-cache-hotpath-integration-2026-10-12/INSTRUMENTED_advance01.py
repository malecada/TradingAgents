def _advance_checked(state,a,b,c,*,max_operations,edge_cache_policy=None,normalizer=None,edge_chunk_fill=None):
    """Private body for an exclusively owned state checked in this same call.

    The caller must validate state, inputs and positive operation budget before
    entry, with no intervening mutation of them or external callback.
    """
    n,m=state['shape'];right_edges=b.edge_index.shape[1];total=a.edge_index.shape[1]*right_edges
    # At most4096float64 weights+4096validity bytes =36864B; no state fields.
    reuse=(0<total<=4096 and max_operations>total and _immutable_edges(a) and _immutable_edges(b)
           and all(type(state[name]) is np.ndarray for name in NAMES) and _reuse_runtime())
    adaptive=False
    if _adaptive_selected(edge_cache_policy) and 4096<total<=16384 and max_operations>total:
        adaptive=(_immutable_edges(a) and _immutable_edges(b) and all(type(state[name]) is np.ndarray for name in NAMES)
                  and _reuse_runtime() and np.geterr()==dict(divide='warn',over='warn',under='ignore',invalid='warn'))
        if adaptive:reuse=True
    feature_pins=(a.edge_features,b.edge_features);cached=valid=None
    state['safe']=False
    scalar_entries=scalar_chunks=0
    try:
        used=0
        while used<max_operations and state['phase']!='done':
            phase=state['phase']
            if phase=='nodes':
                u,i=divmod(state['cursor'],m)
                state['V'][u,i]=agreement(a.node_features[u],b.node_features[i]);state['cursor']+=1;used+=1
                scalar_entries+=1;scalar_chunks+=1
                if state['cursor']==n*m:
                    state['M'][:]=state['V'];state.update(phase='outer',cursor=0)
            elif phase=='outer':
                if reuse and (a.edge_features is not feature_pins[0] or b.edge_features is not feature_pins[1] or not _reuse_runtime()):
                    reuse=False;cached=valid=None
                if state['beta']>c['beta_final'] or state['iterations']>=c['max_iterations']:
                    state['phase']='done';continue
                state['Q'][:]=c['alpha']*state['V'];state.update(phase='edges',cursor=0);used+=1
            elif phase=='edges':
                if state['cursor']==total:state.update(phase='normalize_scale',cursor=0);continue
                # Bounded ordered edge accumulation; no agreement approximation.
                # Keep single-operation and nonstandard error-mode calls scalar.
                count=min(256 if adaptive and reuse else 1024,total-state['cursor'],max_operations-used)
                phase_timing.add_count('chunk_'+('lt8' if count<8 else '8to255' if count<256 else '256to1023' if count<1024 else '1024')+'_calls',1)
                if (count>=8 and a.edge_features.dtype==np.float64 and b.edge_features.dtype==np.float64
                        and np.geterr()['under']=='ignore'
                        and all(mode in ('ignore','warn') for mode in np.geterr().values())):
                    start=state['cursor']
                    with _post_cache_measure('geometry'):
                        positions=np.arange(start,start+count,dtype=np.int64)
                        left,right=np.divmod(positions,right_edges)
                        u,v=a.edge_index[:,left];i,j=b.edge_index[:,right]
                        old_values=state['M'][v,j]
                    # Per-chunk proof domain: each product has magnitude <=.5;
                    # at most 1024 additions start from finite |Q|<=1e100.
                    # Overflow/invalid cannot occur; underflow must be ignored.
                    # Outside this domain retain the literal scalar operation.
                    with _post_cache_measure('finite_accumulation_domain'):
                        eligible_chunk=np.all(np.abs(old_values)<=1.) and np.all(np.abs(state['Q'][u,i])<=1e100)
                    if eligible_chunk:
                        with _post_cache_measure('weight_dispatch'):
                            weights=np.empty(count,dtype=np.float64)
                            if reuse and cached is not None and valid[start:start+count].all():
                                # Exact copy only: lazy population and ordered arithmetic remain below.
                                weights[:]=cached[start:start+count]
                            else:
                                offset=0;native_progress=None
                                try:
                                    native_used=False
                                    if (edge_chunk_fill is not None and not reuse and _reuse_runtime()
                                            and _immutable_edges(a) and _immutable_edges(b)):
                                        native_progress=[0]
                                        native_used=edge_chunk_fill(weights,a.edge_features,b.edge_features,left,right,count,agreement,native_progress)
                                        # Selected adapter appends a telemetry-only success
                                        # marker after recording its actual backend.
                                        if native_used is True and len(native_progress)==1:
                                            phase_timing.add_count('agreement_native_chunks',1)
                                            phase_timing.add_count('agreement_native_entries',count)
                                    if not native_used:
                                        native_progress=None
                                        for offset in range(count):
                                            position=start+offset
                                            if reuse and cached is not None and valid[position]:
                                                weights[offset]=cached[position]
                                            else:
                                                weights[offset]=.5*agreement(a.edge_features[left[offset]],b.edge_features[right[offset]])
                                                scalar_entries+=1;scalar_chunks+=1
                                                if reuse:
                                                    if cached is None:
                                                        cached=np.empty(total,dtype=np.float64);valid=np.zeros(total,dtype=np.bool_)
                                                    cached[position]=weights[offset];valid[position]=True
                                except BaseException:
                                    if native_progress is not None and native_progress[0] is not None:
                                        offset=native_progress[0]
                                    # Reproduce the scalar prefix and cursor on agreement failure.
                                    for offset2 in range(offset):
                                        k,l=left[offset2],right[offset2]
                                        u,v=a.edge_index[:,k];i,j=b.edge_index[:,l]
                                        state['Q'][u,i]+=weights[offset2]*state['M'][v,j]
                                        state['cursor']+=1;used+=1
                                    raise
                        with _post_cache_measure('multiply'):
                            np.multiply(weights,old_values,out=weights)
                        with _post_cache_measure('ordered_scatter'):
                            np.add.at(state['Q'],(u,i),weights)
                        state['cursor']+=count;used+=count
                        if state['cursor']==total:state.update(phase='normalize_scale',cursor=0)
                        continue
                k,l=divmod(state['cursor'],right_edges);u,v=a.edge_index[:,k];i,j=b.edge_index[:,l]
                state['Q'][u,i]+=.5*agreement(a.edge_features[k],b.edge_features[l])*state['M'][v,j]
                scalar_entries+=1;scalar_chunks+=1
                state['cursor']+=1;used+=1
                if state['cursor']==total:state.update(phase='normalize_scale',cursor=0)
            elif phase in NORMALIZATION:
                # Q is complete and the old M is no longer needed for edge
                # accumulation. Reuse M as normalization scratch, retaining only
                # V/M/Q rather than allocating a fourth dense state matrix.
                start=state['cursor'];cap=state['max_chunk_entries'];matrix=state['M']
                if phase=='normalize_scale':
                    if start==0 and (np.any(state['Q']<0) or (state['beta']>1 and float(state['Q'].max())>np.finfo(np.float64).max/state['beta'])):
                        raise ValueError('invalid or overflowing normalization input')
                    end=min(n*m,start+cap)
                    np.multiply(state['Q'].reshape(-1)[start:end],state['beta'],out=matrix.reshape(-1)[start:end])
                    limit=n*m;next_phase='normalize_rows'
                elif phase=='normalize_rows':
                    end=min(n,start+max(1,cap//m));block=matrix[start:end]
                    block-=(logsumexp(block,axis=1,keepdims=True) if normalizer is None else normalizer.lse(block,axis=1,keepdims=True,fallback=logsumexp))
                    limit=n;next_phase='normalize_columns'
                elif phase=='normalize_columns':
                    end=min(m,start+max(1,cap//n));block=matrix[:,start:end]
                    if block.shape[1]==1 and m>1:
                        padded=np.repeat(block,2,axis=1)
                        block-=(logsumexp(padded,axis=0,keepdims=True) if normalizer is None else normalizer.lse(padded,axis=0,keepdims=True,fallback=logsumexp))[:,:1]
                    else:
                        block-=(logsumexp(block,axis=0,keepdims=True) if normalizer is None else normalizer.lse(block,axis=0,keepdims=True,fallback=logsumexp))
                    limit=m;next_phase='normalize_exp'
                else:
                    end=min(n*m,start+cap)
                    target=matrix.reshape(-1)[start:end];np.exp(target,out=target)
                    limit=n*m;next_phase='outer'
                state['cursor']=end;used+=1
                if end==limit:
                    if phase=='normalize_exp':
                        state['beta']*=1+c['beta_rate'];state['iterations']+=1
                    state.update(phase=next_phase,cursor=0)
        state['safe']=True
        return used
    except BaseException:
        state['safe']=False
        raise
    finally:
        phase_timing.add_count('agreement_scalar_entries',scalar_entries)
        phase_timing.add_count('agreement_scalar_chunks',scalar_chunks)
