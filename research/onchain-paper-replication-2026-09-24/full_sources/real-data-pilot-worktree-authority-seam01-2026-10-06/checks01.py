"""Empty Git topology fixtures; no admission/run/Owner authority is minted."""
import ast,hashlib,json,os,subprocess,sys,types,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT))
from tradingagents.research import admission

def extract(path,names,namespace):
    tree=ast.parse(path.read_text());nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in names]
    assert {n.name for n in nodes}==set(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),namespace)

def require(value,message):
    if not value:raise ValueError(message)

job=types.ModuleType('tradingagents.research.onchain_replication.job')
job.Path=Path;job.subprocess=subprocess
extract(ROOT/'tradingagents/research/onchain_replication/job.py',['workspace_binding'],job.__dict__)
sys.modules[job.__name__]=job
ns={'__package__':'tradingagents.research.onchain_replication','Path':Path,'require':require,'hashlib':hashlib,'json':json,'FILE_MAX':4*1024**2}
extract(HERE/'real_pilot_import_caller.py',['_read','_source_authority_root'],ns)
check=ns['_source_authority_root']

class Topology(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.area=HERE/'empty-git-fixtures01';cls.area.mkdir()
        cls.repo=cls.area/'directory';cls.repo.mkdir()
        cls.worktree=cls.area/'worktree'
        env=dict(os.environ,GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1',GIT_TERMINAL_PROMPT='0')
        def git(*args):return subprocess.check_output(['git',*args],cwd=cls.repo,env=env,stderr=subprocess.STDOUT,text=True)
        git('init','--quiet','--template=')
        git('-c','user.name=Offline Fixture','-c','user.email=fixture@example.invalid','commit','--quiet','--allow-empty','--no-gpg-sign','-m','Empty topology fixture')
        git('worktree','add','--quiet','--detach',str(cls.worktree),'HEAD')
        cls.actual=job.workspace_binding(cls.worktree)
        cls.observation={'directory_marker':(cls.repo/'.git').is_dir(),'worktree_marker':(cls.worktree/'.git').is_file(),'worktree_layout':cls.actual,'empty_commit_tree':git('ls-tree','HEAD').strip()}
        assert cls.observation['empty_commit_tree']==''
    def record(self,value=None):
        value=self.actual if value is None else value
        raw=json.dumps(value,sort_keys=True).encode();path=self.worktree/'execution-workspace.json';path.write_bytes(raw)
        return types.SimpleNamespace(root=self.worktree,inputs={'execution_workspace':{'path':path.name,'sha256':hashlib.sha256(raw).hexdigest()}})
    def test_directory_repository_legacy_and_real_worktree(self):
        self.assertTrue(check(types.SimpleNamespace(root=self.repo,inputs={})))
        self.assertTrue(check(self.record()))
    def test_wrong_root_common_dir_and_missing_role_refused(self):
        for field,value in [('root',str(self.repo)),('git_common',str(self.worktree/'.git')),('ledger',str(self.repo/'research_runs')),('artifacts',str(self.repo/'research_artifacts'))]:
            with self.subTest(field=field):
                with self.assertRaises(ValueError):check(self.record(self.actual|{field:value}))
        with self.assertRaises(ValueError):check(types.SimpleNamespace(root=self.worktree,inputs={}))
        sub=self.worktree/'wrong-subroot';sub.mkdir()
        with self.assertRaises(ValueError):check(types.SimpleNamespace(root=sub,inputs={}))
    def test_changed_hash_and_redirected_marker_refused(self):
        ad=self.record();(self.worktree/'execution-workspace.json').write_bytes(b'{}')
        with self.assertRaises(ValueError):check(ad)
        wrong=self.area/'redirected';wrong.mkdir();(wrong/'.git').symlink_to(self.worktree/'.git')
        with self.assertRaises(ValueError):check(types.SimpleNamespace(root=wrong,inputs={}))
    def test_inverse_preserves_all_other_source_bytes(self):
        change=json.loads((HERE/'CHANGE01.json').read_bytes());body=(HERE/'real_pilot_import_caller.py').read_text()
        self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),change['after_sha256'])
        for item in reversed(change['literal_edits']):
            self.assertEqual(body.count(item['after']),1);body=body.replace(item['after'],item['before'])
        self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),change['before_sha256'])
        self.assertEqual(body,(ROOT/change['source_path']).read_text())

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Topology))
    assert 'numpy' not in sys.modules and 'torch' not in sys.modules
    (HERE/'ACTUAL_FIXTURES01.json').write_text(json.dumps(Topology.observation,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
