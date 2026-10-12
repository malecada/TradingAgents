from pathlib import Path
import ast,difflib,json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
changes={
'imported_authority_lease.py':[("def target_lease(target,*,boundary=False):","def target_lease(target,*,boundary=False,_return_value=False):"),("    try:\n        if id(target) not in contract.targets:","    try:\n        require(type(_return_value) is bool and (not _return_value or boundary is True),\n                'checked value requires explicit full boundary')\n        if id(target) not in contract.targets:"),("        contract.target=target;contract.check(boundary=boundary)","        contract.target=target\n        if _return_value:return contract.check(boundary=boundary,_return_value=True)\n        contract.check(boundary=boundary)")],
'imported_mcm_identity.py':[("    def check(self):\n        if getattr(self.execution,'_sampled_authority_lease',None) is not None:\n            from .imported_authority_lease import target_lease\n            target_lease(self,boundary=True)","    def check(self):\n        leased=getattr(self.execution,'_sampled_authority_lease',None) is not None\n        if leased:\n            from .imported_authority_lease import target_lease\n            checked=target_lease(self,boundary=True,_return_value=True)"),("        require(canonical_bytes(self.execution.check())==self._execution_pin,'completed imported execution identity changed')","        require(canonical_bytes(checked if leased else self.execution.check())==self._execution_pin,'completed imported execution identity changed')")]}
manifest={}
for name,replacements in changes.items():
    src=ROOT/'tradingagents/research/onchain_replication'/name;old=src.read_text();new=old
    for before,after in replacements:
        assert new.count(before)==1,(name,before);new=new.replace(before,after)
    restored=new
    for before,after in reversed(replacements):
        assert restored.count(after)==1;restored=restored.replace(after,before)
    assert restored==old and ast.dump(ast.parse(restored))==ast.dump(ast.parse(old))
    (HERE/('baseline_'+name)).write_text(old);(HERE/name).write_text(new)
    for kind,a,b in [('patch',old,new),('inverse',new,old)]:
        (HERE/(name+'.'+kind)).write_text(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=name,tofile=name)))
    manifest[name]={'baseline_sha256':hashlib.sha256(old.encode()).hexdigest(),'candidate_sha256':hashlib.sha256(new.encode()).hexdigest(),'literal_and_ast_inverse':True}
(HERE/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
