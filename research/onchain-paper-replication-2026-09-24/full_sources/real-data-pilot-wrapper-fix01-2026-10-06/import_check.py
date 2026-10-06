"""Source/import authentication only; no source/input consumers executed."""
import importlib,importlib.util,hashlib,json,sys
from pathlib import Path
root=Path.cwd();r=Path(__file__).resolve().parent
for name in ('real_pilot_import_caller','original_import_preparation','original_import_stage','compact_mcm','compact_owner','real_pilot_training','archive_dispatch','typed_payload_operations','typed_tail_binding','mcm_raw_parts','imported_authority_lease'):
 importlib.import_module('tradingagents.research.onchain_replication.'+name)
spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication.wrapper_candidate',r/'candidate/imported_authority_lease.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
sources={}
for name,module in tuple(sys.modules.items()):
 p=Path(getattr(module,'__file__','') or '.')
 if p.is_absolute() and p.is_relative_to(root/'tradingagents') and p.suffix=='.py':sources[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
loaded=m._loaded(root,sources);m._authenticate_loaded(loaded,sources,root)
print(json.dumps({'status':'passed','candidate_sha256':hashlib.sha256((r/'candidate/imported_authority_lease.py').read_bytes()).hexdigest(),'source_modules':len(loaded),'captured_functions':sum(len(row[2]) for row in loaded.values()),'scope':'imports only; no model construction/arrays/claims or real inputs'},indent=2))
