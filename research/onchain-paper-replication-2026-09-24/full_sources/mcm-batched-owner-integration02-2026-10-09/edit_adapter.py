from pathlib import Path
H=Path(__file__).resolve().parent;p=H/'compact_mcm_batched.py';s=p.read_text()
s=s.replace('Candidate local-retention route. No registration, empirical or offload admission.','Selected local/typed-offload route. No registration or empirical admission.')
s=s.replace("FORMAT = 'ordered-mcm-batch-closure-v1'","FORMAT = 'ordered-mcm-batch-closure-v2'")
a=s.index("BASE = ");b=s.index('require = io._require',a)
s=s[:a]+"PACKAGE = 'tradingagents.research.onchain_replication'\nMODULES = {'driver':'batched_driver','journal':'batched_journal','executor':'batched_pair_executor'}\n"+s[b:]
s=s.replace("policy['schema_version'] == 3","policy['schema_version'] == 4")
s=s.replace("'max_checkpoint_bytes'}, 'batched bounds schema'","'max_checkpoint_bytes','retention','max_spool_bytes','max_offload_metadata_bytes','max_offload_entries'}, 'batched bounds schema'")
s=s.replace("    for k in ('batch_cells'","    require(b['retention'] in ('local-v2','typed-recover-before-retire-v2'),'explicit batched retention route required')\n    require(type(b['max_spool_bytes']) is int and b['max_spool_bytes'] >= 4*pairs and type(b['max_offload_metadata_bytes']) is int and 0 < b['max_offload_metadata_bytes'] < 2**63 and type(b['max_offload_entries']) is int and 0 < b['max_offload_entries'] <= 4000000,'explicit spool/metadata bounds required')\n    for k in ('batch_cells'")
a=s.index('def _modules(');b=s.index('@contextmanager',a)
s=s[:a]+'''def _modules(root, admission=None):
    import importlib
    result={name:importlib.import_module(PACKAGE+'.'+module) for name,module in MODULES.items()}
    # ONE packaged journal class is shared with the exact typed semantics helper.
    if admission is not None:
        names=tuple(MODULES.values())+('compact_mcm_batched','registered_offload','batched_offload_semantics','typed_payload_policy','typed_payload_operations')
        for name in names:
            module=importlib.import_module(PACKAGE+'.'+name)
            relative='tradingagents/research/onchain_replication/'+name+'.py'
            require(Path(module.__file__).resolve()==root/relative and admission.experiment['source_files'].get(relative)==file_hash(root/relative),'batched installed source not registered/current')
    return result


'''+s[b:]
a=s.index('def _checkpoint_inventory(');b=s.index('def _token_file',a)
s=s[:a]+'''def _checkpoint_inventory(root, *, max_entries=65536):
    """Typed complete tree, including empty dirs; bounded opaque-body hashing."""
    require(root.is_dir() and root.resolve()==root,'inventory root redirected')
    digest=hashlib.sha256();files=total=directories=entries=0
    def visit(path):
        nonlocal files,total,directories,entries
        entries+=1;require(entries<=max_entries,'inventory entry ceiling exceeded')
        st=path.lstat();relative=str(path.relative_to(root))
        require(not stat.S_ISLNK(st.st_mode),'inventory symlink refused')
        row={'name':relative,'identity':list(io._signature(st))}
        if stat.S_ISDIR(st.st_mode):
            row['type']='directory';directories+=1;digest.update(io._json(row))
            with os.scandir(path) as scan:
                names=[]
                for entry in scan:
                    require(len(names)<max_entries,'directory entry ceiling exceeded');names.append(entry.name)
            for name in sorted(names):visit(path/name)
        else:
            require(stat.S_ISREG(st.st_mode) and st.st_nlink==1,'inventory special/link refused')
            body_hash=hashlib.sha256();child=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
            with os.fdopen(child,'rb') as stream:
                require(io._signature(os.fstat(stream.fileno()))==io._signature(st),'inventory opened inode differs')
                for block in iter(lambda:stream.read(262144),b''):body_hash.update(block)
                require(io._signature(os.fstat(stream.fileno()))==io._signature(st),'inventory opened body changed')
            row.update(type='regular',sha256=body_hash.hexdigest());digest.update(io._json(row));files+=1;total+=st.st_size
        require(io._signature(path.lstat())==io._signature(st),'inventory changed during hash')
    visit(root)
    return {'files':files,'directories':directories,'entries':entries,'bytes':total,'sha256':digest.hexdigest()}


def _children(root, expected):
    require(root.resolve()==root and root.is_dir(),'child inventory root redirected')
    expected=set(expected);found=set()
    with os.scandir(root) as scan:
        for entry in scan:
            require(entry.name in expected and entry.name not in found,'unexpected batched child')
            st=entry.stat(follow_symlinks=False)
            require(stat.S_ISREG(st.st_mode) and st.st_nlink==1,'batched child type differs')
            found.add(entry.name)
    require(found==expected,'missing batched child')


def _spool(root,binding, *, chunks=False):
    path=root/'stream/scores.f32';fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        st=os.fstat(fd);sig=io._signature(st)
        require(stat.S_ISREG(st.st_mode) and stat.S_IMODE(st.st_mode)==0o600 and st.st_nlink==1 and sig[:2]==tuple(binding['spool_inode']) and st.st_size==4*binding['cells'],'spool identity/extent differs')
        digest=hashlib.sha256();remaining=st.st_size
        while remaining:
            block=os.read(fd,min(4*binding['batch_cells'],remaining));require(block and len(block)%4==0,'short/misaligned spool')
            digest.update(block);remaining-=len(block)
            if chunks:yield block
        require(not os.read(fd,1) and digest.hexdigest()==binding['spool_sha256'],'spool bytes differ')
        require(sig==io._signature(os.fstat(fd))==io._signature(path.lstat()),'spool changed')
    finally:os.close(fd)


'''+s[b:]
s=s.replace("        for _ in _tokens(root,binding,modules):pass",'''        _children(root/'stream',{'closure-tokens.bin','scores.f32'})
        if binding['retention']=='local-v2':
            _children(root/'matching',(f'{i:08d}'+suffix for i in range(binding['batches']) for suffix in modules['driver'].SUFFIXES))
            for _ in _tokens(root,binding,modules):pass
        else:
            require(binding['retention']=='typed-recover-before-retire-v2','retention schema differs')
            _children(root/'matching',())
            external=binding['external']
            require(external['coverage']['owner']==contract['owner'] and external['coverage']['cells']==contract['pairs'] and external['coverage']['batches']==binding['batches'],'external owner/full coverage differs')
            work=Path(external['directory'])
            require(_checkpoint_inventory(work,max_entries=external['max_entries'])==external['inventory'],'anchored external metadata changed')
            require(json.loads((work/'final/accepted-coverage.json').read_bytes())==external['coverage'],'actual final recovery receipt differs')
            # Original token file is preserved although source files retired.
            token_fd,token_sig=_token_file(root,binding)
            try:
                digest=hashlib.sha256()
                for i in range(binding['batches']):
                    token=os.read(token_fd,168);require(len(token)==168,'short original tokens');digest.update(token)
                    record=json.loads((work/f'preserve/{i:08d}/offload.json').read_bytes())
                    require(record['binding']['source_tokens']==token.hex() and record['batch']==i,'anchored original source tokens differ')
                require(digest.hexdigest()==binding['tokens_sha256'] and token_sig==io._signature(os.fstat(token_fd))==io._signature((root/'stream/closure-tokens.bin').lstat()),'original tokens changed')
            finally:os.close(token_fd)
        for _ in _spool(root,binding):pass''')
