import ast,hashlib,importlib.util,json,os,stat,sys,types
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).resolve().parent;A=R.parent/'held-consumer-one-use-parent-preparation01-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest()
assert H((A/'MANIFEST01.json').read_bytes())=='4727a73ff75b5bc74a6b66b19b7fab0b6b5c508bc30d5d444d28687c825e0160'
assert H((A/'launch_success01.py').read_bytes())=='1e3c7a2c5da35356815489d9bc9c85944e7430a91608fd19f5f2cba7364fa5cf'
manifest=json.loads((A/'MANIFEST01.json').read_bytes());rows=manifest.get('files',manifest.get('members'));names=[]
for r in rows:
 p=A/r['path'];s=p.lstat();assert stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==r['mode'] and s.st_nlink==r['links'] and s.st_size==r['bytes'] and H(p.read_bytes())==r['sha256'];names.append(r['path'])
assert sorted(names)==sorted(str(p.relative_to(A)) for p in A.rglob('*') if p.is_file() and p.name!='MANIFEST01.json')
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=load(A/'launch_success01.py','review_parent');semantic=load(A/'held_outcome02.py','review_semantic');assert H((A/'held_outcome02.py').read_bytes())==p.PARSER_SHA
release=json.loads((A/'release-unreleased01.json').read_bytes());reader=semantic.Reader(p.CAP);reg=semantic.sources(reader,release);exp=reg['experiments'][p.IDENTITY];inp={k:H(semantic.input_body(reader,exp,k)) for k in sorted(exp['inputs'])};reader.recheck();assert len(inp)==33 and len(exp['outputs'])==6
# HUP1: exact original post-tail function under exact extracted namespace.
rawpath=p.CAP/'fixture_tools/raw_receipts01.py';raw=rawpath.read_bytes();assert H(raw)==release['source_files']['fixture_tools/raw_receipts01.py'];fn=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='authenticate_post_tail')
root=R/'posttail-tiny';root.mkdir();s=root.stat();limits={'disk_floor_bytes':10*p.GIB,'storage_budget':{'limits':{'max_allocated_bytes':100,'max_logical_bytes':100,'max_entries':10}}}
value={'disk_floor_bytes':10*p.GIB,'disk_free_bytes':11*p.GIB,'excludes_own_file':True,'remaining_final_file_allowance':65536,'observation':{'root':str(root),'root_device':s.st_dev,'root_inode':s.st_ino,'allocated_bytes':0,'logical_file_bytes':0,'entries':0}}
ns={'Path':Path,'GIB':p.GIB,'require':p.require,'metadata':lambda root,name:value};exec(compile(ast.Module([fn],[]),str(rawpath),'exec'),ns);missing=[]
for stage in (0,1):
 try:ns['authenticate_post_tail'](root,'synthetic-metadata-only',limits)
 except NameError as e:missing.append(e.name)
 else:raise AssertionError('missing global not reproduced')
 if stage==0:ns['digest']=H
assert missing==['digest','body'],missing
print('REPRODUCED HUP1:',missing,'absent from actual parent namespace')
# HUP2: actual reap function, qualified error-injection process; no OS signals.
first=MemoryError('first actual wait');calls=[]
class Process:
 pid=12345
 def poll(self):calls.append('poll');return None
 def wait(self,timeout):calls.append('wait'+str(timeout));raise first
with patch.object(p,'ticks',return_value='known'),patch.object(p.os,'killpg',side_effect=lambda pid,sig:calls.append('signal'+str(sig))):
 try:p.reap_controller(Process(),'known')
 except BaseException as e:assert e is first
 else:raise AssertionError('missing wait fatal')
assert calls==['poll','signal15','wait60'],calls
print('REPRODUCED HUP2:',calls,'no escalation/final independent wait')
# HUP3: actual write after the original created directory is redirected.
original=R/'attempt-owned';original.mkdir();foreign=R/'foreign-owned';foreign.mkdir();original.rename(R/'attempt-retained');original.symlink_to(foreign,target_is_directory=True)
p.write(original,'receipt.json',{'synthetic_fixture_only':True})
assert (foreign/'receipt.json').is_file() and not (R/'attempt-retained'/'receipt.json').exists()
print('REPRODUCED HUP3: actual write succeeded through replaced parent into separate owned directory')
# HUP4: exact selected parser's actual distinct uncertainty class, no fake class.
uncertain=semantic.CleanupFailure('ordinary descriptor uncertainty');later=MemoryError('first actual fatal');chosen=p.select(uncertain,later);assert chosen is uncertain
print('REPRODUCED HUP4: selected parser CleanupFailure masks later first MemoryError')
# Positive controls: bounded real bootstrap and firstfatal independentFDclose.
boot=R/'bootstrap';boot.mkdir();(boot/'source.py').write_bytes(b'opaque');assert p.bootstrap(boot,'source.py',H(b'opaque'))==b'opaque'
close=os.close;closed=[];first_read=MemoryError('read first')
def close_later(fd):closed.append(fd);close(fd);raise OSError('after close')
with patch.object(p.os,'read',side_effect=first_read),patch.object(p.os,'close',close_later):
 try:p.bootstrap(boot,'source.py',H(b'opaque'))
 except BaseException as e:assert e is first_read
 else:raise AssertionError('missing read fatal')
assert len(closed)==len(set(closed))==2
# Default actual source origin cannot prepare or reserve.
try:p.prepared(A/'REQUEST_TEMPLATE01.json',H((A/'REQUEST_TEMPLATE01.json').read_bytes()))
except ValueError as e:assert str(e)=='caller origin/cwd differs'
else:raise AssertionError('uninstalled source prepared')
assert not any(n in sys.modules for n in ('numpy','torch','scipy'))
result={'decision':'WITHHELD','findings':['HUP1','HUP2','HUP3','HUP4'],'candidate_sha256':H((A/'launch_success01.py').read_bytes()),'manifest_bodies':len(rows),'actual_current_source_registration_bodies':205,'opaque_input_hashes':inp,'outputs':exp['outputs'],'original_posttail_source_sha256':H(raw),'HUP1_missing_globals':missing,'HUP2_cleanup_calls':calls,'HUP3_outside_owned_write':str(foreign/'receipt.json'),'HUP4_actual_parser_cleanup_class':semantic.CleanupFailure.__name__,'real_bootstrap_firstfatal_closes_once':2,'actual_launch_claim_or_native_invoked':False,'numerical_imports':False,'positive_full_prepared_or_finish_check':False}
(R/'READBACK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print('PASS manifest/205source/33opaqueinputs/bootstrap controls; four exact source counterexamples retained')
