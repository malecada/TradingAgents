from pathlib import Path
import hashlib,json,difflib
D=Path(__file__).resolve().parent;ROOT=D.parents[3];P=Path('tradingagents/research/onchain_replication');T=D/'candidate'/P
bases={n:ROOT/P/n for n in ('imported_mcm_identity.py','mcm_score_stream.py','compact_mcm.py')}
bases['real_pilot_import_caller.py']=D.parent/'real-data-pilot-writable-storage-scope02-2026-10-05/candidate'/P/'real_pilot_import_caller.py'
records={}
def build(name,edits):
 old=bases[name].read_text();s=old
 for a,b in edits:assert s.count(a)==1,(name,a);s=s.replace(a,b)
 inverse=s
 for a,b in reversed(edits):assert inverse.count(b)==1;inverse=inverse.replace(b,a)
 assert inverse==old
 (T/name).write_text(s);(D/(name+'.patch')).write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='baseline/'+name,tofile='candidate/'+name)))
 records[name]={'baseline':str(bases[name]),'baseline_sha256':hashlib.sha256(old.encode()).hexdigest(),'candidate_sha256':hashlib.sha256(s.encode()).hexdigest(),'edits':[{'old':a,'new':b} for a,b in edits]}
build('imported_mcm_identity.py',[
 ('    def final(self,*,full_graph=True):\n        self._pins();', "    def final(self,*,full_graph=True):\n        if full_graph and getattr(self.execution,'_sampled_authority_lease',None) is not None:\n            from .imported_authority_lease import target_lease\n            target_lease(self,boundary=True)\n        self._pins();"),
 ('        self.execution.check();self.final(full_graph=False)', "        if getattr(self.execution,'_sampled_authority_lease',None) is not None:\n            from .imported_authority_lease import target_lease\n            target_lease(self)\n        else:self.execution.check();self.final(full_graph=False)"),
 ('    def check(self):\n        self.lease();run=', "    def check(self):\n        if getattr(self.execution,'_sampled_authority_lease',None) is not None:\n            from .imported_authority_lease import target_lease\n            target_lease(self,boundary=True)\n        self.lease();run=")])
build('mcm_score_stream.py',[
 ("            self._imported.final(full_graph=False)\n            require(self.scope==self._imported.derive_scope() and self.workload==self.scope['workflow'],'imported stream workload changed')", "            if getattr(self._imported.execution,'_sampled_authority_lease',None) is not None:\n                from .imported_authority_lease import target_lease\n                target_lease(self._imported)\n                require(self.scope==self._imported.scope and self.workload==self.scope['workflow'],'sampled stream scope changed')\n            else:\n                self._imported.final(full_graph=False)\n                require(self.scope==self._imported.derive_scope() and self.workload==self.scope['workflow'],'imported stream workload changed')"),
 ("                index = self.batches.chunks; start_cell = self.active.start['start_cell']", "                if self._imported is not None and getattr(self._imported.execution,'_sampled_authority_lease',None) is not None:\n                    from .imported_authority_lease import target_lease\n                    target_lease(self._imported,boundary=True)\n                index = self.batches.chunks; start_cell = self.active.start['start_cell']"),
 ("    def finish(self):\n        self._check()", "    def finish(self):\n        if self._imported is not None and getattr(self._imported.execution,'_sampled_authority_lease',None) is not None:\n            from .imported_authority_lease import target_lease\n            target_lease(self._imported,boundary=True)\n        self._check()")])
build('compact_mcm.py',[
 ("            stage.lease(); dictionary.lease(); io._root(root,fd)", "            if _imported(dictionary) and getattr(dictionary.execution,'_sampled_authority_lease',None) is not None:\n                from .imported_authority_lease import target_lease\n                require(owner.active is stage,'actual active producer stage differs');target_lease(dictionary)\n            else:stage.lease(); dictionary.lease()\n            io._root(root,fd)"),
 ("        if ledger is None:\n            log_terminal = log.finish()", "        if _imported(dictionary) and getattr(dictionary.execution,'_sampled_authority_lease',None) is not None:\n            from .imported_authority_lease import target_lease\n            target_lease(dictionary,boundary=True)\n        if ledger is None:\n            log_terminal = log.finish()")])
build('real_pilot_import_caller.py',[
 ("    resource_subset = 'population_scope' in p", "    interval='imported_authority_lease_input' in p\n    require(not interval or (full and type(p['imported_authority_lease_input']) is str and bool(p['imported_authority_lease_input'])),'explicit schema2 interval input required')\n    resource_subset = 'population_scope' in p"),
 ("| ({'population_scope'} if resource_subset else set()), 'pilot plan fields differ')", "| ({'population_scope'} if resource_subset else set()) | ({'imported_authority_lease_input'} if interval else set()), 'pilot plan fields differ')"),
 ("    require(roles <= set(ad.inputs), 'real population/config/graph inputs not registered')", "    if p.get('imported_authority_lease_input') is not None:\n        from .imported_authority_interval import policy\n        policy(_read(ad,p['imported_authority_lease_input']));roles.add(p['imported_authority_lease_input'])\n    require(roles <= set(ad.inputs), 'real population/config/graph inputs not registered')"),
 ("        execution = original_import_stage.ImportedExecution(stage)", "        execution = original_import_stage.ImportedExecution(stage)\n        if p.get('imported_authority_lease_input') is not None:\n            from .imported_authority_lease import activate\n            activate(execution,p['imported_authority_lease_input'])")])
(D/'SOURCE_DELTA01.json').write_text(json.dumps(records,indent=2)+'\n')
