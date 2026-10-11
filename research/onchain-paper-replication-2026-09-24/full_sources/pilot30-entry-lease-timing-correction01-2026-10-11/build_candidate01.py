"""Source-only segmentation of selected imported entry authority checks."""
import difflib,hashlib,json
from pathlib import Path
ROOT=Path.cwd().resolve();H=Path(__file__).resolve().parent;P=ROOT/'tradingagents/research/onchain_replication/compact_mcm_batched.py'
HELPER='''def _entry_lease(target, execution):
    """Complete genuine validation between selected entry preparation phases.

    The original scheduler owns all timestamps and rejects already stale work.
    No grace period, clock assignment or previous validation is reused here.
    """
    if 'compiled_normalization_policy' not in execution:return
    if getattr(target.execution,'_sampled_authority_lease',None) is None:return
    from .imported_authority_lease import target_lease
    target_lease(target,boundary=True)


'''
def main():
 old=P.read_text();new=old.replace('def produce(target, *, graph_hash,input_name,output_input,held):',HELPER+'def produce(target, *, graph_hash,input_name,output_input,held):')
 a="        b=validate(policy,start['cells']);modules=_modules(";b="        b=validate(policy,start['cells'])\n        _entry_lease(target,b['execution'])\n        modules=_modules(";assert new.count(a)==1;new=new.replace(a,b)
 a="        normalization=_compiled_inputs(b['execution'],owner.bound._run)\n        owner.boundary();target.check()";b="        _entry_lease(target,b['execution'])\n        normalization=_compiled_inputs(b['execution'],owner.bound._run)\n        _entry_lease(target,b['execution'])\n        owner.boundary();target.check()";assert new.count(a)==1;new=new.replace(a,b)
 (H/P.name).write_text(new)
 for left,right,suffix in [(old,new,'.patch'),(new,old,'.inverse.patch')]:
  (H/(P.name+suffix)).write_text(''.join(difflib.unified_diff(left.splitlines(True),right.splitlines(True),fromfile=str(P),tofile=str(H/P.name))))
 paths=[P,ROOT/'tradingagents/research/onchain_replication/imported_authority_interval.py',ROOT/'tradingagents/research/onchain_replication/imported_authority_lease.py',ROOT/'tradingagents/research/onchain_replication/compact_mcm.py',ROOT/'tradingagents/research/onchain_replication/imported_mcm_identity.py',ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs/eth-paper-real-data-end-to-end-resource-20261011-30/guard/child.log']
 (H/'BASELINES01.json').write_text(json.dumps({str(p.relative_to(ROOT)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in paths},sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()
