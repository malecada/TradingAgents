"""Original outcome and exact installed-source joins only; no probe/import replay."""
import ast,datetime,hashlib,json,os,re,resource,signal,stat
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(15)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];Q=F/'pilot34-native-owner-qualification02-2026-10-11';I=F/'pilot34-serializer-postclosure-install01-2026-10-11';B=F/'pilot34-five-module-serialization-bundle01-2026-10-11';K=F/'pilot34-linux-memfd-compatibility-probe01-2026-10-11';checks=[];refs={}
def read(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<2*1024**2;b=p.read_bytes();refs[str(p.relative_to(R))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
def js(p):return json.loads(read(p))
def ck(v,n):checks.append({'check':n,'pass':bool(v)});assert v,n
def pin(ref):
 p=Path(ref['path']);p=p if p.is_absolute() else R/p;b=read(p);ck(hashlib.sha256(b).hexdigest()==ref['sha256'] and len(b)==ref['bytes'],'exact reference '+str(p.relative_to(R)));return b
launch=js(Q/'ROOT_LAUNCH02.json');end=js(Q/'ROOT_EXIT02.json');result=json.loads(pin(end['engineering_result']));rawerr=pin(end['raw_stderr']).decode();rawout=pin(end['raw_stdout'])
for ref in (launch['command'],launch['entry_review'],launch['accepted_failed34_return']):pin(ref)
ck(launch['accepted_failed34_return']['sha256']=='15f94fd288e1bf89feb911e578829303e9b223be70524047a70053b894381af8' and launch['entry_review']['sha256']=='dcf05fea48f4ffd4b2a99cdf91fe951b92f77bac399a3cdef70a30e0093cce3d','actual prerequisite anchors')
ck(launch['identity']==result['identity']=='edge-owner-and-kernel-qualification-20261011-02' and launch['maximum_attempts']==1,'permanent exact one-use engineering identity')
ck(end['actual_child_exit_code']==1 and end['actual_child_pid']==2411511 and end['child_reaped'] is True and end['child_pid_absent'] is True and end['timed_out'] is False,'Root actual exit/reap/absence and no timeout receipt')
ck(0<end['elapsed_seconds']==0.3204294800016214<launch['outer_timeout_seconds']==60,'retained bounded wall duration')
ck(result['status']=='FAILED' and result['failure']=={'message':"module 'fcntl' has no attribute 'F_SEAL_WRITE'",'notes':[],'type':'AttributeError'} and result['checks']==[] and result['reporting_errors']==[],'original empty-case failed result')
ck(len(result['phases'])==1 and result['phases'][0]['phase']=='actual-sealed-owner-borrow' and result['ru_maxrss_kib']==56416 and result['actual_financial_trial'] is None and result['actual_genuine_scientific_owner'] is None and result['whole_pilot_complete'] is False,'partial phase and null claims retained')
ck(rawout==b'' and 'compiled_edge_owner.py", line 130, in acquire' in rawerr and "AttributeError: module 'fcntl' has no attribute 'F_SEAL_WRITE'" in rawerr and 'qualify02.py", line 97, in main' in rawerr,'original raw traceback authenticates exact failed seam')
command=json.loads(pin(launch['command']));options=dict(zip(command['argv'][3::2],command['argv'][4::2]));owner=read(Path(options['--owner'])).decode();harness=read(Q/'qualify02.py').decode()
ck(hashlib.sha256(owner.encode()).hexdigest()==options['--owner-sha256'] and hashlib.sha256(harness.encode()).hexdigest()=='7d85464ab5ffe6c1ab028c7bd893d50ebc24341e2d28857e74786902494c4560','actual failed owner/harness source pins')
ck(owner.index('seals=fcntl.F_SEAL_WRITE')<owner.index('fd=os.memfd_create')<owner.index('ExtensionFileLoader'),'failure before descriptor acquisition or extension loader')
ck(harness.index('import numpy')<harness.index('lease = owner.borrow')<harness.index('a, b = graph(), graph()'),'scientific packages imported before failure; synthetic graph work not reached')
pid_observation={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':2411511,'proc_entry_absent':not os.path.lexists('/proc/2411511')};ck(pid_observation['proc_entry_absent'],'fresh original child PID metadata absent; no process bodies read')
integration=js(I/'INTEGRATION01.json');ck(refs[str((I/'INTEGRATION01.json').relative_to(R))]['sha256']=='bbab2992398b06cd8a9fd583f95cc973d7944364279ccfb2bffdf0a3f5b9da59','exact Root installation receipt')
pin(integration['accepted_failed34_recovery']);plan=json.loads(pin(integration['installation_plan']));ck(integration['accepted_failed34_recovery']==launch['accepted_failed34_return'],'installation after same accepted failed34 recovery')
ck(integration['all_bases_verified_before_first_write'] is True and integration['actual_empirical_claim'] is None and integration['actual_native_execution'] is False and integration['numerical_modules_imported'] is False,'recorded transactional precheck and source-only install limits')
ck(integration['source_reviews']==plan['accepted_source_reviews'],'exact accepted source review pair')
for ref in integration['source_reviews']+plan['dependencies']:pin(ref)
ck(len(integration['modules'])==len(plan['modules'])==5,'exact five-module installation denominator')
def inverse(text,patch):
 lines=text.splitlines(True);out=[];position=0;active=False
 for line in patch.splitlines(True)[2:]:
  if line.startswith('@@'):
   match=re.match(r'@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@',line);assert match;start=int(match[1])-1;assert start>=position;out.extend(lines[position:start]);position=start;active=True
  elif active and line[:1] in (' ','-'):
   assert lines[position]==line[1:];position+=1
   if line[0]==' ':out.append(line[1:])
  elif active and line.startswith('+'):out.append(line[1:])
  else:assert False,line
 out.extend(lines[position:]);return ''.join(out)
installed=[]
for actual,planned in zip(integration['modules'],plan['modules'],strict=True):
 ck(actual['accepted_source']==planned['accepted_source'] and actual['destination']['path']==planned['destination'] and actual['original_base']==planned['required_base'] and actual['inverse_patch']==planned['inverse_patch'],'exact planned row '+Path(planned['destination']).name)
 destination=pin(actual['destination']);accepted=pin(actual['accepted_source']);bundle=read(R/planned['bundle_source']);ck(destination==accepted==bundle,'installed accepted and bundled bodies identical '+Path(planned['destination']).name);ast.parse(destination)
 original=inverse(destination.decode(),read(R/planned['inverse_patch']).decode()).encode();ck(len(original)==actual['original_base']['bytes'] and hashlib.sha256(original).hexdigest()==actual['original_base']['sha256'],'in-memory inverse joins original base '+Path(planned['destination']).name)
 installed.append(actual['destination'])
probe=js(K/'PROBE01.json');precheck=js(K/'PRECHECK_UNAVAILABLE01.json')
ck(probe['status']=='PASS_ACTUAL_LINUX_KERNEL_SEALS' and probe['flags']==3 and probe['F_ADD_SEALS']==1033 and probe['F_GET_SEALS']==1034 and probe['seal_mask']==probe['actual_kernel_seals']==15 and probe['fd_closed'] is True and probe['refusals']==['write','grow','shrink'],'retained finite kernel probe summary fields')
ck(precheck['exit_code']==1 and precheck['actual_tool_chunk']=='fbc9ce' and precheck['rerun_claim'] is False,'original feature-observation failure retained')
out={'decision':'ACCEPT_ORIGINAL_OWNER02_FAILED_CLOSURE_AND_EXACT_SERIALIZER_INSTALL_JOINS','checks':checks,'references':refs,'original_child_pid_observation':pid_observation,'owner02_result':result,'original_child_exit':end,'installed_modules':installed,'probe_summary':probe,'probe_evidence_limit':'Only PROBE01 and PRECHECK_UNAVAILABLE01 available at this check; no probe execution or source reconstruction. Await separately retained original raw/source observation if supplied.','limitations':['Actual attempt imported NumPy/SciPy before failing; no synthetic graph/native extension load reached by authenticated source/trace ordering.','One preborrow phase label is not successful native load. Original identity remains spent/failed.','Reap and install pre-write base checks are authenticated Root receipts; current PID absence, current installed bytes and in-memory inverse were independently checked.','Financial trial accounting not reread or changed; null scientific/financial result fields retained.','No performance/capacity/full caller or new identity authority. New increment preservation is separate.']}
with (P/'CHECK01.json').open('x') as f:json.dump(out,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'decision':out['decision'],'checks':len(checks)}))
