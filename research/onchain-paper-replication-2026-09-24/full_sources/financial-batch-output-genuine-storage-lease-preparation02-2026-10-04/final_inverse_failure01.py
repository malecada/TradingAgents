# Exact failed stdin body retained after its original execution (do not rerun).
from pathlib import Path
import ast,hashlib,json,difflib
H=Path('research/onchain-paper-replication-2026-09-24/full_sources/financial-batch-output-genuine-storage-lease-preparation02-2026-10-04');p=H/'storage_lease01.py';before=p.read_text();a='# Once a file reaches its declared final extent it cannot change.';b='# Final extent seals only the sampled stat fingerprint, never bytes.';assert before.count(a)==1;after=before.replace(a,b);(H/'storage_lease01.precomment.py').write_text(before);p.write_text(after)
assert ast.dump(ast.parse(before),include_attributes=False)==ast.dump(ast.parse(after),include_attributes=False)
i=json.loads((H/'INVERSE01.json').read_text());i['edits'].append({'before':a,'after':b});reverse=after
for e in reversed(i['edits']):assert reverse.count(e['after'])==1;reverse=reverse.replace(e['after'],e['before'])
assert i['added_function'] in reverse;reverse=reverse.replace(i['added_function'],'');original=(H/'storage_lease01.original.py').read_text();assert reverse==original
(H/'INVERSE_FINAL02.json').write_text(json.dumps(i,indent=2,sort_keys=True)+'\n');(H/'SOURCE_FINAL02.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),after.splitlines(True),fromfile='original92e5',tofile='successor02')))
(H/'FINAL_SOURCE_CHECK02.json').write_text(json.dumps({'checks':4,'full_byte_inverse':True,'full_AST_inverse':True,'precomment_AST_identical':True,'scope':'comment makes stat-only limitation explicit; tested executable AST unchanged','source_sha256':hashlib.sha256(after.encode()).hexdigest(),'executed_source_sha256':hashlib.sha256(before.encode()).hexdigest()},indent=2,sort_keys=True)+'\n')
