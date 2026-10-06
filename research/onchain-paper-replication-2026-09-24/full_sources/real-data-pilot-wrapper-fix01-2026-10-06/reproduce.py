"""Import-only reproduction: no Binding instances, leases, arrays or claims."""
import hashlib,json,sys
from pathlib import Path
from tradingagents.research.onchain_replication import typed_tail_binding, imported_authority_lease as lease
root=Path.cwd();p=Path(typed_tail_binding.__file__)
sources={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()}
fn=typed_tail_binding.Binding.__repr__
result={'offender':'typed_tail_binding.Binding.__repr__','wrapper_globals':fn.__globals__['__name__'],'wrapper_qualname':fn.__code__.co_qualname,'freevars':fn.__code__.co_freevars,'generated_methods':{k:v.__code__.co_filename for k,v in vars(typed_tail_binding.Binding).items() if hasattr(v,'__code__')}}
try:lease._loaded(root,sources)
except ValueError as error:result.update(status='RED',reason=str(error))
else:raise AssertionError('baseline unexpectedly accepted')
print(json.dumps(result,indent=2))
