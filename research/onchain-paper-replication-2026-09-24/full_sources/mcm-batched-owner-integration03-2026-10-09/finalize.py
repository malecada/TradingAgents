from pathlib import Path
import ast,json,hashlib,difflib
H=Path(__file__).resolve().parent;F=H.parent;R=Path.cwd();old=F/'mcm-batched-owner-integration02-2026-10-09';review=F/'mcm-batched-owner-integration-review02-2026-10-09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
replacements={}
for name in ('compact_mcm_batched.py','batched_journal.py'):
 a=(old/name).read_text();b=(H/name).read_text();ast.parse(b)
 (H/(name+'.patch')).write_text(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=str((old/name).relative_to(R)),tofile=str((H/name).relative_to(R)))))
 replacements[name]={'old_sha256':sha(old/name),'source_sha256':sha(H/name)}
def functions(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.FunctionDef)}
a=functions(old/'compact_mcm_batched.py');b=functions(H/'compact_mcm_batched.py')
unchanged=['checkpoint','execute','sink','post_batch','consume','final_batches','produce','verify_content','_modules','validate','stage_content','output_chunks','output_source']
for name in unchanged:assert a[name]==b[name],name
aj=functions(old/'batched_journal.py');bj=functions(H/'batched_journal.py')
for name in aj:
 if name!='__init__':assert aj[name]==bj[name],name
manifest=json.loads((old/'MANIFEST.json').read_text());inherited={n:entry['source_sha256'] for n,entry in manifest['sources'].items() if n not in replacements}
for n,digest in inherited.items():assert sha(old/n)==digest
paths=[old/'MANIFEST.json',review/'WITHHELD02.json',review/'ACQUISITION02.json',review/'INVENTORY03.json']+list(H.glob('*RESULT01.json'))+[H/'ACQUISITION01.json',H/'INVENTORY01.json',H/'REPORT.md']+list(H.glob('*TEST01.log'))+list(H.glob('verify*.py'))
out={'source_only':True,'replacements':replacements,'inherited_from':str(old.relative_to(R)),'inherited_sources':inherited,'unchanged_adapter_functions':unchanged,'journal_non_constructor_AST_identical':True,'evidence':{str(p.relative_to(R)):sha(p) for p in paths},'genuine_authority_or_numerical_execution':False,'admission':False}
(H/'MANIFEST.json').write_text(json.dumps(out,indent=2)+'\n');print('MANIFEST',sha(H/'MANIFEST.json'));print(json.dumps(replacements,indent=2))
