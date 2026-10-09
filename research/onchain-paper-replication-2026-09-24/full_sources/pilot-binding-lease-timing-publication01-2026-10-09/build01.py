from pathlib import Path
import ast,difflib,json
P=Path(__file__).resolve().parent;R=P.parents[3];S=R/'tradingagents/research/onchain_replication';F=P.parent;G=F/'matching-real-geometry-publication01-2026-10-09';T=F/'pilot-binding-lease-timing01-2026-10-09'
origins={n:(G/n if n in ('compact_mcm_batched.py','batched_numeric_execution.py','geometry_publication.py') else T/n if n=='matching_owner.py' else S/n) for n in ['matching_owner.py','compact_owner.py','compact_mcm_batched.py','batched_numeric_execution.py','imported_authority_lease.py','geometry_publication.py']};texts={n:p.read_text() for n,p in origins.items()};changes={n:[] for n in texts}
def replace(n,a,b):
 assert texts[n].count(a)==1,(n,a,texts[n].count(a));texts[n]=texts[n].replace(a,b);changes[n].append([a,b])
n='matching_owner.py'
replace(n,'self._totals=(0,)*12;self.closed=False','self._totals=(0,)*12;self._counter_pin=self._totals;self.closed=False')
replace(n,"require(type(self._totals) is tuple and len(self._totals)==12","require(self._totals is self._counter_pin and type(self._totals) is tuple and len(self._totals)==12")
replace(n,'finish=self._now();self._check(binding)','finish=self._now();self._check(binding)\n                require(finish>=start,\'binding timing interval reversed\')')
replace(n,'self._totals=tuple(values)','self._totals=tuple(values);self._counter_pin=self._totals')
addition='''
BINDING_TIMING_POLICY={'format':'binding-lease-phases-v1','max_body_bytes':640}

def binding_timing_policy(value):
    if value is None:return None
    require(type(value) is dict and set(value)==set(BINDING_TIMING_POLICY)
            and type(value['format']) is str and type(value['max_body_bytes']) is int
            and value==BINDING_TIMING_POLICY,'explicit binding timing policy required')
    return dict(value)

def binding_timing_counters(value):
    names={'binding_timing_closed'}|{'binding_'+phase+'_'+suffix for phase in _LEASE_TIMING_PHASES for suffix in ('calls','ns','failures')}
    require(type(value) is dict and set(value)==names and all(type(x) is int and 0<=x<=_LEASE_TIMING_LIMIT for x in value.values()),'exact binding counters required')
    require(value['binding_timing_closed']==0 and all(value['binding_'+p+'_failures']<=value['binding_'+p+'_calls'] for p in _LEASE_TIMING_PHASES),'completed binding timing required')
    encoded=(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\\n').encode()
    require(len(encoded)<=640,'binding timing body cap')
    return dict(value)

'''
replace(n,'\nclass Binding:\n',addition+'\nclass Binding:\n')
n='compact_owner.py'
needle='''        self.bound.lease()
'''
assert texts[n].count(needle)==1
replace(n,needle,'''        if not hasattr(self,'_binding_timing_pin'):
            self.bound.lease()
        else:
            observer=self._binding_timing
            require(observer is self._binding_timing_pin and type(observer) is matching_owner.BindingLeaseTiming,'selected binding observer changed')
            observer._check(self.bound)
            self.bound.lease(observer=observer)
''')
pos=texts[n].index('    def lease(self):',texts[n].index('class Owner:'))
method='''    def select_binding_timing(self,selection):
        require(type(self) is Owner and matching_owner.binding_timing_policy(selection) is not None,'actual selected owner timing required')
        if not hasattr(self,'_binding_timing_pin'):
            self._binding_timing=matching_owner.BindingLeaseTiming(self.bound)
            self._binding_timing_pin=self._binding_timing
        require(self._binding_timing is self._binding_timing_pin,'selected binding observer changed')
        self._binding_timing._check(self.bound)
        return self._binding_timing

'''
# Record insertion as exact reversible replacement.
replace(n,texts[n][pos:pos+len('    def lease(self):')],method+'    def lease(self):') if texts[n].count('    def lease(self):')==1 else None
# Owner and Stage both have lease: use unique neighboring class-method body anchor.
if method not in texts[n]:
 anchor="    def lease(self):\n        require(not self.poisoned and not self.closed, 'compact owner is terminal or poisoned')"
 replace(n,anchor,method+anchor)