a=s.index('    modules=_modules(producer.ROOT);binding=',s.index('def output_chunks'));b=s.index('\n\ndef _compute',a)
s=s[:a]+"    binding=args['contract']['batched']\n    yield from _spool(Path(args['stage_root']),binding,chunks=True)\n"+s[b:]
s=s.replace("    token_pin=io._signature(os.fstat(fd))[:2];token_hash=hashlib.sha256();seen=0",'''    token_pin=io._signature(os.fstat(fd))[:2];token_hash=hashlib.sha256();seen=0
    spool_fd=os.open(stream/'scores.f32',os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    spool_pin=io._signature(os.fstat(spool_fd))[:2];spool_hash=hashlib.sha256()
    external=None;post_batch=final_batches=None
    if b['retention']=='typed-recover-before-retire-v2':
        from . import registered_offload as offload
        offload._selected(target.owner,stage)
        work=target.owner.bound._run.admission.root/'research_artifacts/onchain_batched_offload'/target.owner.identity/stage.name
        durable_mkdir(work.parent);work.mkdir();(work/'preserve').mkdir()
        anchors=bytearray(((start['cells']+b['batch_cells']-1)//b['batch_cells'])*32)
        def post_batch(j,batch,token,original):
            boundary();require(type(j) is modules['journal'].BatchJournal,'shared actual journal class differs')
            record=offload.preserve_and_retire(target.owner,stage,journal=j,batch=batch,tokens=token,work=work/f'preserve/{batch:08d}')
            encoded=offload.typed._read(work/f'preserve/{batch:08d}/offload.json')
            require(json.loads(encoded)==record,'actual offload receipt differs')
            anchors[batch*32:(batch+1)*32]=hashlib.sha256(encoded).digest()
            boundary()
        def consume(batch,rows):
            with np.errstate(over='raise',invalid='raise'):
                expected=np.asarray([row[2] for row in rows],dtype='<f8').astype('<f4').tobytes()
            require(os.pread(spool_fd,len(expected),4*rows[0][0])==expected,'fresh recovered f64/cast differs from original spool')
        def final_batches(j,tokens,batch_count,original):
            nonlocal external
            boundary();os.fsync(spool_fd)
            records=((work/f'preserve/{i:08d}/offload.json',bytes(anchors[i*32:(i+1)*32]).hex()) for i in range(batch_count))
            coverage=offload.finalize(target.owner,stage,records=records,batch_count=batch_count,journal=j,work=work/'final',consume=consume)
            inventory=_checkpoint_inventory(work,max_entries=b['max_offload_entries'])
            require(inventory['bytes']<=b['max_offload_metadata_bytes'],'offload retained metadata allowance exceeded')
            external={'directory':str(work),'coverage':coverage,'inventory':inventory,'max_entries':b['max_offload_entries']}
            boundary();require(_checkpoint_inventory(work,max_entries=b['max_offload_entries'])==inventory,'external closure changed after final boundary')''')
