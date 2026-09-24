"""Immutable exact-state checkpoints. Loading never grants a run/cell lease."""
import io
import random
import numpy as np
import torch
from .cache import publish,read_artifact
from .provenance import canonical_bytes,digest,require_hash


REQUIRED={'model','optimizer','scheduler','rng','epoch','batch','logs','epoch_loss','epoch_count'}
RNG_REQUIRED={'python','numpy_global','pcg64','torch_cpu','torch_cuda'}


def seed_all(seed):
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    return np.random.Generator(np.random.PCG64(seed))


def _provenance(value):
    if set(value)!={'source_hashes','config_hash','input_hash','dictionary_hash','fold_id','cell_id','source_commit'}:raise ValueError('checkpoint provenance fields')
    for key in ('config_hash','input_hash','dictionary_hash'):require_hash(value[key])
    if not value['source_hashes']:raise ValueError('checkpoint sources required')
    for h in value['source_hashes']:require_hash(h)
    if len(value['source_commit'])!=40 or any(c not in '0123456789abcdef' for c in value['source_commit']):raise ValueError('checkpoint source commit')
    if not value['fold_id'] or not value['cell_id']:raise ValueError('checkpoint cell identity')


def save_checkpoint(root,model,optimizer,rng,provenance,*,epoch,batch,logs,epoch_loss=0.,epoch_count=0):
    _provenance(provenance)
    numpy_state=np.random.get_state()
    state={'model':model.state_dict(),'optimizer':optimizer.state_dict(),'scheduler':None,
           'epoch':epoch,'batch':batch,'logs':logs,'epoch_loss':epoch_loss,'epoch_count':epoch_count,
           'rng':{'python':random.getstate(),'numpy_global':(numpy_state[0],numpy_state[1].tolist(),*numpy_state[2:]),
                  'pcg64':rng.bit_generator.state,'torch_cpu':torch.get_rng_state(),
                  'torch_cuda':torch.cuda.get_rng_state_all() if torch.cuda.is_available() else []}}
    stream=io.BytesIO();torch.save(state,stream)
    key=digest(canonical_bytes({'provenance':provenance,'epoch':epoch,'batch':batch}))
    return publish(root,key,{'state.pt':stream.getvalue()},provenance)


def load_checkpoint(path,model,optimizer,rng,expected_provenance):
    _provenance(expected_provenance)
    data=read_artifact(path,expected_provenance)
    state=torch.load(io.BytesIO(data['state.pt']),map_location='cpu',weights_only=True)
    if set(state)!=REQUIRED or not isinstance(state['rng'],dict) or set(state['rng'])!=RNG_REQUIRED:raise ValueError('incomplete checkpoint state')
    if state['scheduler'] is not None or any(type(state[k]) is not int or state[k]<0 for k in ('epoch','batch','epoch_count')):raise ValueError('invalid checkpoint cursor/state')
    if len(state['rng']['torch_cuda'])!=(torch.cuda.device_count() if torch.cuda.is_available() else 0):raise ValueError('checkpoint device topology mismatch')
    model.load_state_dict(state['model'],strict=True);optimizer.load_state_dict(state['optimizer'])
    random.setstate(state['rng']['python'])
    n=state['rng']['numpy_global'];np.random.set_state((n[0],np.asarray(n[1],dtype=np.uint32),*n[2:]))
    rng.bit_generator.state=state['rng']['pcg64'];torch.set_rng_state(state['rng']['torch_cpu'])
    if torch.cuda.is_available():torch.cuda.set_rng_state_all(state['rng']['torch_cuda'])
    return state
