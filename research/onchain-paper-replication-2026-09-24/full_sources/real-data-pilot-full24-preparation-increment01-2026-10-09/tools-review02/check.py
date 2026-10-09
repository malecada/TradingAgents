import ast,hashlib,io,json,os,stat,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;D=HERE.parent
# Only extract the changed selection loop and archive member loops. Never execute helpers.
sel=ast.parse((D/'select02.py').read_text());loop=next(n for n in sel.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='relative')
code=compile(ast.Module(body=[loop],type_ignores=[]),'actual-select02-loop','exec')
root=HERE/'fixture';root.mkdir();(root/'plain').write_bytes(b'opaque fixture\x00');os.symlink('nonexistent-target',root/'link')
def run(names):
 g={'ROOT':root,'names':names,'rows':[],'directories':set(),'os':os,'stat':stat,'hashlib':hashlib};exec(code,g);return g['rows']
rows=run(['plain','link']);assert rows[1]['type']=='symlink' and rows[1]['linkname']=='nonexistent-target'
os.link(root/'plain',root/'hard')
try:run(['hard'])
except AssertionError:pass
else:raise AssertionError('hardlink admitted')
os.unlink(root/'hard')
os.mkfifo(root/'fifo')
try:run(['fifo'])
except AssertionError:pass
else:raise AssertionError('FIFO admitted')
# Sparse extent: no large body read, actual finite extent refusal.
with (root/'oversize').open('wb') as f:f.truncate(64*1024**2+1)
try:run(['oversize'])
except AssertionError:pass
else:raise AssertionError('oversize admitted')
cap=ast.parse((D/'capture02.py').read_text());withs=[n for n in cap.body if isinstance(n,ast.With)]
write_loop=withs[0].body[0];read_loop=withs[1].body[1]
b=io.BytesIO()
with tarfile.open(fileobj=b,mode='w',format=tarfile.PAX_FORMAT) as t:exec(compile(ast.Module(body=[write_loop],type_ignores=[]),'actual-capture02-members','exec'),{'R':root,'rows':rows,'t':t,'tarfile':tarfile,'stat':stat,'os':os,'hashlib':hashlib,'io':io})
b.seek(0)
with tarfile.open(fileobj=b,mode='r') as t:
 members=t.getmembers();exec(compile(ast.Module(body=[read_loop],type_ignores=[]),'actual-capture02-readback','exec'),{'members':members,'rows':rows,'t':t,'hashlib':hashlib})
os.unlink(root/'link');os.symlink('changed-target',root/'link')
try:
 with tarfile.open(fileobj=io.BytesIO(),mode='w') as t:exec(compile(ast.Module(body=[write_loop],type_ignores=[]),'actual-capture02-mutated-link','exec'),{'R':root,'rows':rows,'t':t,'tarfile':tarfile,'stat':stat,'os':os,'hashlib':hashlib,'io':io})
except AssertionError:pass
else:raise AssertionError('changed target admitted')
print(json.dumps({'actual_source_seams':True,'passes':['dangling_link_metadata_without_target_read','regular_and_symlink_tar_roundtrip','hardlink_refusal','FIFO_refusal','over64MiB_refusal_before_read','changed_symlink_target_refusal'],'no_helpers_executed':True}))
