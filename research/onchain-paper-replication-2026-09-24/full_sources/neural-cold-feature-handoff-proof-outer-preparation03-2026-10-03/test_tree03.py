"""Actual typed tree verifier with explicit in-memory Git/metadata fixtures only."""
import copy,hashlib,json,pathlib,sys,types,unittest
D=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(D));import proof_release01 as release
A='a'*40;B='b'*40
class Tests(unittest.TestCase):
 def exercise(self,mutate=lambda state:None):
  raw=lambda x:json.dumps(x,sort_keys=True,separators=(',',':')).encode();sha=lambda x:hashlib.sha256(x).hexdigest();files={}
  def put(path,value):files[path]=raw(value);return {'path':path,'sha256':sha(files[path]),'bytes':len(files[path]),'kind':'document'}
  first={'parent':None,'family':'f','inputs':{'environment':{'path':'env','sha256':'e'*64,'dataset':'synthetic-cold'}},'source_files':{str(i):'s'*64 for i in range(195)}}
  material={'inputs':{n:{'path':'emitted/'+n,'sha256':'i'*64,'dataset':'synthetic-cold'} for n in release.MATERIAL_INPUTS}}
  second=copy.deepcopy(first);second.update(parent=release.IDENTITIES['materialize'],inputs={('execution_job' if n=='future_execution_job' else n):v for n,v in material['inputs'].items()}|{'environment':first['inputs']['environment']});charter=put('new/charter',{'qualified':'not an actual charter'});second['charter']={'path':charter['path'],'sha256':charter['sha256']}
  oldreg={'schema_version':1,'program_id':release.PROGRAM,'families':{'f':{'attempt_budget':2,'prior_attempts':0,'history_reference':'unchanged'}},'datasets':{'synthetic-cold':{'exposures':[]}},'experiments':{release.IDENTITIES['materialize']:first}};newreg=copy.deepcopy(oldreg);newreg['experiments'][release.IDENTITIES['compare']]=second
  oldref=put('old/registration',oldreg);newref=put('new/registration',newreg);original={'source':A,'registration':oldref,'sources':{'path':'old/source'},'phase_contract':{'path':'old/phase'}}
  phase=put('new/phase',{'qualified':'phase'});sources=put('new/source',{'qualified':'source'});current={'source':B,'registration':newref,'sources':sources,'phase_contract':phase};prior={'accepted':{'qualified':'accepted'},'wait':{'qualified':'wait'}}
  rows=sorted([{'path':newref['path'],'sha256':newref['sha256'],'role':'comparison-registration'},{'path':charter['path'],'sha256':charter['sha256'],'role':'comparison-charter'}],key=lambda x:x['path'])
  evolution={'schema_version':1,'kind':'cold-proof-additive-registration-evolution-v1','parent_source':A,'original_registration':oldref,'current_registration':newref,'accepted':prior['accepted'],'wait':prior['wait'],'additions':rows};evref=put('new/evolution',evolution);prior['evolution']=evref
  git={(A,oldref['path']):files[oldref['path']],**{(B,p):v for p,v in files.items()}};diff=[('A',r['path']) for r in rows]+[('A',evref['path'])]
  state={'files':files,'git':git,'diff':diff,'head':B,'parents':B+' '+A,'evolution':evolution,'current':current,'original':original,'experiment':second,'material':material,'prior':prior,'newreg':newreg}
  mutate(state)
  def deref(root,reference):
   data=files[reference['path']];release.require(sha(data)==reference['sha256'],'fixture hash differs');return json.loads(data)
  def command(args,**kwargs):
   if args[1]=='rev-parse':return state['head']+'\n'
   if args[1]=='rev-list':return state['parents']+'\n'
   if args[1]=='show':commit,path=args[2].split(':',1);return git[(commit,path)]
   if args[1]=='diff-tree':return ''.join(status+'\0'+path+'\0' for status,path in diff).encode()
   raise AssertionError(args)
  previous={n:getattr(release,n) for n in ('deref','body','subprocess')};release.deref=deref;release.body=lambda root,path:files[path];release.subprocess=types.SimpleNamespace(check_output=command)
  try:return release._evolution_tree(None,current,original,second,material,prior)
  finally:
   for n,v in previous.items():setattr(release,n,v)
 def test_exact_minimal_additions(self):self.assertEqual(self.exercise()['addition_count'],2)
 def test_extra_source_runtime_old_data_or_unknown_addition_refused(self):
  for path in ('tradingagents/model.py','runtime.json','old/input.json','new/arbitrary.json'):
   with self.subTest(path=path),self.assertRaises(ValueError):self.exercise(lambda s:s['diff'].append(('A',path)))
 def test_existing_modification_deletion_rename_refused(self):
  for status in ('M','D','R100'):
   with self.subTest(status=status),self.assertRaises(ValueError):self.exercise(lambda s:s['diff'].__setitem__(0,(status,s['diff'][0][1])))
 def test_wrong_parent_merge_or_unchanged_commit_refused(self):
  for mutate in (lambda s:s.update(parents=B+' '+'c'*40),lambda s:s.update(parents=B+' '+A+' '+'c'*40),lambda s:s.update(head=A)):
   with self.assertRaises(ValueError):self.exercise(mutate)
 def test_original_registration_and_added_body_git_mismatch(self):
  for commit,path in ((A,'old/registration'),(B,'new/charter'),(B,'new/evolution')):
   with self.subTest(commit=commit,path=path),self.assertRaises(ValueError):self.exercise(lambda s:s['git'].__setitem__((commit,path),b'changed'))
 def test_self_hash_or_rechained_arbitrary_addition_refused(self):
  def change(s):
   e=s['evolution'];e['additions'].append({'path':'new/evolution','sha256':'x'*64,'role':'emitted-input'});data=json.dumps(e,sort_keys=True,separators=(',',':')).encode();s['files']['new/evolution']=data;s['git'][(B,'new/evolution')]=data;s['prior']['evolution'].update(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
  with self.assertRaises(ValueError):self.exercise(change)
if __name__=='__main__':unittest.main(verbosity=2)
