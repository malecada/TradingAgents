from pathlib import Path
import ast,hashlib,json,difflib
H=Path(__file__).resolve().parent;before=(H/'storage_lease01.precomment.py').read_text();after=(H/'storage_lease01.py').read_text();a='# Once a file reaches its declared final extent it cannot change.';b='# Final extent seals only the sampled stat fingerprint, never bytes.'
assert before.replace(a,b)==after and before.count(a)==1
assert ast.dump(ast.parse(before),include_attributes=False)==ast.dump(ast.parse(after),include_attributes=False)
i=json.loads((H/'INVERSE01.json').read_text());i['edits'].append({'before':a,'after':b});reverse=after
for e in i['edits']:
 assert reverse.count(e['after'])==1
 reverse=reverse.replace(e['after'],e['before'])
assert i['added_function'] in reverse;reverse=reverse.replace(i['added_function'],'');original=(H/'storage_lease01.original.py').read_text();assert reverse==original
assert ast.dump(ast.parse(reverse),include_attributes=False)==ast.dump(ast.parse(original),include_attributes=False)
(H/'INVERSE_FINAL02.json').write_text(json.dumps(i,indent=2,sort_keys=True)+'\n');(H/'SOURCE_FINAL02.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),after.splitlines(True),fromfile='original92e5',tofile='successor02')))
r={'checks':5,'full_byte_inverse':True,'full_AST_inverse':True,'precomment_AST_identical':True,'scope':'comment makes stat-only limitation explicit; tested executable AST unchanged','source_sha256':hashlib.sha256(after.encode()).hexdigest(),'executed_source_sha256':hashlib.sha256(before.encode()).hexdigest()}
(H/'FINAL_SOURCE_CHECK02.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r))
