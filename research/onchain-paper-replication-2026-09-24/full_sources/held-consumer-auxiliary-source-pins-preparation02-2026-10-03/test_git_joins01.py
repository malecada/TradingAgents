"""Extract exact new readback block; synthetic Git responses, not actual authority."""
import ast,copy,hashlib,json,pathlib,types,unittest
from test_auxiliary01 import P,G,fixture,role
T=ast.parse((P/'build_release_draft01.py').read_text());F=next(n for n in T.body if isinstance(n,ast.FunctionDef) and n.name=='held_metadata_draft');start=next(i for i,n in enumerate(F.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='auxiliary')
BLOCK=compile(ast.Module(F.body[start:start+2],[]),'actual-aux-current-design-block','exec')
class Tests(unittest.TestCase):
 def invoke(self,corrupt=None):
  source,roles=fixture();plan=G['held_input_plan'](roles,source);source['source_origins']=[];files={};calls=[]
  for i,path in enumerate(source['source_files']):
   raw=('synthetic implementation %d'%i).encode();source['source_origins'].append({'path':path,'sha256':G['sha'](raw),'bytes':len(raw)});files[path]=raw
  for r in roles.values():files[r['reference']['path']]=r['document'].encode() if isinstance(r['document'],str) else G['canonical'](r['document'])
  def read(root,ref):
   raw=files[ref['path']];assert len(raw)==ref['bytes'] and G['sha'](raw)==ref['sha256'];return raw
  def git(root,*args):
   calls.append(args)
   if args[0]=='merge-base':
    if corrupt=='nonancestor':raise ValueError('not ancestor')
    return b''
   commit,path=args[2].split(':',1);raw=files[path]
   if args[1]=='-s':return str(len(raw)+(1 if corrupt=='extent' and path=='metadata/allocation.json' else 0)).encode()
   if corrupt=='design-code' and commit=='2'*40 and path.startswith('tradingagents/'):return b'changed'
   if corrupt=='design-review' and commit=='2'*40 and path=='metadata/review.json':return b'changed'
   if corrupt=='current-registration' and commit=='1'*40 and path=='metadata/registration.json':return b'changed'
   return raw
  ns=dict(plan=plan,source_plan=source,source='1'*40,design_source='2'*40,root=pathlib.Path('/synthetic-only'),roles=roles,builder=types.SimpleNamespace(_held_git=git,held_document=read),generator=types.SimpleNamespace(AUXILIARY_ROLES=G['AUXILIARY_ROLES'],sha=G['sha']),require=G['require'])
  exec(BLOCK,ns);return ns['auxiliary'],calls
 def test_exact_all_current_and_design_metadata(self):
  out,calls=self.invoke();self.assertTrue(out['committed_metadata_readback']);self.assertEqual(len(calls),1+199*2+6*2*2);self.assertFalse(out['execution_admitted'])
 def test_current_design_corruptions(self):
  for corruption in ['nonancestor','extent','design-code','design-review','current-registration']:
   with self.subTest(corruption=corruption),self.assertRaises(ValueError):self.invoke(corruption)
 def test_declaration_render_matches_frozen_schema(self):
  s,r=fixture();self.assertEqual(G['render_held_auxiliary_declaration'](r,s),r['auxiliary_sources']['document'])
  r['budget_review']=None
  with self.assertRaises(ValueError):G['render_held_auxiliary_declaration'](r,s)
 def test_dependent_case_requires_new_case_and_charter_declaration(self):
  s,r=fixture();reg=r['registration']['document'];exp=reg['experiments']['future-held-fixture'];dependent=copy.deepcopy(exp);dependent['charter']={'path':'metadata/dependent.md','sha256':G['sha'](b'Dependent synthetic charter')};reg['experiments']['future-held-dependent']=dependent
  r['case_contract']['document']['experiment_id']='future-held-dependent'
  with self.assertRaises(ValueError):G['held_input_plan'](r,s)
  r['charter']=role('metadata/dependent.md','Dependent synthetic charter');r['auxiliary_sources']=role('metadata/dependent-aux.json',G['render_held_auxiliary_declaration'](r,s))
  aux=[r[k]['reference'] for k in (*G['AUXILIARY_ROLES'],'auxiliary_sources')];dependent['source_files']={**s['source_files'],**{v['path']:v['sha256'] for v in aux}}
  out=G['held_input_plan'](r,s);self.assertEqual(out['experiment_id'],'future-held-dependent');self.assertEqual(out['auxiliary_metadata']['auxiliary_count'],5);self.assertEqual(r['budget_extension']['document']['initial_experiment'],'future-held-fixture')
 def test_inverse_untouched_functions_and_full_prefix(self):
  for name,seam,extras in [('generate_inputs01.py','held_input_plan',{'held_auxiliary_metadata','render_held_auxiliary_declaration'}),('build_release_draft01.py','held_metadata_draft',set())]:
   old=(P/(name+'.baseline04.txt')).read_text();new=(P/name).read_text();a=ast.parse(old);b=ast.parse(new);oldfn=next(x for x in a.body if isinstance(x,ast.FunctionDef) and x.name==seam);newfn=next(x for x in b.body if isinstance(x,ast.FunctionDef) and x.name==seam);lines=new.splitlines(True);edits=[(newfn.lineno,newfn.end_lineno,old.splitlines(True)[oldfn.lineno-1:oldfn.end_lineno])]
   for n in b.body:
    if isinstance(n,ast.FunctionDef) and n.name in extras:edits.append((n.lineno,n.end_lineno,[]))
    if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='AUXILIARY_ROLES':edits.append((n.lineno,n.end_lineno,[]))
    if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='HELD_ROLES':
     prior=next(x for x in a.body if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id=='HELD_ROLES');edits.append((n.lineno,n.end_lineno,old.splitlines(True)[prior.lineno-1:prior.end_lineno]))
   for start,end,rows in sorted(edits,reverse=True):lines[start-1:end]=rows
   restored=''.join(lines);self.assertEqual(ast.dump(ast.parse(restored)),ast.dump(a))
   # Only blank separators introduced by new helpers remain after removal.
   self.assertEqual([l for l in restored.splitlines() if l.strip()],[l for l in old.splitlines() if l.strip()])
   exact=new
   if extras:exact=exact[:exact.index('AUXILIARY_ROLES=')]+exact[exact.index('def held_input_plan('):]
   t=ast.parse(exact);nf=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==seam);ls=exact.splitlines(True);ls[nf.lineno-1:nf.end_lineno]=old.splitlines(True)[oldfn.lineno-1:oldfn.end_lineno];exact=''.join(ls)
   if extras:
    oldrole=next(l for l in old.splitlines(True) if l.startswith('HELD_ROLES='));newrole=next(l for l in exact.splitlines(True) if l.startswith('HELD_ROLES='));exact=exact.replace(newrole,oldrole,1)
   self.assertEqual(exact,old)
if __name__=='__main__':unittest.main(verbosity=2)
