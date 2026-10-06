"""One finite numerical resource update, never admission or completed fitting.

The caller must establish the genuine ResearchRun/current imported Binding/Owner
and pass its boundary checker. A callback is not authority by itself. This helper
creates no capabilities and must not be used by an unadmitted launcher. All data
come from the caller's admitted evaluation.batch_factory and complete graphs.
"""
import hashlib
import json
import os
from pathlib import Path
import time

MODEL_SHA = '29af65736dddfbd22b5ce94c6ff3e507041b00dc81dfcc94c6919a615a68dcb7'
TRAINING_SHA = 'c46c39a81658d1fb9ae9c97989bb0ffb6b932f77099d6c06d6bbf7bfb7640f11'


def _require(value, message):
    if not value:
        raise ValueError(message)


def _encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _tensor_hash(tensor):
    # No whole-array copy: caller-owned contiguous CPU storage, bounded hash slices.
    view = memoryview(tensor.detach().numpy()).cast('B')
    digest = hashlib.sha256()
    for offset in range(0, len(view), 1024**2):
        digest.update(view[offset:offset+1024**2])
    return digest.hexdigest()


def _same(a, b, torch):
    if type(a) is not type(b):
        return False
    if isinstance(a, torch.Tensor):
        return a.dtype == b.dtype and a.shape == b.shape and torch.equal(a, b)
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(_same(a[k], b[k], torch) for k in a)
    if isinstance(a, (tuple, list)):
        return len(a) == len(b) and all(_same(x, y, torch) for x, y in zip(a, b))
    return a == b


class _Writer:
    def __init__(self, stream, limit):
        self.stream, self.limit, self.count = stream, limit, 0

    def write(self, value):
        if self.count + len(value) > self.limit:
            raise ValueError('pilot checkpoint byte limit exceeded; partial retained')
        n = self.stream.write(value)
        self.count += n
        return n

    def flush(self):
        self.stream.flush()


