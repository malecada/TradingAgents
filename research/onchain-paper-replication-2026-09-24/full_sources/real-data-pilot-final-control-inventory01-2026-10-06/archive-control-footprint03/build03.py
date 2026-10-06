"""Only two source-seam corrections; predecessor remains byte-preserved."""
import ast,difflib,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;PREV=HERE.parent/'archive-control-footprint02';OUT=HERE/'candidate';OUT.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
def raw(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
need=lambda ok,msg: None if ok else (_ for _ in ()).throw(ValueError(msg))
need(sha((PREV/'MANIFEST02.json').read_bytes())=='027d9812462e59977dcb64270018d40f938ce6b8fe471b2ef89f2acb9ce34bf8','withheld predecessor manifest changed')
manifest=json.loads((PREV/'MANIFEST02.json').read_text())
for rel,ref in manifest['files'].items():need(sha((PREV/rel).read_bytes())==ref['sha256'],'withheld predecessor bytes changed: '+rel)
corrections={
 'archive_read_controls.py':[("            finally:os.close(fd)","            finally:io._cleanup((lambda:os.close(fd),),primary=sys.exc_info()[1])"),("    finally:os.close(dfd)","    finally:io._cleanup((lambda:os.close(dfd),),primary=sys.exc_info()[1])")],
 'archive_read_control_capacity.py':[("and type(value['schema_version']) is int,","and type(value['schema_version']) is int and type(value['shard_bytes']) is int,")],
}
proof={};delta=[]
for p in sorted((PREV/'candidate').glob('*.py')):
    old=p.read_text();new=old
    for before,after in corrections.get(p.name,[]):
        need(new.count(before)==1,'source seam differs: '+p.name);new=new.replace(before,after)
    (OUT/p.name).write_text(new);compile(new,str(OUT/p.name),'exec')
    inverse=new
    for before,after in reversed(corrections.get(p.name,[])):
        need(inverse.count(after)==1,'inverse seam differs');inverse=inverse.replace(after,before)
    need(inverse==old,'literal inverse differs')
    need(ast.dump(ast.parse(inverse))==ast.dump(ast.parse(old)),'AST inverse differs')
    proof[p.name]={'before_sha256':sha(old.encode()),'after_sha256':sha(new.encode()),'unchanged':new==old,'literal_inverse_equal':True,'ast_inverse_equal':True}
    delta.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+p.name,tofile='b/'+p.name))
(HERE/'DELTA03.patch').write_text(''.join(delta))
(HERE/'INVERSE03.json').write_bytes(raw({'status':'CANDIDATE_NOT_INSTALLED','files':proof,'changed_files':sorted(corrections),'unchanged_file_count':sum(v['unchanged'] for v in proof.values())}))
for name in ('SOURCE_PINS01.json','ARITHMETIC02.json'):(HERE/name).write_bytes((PREV/name).read_bytes())
(HERE/'WITHHELD_PREDECESSOR03.json').write_bytes(raw({'status':'WITHHELD_PREDECESSOR_NOT_MODIFIED','path':str(PREV),'manifest_sha256':sha((PREV/'MANIFEST02.json').read_bytes()),'reasons':['bare shard/directory close could replace primary or earlier cleanup failure','float shard_bytes accepted by dict equality'],'previous_13_checks':'reused for unchanged seams only; do not cover these defects','arithmetic_bytes_unchanged':True}))
