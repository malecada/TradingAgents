from pathlib import Path
p=Path('tradingagents/research/onchain_replication/neural_physical.py');s=p.read_text()
a=s.index('class Scope:');b=s.index('    @contextmanager\n    def _locked',a)
s=s[:a]+'''class Scope:
    def __setattr__(self,name,value):
        if getattr(self,'_sealed',False) and name not in ('tail',):raise AttributeError('physical original authority is immutable')
        object.__setattr__(self,name,value)

    @classmethod
    def create(cls,root,experiment,source,policy,launcher):
        from .neural_authority import ParentAuthority
        root=Path(root).resolve();policy=validate(policy)
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',experiment) or not re.fullmatch('[0-9a-f]{40}',source):raise ValueError('physical job identity differs')
        roots={'control':root/PREFIX/'runs'/experiment,'lifecycle':root/'research_runs'/experiment,'producer':root/PREFIX/'sources'/experiment}
        if any(os.path.lexists(p) for k,p in roots.items() if k!='control'):raise ValueError('physical roots must be fresh')
        for path in roots.values():
            if path.resolve()!=path:raise ValueError('physical fresh root ancestor redirected')
        base=roots['control']
        if base.resolve()!=base or _identity(base)[0]!=root.stat().st_dev:raise ValueError('physical control ancestor/device differs')
        _write(base/'physical.lock',b'')
        original={'identities':{'control':_identity(base)},'claim_sha256':None,'receipts':{}}
        anchor_hash=None
        def handle(request):
            if request.get('anchor_sha256')!=anchor_hash:raise ValueError('physical original launch authority differs')
            op=request.get('op')
            if op=='get' and set(request)=={'op','anchor_sha256'}:return original
            if op=='birth' and set(request)=={'op','role','anchor_sha256'}:
                role=request['role']
                if role not in ('lifecycle','producer') or role in original['identities']:raise ValueError('physical original birth is exclusive')
                if role=='producer' and original['claim_sha256'] is None:raise ValueError('physical producer before claim birth')
                path=roots[role]
                if path.resolve()!=path or os.path.lexists(path):raise ValueError('physical original fresh birth redirected/replaced')
                if not path.parent.is_dir() or _identity(path.parent)[0]!=root.stat().st_dev:raise ValueError('physical root parent scaffold missing/device differs')
                path.mkdir(exist_ok=False);_sync(path.parent)
                identity=_identity(path);original['identities'][role]=identity
                name='physical-birth-'+role+'.json'
                data=_bounded_encode({'role':role,'identity':identity,'anchor_sha256':anchor_hash},policy['max_json_bytes'])
                _write(base/name,data);original['receipts'][name]=hashlib.sha256(data).hexdigest()
                return original
            if op=='claim' and set(request)=={'op','value','anchor_sha256'}:
                value=request['value']
                if original['claim_sha256'] is not None or 'lifecycle' not in original['identities']:raise ValueError('physical claim birth is exclusive')
                if value.get('experiment_id')!=experiment or value.get('source')!=source:raise ValueError('physical claim owner differs')
                life=roots['lifecycle']
                if _identity(life)!=original['identities']['lifecycle'] or life.resolve()!=life:raise ValueError('physical original lifecycle root replaced')
                data=_bounded_encode(value,policy['max_json_bytes'])
                _write(life/'claim.json',data);original['claim_sha256']=hashlib.sha256(data).hexdigest()
                return original
            raise ValueError('physical authority request schema differs')
        authority=ParentAuthority(policy['max_json_bytes'],handle)
        try:
            anchor={'schema_version':1,'root':str(root),'experiment':experiment,'source':source,'policy':policy,'launcher':launcher,
                    'roots':{k:str(p) for k,p in roots.items()},'control_identity':_identity(base),
                    'lock_identity':[(base/'physical.lock').stat().st_dev,(base/'physical.lock').stat().st_ino],
                    'parent_authority':authority.identity}
            data=_bounded_encode(anchor,policy['max_json_bytes']);anchor_hash=hashlib.sha256(data).hexdigest()
            _write(base/'physical-anchor.json',data)
            self=cls.open(root,experiment,source,policy,original_anchor=anchor_hash)
            object.__setattr__(self,'_server',authority)
            return self
        except BaseException as primary:
            try:authority.close()
            except BaseException as error:primary.add_note('physical authority close: '+repr(error))
            raise

    @classmethod
    def open(cls,root,experiment,source,policy,*,original_anchor=None):
        root=Path(root).resolve();base=root/PREFIX/'runs'/experiment
        policy=validate(policy)
        # Bounded type/extent admission is required even if supplied authority is missing.
        raw=_read(base/'physical-anchor.json',policy['max_json_bytes'])
        if not isinstance(original_anchor,str) or hashlib.sha256(raw).hexdigest()!=original_anchor:raise ValueError('physical original anchor capability required/differs')
        anchor=json.loads(raw)
        if anchor['root']!=str(root) or anchor['experiment']!=experiment or anchor['source']!=source or anchor['policy']!=policy:raise ValueError('physical anchor contract differs')
        expected={'control':str(base),'lifecycle':str(root/'research_runs'/experiment),'producer':str(root/PREFIX/'sources'/experiment)}
        if anchor['roots']!=expected or _identity(base)!=anchor['control_identity'] or base.resolve()!=base:raise ValueError('physical original control/root mapping differs')
        self=cls();self.root=root;self.base=base;self.anchor=anchor;self.anchor_hash=original_anchor;self.policy=dict(policy);self.roots={k:Path(v) for k,v in expected.items()};self.tail=False
        self.lock_identity=anchor['lock_identity'];self._server=None;self._sealed=True
        self._original()
        return self

    def _original(self,**value):
        from .neural_authority import request
        if hashlib.sha256(_encode(self.anchor)).hexdigest()!=self.anchor_hash:raise ValueError('physical in-process original authority changed')
        return request(self.anchor['parent_authority'],self.anchor_hash,value or {'op':'get'},self.policy['max_json_bytes'])

    def close_authority(self):
        if self._server is None:raise ValueError('physical scope does not own parent authority')
        self._server.close()

    def birth(self,role):
        if role not in ('lifecycle','producer'):raise ValueError('physical root role differs')
        with self._locked():
            self._scan(reserve=16384+self.policy['max_json_bytes'])
            self._original(op='birth',role=role)
            self._scan()
        return self.roots[role]

''' + s[b:]
s=s.replace("if os.fstat(fd).st_ino!=self.lock_identity", "if [os.fstat(fd).st_dev,os.fstat(fd).st_ino]!=self.lock_identity")
s=s.replace("fcntl.flock(fd,fcntl.LOCK_EX);yield", "fcntl.flock(fd,fcntl.LOCK_EX);self._original();yield;self._original()")
s=s.replace("    def _state(self):return json.loads(_read(self.base/'physical-state.json',self.policy['max_json_bytes']))", "    def _state(self):return self._original()")
s=s.replace("state=self._state();changed=False;allocated=logical=files=entries=0", "state=self._state();allocated=logical=files=entries=0\n        for name,expected in state['receipts'].items():\n            if _hash(self.base/name,self.policy['max_json_bytes'])!=expected:raise ValueError('physical original birth receipt changed')")
s=s.replace("if role not in state['identities']:state['identities'][role]=actual;changed=True", "if role not in state['identities']:raise ValueError('physical original birth required; unrecorded root')")
s=s.replace("if state['claim_sha256'] is None:state['claim_sha256']=identity;changed=True", "if state['claim_sha256'] is None:raise ValueError('physical original claim publication required')")
s=s.replace("        if changed:_write(self.base/'physical-state.json',_encode(state),replace=True)", "        if self._original()!=state:raise ValueError('physical original authority changed during scan')")
s=s.replace("            if replace:_write(path,data,replace=True)", "            if path==self.roots['lifecycle']/'claim.json':\n                if replace:raise ValueError('physical original claim cannot be replaced')\n                self._original(op='claim',value=value)\n            elif replace:_write(path,data,replace=True)")
p.write_text(s)