def run_one_update(*, model_factory, batch_factory, indices, graph_features,
                   graph_contracts, graph_sequences, model_config, training_config,
                   provenance, directory, authority_check, max_checkpoint_bytes,
                   task='classification', seed=11, model_execution=None):
    """Use exactly seven complete graphs and one real batch; retain failures.

    graph_contracts maps seven graph SHA256 identities to {nodes, edges,
    mcm_sha256, edge_index_sha256}; tensor hashes are SHA256 of contiguous CPU raw
    bytes (not NPY files). The caller binds these contracts to actual imported
    Owner evidence. graph_sequences is the registered 16x28 hash membership;
    indices names exactly16 consecutive eligible rows in the existing batch factory.
    model_factory runs after seed_all(11) and must return the original model.
    model_execution defaults to eager (None). Known streamed and explicit
    checkpointed-streamed policies must be registered by the caller; neither
    changes the frozen scientific config or grants execution admission.
    authority_check raises on lost Run/Binding/Owner/guard authority.
    """
    _require(callable(authority_check), 'current caller authority checker required')
    authority_check()  # Before imports, output birth or tensor work.
    _require(type(seed) is int and seed == 11 and task in ('classification', 'regression'), 'fixed seed/task differs')
    _require(hashlib.sha256(_encode(model_config)).hexdigest() == MODEL_SHA, 'frozen model config differs')
    _require(hashlib.sha256(_encode(training_config)).hexdigest() == TRAINING_SHA, 'frozen training config differs')
    _require(type(max_checkpoint_bytes) is int and 0 < max_checkpoint_bytes <= 4*1024**2, 'finite checkpoint cap required')
    _require(type(indices) is list and len(indices) == 16 and all(type(i) is int and i >= 0 for i in indices)
             and indices == list(range(indices[0], indices[0]+16)), 'exact consecutive chronological batch16 required')
    _require(type(graph_contracts) is dict and len(graph_contracts) == 7
             and set(graph_features) == set(graph_contracts), 'exact seven graph population required')
    _require(len({id(g) for g in graph_features.values()}) == 7, 'distinct graph hashes require distinct graph objects')
    _require(type(graph_sequences) is list and len(graph_sequences) == 16
             and all(type(row) is list and len(row) == 28 for row in graph_sequences), 'exact16x28 graph membership required')
    _require({h for row in graph_sequences for h in row} == set(graph_contracts), 'batch graph hash union differs')
    # Freeze small documentary contracts; no arrays or authority are copied here.
    model_config = json.loads(_encode(model_config))
    training_config = json.loads(_encode(training_config))
    indices = list(indices)
    execution_input = json.loads(_encode(model_execution))
    contracts = json.loads(_encode(graph_contracts))
    sequences = json.loads(_encode(graph_sequences))
    provenance_raw = _encode(provenance)
    _require(len(provenance_raw) <= 65536, 'bounded pilot provenance required')
    directory = Path(directory)
    _require(directory.is_absolute() and directory.resolve() == directory and directory.parent.is_dir(), 'canonical existing parent required')
    directory.mkdir(mode=0o700, exist_ok=False)
    started = time.monotonic()
    seconds = {}
    steps = 0
    optimizer_started = False

    def write(name, value):
        raw = _encode(value) + b'\n'
        _require(len(raw) <= 65536, 'bounded pilot receipt required')
        with (directory/name).open('xb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())

    def event(phase, state):
        with (directory/'phases.jsonl').open('ab') as stream:
            stream.write(_encode({'phase':phase, 'state':state, 'elapsed_seconds':time.monotonic()-started})+b'\n')
            stream.flush(); os.fsync(stream.fileno())

    def phase(name, fn):
        authority_check()
        event(name, 'before')
        begin = time.monotonic()
        value = fn()
        seconds[name] = time.monotonic()-begin
        event(name, 'after')
        authority_check()
        return value

    try:
        import torch
        from .model import ReplicationModel, validate_execution
        from .checkpoints import seed_all, capture_rng, restore_rng
        _require(torch.get_num_threads() <= 2, 'caller must establish at most two torch threads')
        validated_execution = validate_execution(execution_input)
        selected_execution = None if validated_execution is None else dict(validated_execution)
        selected_checkpointing = selected_execution is not None and selected_execution.get('graph_activation_checkpointing',False)

        def validate_graphs():
            for key, contract in contracts.items():
                _require(type(key) is str and len(key) == 64 and all(c in '0123456789abcdef' for c in key), 'graph hash identity differs')
                _require(set(contract) == {'nodes','edges','mcm_sha256','edge_index_sha256'} and type(contract['nodes']) is int and contract['nodes'] > 0
                         and type(contract['edges']) is int and contract['edges'] >= 0, 'graph contract fields differ')
                graph = graph_features[key]
                _require(type(graph) is dict and set(graph) == {'mcm','edge_index'}, 'complete unmasked graph features required')
                mcm, edges = graph['mcm'], graph['edge_index']
                for tensor in (mcm, edges):
                    _require(isinstance(tensor, torch.Tensor) and tensor.device.type == 'cpu' and tensor.is_contiguous()
                             and not tensor.requires_grad, 'fixed contiguous CPU graph tensors required')
                _require(mcm.dtype == torch.float32 and tuple(mcm.shape) == (contract['nodes'],32), 'complete MCM32 node denominator differs')
                _require(edges.dtype == torch.int64 and tuple(edges.shape) == (2,contract['edges']), 'complete edge denominator differs')
                _require(torch.isfinite(mcm).all().item(), 'nonfinite MCM')
                _require(not edges.numel() or (edges.min().item() >= 0 and edges.max().item() < len(mcm)), 'graph edge endpoint differs')
                _require(_tensor_hash(mcm) == contract['mcm_sha256'] and _tensor_hash(edges) == contract['edge_index_sha256'], 'complete graph tensor bytes differ')

        phase('graph_validation', validate_graphs)
        rng = seed_all(seed)
        model = phase('model', model_factory)
        _require(type(model) is ReplicationModel and model.config == model_config and model.graph.config == model_config
                 and model.task == task and model.graph_activation_checkpointing is selected_checkpointing, 'original trainable model/config or selected checkpoint execution differs')
        _require(model.execution == selected_execution and model.graph.execution == selected_execution,
                 'model and graph execution differ from explicit selection')
        _require(all(p.requires_grad and p.device.type == 'cpu' and p.dtype == torch.float32 for p in model.parameters()), 'all original CPUfloat32 parameters must train')
        inputs, targets = phase('batch', lambda: batch_factory(list(indices)))
        _require(type(inputs) is dict and set(inputs) == {'prices','graph_sequences'}, 'unmasked real batch fields differ')
        prices = inputs['prices']
        _require(isinstance(prices, torch.Tensor) and prices.dtype == torch.float32 and prices.device.type == 'cpu'
                 and tuple(prices.shape) == (16,28,1) and torch.isfinite(prices).all().item(), 'real finite16x28 prices required')
        actual = inputs['graph_sequences']
        _require(len(actual) == 16 and all(len(row) == 28 for row in actual), 'actual graph sequence extent differs')
        _require(all(actual[i][j] is graph_features[h] for i,row in enumerate(sequences) for j,h in enumerate(row)), 'actual graph object/hash reuse differs')
        _require(isinstance(targets,torch.Tensor) and targets.device.type == 'cpu', 'real CPU targets required')
        if task == 'classification':
            _require(targets.dtype == torch.int64 and tuple(targets.shape) == (16,) and ((targets == 0)|(targets == 1)).all().item(), 'real binary16 labels required')
        else:
            _require(targets.dtype == torch.float32 and tuple(targets.shape) == (16,1) and torch.isfinite(targets).all().item(), 'real finite16x1 targets required')
        model.train()
        t = training_config
        optimizer = torch.optim.Adam(model.parameters(), lr=t['learning_rate'], betas=tuple(t['betas']), eps=t['epsilon'], weight_decay=t['weight_decay'])
        optimizer.zero_grad(set_to_none=True)
        output = phase('forward', lambda: model(**inputs))
        _require(tuple(output.shape) == ((16,2) if task == 'classification' else (16,1)), 'real output cardinality differs')
        loss = torch.nn.functional.cross_entropy(output,targets) if task == 'classification' else torch.nn.functional.mse_loss(output,targets)
        _require(torch.isfinite(loss).item(), 'nonfinite pilot loss')
        loss_value = float(loss.detach())
        phase('backward', loss.backward)
        gradients = {}
        for name, parameters in model.parameter_groups().items():
            grads = [p.grad for p in parameters]
            _require(grads and all(g is not None and torch.isfinite(g).all().item() for g in grads), 'missing/nonfinite '+name+' gradients')
            nonzero = sum(torch.count_nonzero(g).item() for g in grads)
            _require(nonzero > 0, 'disconnected/zero '+name+' gradients')
            gradients[name] = {'tensors':len(grads), 'nonzero_elements':nonzero}
        phase('clip', lambda: torch.nn.utils.clip_grad_norm_(model.parameters(), t['gradient_clip_norm'], error_if_nonfinite=True))
        def step():
            nonlocal optimizer_started, steps
            optimizer_started = True
            optimizer.step()
            steps = 1
        phase('optimizer', step)
        _require(all(torch.isfinite(p).all().item() for p in model.parameters()), 'nonfinite updated model')
        del output, loss
        state = {'schema_version':1, 'kind':'real-data-resource-update', 'model':model.state_dict(),
                 'optimizer':optimizer.state_dict(), 'rng':capture_rng(rng), 'optimizer_steps':1,
                 'financial_fit_complete':False, 'seed':11, 'task':task, 'model_config':model_config,
                 'model_execution':selected_execution,
                 'training_config':training_config, 'provenance':json.loads(provenance_raw),
                 'indices':indices, 'graph_sequences':sequences, 'graph_contracts':contracts, 'loss':loss_value}
        checkpoint = directory/'checkpoint.pt'
        def save():
            with checkpoint.open('xb') as stream:
                torch.save(state, _Writer(stream,max_checkpoint_bytes))
                stream.flush(); os.fsync(stream.fileno())
        phase('checkpoint', save)
        def readback():
            _require(0 < checkpoint.stat().st_size <= max_checkpoint_bytes, 'checkpoint byte extent differs')
            loaded = torch.load(checkpoint,map_location='cpu',weights_only=True)
            _require(_same(state,loaded,torch), 'checkpoint exact state readback differs')
            model.load_state_dict(loaded['model'],strict=True)
            optimizer.load_state_dict(loaded['optimizer'])
            restore_rng(loaded['rng'],rng)
            _require(_same(model.state_dict(),loaded['model'],torch) and _same(optimizer.state_dict(),loaded['optimizer'],torch)
                     and _same(capture_rng(rng),loaded['rng'],torch), 'checkpoint restored model/optimizer/RNG differs')
        phase('readback', readback)
        phase('final_graph_validation', validate_graphs)
        result = {'schema_version':1,'status':'complete','scope':'one numerical resource update only',
                  'optimizer_steps':1,'financial_fit_complete':False,'paper_financial_fits':0,
                  'batch':16,'lookback':28,'unique_graphs':7,'graph_references':448,'seed':11,
                  'model_execution':selected_execution,
                  'loss':loss_value,'gradients':gradients,'seconds':seconds,
                  'checkpoint_exact_readback':True,'checkpoint_bytes':checkpoint.stat().st_size,
                  'checkpoint_sha256':hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
                  'elapsed_seconds':time.monotonic()-started}
        write('complete.json',result)
        return result
    except BaseException as error:
        try:
            write('failed.json',{'status':'failed','type':type(error).__name__,'error':str(error)[:2048],
                  'optimizer_steps':steps,'optimizer_step_started':optimizer_started,'financial_fit_complete':False,
                  'seconds':seconds,'elapsed_seconds':time.monotonic()-started,'partial_files_retained':True})
        except BaseException as secondary:
            error.add_note('pilot failure receipt failed: '+repr(secondary))
        raise
