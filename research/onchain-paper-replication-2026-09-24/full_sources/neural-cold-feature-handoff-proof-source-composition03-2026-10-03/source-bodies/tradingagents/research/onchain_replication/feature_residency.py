"""Hash-verified fixed graph features loaded for one chronological batch.

The policy bounds unique stored feature-array bytes loaded for a batch. It does
not bound vector expansion, prices/targets, model state/activations, temporary
copies, Python metadata or page cache; the enclosing resource guard covers those.
"""
from collections.abc import Mapping
from .component_store import reference_bytes,materialize_component


def read_feature_policy(run,input_name):
    """Execution policy is an admitted input, not a new representation identity."""
    if input_name is None:return None
    import json
    if not isinstance(input_name,str) or not input_name:raise ValueError('feature residency input required')
    policy=json.loads(run.read_input(input_name))
    if (not isinstance(policy,dict) or set(policy)!={'schema_version','mode','max_unique_feature_bytes'}
            or type(policy['schema_version']) is not int or policy['schema_version']!=1 or policy['mode']!='batch'
            or type(policy['max_unique_feature_bytes']) is not int or policy['max_unique_feature_bytes']<=0):
        raise ValueError('feature residency policy differs')
    return policy


class FixedFeatureMap(Mapping):
    def __init__(self,references,hashes,*,max_unique_feature_bytes):
        if type(max_unique_feature_bytes) is not int or max_unique_feature_bytes<=0:raise ValueError('positive batch array bound required')
        if not references or set(references)!=set(hashes):raise ValueError('feature reference membership differs')
        self._references=dict(references);self._hashes=dict(hashes)
        self.max_unique_feature_bytes=max_unique_feature_bytes

    def __len__(self):return len(self._references)
    def __iter__(self):return iter(self._references)
    def __getitem__(self,key):return self.load_batch([key])[key]

    def verified_hashes(self):
        from .evaluation import feature_hash
        actual={h:feature_hash(v) for h,v in self._references.items()}
        if actual!=self._hashes:raise ValueError('feature reference hashes differ')
        return actual

    def load_batch(self,keys):
        from .evaluation import feature_hash
        unique=list(dict.fromkeys(keys))
        values={h:self._references[h] for h in unique}
        if reference_bytes(values)>self.max_unique_feature_bytes:raise ValueError('batch feature array bound exceeded before loading')
        loaded=materialize_component(values,max_array_bytes=self.max_unique_feature_bytes)
        if {h:feature_hash(v) for h,v in loaded.items()}!={h:self._hashes[h] for h in unique}:raise ValueError('loaded feature hashes differ')
        return loaded
