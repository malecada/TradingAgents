import ast,difflib,json,sys
from pathlib import Path
import restore_sharded01 as M
R=M.R;H=Path(__file__).resolve().parent;old=R.read(H,'original-restore_union01.py');new=R.read(H,'restore_sharded01.py');ops=[]
for tag,a,b,c,d in difflib.SequenceMatcher(a=old.decode().splitlines(keepends=True),b=new.decode().splitlines(keepends=True),autojunk=False).get_opcodes():
 ops.append({'tag':tag,'old_start':a,'old_end':b,'new_start':c,'new_end':d,'old_text':''.join(old.decode().splitlines(keepends=True)[a:b]),'new_text':''.join(new.decode().splitlines(keepends=True)[c:d])})
assert ''.join(x['old_text'] for x in ops).encode()==old and ''.join(x['new_text'] for x in ops).encode()==new
inverse=''.join(x['old_text'] for x in ops);assert inverse.encode()==old and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(old))
R.put(H/'INVERSE01.json',{'original_sha256':R.digest(old),'candidate_sha256':R.digest(new),'kind':'complete ordered source chunk inverse; declared new sharded orchestration, not identical single archive algorithm','chunks':ops})
assert Path(M.PLAN.__file__).resolve()==H/'shards01.py';assert R.digest(R.read(H,'shards01.py'))=='9c38c0893790c22e3b0142a8ab175dceb9b14dd0aeeb80edc206e5329ffcbbba'
assert not any(n in sys.modules for n in ('numpy','torch','scipy','pandas'))
R.put(H/'CHECKS02.json',{'checks':5,'full_byte_AST_inverse':True,'exact_pinned_planner_origin':True,'planner_sha256':'9c38c0893790c22e3b0142a8ab175dceb9b14dd0aeeb80edc206e5329ffcbbba','no_numerical_imports':True,'source_sha256':R.digest(new),'no_actual_remote_capture_or_recovery':True});print('PASS',5,R.digest(new))
