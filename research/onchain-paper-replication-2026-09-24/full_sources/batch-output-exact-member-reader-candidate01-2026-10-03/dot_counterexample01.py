"""Exact original scaffold counterexample; retained expected RED."""
import importlib.util,hashlib
from pathlib import Path
p=Path(__file__).parent.parent/'batch-output-offload-investigation-2026-10-03/member_ranges01.py'
s=importlib.util.spec_from_file_location('prior_member_scaffold',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
v={'schema_version':1,'kind':'non-tail-exact-member-plan-v1','role':'score-batch','owner':'ab'*32,'stage_sha256':'cd'*32,'container_sha256':'ef'*32,'scope':{k:'12'*32 for k in m.SCOPES},'path':'.','dtype':'<f8','order':'row-major','rows':1,'motifs':32,'start_cell':0,'cells':1,'header_bytes':0,'bytes':8,'sha256':hashlib.sha256(b'\0'*8).hexdigest(),'chunk_bytes':8}
try:m.validate(v)
except ValueError:print('PASS: directory-as-member refused')
else:raise AssertionError('original scaffold accepts path=. before file-facing integration')
