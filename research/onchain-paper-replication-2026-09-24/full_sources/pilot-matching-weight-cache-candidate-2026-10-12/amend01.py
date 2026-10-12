from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3];S=R/'tradingagents/research/onchain_replication';p=P/'matching_numeric_policy.py';s=p.read_text();(P/'RAW_matching_numeric_policy01.py').write_text(s)
s=s.replace('    def fill(self,out,left,right,li,ri,count,scalar,progress):\n        self.current()\n        if dict(self.policy)[\'format\']==CACHE_POLICY[\'format\']:',"    def fill(self,out,left,right,li,ri,count,scalar,progress):\n        if hasattr(self,'_cache_owner'):")
s=s.replace('            try:\n                selected=_cache_fill','            try:\n                self.current()\n                selected=_cache_fill',1)
s=s.replace('            except BaseException:\n                _cache_release(self)\n                raise\n        if (type(count)',"            except BaseException as primary:\n                try:_cache_release(self)\n                except BaseException as cleanup:\n                    try:BaseException.add_note(primary,'cache release failed: '+repr(cleanup))\n                    except BaseException:pass\n                raise\n        self.current()\n        if (type(count)",1)
s=s.replace('chain.append(current);current=current.base',"chain.append((current,current.dtype.str,tuple(current.shape),tuple(current.strides),current.nbytes,current.__array_interface__['data'][0]));current=current.base")
s=s.replace("if current is not saved or type(current) is not np.ndarray or current.flags.writeable:","if (current is not saved[0] or type(current) is not np.ndarray or current.flags.writeable\n                or current.dtype.str!=saved[1] or tuple(current.shape)!=saved[2]\n                or tuple(current.strides)!=saved[3] or current.nbytes!=saved[4]\n                or current.__array_interface__['data'][0]!=saved[5]):")
s=s.replace('adapter._cache_storage=None','adapter._cache_storage=adapter._cache_storage_pins=None')
s=s.replace('cache_weight_bytes=0,cache_validity_bytes=0,cache_oversize_chunks=0)', 'cache_weight_bytes=0,cache_validity_bytes=0,cache_oversize_chunks=0,cache_peak_retained_bytes=0,cache_hit_chunks=0,cache_allocations=0,cache_allocated_bytes=0,cache_released_bytes=0)')
s=s.replace("weights.nbytes+valid.nbytes+4096!=adapter._counts['cache_reserved_bytes']", "weights.nbytes+valid.nbytes+16384!=adapter._counts['cache_reserved_bytes']")
needle="            raise ValueError('cached storage changed')\n"
s=s.replace(needle,needle+'''        for array,saved in zip((weights,valid),adapter._cache_storage_pins,strict=True):
            if (array.dtype.str,tuple(array.shape),tuple(array.strides),array.nbytes,
                    array.__array_interface__['data'][0],id(array.base))!=saved:
                raise ValueError('cached storage header changed')
''')
s=s.replace('reserved=9*total+4096','reserved=9*total+16384')
s=s.replace('    pins=(_feature_pin(left),_feature_pin(right))\n    if any(pin is None for pin in pins):return None\n    if adapter._cache_pair is None:', '    if adapter._cache_pair is None:\n        pins=(_feature_pin(left),_feature_pin(right))\n        if any(pin is None for pin in pins):return None')
s=s.replace("adapter._counts.update(cache_reserved_bytes=reserved,cache_weight_bytes=weights.nbytes,cache_validity_bytes=valid.nbytes)","""adapter._cache_storage_pins=tuple((a.dtype.str,tuple(a.shape),tuple(a.strides),a.nbytes,
            a.__array_interface__['data'][0],id(a.base)) for a in (weights,valid))
        adapter._counts.update(cache_reserved_bytes=reserved,cache_weight_bytes=weights.nbytes,
            cache_validity_bytes=valid.nbytes,cache_peak_retained_bytes=reserved)
        adapter._counts['cache_allocations']+=1;adapter._counts['cache_allocated_bytes']+=reserved
        phase_timing.add_count('cache_allocations',1)
        phase_timing.add_count('cache_allocated_bytes',reserved)
    if np.shares_memory(out,adapter._cache_weights) or np.shares_memory(out,adapter._cache_valid):return False""")
s=s.replace("    adapter._counts['cache_miss_entries']+=misses\n", """    adapter._counts['cache_miss_entries']+=misses
    if count>misses:
        adapter._counts['cache_hit_chunks']+=1
        phase_timing.add_count('cache_hit_chunks',1)
        phase_timing.add_count('cache_hit_entries',count-misses)
""")
s=s.replace("    adapter._cache_pair=adapter._cache_weights=adapter._cache_valid=adapter._cache_storage=None\n    adapter._counts['cache_reserved_bytes']=0", "    adapter._cache_pair=adapter._cache_weights=adapter._cache_valid=adapter._cache_storage=adapter._cache_storage_pins=None\n    released=adapter._counts['cache_reserved_bytes']\n    adapter._counts['cache_reserved_bytes']=0")
s += "    if released:\n        adapter._counts['cache_released_bytes']+=released\n        phase_timing.add_count('cache_released_bytes',released)\n"
p.write_text(s)
data=(S/'phase_timing.py').read_bytes();(P/'BASELINE_phase_timing.py').write_bytes(data)
s=data.decode().replace("'chunk_8to255_calls','chunk_256to1023_calls','chunk_1024_calls'))", "'chunk_8to255_calls','chunk_256to1023_calls','chunk_1024_calls',\n    'cache_hit_chunks','cache_hit_entries','cache_allocations','cache_allocated_bytes','cache_released_bytes'))")
(P/'phase_timing.py').write_text(s)
