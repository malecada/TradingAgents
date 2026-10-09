"""Source-only private matching session for exclusively owned immutable inputs.

Caller supplies the changed engine/annealing modules. No Run, Owner, checkpoint
authority or empirical grant is created. Graphs are validated and hashed at
entry; immutable buffer/metadata/config pins are checked on every advance.
Every mutable numerical state check remains. Real checkpoint publication uses
the unchanged public save API and its full checks. Source/runtime authority is
the caller's entry/checkpoint/batch/final responsibility.
"""
import json
from . import adaptive_edge_policy
from types import MappingProxyType
import numpy as np
from tradingagents.research.onchain_replication.contracts import AttributedGraph


def require(value, message):
    if not value:
        raise ValueError(message)


def config_pin(config):
    require(type(config) is dict and all(type(k) is str and
            type(v) in (str, int, float, bool) for k, v in config.items()),
            'plain primitive config required')
    return tuple(sorted((k, type(v), v) for k, v in config.items()))


def array_pin(array):
    require(type(array) is np.ndarray and array.flags.c_contiguous,
            'ordinary contiguous array required')
    chain = []
    current = array
    for _ in range(4):
        if type(current) is bytes:
            return (array, tuple(chain), current, array.dtype.str,
                    tuple(array.shape), tuple(array.strides), array.nbytes)
        require(type(current) is np.ndarray and not current.flags.writeable,
                'immutable bytes-backed array required')
        chain.append(current)
        current = current.base
    raise ValueError('bounded immutable base chain required')


def graph_pin(graph):
    require(type(graph) is AttributedGraph and type(graph.node_ids) is tuple
            and all(type(x) is str for x in graph.node_ids)
            and type(graph.parent_hash) is type(graph.center_id) is str,
            'ordinary immutable attributed graph required')
    return (graph.node_ids, graph.parent_hash, graph.center_id,
            tuple(array_pin(getattr(graph, name)) for name in
                  ('node_features', 'edge_index', 'edge_features')))


def rejoin(graph, pin):
    require(graph.node_ids is pin[0] and graph.parent_hash == pin[1]
            and graph.center_id == pin[2], 'graph identity metadata changed')
    for name, saved in zip(('node_features', 'edge_index', 'edge_features'),
                           pin[3], strict=True):
        current = getattr(graph, name)
        require(current is saved[0] and current.dtype.str == saved[3]
                and tuple(current.shape) == saved[4]
                and tuple(current.strides) == saved[5]
                and current.nbytes == saved[6] and current.flags.c_contiguous,
                'graph array metadata changed')
        for item in saved[1]:
            require(current is item and not current.flags.writeable,
                    'graph array base changed')
            current = current.base
        require(current is saved[2], 'graph immutable byte owner changed')


class ImmutablePairSession:
    def __init__(self, a, b, config, *, engine, annealing, edge_cache_policy=None):
        require(engine.ann is annealing and
                callable(getattr(engine, '_check_owned', None)) and
                callable(getattr(engine, '_advance_owned', None)) and
                callable(getattr(annealing, '_check_state_identity', None)),
                'explicit changed engine required')
        adaptive_edge_policy.attach(self,edge_cache_policy)
        self.engine, self.annealing = engine, annealing
        self.a, self.b, self.config = a, b, config
        self.config_pin = config_pin(config)
        # Exactly the original validation and typed hashes at entry.
        annealing.validate_pair(a, b, config)
        self.identity = MappingProxyType(annealing.identity(a, b, config))
        self.pins = (graph_pin(a), graph_pin(b))
        self.functions = tuple((module, name, getattr(module, name),
                                getattr(module, name).__code__) for module, name in
            ((engine, 'policy'), (engine, '_check_owned'),
             (engine, '_advance_owned'), (engine, 'matrix_identity'),
             (engine.hard, 'check'), (engine.hard, 'create'),
             (engine.hard, 'advance'),
             (annealing, 'normalization_policy'),
             (annealing, '_check_state_identity'),
             (annealing, '_advance_checked')))
        self.dependencies = ((engine, 'ann', annealing),
                             (engine, 'hard', engine.hard),
                             (engine, 'np', engine.np),
                             (annealing, 'np', annealing.np))
        self.closed = False
        self.advances = 0

    def current(self):
        require(not self.closed, 'matching session closed')
        adaptive_edge_policy.current(self)
        require(config_pin(self.config) == self.config_pin, 'matching config changed')
        rejoin(self.a, self.pins[0]); rejoin(self.b, self.pins[1])
        for module, name, dependency in self.dependencies:
            require(getattr(module, name) is dependency,
                    'matching module dependency changed')
        for module, name, function, code in self.functions:
            require(getattr(module, name) is function and function.__code__ is code,
                    'matching function changed')

    def check(self, state):
        self.current()
        def checked(inner, a, b, config):
            require(a is self.a and b is self.b and config is self.config,
                    'matching session redirected')
            self.annealing._check_state_identity(
                inner, a, b, config, lambda: self.identity)
        self.engine._check_owned(state, self.a, self.b, self.config, checked)

    def advance(self, state, *, max_operations):
        self.check(state)
        require(type(max_operations) is int and max_operations > 0,
                'positive operation allowance required')
        # No external callback between current-input/state check and body.
        result = self.engine._advance_owned(
            state, self.a, self.b, self.config, max_operations=max_operations,**adaptive_edge_policy.options(self))
        adaptive_edge_policy.current(self)
        self.advances += 1
        return result

    def close(self):
        # Session never owns state/ranking files; caller must engine.close(state).
        self.closed = True
        self.a = self.b = self.config = self.pins = self.identity = None
