from pathlib import Path
P=Path(__file__).resolve().parent;p=P/'matching_numeric_policy.py';s=p.read_text();(P/'RAW_matching_numeric_policy03.py').write_text(s)
s=s.replace('max_pair_cache_bytes=32*1024**2','max_cache_retained_bytes=32*1024**2,max_cache_scratch_bytes=64*1024')
s=s.replace("CACHE_POLICY['max_pair_cache_bytes']", "dict(adapter.policy)['max_cache_retained_bytes']")
needle='\ndef attach(owner,value):';s=s.replace(needle,'''\ndef cache_reservation(value):
    selected=freeze(value)
    if selected is None:return 0
    policy=dict(selected)
    if policy['format']==POLICY['format']:return 0
    return policy['max_cache_retained_bytes']+policy['max_cache_scratch_bytes']

'''+needle)
p.write_text(s)
p=P/'numeric_checks01.py';s=p.read_text().replace('max_pair_cache_bytes=32*1024**2+1','max_cache_retained_bytes=32*1024**2+1');p.write_text(s)
