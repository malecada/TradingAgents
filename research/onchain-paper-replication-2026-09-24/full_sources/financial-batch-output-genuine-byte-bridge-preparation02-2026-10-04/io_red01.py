import sys,json
from pathlib import Path
p=Path(__file__).resolve().parent
sys.path.insert(0,str(p))
import byte_bridge01 as B,recovery04 as R,owned_io as IO
try:B._write(R,IO,p/'draft-write-red.json',b'opaque')
except BaseException as e:
 print(json.dumps({'status':'RED_DRAFT_CONTEXTMANAGER_MISUSED_AS_FD','error_type':type(e).__name__,'body_created':(p/'draft-write-red.json').exists()}))
 raise
