from pathlib import Path
H=Path(__file__).resolve().parent;p=H/'compact_mcm_batched.py';s=p.read_text()
s=s.replace("        _children(root/'stream',{'closure-tokens.bin','scores.f32'})","        require(io._signature((root/'matching').lstat())[:2]==tuple(binding['journal_inode']),'matching root inode differs')\n        _children(root/'stream',{'closure-tokens.bin','scores.f32'})")
s=s.replace("            work=Path(external['directory'])", "            from . import registered_offload as offload\n            work=Path(external['directory'])")
s=s.replace("json.loads((work/'final/accepted-coverage.json').read_bytes())","json.loads(offload.typed._read(work/'final/accepted-coverage.json'))")
s=s.replace("                digest=hashlib.sha256()\n                for i", "                digest=hashlib.sha256();aggregate=hashlib.sha256();cursor=0\n                for i")
s=s.replace("                    record=json.loads((work/f'preserve/{i:08d}/offload.json').read_bytes())", "                    encoded=offload.typed._read(work/f'preserve/{i:08d}/offload.json');record=json.loads(encoded)")
s=s.replace("                    require(record['binding']['source_tokens']==token.hex() and record['batch']==i,'anchored original source tokens differ')", """                    require(record['binding']['source_tokens']==token.hex() and record['batch']==i and record['start']==cursor and record['binding']['root']==str(root/'matching') and record['binding']['root_pin']==binding['journal_inode'],'anchored original source tokens differ')
                    parts=list(offload.typed.iter_history_parts(record['history'],binding=record['binding'],kind=offload.KIND))
                    require(len(parts)==1 and parts[0]['receipt']==record['receipt'],'original typed transport history differs')
                    fresh_raw=offload.typed._read(work/f'final/{i:08d}/complete.json');fresh=json.loads(fresh_raw)
                    require(fresh['original_history']==record['history'] and fresh['source_binding']==record['binding'] and fresh['start']==cursor and fresh['stop']==record['stop'],'fresh recovery history join differs')
                    complete=offload.typed.check_history(fresh['history'],binding=record['binding'],kind=offload.KIND)
                    require(complete['parts']==0 and complete['recovered_bytes']==record['manifest']['archive_bytes'],'actual fresh recovered byte denominator differs')
                    for _ in offload.typed.iter_history_parts(fresh['history'],binding=record['binding'],kind=offload.KIND):pass
                    aggregate.update(hashlib.sha256(encoded).digest());aggregate.update(hashlib.sha256(fresh_raw).digest());cursor=record['stop']""")
s=s.replace("                require(digest.hexdigest()==binding['tokens_sha256']", "                require(cursor==binding['cells'] and aggregate.hexdigest()==external['coverage']['original_and_fresh_history_aggregate_sha256'],'external aggregate/full denominator differs')\n                require(digest.hexdigest()==binding['tokens_sha256']")
# Close setup-born journal/token fd on any external selection or directory failure.
a=s.index("    spool_fd=os.open(");b=s.index('    def sink(',a)
segment=s[a:b];s=s[:a]+"    spool_fd=None\n    try:\n"+''.join('    '+line if line.strip() else line for line in segment.splitlines(True))+"    except BaseException:\n        io._cleanup((lambda:os.close(fd),journal.close)+((lambda:os.close(spool_fd),) if spool_fd is not None else ()))\n        raise\n"+s[b:]
# default clean map on pre-Produced failure
s=s.replace('owner=target.owner;held.check(owner);root=None;fd=None;stage=None','owner=target.owner;held.check(owner);root=None;fd=None;stage=None;mapped=None;matrix=None')
s=s.replace("        owner.poisoned=True;raise", "        owner.poisoned=True\n        matrix=None\n        if mapped is not None:\n            try:mapped.close()\n            except BaseException as later:error.add_note('Batched mmap cleanup: '+repr(later))\n        raise")
p.write_text(s)
