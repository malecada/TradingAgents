"""Source-only private matching session for exclusively owned immutable inputs.

Caller supplies the changed engine/annealing modules. No Run, Owner, checkpoint
authority or empirical grant is created. Graphs are validated and hashed at
entry; immutable buffer/metadata/config pins are checked on every advance.
Every mutable numerical state check remains. Real checkpoint publication uses
the unchanged public save API and its full checks. Source/runtime authority is
the caller's entry/checkpoint/batch/final responsibility.
"""
import json
from . import adaptive_edge_policy, matching_numeric_policy, phase_timing
from . import compiled_normalization_policy
from . import compiled_edge_owner
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
    def __init__(self, a, b, config, *, engine, annealing, edge_cache_policy=None,compiled_normalization_policy_value=None,_normalization_owner=None,edge_chunk_owner=None,numeric_kernel_policy=None):
        require(engine.ann is annealing and
                callable(getattr(engine, '_check_owned', None)) and
                callable(getattr(engine, '_advance_owned', None)) and
                callable(getattr(annealing, '_check_state_identity', None)),
                'explicit changed engine required')
        matching_numeric_policy.attach(self,numeric_kernel_policy)
        self._numeric_adapter = None if numeric_kernel_policy is None else matching_numeric_policy.NumericAgreementAdapter(numeric_kernel_policy)
        self._numeric_pin = self._numeric_adapter
        self._numeric_class = matching_numeric_policy.NumericAgreementAdapter
        self._numeric_methods = tuple((name,getattr(self._numeric_class,name),getattr(self._numeric_class,name).__code__) for name in ("__init__","fill","current","snapshot"))
        self._fill_edge_function = type(self)._fill_edge
        self._fill_edge_code = self._fill_edge_function.__code__
        adaptive_edge_policy.attach(self,edge_cache_policy)
        compiled_normalization_policy.attach(self,compiled_normalization_policy_value)
        require(edge_chunk_owner is None or type(edge_chunk_owner) is compiled_edge_owner.EdgeOwner, "typed edge owner required")
        compiled_edge_owner.attach(self,None if edge_chunk_owner is None else dict(edge_chunk_owner.policy))
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
        # Allocate the terminal cleanup closure before acquiring any backend.
        # Its original capability is independent of the checked mutable attrs.
        owned_close = None
        close_attempted = False
        close_error = None
        def owned_cleanup():
            nonlocal close_attempted, close_error
            if close_error is not None:raise close_error
            if close_attempted:return
            close_attempted = True
            if owned_close is not None:
                try:owned_close()
                except BaseException as error:
                    close_error = error
                    raise
        self._normalizer_cleanup = owned_cleanup
        normalizer = None
        try:
            normalizer = compiled_normalization_policy.open_backend(self) if _normalization_owner is None else _normalization_owner.borrow(self)
            owned_close = normalizer.close if normalizer is not None else None
            self._normalizer = normalizer
            self._normalizer_pin = normalizer
            self._normalizer_functions = tuple((name,getattr(normalizer,name),getattr(normalizer,name).__code__) for name in (("lse","close") if _normalization_owner is None else ("lse","close","current"))) if normalizer is not None else ()
        except BaseException as primary:
            # Until this constructor returns, the executor has no session to
            # close. Attempt acquired cleanup here, retaining the primary error.
            try:
                if normalizer is not None and owned_close is None:owned_close = normalizer.close
                owned_cleanup()
            except BaseException as cleanup:
                try:BaseException.add_note(primary, 'session construction cleanup failed: '+repr(cleanup))
                except BaseException:pass
            raise


        try:
            self._edge_lease = None
            self._edge_pin = None
            self._edge_functions = ()
            if edge_chunk_owner is not None:
                normal_cleanup = self._normalizer_cleanup
                edge_close = None
                def combined_cleanup():
                    primary = None
                    try:normal_cleanup()
                    except BaseException as error:primary = error
                    try:
                        if edge_close is not None:edge_close()
                    except BaseException as error:
                        if primary is None:primary = error
                        else:
                            try:BaseException.add_note(primary, 'edge release failed: '+repr(error))
                            except BaseException:pass
                    if primary is not None:raise primary
                self._normalizer_cleanup = combined_cleanup
                lease = None
                try:
                    require(type(edge_chunk_owner) is compiled_edge_owner.EdgeOwner, 'typed authenticated edge owner required')
                    lease = edge_chunk_owner.borrow(self)
                    edge_close = lease.close
                    self._edge_lease = self._edge_pin = lease
                    self._edge_functions = tuple((name,getattr(lease,name),getattr(lease,name).__code__) for name in ('fill','current','close'))
                except BaseException as primary:
                    try:
                        if lease is not None and edge_close is None:edge_close = lease.close
                        combined_cleanup()
                    except BaseException as error:
                        try:BaseException.add_note(primary, 'edge session construction cleanup failed: '+repr(error))
                        except BaseException:pass
                    raise
        except BaseException as primary:
            try:self._normalizer_cleanup()
            except BaseException as error:
                try:BaseException.add_note(primary, 'edge setup cleanup failed: '+repr(error))
                except BaseException:pass
            raise

        prior_cleanup=self._normalizer_cleanup
        try:
            if matching_numeric_policy.cache_selected(self._numeric_adapter):
                cached_adapter=self._numeric_adapter
                release_cache=matching_numeric_policy._cache_release
                def numeric_cleanup():
                    primary=None
                    try:release_cache(cached_adapter)
                    except BaseException as error:primary=error
                    try:prior_cleanup()
                    except BaseException as error:
                        if primary is None:primary=error
                        else:
                            try:BaseException.add_note(primary,'remaining session cleanup failed: '+repr(error))
                            except BaseException:pass
                    if primary is not None:raise primary
                self._normalizer_cleanup=numeric_cleanup
        except BaseException as primary:
            try:prior_cleanup()
            except BaseException as cleanup:
                try:BaseException.add_note(primary,'numeric cleanup setup failed: '+repr(cleanup))
                except BaseException:pass
            raise

    def _edge_current(self):
        compiled_edge_owner.current_policy(self)
        require(self._edge_lease is self._edge_pin, 'edge lease replaced')
        for name,function,code in self._edge_functions:
            require(getattr(self._edge_lease,name) is function and function.__code__ is code, 'edge lease method replaced')
        if self._edge_lease is not None:self._edge_functions[1][1]()

    def current(self):
        require(not self.closed, 'matching session closed')
        matching_numeric_policy.current(self)
        require(self._numeric_adapter is self._numeric_pin, 'numeric adapter replaced')
        require(matching_numeric_policy.NumericAgreementAdapter is self._numeric_class, 'numeric class replaced')
        for name,function,code in self._numeric_methods:
            require(getattr(self._numeric_class,name) is function and function.__code__ is code, 'numeric method replaced')
            if self._numeric_adapter is not None:
                require(name not in vars(self._numeric_adapter), 'numeric method shadowed')
        require(type(self)._fill_edge is self._fill_edge_function and type(self)._fill_edge.__code__ is self._fill_edge_code and '_fill_edge' not in vars(self), 'numeric fill seam changed')
        if self._numeric_adapter is not None:self._numeric_adapter.current()
        self._edge_current()
        adaptive_edge_policy.current(self)
        compiled_normalization_policy.current(self)
        require(self._normalizer is self._normalizer_pin, "normalization backend changed")
        for name,function,code in self._normalizer_functions:
            require(getattr(self._normalizer,name) is function and function.__code__ is code, "normalization function changed")
        if len(self._normalizer_functions)==3:self._normalizer_functions[2][1]()
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
        with phase_timing.measure("state_scan"):
            self.engine._check_owned(state, self.a, self.b, self.config, checked)

    def _fill_edge(self, out, left, right, li, ri, count, scalar, progress):
        if self._numeric_adapter.fill(out,left,right,li,ri,count,scalar,progress):
            progress.append('telemetry_recorded')
            return True
        if self._edge_lease is not None:
            accepted=self._edge_functions[0][1](out,left,right,li,ri,count,scalar,progress)
            if accepted is True:
                phase_timing.add_count('agreement_native_chunks',1)
                phase_timing.add_count('agreement_native_entries',count)
                progress.append('telemetry_recorded')
            return accepted
        return False

    def advance(self, state, *, max_operations):
        self.check(state)
        require(type(max_operations) is int and max_operations > 0,
                'positive operation allowance required')
        # No external callback between current-input/state check and body.
        result = self.engine._advance_owned(
            state, self.a, self.b, self.config, max_operations=max_operations,**adaptive_edge_policy.options(self),**({"normalizer":self._normalizer} if self._normalizer is not None else {}),**({"edge_chunk_fill":self._fill_edge} if self._numeric_adapter is not None else ({"edge_chunk_fill":self._edge_functions[0][1]} if self._edge_lease is not None else {})))
        adaptive_edge_policy.current(self)
        compiled_normalization_policy.current(self)
        require(self._normalizer is self._normalizer_pin, "normalization backend changed")
        for name,function,code in self._normalizer_functions:
            require(getattr(self._normalizer,name) is function and function.__code__ is code, "normalization function changed")
        if len(self._normalizer_functions)==3:self._normalizer_functions[2][1]()
        self._edge_current()
        matching_numeric_policy.current(self)
        if self._numeric_adapter is not None:self._numeric_adapter.current()
        self.advances += 1
        return result

    def close(self):
        # Session never owns state/ranking files; caller must engine.close(state).
        cleanup = self._normalizer_cleanup
        try:
            self.closed = True
            self.a = self.b = self.config = self.pins = self.identity = None
        except BaseException as primary:
            try:cleanup()
            except BaseException as error:
                try:BaseException.add_note(primary, 'session close cleanup failed: '+repr(error))
                except BaseException:pass
            raise
        else:cleanup()
