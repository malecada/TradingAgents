from pathlib import Path
P=Path(__file__).resolve().parent
S=P.parents[3]/'tradingagents/research/onchain_replication'
for name in ('archive_owner_policy.py','archive_owner_operations.py','typed_payload_operations.py'):
 text=(S/name).read_text();(P/('BASELINE_'+name)).write_text(text)
 if name=='archive_owner_policy.py':
  pos=text.index('\ndef _inputs(')
  text=text[:pos]+'''\ndef _poll_target(owner,target):
    from .imported_mcm_identity import Target
    require(type(target) is Target and target.owner is owner and target.execution._owner is owner,
        'genuine same-owner archive target required')
    execution=target.execution
    target.lease()
    require(type(target) is Target and target.owner is owner and target.execution is execution
        and execution._owner is owner,'archive target changed during poll')

'''+text[pos:]
  text=text.replace('def _inputs(owner, name):','def _inputs(owner, name, *, target=None):')
  text=text.replace("    item = json.loads(run.read_input(selected['plan_input']))", "    if target is not None:_poll_target(owner,target)\n    item = json.loads(run.read_input(selected['plan_input']))")
  text=text.replace('    for value in (selected,item):','    if target is not None:_poll_target(owner,target)\n    for value in (selected,item):')
  text=text.replace('def _record(owner, name, transport):','def _record(owner, name, transport, *, target=None):')
  text=text.replace('    owner.boundary();compact_owner.verify_current(owner)','    owner.boundary();compact_owner.verify_current(owner)\n    if target is not None:_poll_target(owner,target)')
  text=text.replace('    policy,reference = _inputs(owner,name)','    policy,reference = _inputs(owner,name,**({\'target\':target} if target is not None else {}))')
  text=text.replace('require(_inputs(owner,name) ==','require(_inputs(owner,name,**({\'target\':target} if target is not None else {})) ==')
  text=text.replace('    def check(self):','    def check(self,*,target=None):')
  text=text.replace('_record(self._owner,self._input,self._transport) ==','_record(self._owner,self._input,self._transport,**({\'target\':target} if target is not None else {})) ==')
  text=text.replace('    def writer_policy(self,name):\n        self.check()','    def writer_policy(self,name,*,target=None):\n        self.check(**({\'target\':target} if target is not None else {}))')
 elif name=='archive_owner_operations.py':
  text=text.replace('def _current(self, *, full, sampled_evidence=False):','def _current(self, *, full, sampled_evidence=False, target=None):')
  text=text.replace('if full:self.selection.check()','if full:self.selection.check(**({\'target\':target} if target is not None else {}))')
 else:
  text=text.replace('self.context._outer();self.ledger._current(full=True);self.ledger._stage(stage)',"self.context._outer()\n        if target is not None:self._poll_target_pre_cap()\n        self.ledger._current(full=True,**({'target':target} if target is not None else {}));self.ledger._stage(stage)\n        if target is not None:self._poll_target_pre_cap()")
  text=text.replace("self.ledger.selection.writer_policy(stage.name)['remote_prefix']", "self.ledger.selection.writer_policy(stage.name,**({'target':target} if target is not None else {}))['remote_prefix']")
  text=text.replace("        require(len(self.remote)+13<=127", "        if target is not None:self._poll_target_pre_cap()\n        require(len(self.remote)+13<=127")
  text=text.replace('    def _publish(self,name,value):', '''    def _poll_target_pre_cap(self):
        require(self._target is self._target_pin and self.context._cap is self.parent,
            'typed pre-cap target/capability replaced')
        from .archive_owner_policy import _poll_target
        _poll_target(self.owner,self._target)
        require(self._target is self._target_pin and self.context._cap is self.parent,
            'typed pre-cap target/capability changed after poll')
        self.held.check(self.owner)

    def _publish(self,name,value):''')
  text=text.replace("self.ledger.selection.writer_policy(self.stage.name)['remote_prefix']", "self.ledger.selection.writer_policy(self.stage.name,**({'target':self._target} if self._target is not None else {}))['remote_prefix']")
 (P/name).write_text(text)
