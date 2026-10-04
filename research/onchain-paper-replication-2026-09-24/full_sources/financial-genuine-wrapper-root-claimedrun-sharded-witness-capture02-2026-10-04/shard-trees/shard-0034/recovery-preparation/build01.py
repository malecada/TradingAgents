import ast
from pathlib import Path
H=Path(__file__).resolve().parent
old=(H/'original-restore_union01.py').read_text();tree=ast.parse(old);defs={n.name:ast.get_source_segment(old,n) for n in tree.body if isinstance(n,ast.FunctionDef)}
head=old[:old.index('def hashed')]
text=head+"import time\nfrom pathlib import PurePosixPath\nimport shard_plan01 as PLAN\n\n"
for n in ('hashed','reference','contract','reserve','restore_ordinary'):text+=defs[n]+'\n\n'
text+=old[old.index('EXPECTED_ORIGINALS_SHA256='):old.index('def authenticate_union')]
(H/'restore_sharded01.py').write_text(text)
