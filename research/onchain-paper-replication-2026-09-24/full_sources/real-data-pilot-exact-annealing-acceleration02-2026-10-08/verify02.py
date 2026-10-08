from pathlib import Path
text=(Path(__file__).parent/'verify.py').read_text()
exec(compile(text.split('a=graph(2,')[0],__file__,'exec'))
a=graph(2,[(0,1)],True);b=graph(10,[(i,9) for i in range(9)],True)
def overflow_after3(s):s['M'][:]=np.finfo(float).max;s['Q'][:]=0.;s['Q'][0,3]=np.finfo(float).max
oldcall=np.geterrcall()
try:
    for mode in ['warn','raise','call','log']:
        np.seterrcall(Logger() if mode=='log' else callback)
        compare('addition-overflow-after3-'+mode,a,b,overflow_after3,{'under':'ignore','over':mode},mode=='warn')
finally:np.seterrcall(oldcall)
assert all(row['cursor']==3 and row['safe'] is False for row in results)
print(json.dumps({'status':'PASS','boundary_checks':checks,'cases':results},indent=2))
