"""Engineering-only numeric route; no empirical/owner authority or pair receipts."""
import copy,sys,types
from . import adaptive_edge_policy
from . import compiled_normalization_policy
from . import compiled_edge_owner
from . import matching_checkpoint as engine
from tradingagents.research.onchain_replication import matching_pair as pair
from . import matching_annealing as annealing
from .matching_immutable_session import ImmutablePairSession

EXECUTION_ROUTE = "immutable-input-session-v1"

class CheckpointStop(RuntimeError): pass

class PairExecutor:
    def __init__(self,config,policy,schedule,checkpoint,*,authority_poll=None,edge_cache_policy=None,compiled_normalization_policy_value=None,compiled_edge_policy_value=None):
        adaptive_edge_policy.attach(self,edge_cache_policy)
        compiled_normalization_policy.attach(self,compiled_normalization_policy_value)
        compiled_edge_owner.attach(self,compiled_edge_policy_value)
        self.config=copy.deepcopy(config);self.policy=copy.deepcopy(policy)
        self.schedule=copy.deepcopy(schedule);self.checkpoint=checkpoint;self.poisoned=False;self.checkpoints=0;self.reserved_bytes=0
        if authority_poll is not None and not callable(authority_poll):raise ValueError('optional authority poll must be callable')
        self.authority_poll=authority_poll
        if not callable(checkpoint):raise ValueError('checkpoint callback required')
        for k in ('max_checkpoints','calls_per_checkpoint','operations_per_call','max_total_checkpoints','max_total_checkpoint_bytes'):
            if type(schedule.get(k)) is not int or schedule[k]<=0:raise ValueError('positive schedule required')
        if schedule['max_checkpoints']>policy['max_publications']:raise ValueError('checkpoint count exceeds policy')
        self.closed=False
        self._normalization_owner=(compiled_normalization_policy.BackendOwner(dict(self._compiled_normalization_policy))
            if self._compiled_normalization_policy is not None else None)
        self._normalization_owner_pin=self._normalization_owner
        self._normalization_cleanup=self._normalization_owner.close if self._normalization_owner is not None else lambda:None
        self._edge_owner=None;self._edge_owner_pin=None
        if self._compiled_edge_policy is not None:
            normal_cleanup=self._normalization_cleanup
            edge_cleanup=None
            def combined_cleanup():
                primary=None
                try:normal_cleanup()
                except BaseException as error:primary=error
                try:
                    if edge_cleanup is not None:edge_cleanup()
                except BaseException as error:
                    if primary is None:primary=error
                    else:
                        try:BaseException.add_note(primary,'edge owner cleanup failed: '+repr(error))
                        except BaseException:pass
                if primary is not None:raise primary
            self._normalization_cleanup=combined_cleanup
            owner=None
            try:
                owner=compiled_edge_owner.EdgeOwner(dict(self._compiled_edge_policy),numpy=annealing.np,scipy=sys.modules['scipy'],agreement=annealing.agreement)
                edge_cleanup=owner.close
                edge_cleanup=types.FunctionType(edge_cleanup.__code__,edge_cleanup.__globals__,closure=edge_cleanup.__closure__)
                self._edge_owner=self._edge_owner_pin=owner
                self._edge_methods=tuple((name,getattr(owner,name),getattr(owner,name).__code__) for name in ('current','borrow','close'))
            except BaseException as primary:
                try:
                    if owner is not None and edge_cleanup is None:edge_cleanup=owner.close
                    combined_cleanup()
                except BaseException as error:
                    try:BaseException.add_note(primary,'edge parent construction failed: '+repr(error))
                    except BaseException:pass
                raise
    def close(self):
        self.closed=True
        self._normalization_cleanup()

    def __call__(self,a,b,purpose_hash):
        if self.poisoned or self.closed:raise ValueError('executor poisoned or closed')
        state=None;session=None;primary=None
        try:
            if self.authority_poll is not None:self.authority_poll()
            adaptive_edge_policy.current(self)
            compiled_normalization_policy.current(self)
            compiled_edge_owner.current_policy(self)
            if self._edge_owner is not self._edge_owner_pin:raise ValueError('edge parent replaced')
            if self._edge_owner is not None:
                for name,function,code in self._edge_methods:
                    if getattr(self._edge_owner,name) is not function or function.__code__ is not code:raise ValueError('edge parent method replaced')
                self._edge_methods[0][1]()
            if self._normalization_owner is not self._normalization_owner_pin:raise ValueError('normalization owner replaced')
            if self._normalization_owner is not None:self._normalization_owner.current()
            pair.hash_string(purpose_hash)
            pair.policy_check(a,b,self.config,self.policy,allow_checkpoint_layout=True)
            reserved=self.policy['max_checkpoint_bytes']+2*pair.LIMIT
            if (self.checkpoints+self.schedule['max_checkpoints']>self.schedule['max_total_checkpoints']
                    or self.reserved_bytes+self.schedule['max_checkpoints']*reserved>self.schedule['max_total_checkpoint_bytes']):
                raise ValueError('cumulative checkpoint allowance exceeded')
            state=engine.create(a,b,self.config,**{k:self.policy[k] for k in pair.ENGINE_FIELDS})
            session=ImmutablePairSession(a,b,self.config,engine=engine,annealing=annealing,**adaptive_edge_policy.options(self),**compiled_normalization_policy.options(self),**({"_normalization_owner":self._normalization_owner} if self._normalization_owner is not None else {}),**({"edge_chunk_owner":self._edge_owner} if self._edge_owner is not None else {}))
            for ordinal in range(self.schedule['max_checkpoints']):
                for _ in range(self.schedule['calls_per_checkpoint']):
                    if self.authority_poll is not None:self.authority_poll()
                    session.advance(state,max_operations=self.schedule['operations_per_call'])
                    if state['phase']=='done':break
                if state['phase']=='done':
                    if self.authority_poll is not None:self.authority_poll()
                    result=engine.score_only(state,a,b,self.config,max_buffer_bytes=self.policy['max_score_buffer_bytes'],chunk_edges=self.policy['chunk_edges'])
                    if self.authority_poll is not None:
                        self.authority_poll();session.check(state)
                    adaptive_edge_policy.join(self,session)
                    compiled_normalization_policy.join(self,session)
                    compiled_edge_owner.join(self,session)
                    return float(result.score),result.iterations,result.convergence
                self.checkpoints+=1;self.reserved_bytes+=reserved
                self.checkpoint(purpose_hash,ordinal,state,a,b,self.config,self.policy)
            raise CheckpointStop('bounded calls exhausted; checkpoint callback already invoked')
        except BaseException as error:
            self.poisoned=True;primary=error;raise
        finally:
            cleanup_error=None
            actions=[]
            if session is not None:actions.append(session.close)
            if state is not None:actions.append(lambda:engine.close(state))
            for action in actions:
                try:action()
                except BaseException as cleanup:
                    self.poisoned=True
                    if primary is not None:
                        try:BaseException.add_note(primary,'executor cleanup failed: '+repr(cleanup))
                        except BaseException:pass
                    elif cleanup_error is None:cleanup_error=cleanup
                    else:
                        try:BaseException.add_note(cleanup_error,'additional executor cleanup failed: '+repr(cleanup))
                        except BaseException:pass
            if self.poisoned:
                self.closed=True
                try:self._normalization_cleanup()
                except BaseException as cleanup:
                    if primary is not None:
                        try:BaseException.add_note(primary,'executor backend cleanup failed: '+repr(cleanup))
                        except BaseException:pass
                    elif cleanup_error is None:cleanup_error=cleanup
                    else:
                        try:BaseException.add_note(cleanup_error,'additional backend cleanup failed: '+repr(cleanup))
                        except BaseException:pass
            if primary is None and cleanup_error is not None:raise cleanup_error
