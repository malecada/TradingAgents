import pathlib,hashlib,json,ast,sys,importlib.util,subprocess,os
from unittest.mock import patch
D=pathlib.Path(__file__).parent;F=D.parent;P=F/'claim-registration-git-batch-preparation01-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest()
manifest=json.loads((P/'MANIFEST.json').read_bytes());assert H((P/'MANIFEST.json').read_bytes())=='a73a1f33429fb8e3201eefdfb6b1cbba5869576d65e26a6953cea87925d608ad'
for r in manifest['files']:b=(P/r['path']).read_bytes();assert len(b)==r['bytes'] and H(b)==r['sha256']
a=(P/'verify.candidate01.py').read_text();b=(P/'verify.baseline01.py').read_text();t=ast.parse(a);helper=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_registration_pair')
lines=a.splitlines(keepends=True);del lines[helper.lineno-1:helper.end_lineno+2];inverse=''.join(lines).replace('    registration_pair = _registration_pair(root, claim)\n    registration = next(registration_pair)','    registration = _blob(root, claim["source"], claim["registration"])').replace('    if next(registration_pair) != registration:','    if _blob(root, claim["design_source"], claim["registration"]) != registration:')
assert inverse==b
spec=importlib.util.spec_from_file_location('review_candidate',P/'verify.candidate01.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0','GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'protocol.allow','GIT_CONFIG_VALUE_0':'never'}
os.environ.update(env);G=D/'tiny-git01';G.mkdir();
def git(*args):return subprocess.check_output(['git','-C',str(G),*args],env=env,stderr=subprocess.PIPE)
git('init');git('config','user.email','review@example.invalid');git('config','user.name','review')
(G/'registration.json').write_bytes(b'{"program_id":"x"}');(G/'line\nbreak.json').write_bytes(b'lf-body');git('add','.');git('commit','-m','synthetic first');one=git('rev-parse','HEAD').decode().strip()
(G/'registration.json').write_bytes(b'{"program_id":"y"}');git('add','.');git('commit','-m','synthetic second');two=git('rev-parse','HEAD').decode().strip()
transport=v._git_transport;calls=[]
def observed(*args):calls.append(args[1:]);return transport(*args)
with patch.object(v,'_git_transport',side_effect=observed):
 assert list(v._registration_pair(G,{'source':one,'registration':'registration.json','design_source':two}))==[b'{"program_id":"x"}',b'{"program_id":"y"}']
 assert list(v._registration_pair(G,{'source':one,'registration':'registration.json','design_source':one}))==[b'{"program_id":"x"}']*2
 assert len(calls)==2 and calls[1][0].count(b'\n')==2
 assert list(v._registration_pair(G,{'source':one,'registration':'line\nbreak.json','design_source':one}))==[b'lf-body']*2
 assert len(calls)==4
frame=lambda x:b'a'*40+b' blob '+str(len(x)).encode()+b'\n'+x+b'\n'
claimdir=D/'synthetic-root/research_runs/sentinel';claimdir.mkdir(parents=True)
base={'experiment_id':'sentinel','source':one,'registration':'registration.json','design_source':two,'registration_sha256':H(b'{"program_id":"x"}'),'program_id':'x'}
checks=0
for body,change,expected in [(b'{"program_id":"x"}',{'registration_sha256':'0'*64},'registration hash'),(b'bad',{'registration_sha256':H(b'bad')},None),(b'{"program_id":"x"}',{'program_id':'z'},'claim program')]:
 (claimdir/'claim.json').write_text(json.dumps(base|change))
 with patch.object(v,'_git_transport',return_value=frame(body)+b'malformed\n'):
  try:v.verify_claim(claimdir)
  except Exception as e:
   if expected:assert expected in str(e)
   else:assert isinstance(e,json.JSONDecodeError)
  else:raise AssertionError('accepted invalid')
 checks+=1
for raw in [frame(b'x')+frame(b'y')+b'extra',frame(b'x')+b'a'*40+b' tree 0\n\n',frame(b'x')+b'a'*40+b' blob 2\nx\n',frame(b'x')+b'a'*40+b' blob 01\nx\n',frame(b'x')]:
 with patch.object(v,'_git_transport',return_value=raw):
  it=v._registration_pair(G,base);assert next(it)==b'x'
  try:next(it)
  except ValueError:pass
  else:raise AssertionError('bad frame accepted')
 checks+=1
# An ordinary delayed missing design does not precede first yielded body.
with patch.object(v,'_git_transport',return_value=b'x'):
 it=v._registration_pair(G,{'source':one,'registration':'registration.json'});assert next(it)==b'x'
 try:next(it)
 except KeyError:pass
 else:raise AssertionError('missing design accepted')
fatal=KeyboardInterrupt('first fatal');req=v._source_request
with patch.object(v,'_source_request',side_effect=[req(one,'registration.json'),fatal]),patch.object(v,'_git_transport') as never:
 try:next(v._registration_pair(G,base))
 except BaseException as e:assert e is fatal
 else:raise AssertionError('fatal lost')
 never.assert_not_called()
for name in ['_git_transport','_git_cleanup','_verify_sources','_verify_batch','_source_request','_blob']:
 old=next(n for n in ast.parse(b).body if isinstance(n,ast.FunctionDef) and n.name==name);new=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name);assert ast.dump(old)==ast.dump(new)
assert not any(k.split('.')[0] in {'numpy','torch','scipy','pandas','pyarrow'} for k in sys.modules)
out={'decision':'accepted_source_only','source_sha256':H(a.encode()),'manifest_files':len(manifest['files']),'inverse_full_bytes_equal':True,'tiny_git_commits':[one,two],'fresh_transport_calls':len(calls),'ordered_error_cases':checks,'fatal_second_reference_not_delayed':True,'no_actual_research_claim_read_or_started':True,'scope_limit':'Transport-error precedence and bounded pair aggregate differ from two original independent unbounded show calls; no wall share or capacity claim.'}
(D/'READBACK01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
