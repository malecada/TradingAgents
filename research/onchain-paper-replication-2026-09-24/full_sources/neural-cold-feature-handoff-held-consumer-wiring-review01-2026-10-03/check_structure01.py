import pathlib,json,hashlib,ast,importlib.util
D=pathlib.Path(__file__).parent;F=D.parent;R=F.parents[2];P=F/'neural-cold-feature-handoff-held-consumer-wiring-preparation01-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest()
assert H((P/'MANIFEST01.json').read_bytes())=='fa1f1ea1d71ebba0859f993048c81b293ca6342250d2c8320258e0fd6bc6b650';m=json.loads((P/'MANIFEST01.json').read_bytes())
for row in m['files']:b=(P/row['path']).read_bytes();assert H(b)==row['sha256'] and len(b)==row['bytes']
source=json.loads((P/'SOURCE_MAP01.json').read_bytes())
for row in source['install_map']:
 ref=row.get('candidate',row.get('accepted_unchanged_dependency'));b=(R/ref['path']).read_bytes();assert H(b)==ref['sha256'] and len(b)==ref['bytes']
a=(P/'compact_mcm.py').read_text();b=(P/'compact_mcm.baseline01.py').read_text();a=a.replace("        held_consumer = None\n        if _imported(dictionary):\n            from . import held_score_consumer\n            held_consumer = held_score_consumer.preflight(dictionary)\n",'').replace("            stream_terminal = stream.finish()['terminal_sha256']\n            if held_consumer is not None:\n                held_score_consumer.consume(dictionary,stage,held,stream)\n            return actual,stream_terminal,numeric_pin","            return actual,stream.finish()['terminal_sha256'],numeric_pin");assert a==b and ast.dump(ast.parse(a))==ast.dump(ast.parse(b))
s=importlib.util.spec_from_file_location('review_consumer',P/'held_score_consumer.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
h='a'*64;p={'schema_version':1,'kind':v.KIND,'targets':{h:{'output':'read.json'}},'part_bytes':8,'max_read_bytes':40,'max_members':2};assert v._policy(p,[h],['read.json']) is p
refusals=0
for q in [p|{'part_bytes':True},p|{'part_bytes':9},p|{'max_members':0},p|{'targets':{h:{'output':'../read.json'}}},p|{'extra':True}]:
 try:v._policy(q,[h],['read.json'])
 except ValueError:refusals+=1
 else:raise AssertionError('policy accepted')
class Reader:
 members=('chunk-000000000000.bin','chunk-000000000001.bin')
 def __init__(self):self.calls=[];self.parts={self.members[0]:bytes(range(24)),self.members[1]:bytes(range(24,40))}
 def read_part(self,n,o,w):self.calls.append((n,o,w));return self.parts[n][o:o+w]
r=Reader();result=v._read_all(r,5,3,16,40,2);assert result=={'members':2,'parts':3,'bytes':40,'sha256':H(bytes(range(40)))} and r.calls==[(r.members[0],0,16),(r.members[0],16,8),(r.members[1],0,16)]
r.members=tuple(reversed(r.members))
try:v._read_all(r,5,3,16,40,2)
except ValueError:refusals+=1
else:raise AssertionError('wrong members accepted')
r=Reader();r.parts[r.members[1]]=b''
try:v._read_all(r,5,3,16,40,2)
except ValueError:refusals+=1
else:raise AssertionError('short read accepted')
fatal=SystemExit('read fatal')
class Fatal(Reader):
 def read_part(self,*a):raise fatal
try:v._read_all(Fatal(),5,3,16,40,2)
except BaseException as e:assert e is fatal
else:raise AssertionError('fatal lost')
out={'manifest_bodies':len(m['files']),'install_targets':len(source['install_map']),'all_dependency_bodies_hash_equal':True,'whole_inverse_caller_bytes_AST_equal':True,'independent_policy_member_shortread_refusals':refusals,'aligned_complete_bytes_digest':True,'readloop_fatal_identity':True,'authority_scope':'Stand-ins/tiny bytes only; no genuine Target/Owner/Stage/admission/native execution','disposition':'WITHHELD_HCW1_source_read_fatal_and_bound'};(D/'READBACK01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
