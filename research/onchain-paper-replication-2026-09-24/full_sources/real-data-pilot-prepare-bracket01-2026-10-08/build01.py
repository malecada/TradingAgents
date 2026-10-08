from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;R=H.parents[3];M=R/'tradingagents/research/onchain_replication'
T=H.parent/'real-data-pilot-same-boundary-reuse01-2026-10-08/imported_mcm_identity.py'
assert hashlib.sha256(T.read_bytes()).hexdigest()=='39304277c2a0c6278a7524102f15bcfb0f8f9d73f691b51e0cd7a554a65bd7eb'
t=T.read_text();c=(M/'compact_mcm.py').read_text()
(H/'baseline_imported_mcm_identity.py').write_text(t);(H/'baseline_compact_mcm.py').write_text(c)
t=t.replace('        self.check();run=self.owner.bound._run;result={}\n','        self.check();return self._prepare_sources()\n\n    def _prepare_graph(self,key):\n        """Private metadata access inside compact_mcm._prepare check bracket."""\n        self._pins();require(self.key==key,\'imported target key differs\');return self.graph\n\n    def _prepare_sources(self):\n        """Private source scan inside compact_mcm._prepare check bracket."""\n        run=self.owner.bound._run;result={}\n')
a='    dictionary.check(); sources = _sources(dictionary); owner = _owner(dictionary)\n    graph = _graph(dictionary,key); d = dictionary.dictionary\n'
b='''    dictionary.check(); imported = _imported(dictionary)
    sources = dictionary._prepare_sources() if imported else _sources(dictionary)
    owner = _owner(dictionary)
    graph = dictionary._prepare_graph(key) if imported else _graph(dictionary,key)
    d = dictionary.dictionary
'''
assert a in c;c=c.replace(a,b,1)
a='    io._json(start); return graph,kernel,policy,start\n'
b='''    io._json(start)
    if imported:
        # All preparation callbacks have completed. Keep a local result pin
        # across the genuine final check; no reusable authority is issued.
        result_pin = cache_key({'policy':policy,'start':start})
        dictionary.check()
        # Callback-free rejoin of observations used above. This remains a
        # sampled boundary, not an atomic filesystem snapshot.
        dictionary._pins()
        require(dictionary.owner is owner and dictionary.dictionary is d
            and dictionary.graph is graph and dictionary.key == key,
            'imported preparation objects changed')
        require(len(graph.node_ids) == rows and len(d.representatives) == motifs
            and dictionary.scope == expected and dictionary.derive_scope() == expected,
            'imported preparation dimensions/scope changed')
        require(cache_key({'policy':policy,'start':start}) == result_pin,
            'imported preparation result changed')
        require(owner.reserved+pair_reserved <= owner.maximum and owner.active is None
            and name in owner.required and name not in owner.stages
            and not compact_owner.present(owner.root/name),
            'imported preparation stage/reservation changed')
        require(output_path.resolve() == output_path and not compact_owner.present(output_path),
            'imported preparation output changed')
    return graph,kernel,policy,start
'''
assert a in c;c=c.replace(a,b,1)
(H/'imported_mcm_identity.py').write_text(t);(H/'compact_mcm.py').write_text(c)
(H/'HASHES.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in H.glob('*.py')},indent=2)+'\n')
