"""Narrow source-phase refusals; no prospective receipt or archive is fabricated."""
import ast,json,os
from pathlib import Path
import outcome01 as O
import bind_capture01 as C
H=O.HERE;old=H.parent/'financial-wrapper-continuation-current-transport-preparation01-2026-10-05';rows=[]
def reject(name,f):
 try:f()
 except (ValueError,TypeError):rows.append(name)
 else:raise AssertionError(name)
for v in (None,'','x'*64,'0'*63,1):reject('invalid actualpin '+repr(v),lambda v=v:C.pin(v))
reject('null pin refuses before actual source IO',lambda:C.prepare(None,None,None))
reject('unbound capture refuses even prior genuine capture',lambda:O.context((old/'CAPTURE01.json').read_bytes()))
reject('foreign lane refuses',lambda:O.lane_root(1,'remote'))
assert O.CAPTURE is None and O.SOURCE=='d4c81c0961342bfe4c5771aabbef1d46a14cffb8';rows.append('source known capture genuinelynull')
assert all(not os.path.lexists(O.lane_root(0,p)) for p in ('remote','flat')) and not os.path.lexists(C.BOUND_ROOT);rows.append('fresh Root namespaces absent')
for n in ('recover.template01.py','caller_remote01.py','caller_flat01.py','cohort01.py','flat_primitives01.py','receipt01.py','restore_bundle01.py','watch01.py','utilities/recovery_pax01.py','utilities/owned_io.py','utilities/bounded_git01.py'):
 assert (H/n).read_bytes()==(old/n).read_bytes();rows.append('exact primitive/template '+n)
for n in ('outcome01.py','space01.py','bind_entry01.py','bind_capture01.py'):ast.parse((H/n).read_text());rows.append('AST '+n)
assert "'financial-wrapper-continuation-canonical-'+phase+'01-2026-10-05'" in (H/'outcome01.py').read_text();rows.append('exact canonical receiver and flat literals')
print(json.dumps({'passed':len(rows),'checks':rows,'actual_capture_available':False,'actualRootentry':False,'sourcephase_only':True},sort_keys=True))
