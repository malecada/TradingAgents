from pathlib import Path
P=Path(__file__).resolve().parent;p=P/'matching_numeric_policy.py';s=p.read_text();(P/'RAW_matching_numeric_policy02.py').write_text(s)
s=s.replace("    adapter._cache_runtime=(annealing._reuse_runtime,annealing._reuse_runtime.__code__)","    adapter._cache_runtime=(annealing._reuse_runtime,annealing._reuse_runtime.__code__)\n    adapter._cache_round=annealing._nearest_rounding")
s=s.replace("('ndarray','dtype','float64','int64','bool_','empty','zeros','flatnonzero')", "('ndarray','dtype','float64','int64','bool_','empty','zeros','flatnonzero','multiply','add','repeat','all')")
s=s.replace("    if annealing._reuse_runtime is not runtime or runtime.__code__ is not code:", "    if (annealing._reuse_runtime is not runtime or runtime.__code__ is not code\n            or annealing._nearest_rounding is not adapter._cache_round):")
s=s.replace('    if not annealing._reuse_runtime():return False','    if not annealing._reuse_runtime() or scalar is not annealing.agreement:return False')
s=s.replace("    adapter._counts['cache_reserved_bytes']=0\n    adapter._counts['cache_weight_bytes']", "    released=adapter._counts['cache_reserved_bytes']\n    adapter._counts['cache_reserved_bytes']=0\n    adapter._counts['cache_weight_bytes']")
p.write_text(s)
