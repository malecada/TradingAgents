import ast, hashlib, json
from pathlib import Path
p=Path(__file__).resolve().parent
old=ast.parse((p/'baseline.py').read_text());new=ast.parse((p/'candidate01.py').read_text())
names={'_original_batch_rows','_original_git_batch','original_source_blobs'}
old_helper=next(x for x in old.body if isinstance(x,ast.FunctionDef) and x.name=='original_source_blobs')
new.body=[old_helper if isinstance(x,ast.FunctionDef) and x.name=='original_source_blobs' else x for x in new.body if not (isinstance(x,ast.FunctionDef) and x.name in names-{'original_source_blobs'})]
assert ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False)
print('PASS: complete module AST identical after reverting only original_source_blobs and removing its two new helpers')