n='imported_authority_lease.py';replace(n,"'Target','Lease','Interval'}","'Target','Lease','Interval','BindingLeaseTiming'}")
n='compact_mcm_batched.py';replace(n,'from . import geometry_publication','from . import geometry_publication, matching_owner')
replace(n,"| ({'geometry'} if 'geometry' in execution else set()),'explicit numeric execution schema required')","| ({'geometry'} if 'geometry' in execution else set()) | ({'binding_timing'} if 'binding_timing' in execution else set()),'explicit numeric execution schema required')")
replace(n,"    if 'geometry' in execution:\n", "    if 'binding_timing' in execution:\n        require(grouped and matching_owner.binding_timing_policy(execution['binding_timing']) is not None,'selected schema6 binding timing required')\n        require(execution['max_summary_bytes']>=count*8192,'full timing summary reservation required')\n    if 'geometry' in execution:\n")
replace(n,'*, grouped=False, geometry=False):','*, grouped=False, geometry=False, binding_timing=False):')
replace(n,"        if geometry:names+=('geometry_summary','geometry_publication')","        if geometry:names+=('geometry_summary','geometry_publication')\n        if binding_timing:names+=('matching_owner','compact_owner','imported_authority_lease')")
replace(n,"    checkpoints=stage.root/'checkpoints';", "    timing=b['execution'].get('binding_timing')\n    if timing is not None:\n        require(authority_poll is not None,'binding timing requires selected genuine sampled lease')\n        target.owner.select_binding_timing(timing)\n    checkpoints=stage.root/'checkpoints';")
replace(n,"**({'geometry':execution['geometry']} if 'geometry' in execution else {}))", "**({'geometry':execution['geometry']} if 'geometry' in execution else {}),**({'binding_timing':execution['binding_timing'],'binding_owner':target.owner} if 'binding_timing' in execution else {}))")
replace(n,"geometry='geometry' in b['execution'])", "geometry='geometry' in b['execution'],binding_timing='binding_timing' in b['execution'])")
n='batched_numeric_execution.py';replace(n,'from . import geometry_publication','from . import geometry_publication, matching_owner')
replace(n,'authority_poll=None,geometry=None):','authority_poll=None,geometry=None,binding_timing=None,binding_owner=None):')
replace(n,"            self.geometry=geometry_publication.policy(geometry)",'''            self.binding_timing=matching_owner.binding_timing_policy(binding_timing)
            self.binding_owner=binding_owner;self._timing_observer=None;self._timing_snapshot=None
            if self.binding_timing is not None:
                from . import compact_owner
                require(type(binding_owner) is compact_owner.Owner,'genuine timing Owner required')
                self._timing_observer=binding_owner._binding_timing_pin
                self._timing_current()
                require(max_summary_bytes>=self.batches*SUMMARY_LIMIT,'selected timing requires full summary reservation')
            else:require(binding_owner is None,'unselected timing Owner')
            self.geometry=geometry_publication.policy(geometry)''')
replace(n,'    def _root(self):', '''    def _timing_current(self):
        owner=self.binding_owner;observer=self._timing_observer
        require(type(observer) is matching_owner.BindingLeaseTiming and owner._binding_timing is observer is owner._binding_timing_pin,'numeric binding observer changed')
        observer._check(owner.bound)

    def _counters(self):
        value=counters(self.memo)
        if self.binding_timing is not None:
            require(type(self._timing_snapshot) is bytes,'attested timing snapshot missing')
            timing=json.loads(self._timing_snapshot)
            require(raw(timing)==self._timing_snapshot,'timing snapshot canonical bytes differ')
            matching_owner.binding_timing_counters(timing)
            require(not set(timing)&set(value),'binding counter collision')
            value.update(timing)
        return value

    def _root(self):''')
replace(n,'        start=self.ordinal-len(self.buffer)//9', '''        if self.binding_timing is not None:
            self._timing_current()
            self._timing_snapshot=raw(matching_owner.binding_timing_counters(self._timing_observer.snapshot()))
        start=self.ordinal-len(self.buffer)//9''')
# Only two literal counters occurrences inside summary and finish; verifier/function unchanged.
for phrase in ["'counters':counters(self.memo),'elapsed_seconds':self.batch_elapsed", "'counters':counters(self.memo),'elapsed_seconds':self.elapsed_seconds"]:replace(n,phrase,phrase.replace('counters(self.memo)','self._counters()'))
replace(n,"            if self.geometry is not None:binding['geometry']=dict(self.geometry)","            if self.geometry is not None:binding['geometry']=dict(self.geometry)\n            if self.binding_timing is not None:binding['binding_timing']=dict(self.binding_timing)")
replace(n,"        geometry=geometry_publication.policy(binding.get('geometry'))","        timing=matching_owner.binding_timing_policy(binding.get('binding_timing'))\n        if timing is not None:require(binding['max_summary_bytes']>=batches*SUMMARY_LIMIT,'binding timing summary reservation differs')\n        geometry=geometry_publication.policy(binding.get('geometry'))")
replace(n,"            chunk=os.pread(origin,9*(stop-start),9*start);", "            if timing is not None:\n                names={'binding_timing_closed'}|{'binding_'+p+'_'+x for p in matching_owner._LEASE_TIMING_PHASES for x in ('calls','ns','failures')}\n                matching_owner.binding_timing_counters({k:s['counters'][k] for k in names})\n            chunk=os.pread(origin,9*(stop-start),9*start);")
for n,t in texts.items():ast.parse(t);(P/n).write_text(t)
(P/'CHANGES01.json').write_text(json.dumps(changes,indent=2)+'\n');(P/'SOURCE_MAP01.json').write_text(json.dumps({n:str(p.relative_to(R)) for n,p in origins.items()},indent=2)+'\n')
(P/'inverse.patch').write_text(''.join(''.join(difflib.unified_diff(texts[n].splitlines(True),origins[n].read_text().splitlines(True),fromfile=n+'-candidate',tofile=n+'-baseline')) for n in texts))
