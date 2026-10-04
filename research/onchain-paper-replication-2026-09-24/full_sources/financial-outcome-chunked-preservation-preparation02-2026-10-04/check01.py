import copy,hashlib,json,os,shutil,sys
from pathlib import Path
import chunk_archive01 as A
D=Path(__file__).resolve().parent;T=D/'tiny01';T.mkdir();checks=[]
def check(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def refusal(n,fn):
 try:fn()
 except (ValueError,OSError,KeyError,TypeError):checks.append(n);return
 raise AssertionError(n)
def rewrite(path,value):path.write_bytes(A.encode(value))
source=T/'source';source.mkdir();(source/'empty-dir').mkdir();(source/'empty').write_bytes(b'');(source/'opaque').write_bytes(b'opaque bytes\x00\xff\n');(source/'two-chunks').write_bytes(b'x'*(A.CHUNK+19));(source/'.git/objects').mkdir(parents=True);(source/'.git/refs').mkdir();(source/'.git/HEAD').write_bytes(b'ref: refs/heads/opaque\n');os.chmod(source/'empty-dir',0o750)
roots={'closed-opaque':str(source)};archive=T/'archive';result=A.capture(roots,archive);index_hash=result['index_sha256'];check('actual multi-chunk archive',result['chunks']>=3)
restored=T/'flat';receipt=A.restore(archive,index_hash,restored);check('standalone flat exact verification',A.verify_flat(restored,index_hash)==receipt)
check('all written artifacts under4MiB',all(p.stat().st_size<=A.FILE for root in (archive,restored) for p in root.iterdir()))
check('source bytes unchanged',(source/'two-chunks').read_bytes()==b'x'*(A.CHUNK+19))
refusal('archive identity cannot reopen',lambda:A.capture(roots,archive));refusal('restore identity cannot reopen',lambda:A.restore(archive,index_hash,restored));refusal('overlap refused',lambda:A.capture(roots,source/'nested'))
# Every corruption has a separate owned retained archive tree.
for label,mutate in [('missing',lambda r:(r/'chunk-00000000.bin').unlink()),('corrupt',lambda r:(r/'chunk-00000000.bin').write_bytes(b'wrong')),('extra',lambda r:(r/'extra').write_bytes(b'extra')),('missingindex',lambda r:(r/'index.json').unlink())]:
 bad=T/('bad-'+label);shutil.copytree(archive,bad);mutate(bad);refusal(label,lambda bad=bad:A.validate_archive(bad,index_hash,A.Bounds()))
bad=T/'bad-duplicate';shutil.copytree(archive,bad);index=json.loads((bad/'index.json').read_bytes());pagepath=bad/index['pages'][0]['name'];rows=json.loads(pagepath.read_bytes());rows.append(rows[-1]);rewrite(pagepath,rows);index['pages'][0].update(bytes=pagepath.stat().st_size,sha256=A.sha(pagepath.read_bytes()));rewrite(bad/'index.json',index);refusal('duplicate rehashed member',lambda:A.validate_archive(bad,A.sha((bad/'index.json').read_bytes()),A.Bounds()))
bad=T/'bad-path';shutil.copytree(archive,bad);index=json.loads((bad/'index.json').read_bytes());pagepath=bad/index['pages'][0]['name'];rows=json.loads(pagepath.read_bytes());rows[-1]['path']='../escape';rewrite(pagepath,rows);index['pages'][0].update(bytes=pagepath.stat().st_size,sha256=A.sha(pagepath.read_bytes()));rewrite(bad/'index.json',index);refusal('rehashed path traversal',lambda:A.validate_archive(bad,A.sha((bad/'index.json').read_bytes()),A.Bounds()))
bad=T/'bad-link';shutil.copytree(archive,bad);(bad/'chunk-00000000.bin').unlink();(bad/'chunk-00000000.bin').symlink_to(source/'opaque');refusal('chunk symlink',lambda:A.validate_archive(bad,index_hash,A.Bounds()))
linked=T/'source-link';linked.mkdir();(linked/'redirect').symlink_to(source/'opaque');refusal('source symlink',lambda:A.capture({'s':str(linked)},T/'link-capture'))
linked=T/'source-hardlink';linked.mkdir();os.link(source/'opaque',linked/'hard');refusal('source hardlink',lambda:A.capture({'s':str(linked)},T/'hard-capture'))
# Partial publication after a concrete injected write failure is retained.
real=A._write;calls=[]
def fault(directory,name,raw,bounds):
 calls.append(name)
 if name=='chunk-00000001.bin':raise OSError('opaque injected write failure')
 return real(directory,name,raw,bounds)
# Source original hardlink is intentionally not recaptured; separate tiny root.
partial_source=T/'partial-source';partial_source.mkdir();(partial_source/'payload').write_bytes(b'y'*(A.CHUNK+1));A._write=fault
try:
 refusal('partial capture fails',lambda:A.capture({'p':str(partial_source)},T/'partial'))
finally:A._write=real
check('partial chunk and failure preserved',(T/'partial/chunk-00000000.bin').is_file() and (T/'partial/capture-failure.json').is_file() and not (T/'partial/index.json').exists())
# Owned output anchor prevents redirected namespace creation before writing.
write_parent=T/'write-parent';write_parent.mkdir();owned=write_parent/'owned';owned.mkdir();b=A.Bounds();b.anchors[owned]=A.anchor(owned);moved=write_parent/'original-owned';owned.rename(moved);owned.symlink_to(moved,target_is_directory=True);refusal('redirected owned output',lambda:A._write(owned,'should-not-exist',b'opaque',b));check('redirect wrote no body',not (moved/'should-not-exist').exists())
# Preserve successful flat tree; mutate distinct copy.
flatbad=T/'flat-bad';shutil.copytree(restored,flatbad);(flatbad/'body-00000000.bin').write_bytes(b'wrong');refusal('flat body corruption',lambda:A.verify_flat(flatbad,index_hash))
check('no numerical imports',not any(k in sys.modules for k in ('numpy','torch','scipy')))
(D/'CHECKS01.json').write_text(json.dumps({'count':len(checks),'checks':checks,'scope':'owned opaque bytes only; no real outcome, authority or measured100epoch capacity'},indent=2)+'\n');print(len(checks),'passed')
