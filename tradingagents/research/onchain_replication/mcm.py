"""Fixed structural similarity features. The trainable MLP belongs to model.py."""
import numpy as np
from .cache import cache_key
from .dictionary import dictionary_hash
from .neighborhoods import neighborhood
from .matching_reference import match_reference
from .matching import match_batch


def mcm_features(graph,dictionary,matching_config,*,reference=False,device='cpu'):
    if dictionary_hash(dictionary)!=dictionary.identity:raise ValueError('dictionary identity mismatch')
    if cache_key(matching_config)!=dictionary.matching_config_hash:raise ValueError('dictionary/matching configuration mismatch')
    result=np.empty((len(graph.node_ids),len(dictionary.representatives)),dtype=np.float64 if reference else np.float32)
    for center in range(len(graph.node_ids)):
        local=neighborhood(graph,center,dictionary.config)
        pairs=[(local,motif) for motif in dictionary.representatives]
        scores=([match_reference(a,b,matching_config) for a,b in pairs] if reference else match_batch(pairs,matching_config,device))
        result[center]=[s.score for s in scores]
    return result
