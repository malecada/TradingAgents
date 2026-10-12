from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3];S=R/'tradingagents/research/onchain_replication'
base=(P.parent/'pilot40-parent-accounting-continuation-candidate-2026-10-12/batched_continuation.py').read_text();(P/'BASELINE_batched_continuation.py').write_text(base)
helper='''
def _target_identity(run,target):
    from tradingagents.research.lifecycle import ResearchRun
    from .imported_mcm_identity import Target
    require(type(run) is ResearchRun and type(target) is Target,
        'genuine continuation Run/Target required')
    owner=target.owner;execution=target.execution;bound=owner.bound
    require(bound._run is run and execution._owner is owner and execution._bound is bound,
        'continuation target Run/Owner differs')
    return (target,owner,execution,bound)


def _poll_target(run,target):
    pin=_target_identity(run,target)
    target.lease()
    require(all(a is b for a,b in zip(pin,_target_identity(run,target),strict=True)),
        'continuation target authority changed during poll')


def _reader_target(run,reader):
    if len(reader)==4:return None
    require(len(reader)==5 and type(reader[4]) is tuple and len(reader[4])==4,
        'continuation reader target pin differs')
    pin=reader[4];target=pin[0]
    require(all(a is b for a,b in zip(pin,_target_identity(run,target),strict=True)),
        'continuation reader target replaced')
    return target

'''
s=base.replace('\ndef _authority(',helper+'\ndef _authority(',1)
s=s.replace('def _authority(run, m):','def _authority(run, m, *, target=None):')
s=s.replace('    ad=run.admission\n    run._active();run._check_source()', '    ad=run.admission\n    if target is not None:_poll_target(run,target)\n    run._active();run._check_source()\n    if target is not None:_poll_target(run,target)')
s=s.replace('def verify_prefix(run, registered_input, *, expected_contract):','def verify_prefix(run, registered_input, *, expected_contract, target=None):')
s=s.replace("    require(type(run) is ResearchRun, 'genuine continuation admission required')", "    require(type(run) is ResearchRun, 'genuine continuation admission required')\n    target_pin=None if target is None else _target_identity(run,target)")
# Every metadata transaction and final revalidation gets the selected Target.
s=s.replace('max_bytes=MAX_MANIFEST_BYTES)',"max_bytes=MAX_MANIFEST_BYTES,**({'target':target} if target is not None else {}))")
s=s.replace('_authority(run,m)',"_authority(run,m,**({'target':target} if target is not None else {}))")
s=s.replace('_authority(run,_json(manifest))',"_authority(run,_json(manifest),**({'target':target} if target is not None else {}))")
s=s.replace("m.get('provenance_mode')=='legacy-recovered-prefix-v1',descriptors)","m.get('provenance_mode')=='legacy-recovered-prefix-v1',descriptors,**({'target':target} if target is not None else {}))")
s=s.replace("    _READERS[result]=(run,body(expected_contract),m.get('provenance_mode')=='legacy-recovered-prefix-v1',registered_input)","    _READERS[result]=(run,body(expected_contract),m.get('provenance_mode')=='legacy-recovered-prefix-v1',registered_input)\n    if target is not None:\n        require(all(a is b for a,b in zip(target_pin,_target_identity(run,target),strict=True)), 'continuation target changed during verification')\n        _READERS[result]=(*_READERS[result],target_pin)")
s=s.replace('            run,_,_,role=reader','            run,_,_,role=reader[:4]\n            target=_reader_target(run,reader)')
s=s.replace('def _registered_batch(run,refs,index,contract,legacy,descriptors=None):','def _registered_batch(run,refs,index,contract,legacy,descriptors=None,*,target=None):')
s=s.replace('values=run.read_inputs(names,max_each_bytes=1024**2,max_total_bytes=4*1024**2)',"values=run.read_inputs(names,max_each_bytes=1024**2,max_total_bytes=4*1024**2,**({'_continuation_target':target} if target is not None else {}))")
s=s.replace('    run,contract,legacy,_=reader','    run,contract,legacy,_=reader[:4]\n    target=_reader_target(run,reader)')
s=s.replace('legacy,dict(prefix.descriptors))',"legacy,dict(prefix.descriptors),**({'target':target} if target is not None else {}))")
s=s.replace('def _bounded_input(run,name,*,max_bytes):','def _bounded_input(run,name,*,max_bytes,target=None):')
s=s.replace('        run._active();run._check_source()', '        if target is not None:_poll_target(run,target)\n        run._active();run._check_source()\n        if target is not None:_poll_target(run,target)')
(P/'batched_continuation.py').write_text(s)
for name,path in [('lifecycle.py',R/'tradingagents/research/lifecycle.py'),('compact_mcm_batched.py',S/'compact_mcm_batched.py')]:
 text=path.read_text();(P/('BASELINE_'+name)).write_text(text)
 if name=='compact_mcm_batched.py':
  text=text.replace('verify_prefix(target.owner.bound._run,role,expected_contract=continuation)', 'verify_prefix(target.owner.bound._run,role,expected_contract=continuation,target=target)')
 else:
  start=text.index('    def read_inputs(');end=text.index('\n    def write_json(',start);part=text[start:end]
  part=part.replace('max_total_bytes):','max_total_bytes, _continuation_target=None):',1)
  part=part.replace('        with _lock(self.admission.root):',"        if _continuation_target is not None:\n            from .onchain_replication.batched_continuation import _poll_target\n        with _lock(self.admission.root):")
  part=part.replace('            self._active()\n            self._check_source()', '            if _continuation_target is not None:_poll_target(self,_continuation_target)\n            self._active()\n            self._check_source()\n            if _continuation_target is not None:_poll_target(self,_continuation_target)')
  part=part.replace('            for name, path, _ in pins:\n', '            for name, path, _ in pins:\n                if _continuation_target is not None:_poll_target(self,_continuation_target)\n')
  part=part.replace('            for name, _, _ in pins:\n', '            for name, _, _ in pins:\n                if _continuation_target is not None:_poll_target(self,_continuation_target)\n')
  text=text[:start]+part+text[end:]
 (P/name).write_text(text)