s=s.replace("        seen+=len(payload)//4",'''        view=memoryview(payload)
        while view:
            written=os.write(spool_fd,view);require(written>0,'short spool write');view=view[written:]
        spool_hash.update(payload);seen+=len(payload)//4
        require(4*seen<=b['max_spool_bytes'],'spool reservation exceeded')''')
s=s.replace("max_closure_token_bytes=b['max_closure_token_bytes'])","max_closure_token_bytes=b['max_closure_token_bytes'],post_batch=post_batch,final_batches=final_batches)")
s=s.replace("        require(io._signature(os.fstat(fd))[:2]==token_pin,'token descriptor replaced')","        os.fsync(spool_fd)\n        require(io._signature(os.fstat(fd))[:2]==token_pin and io._signature(os.fstat(spool_fd))[:2]==spool_pin,'token/spool descriptor replaced')")
s=s.replace("io._cleanup((lambda:os.close(fd),journal.close) if not journal.closed else (lambda:os.close(fd),))","io._cleanup((lambda:os.close(fd),lambda:os.close(spool_fd),journal.close) if not journal.closed else (lambda:os.close(fd),lambda:os.close(spool_fd)))")
s=s.replace("return {'format':FORMAT,'rows'","return {'retention':b['retention'],'external':external,'spool_inode':list(spool_pin),'spool_sha256':spool_hash.hexdigest(),'format':FORMAT,'rows'")
s=s.replace("b['max_checkpoint_bytes']+4*io.META_LIMIT<=stage.reservation","b['max_checkpoint_bytes']+b['max_spool_bytes']+b['max_offload_metadata_bytes']+4*io.META_LIMIT<=stage.reservation")
p.write_text(s)
p=H/'compact_mcm.py';s=p.read_text().replace("policy['schema_version'] in (1,2,3)","policy['schema_version'] in (1,2,4)");p.write_text(s)
