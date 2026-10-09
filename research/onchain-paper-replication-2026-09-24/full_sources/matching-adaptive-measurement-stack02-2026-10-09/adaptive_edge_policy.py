"""Fixed opt-in operational policy; immutable instance pins, no global selection."""
def freeze(value):
    if value is None or value is False:return None
    expected={'format':'adaptive-lazy-edge-cache-v1','max_edge_products':16384,'chunk_entries':256,'max_scratch_bytes':262144}
    if type(value) is not dict or set(value)!=set(expected) or value!=expected or type(value['format']) is not str or any(type(value[k]) is not int for k in ('max_edge_products','chunk_entries','max_scratch_bytes')):
        raise ValueError('fixed adaptive edge cache policy required')
    return tuple((k,value[k]) for k in sorted(expected))
def attach(owner,value):
    owner._edge_cache_policy=freeze(value);owner._edge_cache_policy_pin=owner._edge_cache_policy
def current(owner):
    if owner._edge_cache_policy is not owner._edge_cache_policy_pin:raise ValueError('adaptive edge cache selection changed')
def options(owner):
    current(owner)
    return {'edge_cache_policy':dict(owner._edge_cache_policy)} if owner._edge_cache_policy is not None else {}
def join(owner,child):
    current(owner);current(child)
    if owner._edge_cache_policy!=child._edge_cache_policy:raise ValueError('adaptive edge cache chain changed')
