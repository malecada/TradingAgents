"""Actual old serializer/paging RED vs complete new hierarchy; metadata only."""
import ast,copy,hashlib,json,pathlib,sys,unittest
D=pathlib.Path(__file__).resolve().parent;OLD=D.parent/'original-import-native-refusal-worker-preparation02-2026-10-03';sys.path.insert(0,str(D));import refusal_inventory03 as new
class Tests(unittest.TestCase):
 def test_actual_old_index_exceeds8k_new_retains_all_members(self):
  tree=ast.parse((OLD/'refusal_outer01.py').read_text());run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run');save=next(n for n in run.body if isinstance(n,ast.FunctionDef) and n.name=='save');guard=next(n for n in run.body if isinstance(n,ast.Try) and any('index = inventory(root)' in ast.unparse(v) for v in n.finalbody));block=next(n for n in guard.finalbody if isinstance(n,ast.Try) and n.body and 'index = inventory(root)' in ast.unparse(n.body[0]))
  root=pathlib.Path('/home/malecada/master_thesis/TradingAgents-audit-fixes/research/onchain-paper-replication-2026-09-24/full_sources/original-import-native-successor-preparation04-2026-10-03/capsule02');values={'schema_version':1,'root':str(root),'root_allocated':4096,'tail_exclusion':'This index and subsequently written outer terminal/readback are hashed and fully counted by final post-tail storage observation; no recursive self-hash claim.','members':[{'path':'research_artifacts/synthetic-closed-metadata/'+str(i).zfill(5)+'.json','bytes':1,'allocated':4096,'kind':'file','sha256':'0'*64} for i in range(2311)]};saved={}
  class Sink:
   def _native_receipt(self,outer,name,value):saved[name]=new.encode(value)
  env={'root':root,'outer':root/'fixture_outer/synthetic-case','inventory':lambda root:copy.deepcopy(values),'json':json,'require':new.require,'resources':Sink(),'hashlib':hashlib,'body':lambda root,path:saved[pathlib.Path(path).name]};exec(compile(ast.Module(body=[save],type_ignores=[]),'actual predecessor save','exec'),env)
  with self.assertRaisesRegex(ValueError,'exceeds8KiB'):exec(compile(ast.Module(body=block.body,type_ignores=[]),'actual predecessor paging','exec'),env)
  self.assertEqual(len(env['references']),71);self.assertEqual(len(new.encode(env['index']|{'pages':env['references']})),8240)
  plan=new.prepare(values,'synthetic-case');self.assertEqual(plan[-1][1]['member_count'],2311);self.assertTrue(all(len(new.encode(v))<=8192 for n,v in plan))
if __name__=='__main__':unittest.main(verbosity=2)
