from pathlib import Path
import hashlib,json,difflib
H=Path(__file__).resolve().parent;S=H.parents[3]/'tradingagents/research/onchain_replication';changes={}
def edit(name,pairs):
 old=(S/name).read_text();new=old
 for a,b in pairs:
  assert new.count(a)==1,(name,a,new.count(a));new=new.replace(a,b)
 (H/name).write_text(new);changes[name]=dict(baseline=hashlib.sha256(old.encode()).hexdigest(),candidate=hashlib.sha256(new.encode()).hexdigest(),replacements=pairs)
edit('batched_pair_executor.py',[
 ('def __init__(self,config,policy,schedule,checkpoint):','def __init__(self,config,policy,schedule,checkpoint,*,authority_poll=None):'),
 ("        if not callable(checkpoint):raise ValueError('checkpoint callback required')","        if authority_poll is not None and not callable(authority_poll):raise ValueError('optional authority poll must be callable')\n        self.authority_poll=authority_poll\n        if not callable(checkpoint):raise ValueError('checkpoint callback required')"),
 ('            pair.hash_string(purpose_hash)','            if self.authority_poll is not None:self.authority_poll()\n            pair.hash_string(purpose_hash)'),
 ("                    session.advance(state,max_operations=self.schedule['operations_per_call'])","                    if self.authority_poll is not None:self.authority_poll()\n                    session.advance(state,max_operations=self.schedule['operations_per_call'])"),
 ("                    result=engine.score_only", "                    if self.authority_poll is not None:self.authority_poll()\n                    result=engine.score_only"),
 ("                    return float(result.score),result.iterations,result.convergence", "                    if self.authority_poll is not None:\n                        self.authority_poll();session.check(state)\n                    return float(result.score),result.iterations,result.convergence")])
pin=changes['batched_pair_executor.py']['candidate']
edit('batched_numeric_reuse.py',[
 ("5e722ec2035e2549f7584a31bf091e0de4d7854c196086f8736179f367d93b2e",pin),
 ('*,max_entries,max_retained_bytes,max_key_bytes):','*,max_entries,max_retained_bytes,max_key_bytes,authority_poll=None):'),
 ('        self.executor=accepted.PairExecutor(config,policy,schedule,self._checkpoint)','        self.authority_poll=authority_poll\n        self.executor=accepted.PairExecutor(config,policy,schedule,self._checkpoint,authority_poll=authority_poll)'),
 ("        require(not self.executor.poisoned and config_bytes", "        require(self.executor.authority_poll is self.authority_poll,'authority poll changed')\n        require(not self.executor.poisoned and config_bytes"),
 ("            self._current();require(type(purpose_hash)","            if self.authority_poll is not None:self.authority_poll()\n            self._current();require(type(purpose_hash)"),
 ("            self._current()\n            if key is not None:","            if self.authority_poll is not None:self.authority_poll()\n            self._current()\n            if key is not None:")])
edit('batched_numeric_execution.py',[
 ('max_entries,max_retained_bytes,max_key_bytes):','max_entries,max_retained_bytes,max_key_bytes,authority_poll=None):'),
 ('max_key_bytes=max_key_bytes)','max_key_bytes=max_key_bytes,authority_poll=authority_poll)')])
edit('batched_driver.py',[
 ('def _tasks(graph, motifs, extraction, policy, descriptor, typed):','def _tasks(graph, motifs, extraction, policy, descriptor, typed, authority_poll=None):'),
 ('    with ArrayNeighborhoodIndex(graph,','    if authority_poll is not None:authority_poll()\n    with ArrayNeighborhoodIndex(graph,'),
 ('        for center in range(len(graph.node_ids)):', '        if authority_poll is not None:authority_poll()\n        for center in range(len(graph.node_ids)):\n            if authority_poll is not None:authority_poll()'),
 ('            try:\n                local_id', '            try:\n                if authority_poll is not None:authority_poll()\n                local_id'),
 ('post_batch=None, final_batches=None):','post_batch=None, final_batches=None, authority_poll=None):'),
 ("        require((post_batch is None", "        require(authority_poll is None or callable(authority_poll),'optional authority poll must be callable')\n        if authority_poll is not None:authority_poll()\n        require((post_batch is None"),
 ('upstream = _tasks(graph, motifs, extraction, policy, descriptor, typed)','upstream = _tasks(graph, motifs, extraction, policy, descriptor, typed, authority_poll)')])
edit('compact_mcm_batched.py',[
 ("    b=validate(policy,start['cells']);p=thaw(target.owner.policy)","    b=validate(policy,start['cells']);p=thaw(target.owner.policy)\n    authority_poll=target.lease if policy['schema_version']==6 and getattr(target.execution,'_sampled_authority_lease',None) is not None else None"),
 ("batch_cells=b['batch_cells'],**{k:execution[k]", "batch_cells=b['batch_cells'],authority_poll=authority_poll,**{k:execution[k]"),
 ('post_batch=post_batch,final_batches=final_batches)','post_batch=post_batch,final_batches=final_batches,authority_poll=authority_poll)')])
(H/'CHANGES01.json').write_text(json.dumps(changes,indent=2)+'\n')
for name in changes:(H/(name+'.inverse.patch')).write_text(''.join(difflib.unified_diff((H/name).read_text().splitlines(True),(S/name).read_text().splitlines(True))))
