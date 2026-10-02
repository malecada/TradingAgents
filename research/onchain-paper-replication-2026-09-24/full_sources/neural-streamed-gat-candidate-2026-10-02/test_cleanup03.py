"""Pure AST tests for cleanup admission; no numerical/module/job imports."""
import argparse
import ast
import copy
from pathlib import Path
import unittest

DECISION = None


class CleanupAdmission(unittest.TestCase):
    def envelope(self, code=5):
        props={'Result':'success','ExecMainStatus':'0','ControlGroup':'',
               'ActiveState':'inactive','SubState':'dead'}
        result={'cleanup_verified':True,'cleanup_stop_returncode':code,
                'phase':'complete','child_exit_code':0,
                'unit_properties':props.copy(),'cleanup_unit_properties':props.copy(),
                'cgroup':'/sys/fs/cgroup/test-closed-unit','monitor_pid':900001,
                'cpu_thread_readback':{'900002':[0,1]}}
        proof={'cpu_ready':{'pid':900002},'child_exit':{'workload_pid':900003,'exit_code':0}}
        return result,proof

    def decision(self, result, proof, exists=lambda path:False):
        try:return DECISION(result,proof,exists=exists)
        except (KeyError,TypeError,ValueError):return False

    def test_normal_stop(self):
        self.assertTrue(self.decision(*self.envelope(0)))

    def test_collected_success_stop5(self):
        self.assertTrue(self.decision(*self.envelope()))

    def test_live_cgroup_refused(self):
        self.assertFalse(self.decision(*self.envelope(),exists=lambda p:str(p).startswith('/sys/fs/cgroup')))

    def test_live_original_pid_refused(self):
        self.assertFalse(self.decision(*self.envelope(),exists=lambda p:str(p)=='/proc/900003'))

    def test_unverified_cleanup_refused(self):
        result,proof=self.envelope();result['cleanup_verified']=False
        self.assertFalse(self.decision(result,proof))

    def test_failed_native_terminal_refused(self):
        result,proof=self.envelope();result['cleanup_unit_properties']['Result']='exit-code'
        self.assertFalse(self.decision(result,proof))

    def test_missing_original_process_proof_refused(self):
        result,proof=self.envelope();del proof['child_exit']['workload_pid']
        self.assertFalse(self.decision(result,proof))

    def test_other_stop_code_refused(self):
        self.assertFalse(self.decision(*self.envelope(1)))


def main():
    global DECISION
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True)
    args=parser.parse_args();tree=ast.parse(args.source.read_text())
    selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_cleanup_complete']
    namespace={'Path':Path}
    if selected:
        exec(compile(ast.Module(body=selected,type_ignores=[]),str(args.source),'exec'),namespace)
        DECISION=namespace['_cleanup_complete']
    else:
        # Execute the actual old admission expression, not a successful stub.
        old=next(n for n in ast.walk(tree) if isinstance(n,ast.Call)
            and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)==2
            and isinstance(n.args[1],ast.Constant) and n.args[1].value=='descendant cleanup unverified')
        expression=compile(ast.Expression(old.args[0]),str(args.source),'eval')
        DECISION=lambda result,proof,exists=None:bool(eval(expression,{}, {'result':result}))
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(CleanupAdmission)
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1


if __name__=='__main__':
    raise SystemExit(main())
