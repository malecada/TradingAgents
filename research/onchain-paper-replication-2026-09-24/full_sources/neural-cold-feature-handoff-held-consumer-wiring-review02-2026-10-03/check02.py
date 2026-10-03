import ast,pathlib,json,hashlib,os,stat,importlib.util,tempfile
from unittest.mock import patch
D=pathlib.Path(__file__).parent;F=D.parent;P=F/'neural-cold-feature-handoff-held-consumer-wiring-preparation02-2026-10-03';Q=F/'neural-cold-feature-handoff-held-consumer-wiring-preparation01-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest()
assert H((P/'MANIFEST02.json').read_bytes())=='4328511bda56e088f09951364f034a7acd07317bfd32af47c034783a2a17b67c'
m=json.loads((P/'MANIFEST02.json').read_bytes())
for r in m['files']:b=(P/r['path']).read_bytes();assert H(b)==r['sha256'] and len(b)==r['bytes']
old=(Q/'held_score_consumer.py').read_text();new=(P/'held_score_consumer.py').read_text();ot=ast.parse(old);nt=ast.parse(new);of=next(n for n in ot.body if isinstance(n,ast.FunctionDef) and n.name=='_body');nf=next(n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name=='_body');lines=new.splitlines(keepends=True);lines[nf.lineno-1:nf.end_lineno]=old.splitlines(keepends=True)[of.lineno-1:of.end_lineno];assert ''.join(lines)==old
assert (Q/'compact_mcm.py').read_bytes()==(P/'compact_mcm.py').read_bytes()
for name in ['test_caller01.py','test_policy01.py','test_selection01.py']:assert (P/name).read_bytes()==(Q/name).read_bytes()
owned=F/'neural-cold-feature-handoff-held-score-reader-preparation01-2026-10-03/owned_io.py';assert H(owned.read_bytes())=='09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb';s=importlib.util.spec_from_file_location('review_owned_io',owned);io=importlib.util.module_from_spec(s);s.loader.exec_module(io)
nf.body=[n for n in nf.body if not isinstance(n,ast.ImportFrom)];require=next(n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name=='require');ns={'source_io':io,'os':os,'stat':stat};exec(compile(ast.Module(body=[require,nf],type_ignores=[]),'actual-owned-body','exec'),ns);body=ns['_body'];checks=[]
with tempfile.TemporaryDirectory(dir=D) as tmp:
 root=pathlib.Path(tmp).resolve();p=root/'source.py';p.write_bytes(b'abc');assert body(p)==b'abc';checks.append('ordinary_real_descriptor_read')
 for first,second in [(MemoryError('first'),OSError('second')),(ValueError('first'),SystemExit('second')),(KeyboardInterrupt('first'),MemoryError('second'))]:
  close=os.close;seen=[]
  def closing(fd):seen.append(fd);close(fd);raise second
  with patch.object(os,'read',side_effect=first),patch.object(os,'close',side_effect=closing):
   try:body(p)
   except BaseException as e:assert e is (second if isinstance(first,ValueError) else first)
   else:raise AssertionError('fatal lost')
  assert len(seen)==len(set(seen))==2;checks.append('first_actual_fatal_and_two_close_once')
 realread=os.read;calls=[]
 def grow(fd,n):
  calls.append(n)
  if len(calls)==1:
   with p.open('ab') as f:f.write(b'x'*100)
  return realread(fd,n)
 with patch.object(os,'read',side_effect=grow):
  try:body(p)
  except ValueError as e:assert 'grew' in str(e)
  else:raise AssertionError('growth accepted')
 assert calls==[4];checks.append('growth_bounded_to_original_plus_one')
 p.write_bytes(b'abc');calls=[]
 def replace(fd,n):
  calls.append(n)
  if len(calls)==1:p.rename(root/'old.py');p.write_bytes(b'abc')
  return realread(fd,n)
 with patch.object(os,'read',side_effect=replace):
  try:body(p)
  except ValueError:pass
  else:raise AssertionError('samebody_inode_replacement_accepted')
 checks.append('same_body_original_inode_replacement_refused')
 os.link(p,root/'hard.py')
 try:body(p)
 except ValueError:pass
 else:raise AssertionError('hardlink accepted')
 (root/'hard.py').unlink();(root/'symlink.py').symlink_to(p)
 try:body(root/'symlink.py')
 except ValueError:pass
 else:raise AssertionError('symlink accepted')
 checks.append('symlink_hardlink_refused')
 p.write_bytes(b'x'*1048577)
 with patch.object(os,'read') as never:
  try:body(p)
  except ValueError:pass
  else:raise AssertionError('oversize accepted')
  never.assert_not_called()
 checks.append('oversize_refused_before_read')
out={'schema_version':1,'decision':'accepted_HCW1_source_correction_only','manifest_members':len(m['files']),'helper_sha256':H(new.encode()),'complete_inverse_bytes_unchanged_outside_body':True,'caller_and_prior_tests_byte_identical':True,'checks':checks,'qualification':'Exact extracted new body with only package import substituted by actual accepted stdlib IO reducer; real disposable descriptors and injected errors, no genuine Owner/native/numerical authority.'};(D/'READBACK02.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
