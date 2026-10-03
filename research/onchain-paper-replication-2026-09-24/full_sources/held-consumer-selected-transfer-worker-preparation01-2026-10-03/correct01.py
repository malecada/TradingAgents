from pathlib import Path
p=Path(__file__).parent
f=p/'held_score_consumer.py';s=f.read_text().replace('from ..runner import ResearchRun','from ..lifecycle import ResearchRun')
s=s.replace("require(len(sizes)<=16,'worker bounded complete member inventory ceiling16')", """names=['start.json','terminal.json']+[f'chunk-{i:012d}.json' for i in range(chunks)]+[f'chunk-{i:012d}.bin' for i in range(chunks)]
        prototype={'owner':'0'*64,'stage':'mcm-'+graph,'stage_intent_sha256':'0'*64,'source':'0'*40,'claim':'0'*64,'role':'score-batches','scope':{k:'0'*64 for k in ('graph','node_order','dictionary','ordered_motifs','matching','workflow')},'container_sha256':'0'*64,'members':[{'name':name,'sha256':'0'*64,'bytes':size} for name,size in zip(names,sizes,strict=True)]}
        require(len(json.dumps(prototype,sort_keys=True,separators=(',',':')).encode())+1<=8192,'complete original member ledger exceeds inherited8KiB control bound')""")
s=s.replace("p,_=transfer_preflight(self.run,self.execution,job_input=self.job_input)","""p,outputs=transfer_preflight(self.run,self.execution,job_input=self.job_input)
            require(all(name not in self.run._published_outputs and not os.path.lexists(self.run.directory/'outputs'/name) for name in outputs),'selected worker output already reserved before namespace birth')""")
f.write_text(s)
f=p/'resource_fixture.py';s=f.read_text().replace("\n        require(len(readbacks)==2", "\n            require(len(readbacks)==2");f.write_text(s)
