from pathlib import Path
import json,hashlib,difflib
H=Path(__file__).resolve().parent;S=H.parents[3]/'tradingagents/research/onchain_replication/batched_numeric_reuse.py';old=S.read_text();new=old.replace('import array,copy,ctypes,hashlib,json,math,struct,sys,types','import array,copy,ctypes,hashlib,json,math,struct,sys,types,time')
needle='        self.authority_poll=authority_poll\n'
insert='''        if authority_poll is not None:
            require(callable(authority_poll),'optional authority poll must be callable')
            original_poll=authority_poll;clock=time.perf_counter_ns
            require(type(clock) is types.BuiltinFunctionType and clock.__module__=='time' and clock.__name__=='perf_counter_ns','builtin authority timer required')
            self._authority_poll_original=original_poll
            names=('authority_poll_calls','authority_poll_ns','authority_poll_failures')
            totals=[0,0,0];limit=2**63-1
            self.counters.update(dict(zip(names,totals)))
            def current_poll():
                require(self._authority_poll_original is original_poll and time.perf_counter_ns is clock,'authority callback/timer changed')
                require(all(type(self.counters.get(k)) is int and self.counters[k]==v for k,v in zip(names,totals)),'authority timing counters changed')
            def measured_poll():
                current_poll();start=clock()
                require(type(start) is int and 0<=start<=limit and totals[0]<limit,'authority timing bound exceeded')
                totals[0]+=1;self.counters[names[0]]=totals[0]
                primary=None
                try:
                    return original_poll()
                except BaseException as error:
                    primary=error;raise
                finally:
                    try:
                        stop=clock();current_poll()
                        require(type(stop) is int and start<=stop<=limit and totals[1]+stop-start<=limit,'authority timing bound exceeded')
                        totals[1]+=stop-start
                        if primary is not None:totals[2]+=1
                        self.counters.update(dict(zip(names,totals)))
                    except BaseException as timing_error:
                        if primary is None:raise
                        primary.add_note('authority timing failed: '+repr(timing_error))
            authority_poll=measured_poll
'''
assert old.count(needle)==1;new=new.replace(needle,insert+needle);(H/'batched_numeric_reuse.py').write_text(new)
(H/'inverse.patch').write_text(''.join(difflib.unified_diff(new.splitlines(True),old.splitlines(True))))
(H/'CHANGE01.json').write_text(json.dumps({'baseline_sha256':hashlib.sha256(old.encode()).hexdigest(),'candidate_sha256':hashlib.sha256(new.encode()).hexdigest(),'insertion':insert},indent=2)+'\n')
