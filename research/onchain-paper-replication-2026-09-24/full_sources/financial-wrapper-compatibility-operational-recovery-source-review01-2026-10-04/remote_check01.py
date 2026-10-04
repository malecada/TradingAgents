from pathlib import Path
import ast,json,hashlib,importlib.util,sys,os,types
O=Path(__file__).resolve().parent;F=O.parent;R=F.parents[2];T=F/'financial-wrapper-compatibility-operational-delta-tooling01-2026-10-04';P=F/'financial-wrapper-complete100-failed-root-remote03-2026-10-04';h=lambda b:hashlib.sha256(b).hexdigest()
old=(P/'recover01.py').read_text();new=(T/'recover01.py').read_text();required=json.loads((T/'REQUIRED_BODIES01.json').read_bytes());tree=ast.parse(old);n=next(x for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REQUIRED' for t in x.targets));lines=old.splitlines(True);lines[n.lineno-1:n.end_lineno]=['REQUIRED = '+repr(required)+'\n'];rebuilt=''.join(lines).replace('fresh-complete100-failed-outcome02-02.git','fresh-operational-source-policy01.git').replace('fresh-actual-remote-complete100-failed-outcome02-supervised-recovered','fresh-actual-remote-operational-source-policy01-supervised-recovered').replace('Exact corrected failed-outcome02 and retained withheld-capture01 bytes recovered. Historical native attempt remains FAILED/spent; remote retrieval starts no claim. Baseline385 Git remains separate.','Exact frozen operational source/policy delta and genuine independent policy review bytes recovered. Original failed histories remain spent; no claim is started. Old385 actual recovered Git plus nine new bodies form an explicitly checked394-object source basis; final registration/caller/runtime-body recovery remain separate.')
assert rebuilt==new;assert h(old.encode())=='9ddc59dd7862d4b0d11c4057e3afc14fec61e260bb375a54d3286a44c1036b46';assert h(new.encode())=='b08f6c2667d28d5415449807fd91dcb8bd898b784f981e209cfc042cca6ed290'
for p in ['watch01.py','utilities/recovery_pax01.py','utilities/owned_io.py','utilities/bounded_git01.py']:assert (T/p).read_bytes()==(P/p).read_bytes()
assert len(required)==10 and sum(x['bytes'] for x in required.values())==451691
for n,x in required.items():b=(R/n).read_bytes();assert len(b)==x['bytes'] and h(b)==x['sha256']
sys.path.insert(0,str(T));spec=importlib.util.spec_from_file_location('opaque_remote_review',T/'recover01.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
q={'remote_commit':'0'*40,'rows':[dict(path=n,**x) for n,x in required.items()]};M.validate_fixed_selection(q);checks=['exact_inverse','ten_current_body_pins','unchanged_primitives']
for label,mut in [('missing',lambda q:q['rows'].pop()),('duplicate',lambda q:q['rows'].append(dict(q['rows'][0]))),('boolsize',lambda q:q['rows'][0].update(bytes=True)),('changedhash',lambda q:q['rows'][0].update(sha256='0'*64)),('path',lambda q:q['rows'][0].update(path='research/../escape'))]:
 z=json.loads(json.dumps(q));mut(z)
 try:M.validate_fixed_selection(z)
 except ValueError:checks.append(label)
 else:raise AssertionError(label)
tiny=O/'tiny';tiny.mkdir(mode=0o700);M.HERE=tiny;M.write(tiny/'intact',b'opaque');assert (tiny/'intact').read_bytes()==b'opaque'
try:M.write(tiny/'intact',b'overwrite')
except FileExistsError:checks.append('exclusive_collision')
else:raise AssertionError('collision')
real=os;proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});M.os=proxy
for i,(a,b) in enumerate([(ValueError('body'),MemoryError('cleanup')),(MemoryError('body'),SystemExit('cleanup')),(SystemExit('body'),MemoryError('cleanup')),(ValueError('body'),ValueError('cleanup'))]):
 def write(fd,data,e=a):raise e
 def close(fd,e=b):real.close(fd);raise e
 proxy.write=write;proxy.close=close
 try:M.write(tiny/f'fatal-{i}',b'x')
 except BaseException as e:
  expected=next((v for v in [a,b] if isinstance(v,MemoryError) or not isinstance(v,Exception)),a);assert e is expected;checks.append('actual_fd_firstfatal_'+str(i))
 else:raise AssertionError('fatal')
M.os=real
r={'schema_version':1,'checks':checks,'source_sha256':h(new.encode()),'required':required,'logical':451691,'source_inverse_exact':True,'unchanged_whole_tree_policy':M.W.POLICY,'actual_external_receipt':None,'qualification':'Validator and real owned FD write/cleanup only; no Git operation/main/entry or fabricated receipt. Fixed selection release remains separate.'};(O/'REMOTE_READBACK01.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS',len(checks),'source and independent real FD/refusal checks')
