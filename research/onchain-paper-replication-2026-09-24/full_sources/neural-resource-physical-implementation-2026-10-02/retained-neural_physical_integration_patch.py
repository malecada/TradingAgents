from pathlib import Path
p=Path('tradingagents/research/onchain_replication/job.py');s=p.read_text()
s=s.replace("    return [sys.executable, '-B', '-m', MODULE, '--mode', mode, '--root', str(Path(args.root).resolve()),\n            '--registration', args.registration, '--experiment', args.experiment, '--source', args.source]", "    command=[sys.executable, '-B', '-m', MODULE, '--mode', mode, '--root', str(Path(args.root).resolve()),\n            '--registration', args.registration, '--experiment', args.experiment, '--source', args.source]\n    if getattr(args,'physical_anchor',None):command+=['--physical-anchor',args.physical_anchor]\n    return command")
s=s.replace("scope=Scope.open(args.root,args.experiment,args.source,policy)", "scope=Scope.open(args.root,args.experiment,args.source,policy,original_anchor=getattr(args,'physical_anchor',None))")
s=s.replace("launch_record=json.loads((_base(args)/'launch.json').read_bytes())", "launch_record=scope.read_metadata(_base(args)/'launch.json')")
start=s.index("    with metadata_scope(scope):",s.index('def launch(args):'));end=s.index('\n\ndef monitor(args):',start)
old=s[start:end]
new="    if scope is not None:args.physical_anchor=scope.anchor_hash\n    primary=None\n    try:\n"+'\n'.join('    '+line for line in old.splitlines())+"\n    except BaseException as error:primary=error;raise\n    finally:\n        if scope is not None:\n            try:scope.close_authority()\n            except BaseException as error:\n                if primary is not None:primary.add_note('physical authority shutdown: '+repr(error))\n                else:raise\n"
s=s[:start]+new+s[end:]
a=s.index("    anchor=_base(args)/'physical-anchor.json'",s.index('def reconcile(args):'));b=s.index('\n\ndef _reconcile(args):',a)
s=s[:a]+"    if getattr(args,'physical_anchor',None) or os.path.lexists(_base(args)/'physical-anchor.json'):\n        raise ValueError('physical external reconciliation lacks original live parent scope; no disk authority fallback')\n    return _reconcile(args)\n"+s[b:]
s=s.replace("    parser.add_argument('--nonce')", "    parser.add_argument('--nonce')\n    parser.add_argument('--physical-anchor')")
p.write_text(s)
p=Path('tradingagents/research/lifecycle.py');s=p.read_text();s=s.replace('            run.directory.mkdir(exist_ok=False)', '''            scope=current_metadata_scope()
            if scope is None:run.directory.mkdir(exist_ok=False)
            else:
                if scope.root!=admitted.root or scope.anchor['experiment']!=experiment or scope.anchor['source']!=source:
                    raise ValueError("physical lifecycle original run authority differs")
                scope.birth('lifecycle')''');p.write_text(s)
p=Path('tradingagents/research/onchain_replication/neural_resource.py');s=p.read_text();s=s.replace('from ..lifecycle import ResearchRun, _immutable','from ..lifecycle import ResearchRun, _immutable, current_metadata_scope')
s=s.replace("    base=job._base(args);owner=", "    scope=current_metadata_scope()\n    if 'physical_policy' in policy:\n        if scope is None or scope.root!=root or scope.anchor['experiment']!=args.experiment or scope.anchor['source']!=args.source or scope.policy!=policy['physical_policy']:\n            raise ValueError('neural original physical authority required')\n        scope.check();args.physical_anchor=scope.anchor_hash\n    base=job._base(args);owner=")
s=s.replace("    durable_mkdir(directory.parent);directory.mkdir(exist_ok=False);sync_directory(directory.parent)", "    scope=current_metadata_scope()\n    if scope is None:\n        durable_mkdir(directory.parent);directory.mkdir(exist_ok=False);sync_directory(directory.parent)\n    elif scope.birth('producer')!=directory:raise ValueError('neural original producer birth differs')")
p.write_text(s)
p=Path('tradingagents/research/onchain_replication/resources.py');s=p.read_text()
s=s.replace('def _child(receipt,cpus,lease_seconds,command,physical=False):','def _child(receipt,cpus,lease_seconds,command,physical=False,physical_context=None):')
a=s.index("    live=json.loads((receipt/'live.json').read_bytes());owner=live['owner_identity'];policy=live['physical_policy']",s.index('def _child'));b=s.index('    with metadata_scope(scope):return',a)
s=s[:a]+'''    if not isinstance(physical_context,str) or len(physical_context)>8192:raise ValueError('physical original child context missing/bounded extent differs')
    context=json.loads(physical_context);policy=context['policy']
    scope=Scope.open(Path.cwd(),context['experiment'],context['source'],policy,original_anchor=context['anchor'])
    live=scope.read_metadata(receipt/'live.json')
    if live['physical_policy']!=policy:raise ValueError('physical child policy differs from original context')
    verify_file_limit(policy['max_file_bytes'],resource.getrlimit(resource.RLIMIT_FSIZE))
''' + s[b:]
s=s.replace("            args.insert(position,'--physical')", "            context={'experiment':physical_scope.anchor['experiment'],'source':physical_scope.anchor['source'],\n                     'policy':physical_policy,'anchor':physical_scope.anchor_hash}\n            args[position:position]=['--physical','--physical-context',json.dumps(context,sort_keys=True)]")
s=s.replace("    parser.add_argument('--physical', action='store_true')", "    parser.add_argument('--physical', action='store_true')\n    parser.add_argument('--physical-context')")
s=s.replace('command, arguments.physical))','command, arguments.physical, arguments.physical_context))')
p.write_text(s)
p=Path('tradingagents/research/onchain_replication/neural_physical.py');s=p.read_text();pos=s.index('    def close_authority(self):')
s=s[:pos]+'''    def read_metadata(self,path):
        path=Path(path)
        if path.resolve()!=path or not any(path.is_relative_to(p) and path!=p for p in self.roots.values()):raise ValueError('physical metadata outside original roots')
        with self._locked():
            self._scan(tail=self.tail)
            value=json.loads(_read(path,self.policy['max_json_bytes']))
            self._scan(tail=self.tail)
            return value

''' + s[pos:];p.write_text(s)
p=Path('tests/research/onchain_replication/test_neural_physical.py');s=p.read_text().replace("assert scope.check()['files']>=9", "assert scope.check()['files']==8")
p.write_text(s)
