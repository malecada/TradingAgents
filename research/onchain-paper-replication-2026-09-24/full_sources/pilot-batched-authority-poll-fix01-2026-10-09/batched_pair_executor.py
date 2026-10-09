"""Engineering-only numeric route; no empirical/owner authority or pair receipts."""
import copy
from tradingagents.research.onchain_replication import matching_checkpoint as engine
from tradingagents.research.onchain_replication import matching_pair as pair
from tradingagents.research.onchain_replication import matching_annealing as annealing
from tradingagents.research.onchain_replication.matching_immutable_session import ImmutablePairSession

EXECUTION_ROUTE = "immutable-input-session-v1"

class CheckpointStop(RuntimeError): pass

class PairExecutor:
    def __init__(self,config,policy,schedule,checkpoint,*,authority_poll=None):
        self.config=copy.deepcopy(config);self.policy=copy.deepcopy(policy)
        self.schedule=copy.deepcopy(schedule);self.checkpoint=checkpoint;self.poisoned=False;self.checkpoints=0;self.reserved_bytes=0
        if authority_poll is not None and not callable(authority_poll):raise ValueError('optional authority poll must be callable')
        self.authority_poll=authority_poll
        if not callable(checkpoint):raise ValueError('checkpoint callback required')
        for k in ('max_checkpoints','calls_per_checkpoint','operations_per_call','max_total_checkpoints','max_total_checkpoint_bytes'):
            if type(schedule.get(k)) is not int or schedule[k]<=0:raise ValueError('positive schedule required')
        if schedule['max_checkpoints']>policy['max_publications']:raise ValueError('checkpoint count exceeds policy')
    def __call__(self,a,b,purpose_hash):
        if self.poisoned:raise ValueError('executor poisoned')
        state=None;session=None;primary=None
        try:
            if self.authority_poll is not None:self.authority_poll()
            pair.hash_string(purpose_hash)
            pair.policy_check(a,b,self.config,self.policy,allow_checkpoint_layout=True)
            reserved=self.policy['max_checkpoint_bytes']+2*pair.LIMIT
            if (self.checkpoints+self.schedule['max_checkpoints']>self.schedule['max_total_checkpoints']
                    or self.reserved_bytes+self.schedule['max_checkpoints']*reserved>self.schedule['max_total_checkpoint_bytes']):
                raise ValueError('cumulative checkpoint allowance exceeded')
            state=engine.create(a,b,self.config,**{k:self.policy[k] for k in pair.ENGINE_FIELDS})
            session=ImmutablePairSession(a,b,self.config,engine=engine,annealing=annealing)
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
                    if primary is not None:primary.add_note('executor cleanup failed: '+repr(cleanup))
                    elif cleanup_error is None:cleanup_error=cleanup
                    else:cleanup_error.add_note('additional executor cleanup failed: '+repr(cleanup))
            if primary is None and cleanup_error is not None:raise cleanup_error
