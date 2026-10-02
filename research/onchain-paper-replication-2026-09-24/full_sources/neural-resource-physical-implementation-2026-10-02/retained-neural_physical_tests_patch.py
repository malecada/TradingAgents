from pathlib import Path
p=Path('tests/research/onchain_replication/test_neural_physical.py');s=p.read_text()
pos=s.index('\ndef fresh(')
s=s[:pos]+'''
@pytest.fixture(autouse=True)
def close_test_authorities(monkeypatch):
    n=module();original=n.Scope.create;created=[]
    def create(cls,*args,**kwargs):
        result=original(*args,**kwargs);created.append(result);return result
    monkeypatch.setattr(n.Scope,'create',classmethod(create))
    yield
    for scope in created:
        try:scope.close_authority()
        except RuntimeError:pass  # Expected refusal tests retain failure in assertion/log.

''' + s[pos:]
s=s.replace("n=module();base=tmp_path/n.PREFIX/'runs'/'invented';base.mkdir(parents=True)\n    return", "n=module();base=tmp_path/n.PREFIX/'runs'/'invented';base.mkdir(parents=True)\n    (tmp_path/'research_runs').mkdir();(tmp_path/n.PREFIX/'sources').mkdir()\n    return",1)
s=s.replace("life=tmp_path/'research_runs/invented';life.mkdir(parents=True);(life/'outputs').mkdir()", "life=scope.birth('lifecycle');(life/'outputs').mkdir()")
s=s.replace("producer=tmp_path/n.PREFIX/'sources/invented';producer.mkdir(parents=True)", "producer=scope.birth('producer')")
s=s.replace("life=tmp_path/'research_runs/invented';life.mkdir(parents=True)", "life=scope.birth('lifecycle')")
s=s.replace("life=scope.roots['lifecycle'];life.mkdir(parents=True)", "life=scope.birth('lifecycle')")
s=s.replace("life=scope.roots['lifecycle'];life.parent.mkdir()", "life=scope.roots['lifecycle']")
s=s.replace("output=tmp_path/'research_runs/invented/outputs/summary.json';output.parent.mkdir(parents=True)", "output=scope.birth('lifecycle')/'outputs/summary.json';output.parent.mkdir()")
s=s.replace("b'x'*60000", "b'x'*61000")
s=s.replace("scope=Scope.open(root,'invented','a'*40,policy)", "scope=Scope.open(root,'invented','a'*40,policy,original_anchor=sys.argv[4])")
s=s.replace("json.dumps(limits()),prefix])", "json.dumps(limits()),prefix,scope.anchor_hash])")
s=s.replace("registration='synthetic',owner_pid=1,nonce='invented')", "registration='synthetic',owner_pid=1,nonce='invented',physical_anchor=scope.anchor_hash)")
s=s.replace("run.directory.mkdir(parents=True);(run.directory/'outputs').mkdir()", "scope.birth('lifecycle');(run.directory/'outputs').mkdir()")
s=s.replace("base=job._base(args);scope=n.Scope.create", "base=job._base(args);(tmp_path/'research_runs').mkdir(exist_ok=True);(tmp_path/n.PREFIX/'sources').mkdir(exist_ok=True)\n    scope=n.Scope.create")
s=s.replace("    scope.immutable(base/'launch.json',{'nonce':'synthetic'", "    args.physical_anchor=scope.anchor_hash\n    scope.immutable(base/'launch.json',{'nonce':'synthetic'")
p.write_text(s)
