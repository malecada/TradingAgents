"""Fixed structural similarity features. The trainable MLP belongs to model.py."""
import time
import numpy as np
from .cache import cache_key
from .dictionary import dictionary_hash
from .neighborhoods import NeighborhoodIndex
from .matching_reference import match_reference
from .matching import match_batch


def mcm_features(graph,dictionary,matching_config,*,reference=False,device='cpu',checkpoint=None,checkpoint_seconds=600.,output=None,start_node=0):
    if dictionary_hash(dictionary)!=dictionary.identity:raise ValueError('dictionary identity mismatch')
    if cache_key(matching_config)!=dictionary.matching_config_hash:raise ValueError('dictionary/matching configuration mismatch')
    if not 0<checkpoint_seconds<=600:raise ValueError('checkpoint interval exceeds protocol')
    shape=(len(graph.node_ids),len(dictionary.representatives));dtype=np.dtype(np.float64 if reference else np.float32)
    result=np.empty(shape,dtype=dtype) if output is None else output
    if result.shape!=shape or result.dtype!=dtype or not 0<=start_node<=shape[0]:raise ValueError('MCM checkpoint dimensions/cursor')
    if start_node and not np.isfinite(result[:start_node]).all():raise ValueError('invalid MCM completed prefix')
    last=time.monotonic()
    index=NeighborhoodIndex(graph)
    for center in range(start_node,len(graph.node_ids)):
        local=index.neighborhood(center,dictionary.config)
        pairs=[(local,motif) for motif in dictionary.representatives]
        scores=([match_reference(a,b,matching_config) for a,b in pairs] if reference else match_batch(pairs,matching_config,device))
        result[center]=[s.score for s in scores]
        if checkpoint and (center+1==len(graph.node_ids) or time.monotonic()-last>=checkpoint_seconds):checkpoint(center+1,result[:center+1]);last=time.monotonic()
    return result
