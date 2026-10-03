"""Actual extracted control-flow; synthetic callbacks, never genuine authority."""
import ast, threading, unittest
from pathlib import Path
C=Path('/home/malecada/master_thesis/onchain-fixture-isolation/neural-cold-proof-native-20261003-02/source/tradingagents/research/onchain_replication')
class Checks(unittest.TestCase):
    def test_receipt_check_two_verifications_one_full(self):
        t=ast.parse((C/'compact_terminal.py').read_bytes())
        cls=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='Receipt')
        ns={'freeze':lambda x:x,'require':lambda x,m: self.assertTrue(x,m)}
        exec(compile(ast.Module(body=[cls],type_ignores=[]),'actual-Receipt','exec'),ns)
        events=[]
        def verify(**kw):events.append(('verify',kw.get('full',False)))
        def live():events.append(('guard',));verify()
        class Owner:_transition=threading.Lock()
        receipt=ns['Receipt']({},live,verify,Owner())
        receipt.check();self.assertEqual(events,[('guard',),('verify',False),('verify',True)])
    def test_native_lease_two_terminal_verifications(self):
        t=ast.parse((C/'compact_native_features.py').read_bytes())
        prep=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='prepare')
        lease=next(n for n in prep.body if isinstance(n,ast.FunctionDef) and n.name=='lease')
        events=[]
        class Terminal:
            def lease(self):events.extend(['guard','verify'])
            def _verify(self,*,full):self_full=full;events.append('verify');self_full is False
        ns={'terminal':Terminal(),'sources':lambda:events.append('dynamic-source-hashes')}
        exec(compile(ast.Module(body=[lease],type_ignores=[]),'actual-native-lease','exec'),ns)
        ns['lease']();self.assertEqual(events,['guard','verify','dynamic-source-hashes','verify'])
if __name__=='__main__':unittest.main(verbosity=2)
