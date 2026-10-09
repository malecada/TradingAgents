from pathlib import Path
import hashlib,json,difflib
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
BASE=ROOT/'tradingagents/research/onchain_replication'
s=(BASE/'compact_mcm_batched.py').read_text(); original=s
s=s.replace("policy['schema_version'] == 5","policy['schema_version'] in (5,6)")
s=s.replace("    b = policy['batched']\n", "    b = policy['batched']\n    grouped=policy['schema_version']==6\n",1)
s=s.replace("'max_offload_anchor_bytes','execution'}, 'batched bounds schema')", "'max_offload_anchor_bytes','execution'} | ({'group_batches'} if grouped else set()), 'batched bounds schema')")
s=s.replace("    require(b['retention'] in ('local-v2','typed-recover-before-retire-v2'),'explicit batched retention route required')", "    require(b['retention'] in (('typed-grouped-recover-before-retire-v1',) if grouped else ('local-v2','typed-recover-before-retire-v2')),'explicit batched retention route required')\n    if grouped:require(type(b['group_batches']) is int and b['group_batches']==16,'explicit sixteen batch groups required')")
s=s.replace("or count*32<=b['max_offload_anchor_bytes']", "or ((count+15)//16 if grouped else count)*32<=b['max_offload_anchor_bytes']")
s=s.replace('def _modules(root, admission=None):','def _modules(root, admission=None, *, grouped=False):')
s=s.replace("        for name in names:","        if grouped:names+=('grouped_offload','grouped_offload_semantics')\n        for name in names:")
s=s.replace("modules=_modules(owner.bound._run.admission.root,owner.bound._run.admission)","modules=_modules(owner.bound._run.admission.root,owner.bound._run.admission,grouped=policy['schema_version']==6)")
s=s.replace("        else:\n            require(binding['retention']=='typed-recover-before-retire-v2'", "        elif binding['retention']=='typed-grouped-recover-before-retire-v1':\n            _verify_grouped(root,contract,binding)\n        else:\n            require(binding['retention']=='typed-recover-before-retire-v2'",1)
needle="        def sink(ordinal,center,motif,payload):"
insert='''        elif b['retention']=='typed-grouped-recover-before-retire-v1':
            from . import grouped_offload as grouped_offload
            grouped_offload.original._selected(target.owner,stage)
            work=target.owner.bound._run.admission.root/'research_artifacts/onchain_batched_offload'/target.owner.identity/stage.name
            durable_mkdir(work.parent);work.mkdir();(work/'preserve').mkdir()
            batch_total=(start['cells']+b['batch_cells']-1)//b['batch_cells']
            group_total=(batch_total+15)//16
            anchors=bytearray(group_total*32);pending=[];groups=0;next_batch=0
            def flush_group(j):
                nonlocal groups
                require(0<len(pending)<=16 and groups<group_total,'finite group flush required')
                items=tuple(pending)
                record=grouped_offload.preserve_and_retire(target.owner,stage,journal=j,items=items,work=work/f'preserve/{groups:08d}')
                encoded=grouped_offload.typed._read(work/f'preserve/{groups:08d}/offload.json')
                require(json.loads(encoded)==record,'actual grouped receipt differs')
                anchors[groups*32:(groups+1)*32]=hashlib.sha256(encoded).digest()
                groups+=1;pending.clear()
            def post_batch(j,batch,token,original):
                nonlocal next_batch
                boundary();require(type(j) is modules['journal'].BatchJournal,'shared actual journal class differs')
                require(type(batch) is int and batch==next_batch<batch_total and type(token) is bytes and len(token)==168,'ordered grouped batch/token differs')
                pending.append((batch,token));next_batch+=1
                if len(pending)==16:flush_group(j)
                boundary()
            def final_batches(j,tokens,batch_count,original):
                nonlocal external
                boundary();os.fsync(spool_fd)
                require(batch_count==next_batch==batch_total,'group batch denominator differs')
                if pending:flush_group(j)
                require(groups==group_total,'group denominator differs')
                records=((work/f'preserve/{i:08d}/offload.json',bytes(anchors[i*32:(i+1)*32]).hex()) for i in range(groups))
                coverage=grouped_offload.finalize(target.owner,stage,records=records,group_count=groups,batch_count=batch_count,journal=j,work=work/'final',spool_fd=spool_fd)
                inventory=_checkpoint_inventory(work,max_entries=b['max_offload_entries'])
                require(inventory['bytes']<=b['max_offload_metadata_bytes'],'offload retained metadata allowance exceeded')
                external={'directory':str(work),'coverage':coverage,'inventory':inventory,'max_entries':b['max_offload_entries'],'group_batches':16,'group_anchors_sha256':anchors.hex()}
                boundary();require(_checkpoint_inventory(work,max_entries=b['max_offload_entries'])==inventory,'external closure changed after final boundary')
'''
s=s.replace(needle,insert+needle)
helper='''def _verify_grouped(root,contract,binding):
    from . import grouped_offload as offload
    _children(root/'matching',())
    external=binding['external'];coverage=external['coverage'];work=Path(external['directory'])
    groups=(binding['batches']+15)//16
    require(external['group_batches']==16 and coverage['format']=='registered-grouped-final-coverage-v1' and coverage['groups']==groups and coverage['owner']==contract['owner'] and coverage['stage']==root.name and coverage['cells']==binding['cells'] and coverage['batches']==binding['batches'],'grouped owner/full coverage differs')
    anchors=bytes.fromhex(external['group_anchors_sha256']);require(len(anchors)==32*groups,'group anchor extent differs')
    require(_checkpoint_inventory(work,max_entries=external['max_entries'])==external['inventory'],'anchored group inventory changed')
    require(json.loads(offload.typed._read(work/'final/accepted-coverage.json'))==coverage,'actual grouped final receipt differs')
    fd,sig=_token_file(root,binding)
    try:
        digest=hashlib.sha256();aggregate=hashlib.sha256();cursor=batch=0
        for group in range(groups):
            encoded=offload.typed._read(work/f'preserve/{group:08d}/offload.json');record=json.loads(encoded)
            require(hashlib.sha256(encoded).digest()==anchors[32*group:32*(group+1)],'group anchor changed')
            items=offload.semantic.from_binding(record['binding']);count=min(16,binding['batches']-batch)
            require(len(items)==count and record['format']=='registered-grouped-offload-v1' and record['first_batch']==batch and record['batches']==count and record['start']==cursor and record['stop']==min(binding['cells'],(batch+count)*binding['batch_cells']) and record['cells']==record['stop']-cursor and record['retired_files']==3*count,'group partition/range differs')
            require(record['binding']['root']==str(root/'matching') and record['binding']['root_pin']==binding['journal_inode'] and record['binding']['manifest_sha256']==offload.semantic.sha(offload.semantic.raw(record['manifest'])),'group source binding differs')
            for index,expected in items:
                token=os.read(fd,168);require(index==batch and len(token)==168 and token==expected,'original grouped token differs');digest.update(token);batch+=1
            parts=list(offload.typed.iter_history_parts(record['history'],binding=record['binding'],kind=offload.KIND))
            require(len(parts)==1 and parts[0]['receipt']==record['receipt'],'actual grouped preservation history differs')
            fresh_raw=offload.typed._read(work/f'final/{group:08d}/complete.json');fresh=json.loads(fresh_raw)
            require(fresh['format']=='registered-grouped-fresh-recovery-v1' and fresh['original_history']==record['history'] and fresh['source_binding']==record['binding'] and fresh['start']==cursor and fresh['stop']==record['stop'] and fresh['first_batch']==record['first_batch'] and fresh['batches']==count,'actual grouped recovery join differs')
            complete=offload.typed.check_history(fresh['history'],binding=record['binding'],kind=offload.KIND)
            require(complete['parts']==0 and complete['recovered_bytes']==record['manifest']['archive_bytes'],'fresh group recovered byte denominator differs')
            for _ in offload.typed.iter_history_parts(fresh['history'],binding=record['binding'],kind=offload.KIND):pass
            aggregate.update(hashlib.sha256(encoded).digest());aggregate.update(hashlib.sha256(fresh_raw).digest());cursor=record['stop']
        require(batch==binding['batches'] and cursor==binding['cells'] and not os.read(fd,1) and digest.hexdigest()==binding['tokens_sha256'] and aggregate.hexdigest()==coverage['original_and_fresh_history_aggregate_sha256'],'group full original denominator differs')
        require(sig==io._signature(os.fstat(fd))==io._signature((root/'stream/closure-tokens.bin').lstat()),'original group tokens changed')
        require(_checkpoint_inventory(work,max_entries=external['max_entries'])==external['inventory'],'group inventory changed during join')
    finally:io._release(lambda:os.close(fd))


'''
s=s.replace('def stage_content(stage):',helper+'def stage_content(stage):')
# Anchors belong in separate finite external record, not the META_LIMIT stage contract.
s=s.replace("'group_anchors_sha256':anchors.hex()", "'group_anchors_sha256':hashlib.sha256(anchors).hexdigest()")
s=s.replace("anchors=bytes.fromhex(external['group_anchors_sha256']);require(len(anchors)==32*groups,'group anchor extent differs')", "anchors_hash=hashlib.sha256()")
s=s.replace("require(hashlib.sha256(encoded).digest()==anchors[32*group:32*(group+1)],'group anchor changed')", "anchors_hash.update(hashlib.sha256(encoded).digest())")
s=s.replace("require(batch==binding['batches'] and cursor==binding['cells']", "require(anchors_hash.hexdigest()==external['group_anchors_sha256'] and batch==binding['batches'] and cursor==binding['cells']")
(HERE/'compact_mcm_batched.py').write_text(s)
a=(BASE/'compact_mcm.py').read_text();c=a.replace("policy['schema_version'] in (1,2,5)","policy['schema_version'] in (1,2,5,6)");assert a!=c
(HERE/'compact_mcm.py').write_text(c)
(HERE/'inverse.patch').write_text(''.join(difflib.unified_diff(s.splitlines(True),original.splitlines(True),fromfile='candidate/compact_mcm_batched.py',tofile='baseline/compact_mcm_batched.py'))+''.join(difflib.unified_diff(c.splitlines(True),a.splitlines(True),fromfile='candidate/compact_mcm.py',tofile='baseline/compact_mcm.py')))
