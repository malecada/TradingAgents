from pathlib import Path
import ast,hashlib,importlib.util,json,os,stat,sys,copy
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';P=F/'financial-wrapper-compatibility-operational-delta-remote-successor02-2026-10-04';sys.path.insert(0,str(P));sp=importlib.util.spec_from_file_location('successor_remote02',P/'recover01.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);h=lambda b:hashlib.sha256(b).hexdigest();rows=[]
def put(n,v):(P/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def ck(n,v):rows.append({'case':n,'passed':bool(v)});assert v,n
def refuse(n,v):
 try:m.validate_fixed_selection(v)
 except (ValueError,TypeError,KeyError):ck(n,True)
 else:ck(n,False)
s={'remote_commit':'0e65d12400e9c63b0eaf1f93bea2c81b10a82743','rows':[dict(path=p,**v) for p,v in sorted(m.REQUIRED.items())]};m.validate_fixed_selection(s);ck('actual fixed15 sorted pure selection body accepted',True)
for i,r in enumerate(s['rows']):
 ck('actual original selected body '+r['path'],len((R/r['path']).read_bytes())==r['bytes'] and h((R/r['path']).read_bytes())==r['sha256'])
 b=copy.deepcopy(s);b['rows'].pop(i);refuse('missing row '+str(i),b)
 for field,value in [('sha256','0'*64),('bytes',True),('bytes',float(r['bytes']))]:
  b=copy.deepcopy(s);b['rows'][i][field]=value;refuse('changed '+field+str(value)+str(i),b)
b=copy.deepcopy(s);b['rows'].append(dict(s['rows'][0]));refuse('duplicate16 row',b)
b=copy.deepcopy(s);b['rows'].append({'path':'research/foreign','bytes':0,'sha256':h(b'')});refuse('foreign16 row',b)
a=ast.parse((P/'ORIGINAL_recover01.py').read_bytes());b=ast.parse((P/'recover01.py').read_bytes())
def strip(t):
 t.body=[n for n in t.body if not (isinstance(n,ast.FunctionDef) and n.name in ('validate_fixed_selection','main')) and not (isinstance(n,ast.Assign) and any(isinstance(z,ast.Name) and z.id=='REQUIRED' for z in n.targets))];return ast.dump(t,include_attributes=False)
ck('all other original AST unchanged',strip(a)==strip(b));ck('main Git cleanup resources unchanged',ast.dump(next(n for n in a.body if isinstance(n,ast.FunctionDef) and n.name=='git'))==ast.dump(next(n for n in b.body if isinstance(n,ast.FunctionDef) and n.name=='git')))
ck('genuine independent watch source and limits',h((P/'watch01.py').read_bytes())=='bdeacaadc053e615245b3e2175089842708719448ec7da970d981e5dc077ca18' and m.W.POLICY=={'logical':67108864,'allocated':100663296,'file':4194304,'members':32768,'depth':32,'samples':8192,'sample_seconds':5,'floor':10737418240})
ck('original process caps retained',m.FILE==4194304 and m.FLOOR==10737418240)
ck('no main or entry called',m.CALLS==[] and m.WATCHES==[] and m.BASELINE is None);ck('no numerical package',not any(n in sys.modules for n in ('torch','numpy','scipy','pandas')))
put('CHECKS01.json',{'status':'PASS_FIXED_SELECTION_SOURCE_ONLY','count':len(rows),'rows':rows,'actual_remote_or_Root_entry':False});put('DRAFT_SELECTION_SHAPE01.json',dict(s,qualification='Pure predicate control only; not an actual one-use Root selection or released Main.'))
(P/'REPORT01.md').write_text('''Prepared exact15-body source-only remote successor02. It retains all original ten operational source/policy review bodies and adds five complete closed failed forensic Root02 capture bodies, total507946B. Fresh receiver namespace changes to fresh-operational-source-policy02.git. The existing format status01 is a receipt schema version, not the spent Root02 identity. Required selection cardinality now refuses any missing, extra or duplicate row. The original53 plus dynamic unique-object operation denominator remains10+unique+2*15; all actual Git children, hard/soft4MiB readback, real exit vs separate reaped exit and cleanup operations are unchanged.

Four literal edits invert exactly to the original remote01 source. Only REQUIRED assignment, validate_fixed_selection cardinality and two main literals change. All other AST/functions and operational limits remain unchanged. Exact accepted watch04 bdeaca/aed124/7a94 is copied; its fixed two100ms waits within original3attempts5s are an explicit operational timing deviation, not a cap increase or scientific modification. Complete source and policy bodies, closed failed originalinitNULL/reaped0/Root1 and originalunknowns remain unchanged.

Actual original selected bodies and pure missing/type/hash/extra controls passed. First source check harness wrongly encoded POLICY field names and is preserved as CHECK_FREEZE01.err with its original script; separately named corrected harness uses the actual original POLICY literal. No main, entry, network transfer, Git child or NUM was executed here. Draft shape metadata is only a validator input, not external source evidence. Exact fresh installed Root selection/Main commit, helper/source review and one-use installed entry release remain absent. Full flat03 actual receipt-bound recovery and genuine composed source-policy proof are separate dependent requirements. Old Root02 cannot be replayed; all failed scope bytes must be preserved and recovered. Receiver aggregate bounds are sampled, not a continuous storage quota, and physical encrypted wire/installed runtime/POSIX/whole empirical capacity are excluded.
''')
put('MACHINE01.json',{'schema_version':1,'decision':'SOURCE_ONLY_READY_FOR_INDEPENDENT_REVIEW','source_sha256':h((P/'recover01.py').read_bytes()),'original_sha256':h((P/'ORIGINAL_recover01.py').read_bytes()),'watch_sha256':h((P/'watch01.py').read_bytes()),'watch_review_sha256':h((P/'WATCH_REVIEW_MACHINE01.json').read_bytes()),'source_checks':len(rows),'all_OTHER_AST_unchanged':True,'literal_inverse_sha256':h((P/'SOURCE_INVERSE01.json').read_bytes()),'selected_rows':15,'selected_bytes':507946,'actual_Root_selection':None,'actual_entry_release':None,'actual_external_receipt':None,'main_entry_started':False,'report_sha256':h((P/'REPORT01.md').read_bytes())})
exclude={'MANIFEST01.json','CHECK_FREEZE02.out','CHECK_FREEZE02.err'};rs=[]
for root,dirs,files in os.walk(P,followlinks=False):
 for n in dirs+files:
  p=Path(root)/n;name=p.relative_to(P).as_posix()
  if name in exclude:continue
  s=p.lstat();r={'path':name,'mode':stat.S_IMODE(s.st_mode),'links':s.st_nlink}
  if stat.S_ISREG(s.st_mode):assert s.st_size<=4194304;r.update(kind='file',bytes=s.st_size,sha256=h(p.read_bytes()))
  elif stat.S_ISDIR(s.st_mode):r.update(kind='directory')
  else:raise AssertionError(name)
  rs.append(r)
put('MANIFEST01.json',{'schema_version':1,'status':'SOURCE_ONLY_READY_FOR_INDEPENDENT_REVIEW','excluded':sorted(exclude),'members':sorted(rs,key=lambda r:r['path']),'typed_members':len(rs)})
print(json.dumps({n:h((P/n).read_bytes()) for n in ('MANIFEST01.json','MACHINE01.json','recover01.py')}));print('checks',len(rows))
