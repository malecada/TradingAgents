from pathlib import Path
import ast,json,hashlib,os,shutil
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');C=R/'research/onchain-paper-replication-2026-09-24/full_sources/heartbeat-root-checkpoint10-2026-10-04';D=C.parent/'financial-wrapper-compatibility-operational-delta-root-remote03-2026-10-04';P=C/'ROOT_REMOTE_CALLER04_AUTH_CONTROLS01';P.mkdir(mode=0o700);h=lambda b:hashlib.sha256(b).hexdigest();rows=[]
def selected(file):
 t=ast.parse(file.read_bytes());first=next(i for i,n in enumerate(t.body) if isinstance(n,ast.Assert) and "ROOT_REMOTE03_INTENT01.json" in ast.unparse(n));last=next(i for i,n in enumerate(t.body[first:],first) if isinstance(n,ast.For));return compile(ast.Module(body=t.body[first:last+1],type_ignores=[]),str(file),'exec')
old=selected(C/'root_operational_remote03.py');new=selected(C/'root_operational_remote04.py');v={'installation_draft_sha256':'4ac66420883fe2605db005152c4492e0597aaab1593ebc9976d1857b0ff6a96d','remote_helper_sha256':'ada3dafc7250452cb6db2eb33cdd5b5ecddb776511e247efcbc858dbb446aabf'}
def check(n,c,d,expected):
 error=None
 try:exec(c,{'D':d,'v':v,'h':h,'json':json})
 except (AssertionError,ValueError,KeyError,FileNotFoundError) as e:error=e
 ok=(error is None)==expected;rows.append({'case':n,'passed':ok,'predicate_returned':error is None,'expected_return':expected,'error':None if error is None else type(error).__name__});assert ok,n
for label,c in [('original',old),('corrected',new)]:check('actual untouched installed predicate '+label,c,D,True)
for mutation in ('helper+draft','draftonly','helperonly','selection+draft','unknown-draft-field'):
 for label,c in [('original',old),('corrected',new)]:
  d=P/(mutation+'-'+label);d.mkdir(mode=0o700);(d/'utilities').mkdir(mode=0o700);s=json.loads((D/'ROOT_INSTALLATION_DRAFT01.json').read_bytes())
  for name in s['helpers_and_selection']:(d/name).write_bytes((D/name).read_bytes())
  if mutation in ('helper+draft','helperonly'):
   (d/'recover01.py').write_bytes(b'opaque altered not executed\n')
   if mutation=='helper+draft':s['helpers_and_selection']['recover01.py']['sha256']=h((d/'recover01.py').read_bytes())
  elif mutation=='draftonly':s['helpers_and_selection'].pop('recover01.py')
  elif mutation=='selection+draft':
   (d/'SELECTED_BODIES01.json').write_bytes(b'opaque altered selection not executed\n');s['helpers_and_selection']['SELECTED_BODIES01.json']['sha256']=h((d/'SELECTED_BODIES01.json').read_bytes())
  else:s['foreign']=True
  (d/'ROOT_INSTALLATION_DRAFT01.json').write_bytes((D/'ROOT_INSTALLATION_DRAFT01.json').read_bytes() if mutation=='helperonly' else (json.dumps(s,sort_keys=True,indent=2)+'\n').encode())
  expected=label=='original' and mutation!='helperonly';check(mutation+' '+label,c,d,expected)
for name in ('ROOT_REMOTE03_INTENT01.json','REMOTE_RECOVERY01.json','FAILED01.json'):assert not os.path.lexists(D/name)
(C/'ROOT_REMOTE_CALLER04_AUTH_CHECKS01.json').write_text(json.dumps({'schema_version':1,'status':'PASS_ORIGINAL_METADATA_BINDING_RED_TO_CORRECTED_REFUSAL_GREEN','source_sha256':h((C/'root_operational_remote04.py').read_bytes()),'rows':rows,'checks':len(rows),'scope':'Extracted exact installed-draft/helper-check AST only. Descriptor data are pure predicate inputs from actual pins, not a release/proof/Admission or accepted future review body. No whole caller or receiver entry.','actual_installed_files_unchanged':True,'attempt_or_intent':False,'new_release':None},indent=2)+'\n');print(len(rows))
