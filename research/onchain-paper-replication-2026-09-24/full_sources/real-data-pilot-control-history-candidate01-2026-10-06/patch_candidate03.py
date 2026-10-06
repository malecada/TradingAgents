from pathlib import Path
P=Path(__file__).resolve().parent/'candidate'
p=P/'archive_control_history.py';s=p.read_text().replace('self.calls=0;self.failed=False','self.calls=0;self.failed=False;self._policy_pin=tuple(sorted(self.p.items()));self._clock_pin=clock')
s=s.replace("            now=self.clock();need", "            need(tuple(sorted(self.p.items()))==self._policy_pin and self.clock is self._clock_pin,'history policy/clock replaced')\n            now=self.clock();need")
p.write_text(s)
p=P/'archive_dispatch.py';s=p.read_text()
s=s.replace("            self._diagnostic_pins={}\n", "            self._history_bundle=(self._history,self._control_journal,self._diagnostic_journal)\n            self._diagnostic_pins={}\n")
s=s.replace("            self._control_journal.append(name,raw);self._bytes+=len(raw);self._publication_count+=1;return", "            if len(raw)>self._history_policy['success_control_bytes']:\n                # Preserve the exact refused original record in finite failure\n                # headroom; no command success or retry is inferred.\n                self._publish('oversize-'+name,value)\n                raise ValueError('original success control exceeds selected record cap; retained, stop')\n            self._control_journal.append(name,raw);self._bytes+=len(raw);self._publication_count+=1;return")
s=s.replace("            require(self._transport._receipt_sink==self._receive_control,'selected receipt sink replaced')", "            require(all(a is b for a,b in zip((self._history,self._control_journal,self._diagnostic_journal),self._history_bundle)) and self._history.p==self._limits['control_history'] and self._history_policy==self._limits['control_history'],'selected history objects/policy replaced')\n            require(self._transport._receipt_sink==self._receive_control,'selected receipt sink replaced')")
# Import only actual selected helper: durability selection is owned by other worker.
s=s.replace("            from . import chunk_durability", "            from . import chunk_durability")
p.write_text(s)
p=P/'archive_owner_operations.py';s=p.read_text().replace("            self._history_context=transport._context", "            self._history_context=transport._context;self._history_pin=self._history")
s=s.replace("            require(self.selection._transport._context is self._history_context,'selected history context changed')", "            require(self.selection._transport._context is self._history_context and self._history is self._history_pin and self._history.p==self._history_context._history_policy,'selected history context changed')")
# Spent counters/config retain immediate checks; growing evidence alone sampled.
s=s.replace("        owners.verify_current(self.owner)\n        self._evidence(sampled=not full)", "        owners.verify_current(self.owner)\n        if self._history is not None:\n            require(owners.cache_key(self._configuration())==self._identity and owners.cache_key(self._spent)==self._spent_sha,'live archive identity/accounting changed')\n        self._evidence(sampled=not full)")
p.write_text(s)
for p in P.glob('*.py'):compile(p.read_bytes(),str(p),'exec')
print('candidate syntax pass')
