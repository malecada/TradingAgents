from pathlib import Path
import ast,hashlib,json,types,copy,os,stat
D=Path(__file__).resolve().parent;B=D.parent;I=B/'financial-wrapper-compatibility-operational-delta-root-remote03-2026-10-04';OLD=B/'financial-wrapper-compatibility-operational-delta-entry-review03-2026-10-04';h=lambda b:hashlib.sha256(b).hexdigest();source=(D/'root_operational_remote04.py').read_text();original=(D/'ORIGINAL_root_operational_remote03.py').read_text();inv=json.loads((D/'SOURCE_INVERSE01.json').read_bytes());rebuilt=source;rows=[]
def ck(n,v,**kw):
 assert v,n;rows.append(dict(name=n,**kw));(D/'PREDICATES01.json').write_text(json.dumps(rows,indent=2)+'\n')
for e in reversed(inv['edits']):assert rebuilt.count(e['new'])==1;rebuilt=rebuilt.replace(e['new'],e['old'])
ck('exact two edit inverse',len(inv['edits'])==2 and rebuilt==original and h(original.encode())=='91b1bc524b614fe6b84cfc1df74d887e94c267b91509b679b563e21f304b83c7' and h(source.encode())=='169c638054cacd242335be40eed2507d49172885a9bdfd106b6f07fe31650e28')
ck('complete AST inverse',ast.dump(ast.parse(rebuilt))==ast.dump(ast.parse(original)))
manifest=json.loads((OLD/'MANIFEST01.json').read_bytes());ck('closed withheld entry03 seal',h((OLD/'MANIFEST01.json').read_bytes())=='5c022598e6130852276229db3374c4afcb66076a3a17fcb5b4344d576a54ac71')
for r in manifest['members']:
 p=OLD/r['path'];s=p.lstat();ck('closed entry03 unchanged:'+r['path'],stat.S_IMODE(s.st_mode)==r['mode'] and ((r['kind']=='directory' and stat.S_ISDIR(s.st_mode)) or (r['kind']=='file' and stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and h(p.read_bytes())==r['sha256'])))
def extracted(text,new):
 t=ast.parse(text);start=next(i for i,x in enumerate(t.body) if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id==('draft_raw' if new else 's') for y in x.targets));end=next(i for i,x in enumerate(t.body) if i>start and isinstance(x,ast.For));return compile(ast.Module(body=t.body[start:end+1],type_ignores=[]),'<exact old/new installation predicate AST>','exec')
codes=[extracted(original,False),extracted(source,True)];raw=(I/'ROOT_INSTALLATION_DRAFT01.json').read_bytes();baseline=json.loads(raw);hashcontext={'installation_draft_sha256':h(raw),'remote_helper_sha256':baseline['helpers_and_selection']['recover01.py']['sha256']};assert set(hashcontext)=={'installation_draft_sha256','remote_helper_sha256'}
for variant in ('unchanged','helper-alone','helper-plus-draft','draft-whitespace','foreign-draft-field','selection-plus-draft','omitted-helper-pin'):
 root=D/('owned-'+variant);root.mkdir();draft=copy.deepcopy(baseline)
 for n in baseline['helpers_and_selection']:
  p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((I/n).read_bytes())
 draftpath=root/'ROOT_INSTALLATION_DRAFT01.json';draftpath.write_bytes(raw)
 if variant in ('helper-alone','helper-plus-draft'):
  p=root/'recover01.py';p.write_bytes(p.read_bytes()+b'\n# opaque review edit, never executed\n')
  if variant=='helper-plus-draft':draft['helpers_and_selection']['recover01.py'].update(sha256=h(p.read_bytes()),bytes=p.stat().st_size)
 elif variant=='draft-whitespace':draftpath.write_bytes(raw+b'\n')
 elif variant=='foreign-draft-field':draft['unreviewed_extra']=True
 elif variant=='selection-plus-draft':
  p=root/'SELECTED_BODIES01.json';p.write_bytes(p.read_bytes()+b'\n');draft['helpers_and_selection']['SELECTED_BODIES01.json'].update(sha256=h(p.read_bytes()),bytes=p.stat().st_size)
 elif variant=='omitted-helper-pin':draft['helpers_and_selection'].pop('recover01.py')
 if variant in ('helper-plus-draft','foreign-draft-field','selection-plus-draft','omitted-helper-pin'):draftpath.write_text(json.dumps(draft,indent=2,sort_keys=True)+'\n')
 for idx,code in enumerate(codes):
  parses=[]
  def loads(b):parses.append(True);return json.loads(b)
  env={'D':root,'json':types.SimpleNamespace(loads=loads),'h':h,'v':hashcontext}
  try:exec(code,env);accepted=True
  except AssertionError:accepted=False
  expected=(variant!='helper-alone') if idx==0 else variant=='unchanged'
  ck(f'{variant}:caller'+('04' if idx else '03'),accepted==expected,installation_predicate_passed=accepted,json_parse_calls=len(parses),not_an_accepted_review_object=True)
  if idx and variant not in ('unchanged','helper-alone'):ck('changed draft refused before parse:'+variant,parses==[])
ck('actual D remains exact',h((I/'ROOT_INSTALLATION_DRAFT01.json').read_bytes())==hashcontext['installation_draft_sha256'] and h((I/'recover01.py').read_bytes())==hashcontext['remote_helper_sha256'])
ck('no Root entry or intent consumed',not (I/'ROOT_REMOTE03_INTENT01.json').exists() and not (I/'ROOT_REMOTE03_SPAWN01.json').exists())
print(json.dumps({'checks':len(rows),'original_paired_change_RED_new_refusal_GREEN':True,'only_extracted_predicate_executed':True,'entry_started':False}))
