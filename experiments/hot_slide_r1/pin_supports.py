"""Three radial slots: constrain tangent/axial means, leave radial motion free."""
import math
import numpy as np

def equation(terms):
    terms=[t for t in terms if abs(t[2])>1e-14]
    terms.sort(key=lambda t:-abs(t[2]) if t[0]>0 else 0)
    return ['*EQUATION',str(len(terms))]+[','.join(f'{n},{d},{c:.12g}' for n,d,c in terms[i:i+4]) for i in range(0,len(terms),4)]

def supports(nodes):
    points={n:tuple(v/1000 for v in p) for n,p in nodes.items()}
    originals=set(points);relations=[];records=[]
    for index,deg in enumerate((90,210,330)):
        a=math.radians(deg);normal=np.array([math.cos(a),math.sin(a)])
        tangent=np.array([-normal[1],normal[0]])
        picked=[n for n,p in nodes.items() if 30.5 < np.dot(p[:2],normal) < 34.5 and abs(abs(np.dot(p[:2],tangent))-2.02)<.025]
        if len(picked)<8:raise ValueError('slot-side sample missing')
        centre=np.mean([points[n] for n in picked],axis=0)
        normal=centre[:2]/np.linalg.norm(centre[:2]);tangent=np.array([-normal[1],normal[0]])
        ref=max(points)+1;points[ref]=tuple(centre);w=1/len(picked)
        for dof in (1,2):
            terms=[(n,k+1,w*float(tangent[k])) for n in picked for k in (0,1)] if dof==1 else [(n,3,w) for n in picked]
            terms=[t for t in terms if abs(t[2])>1e-14];terms.sort(key=lambda t:-abs(t[2]))
            terms.append((ref,dof,-1.))
            relations+=['*EQUATION',str(len(terms))]+[','.join(f'{n},{d},{c:.12g}' for n,d,c in terms[i:i+4]) for i in range(0,len(terms),4)]
        records.append({'ref':ref,'centroid_m':centre.tolist(),'tangent':tangent.tolist(),'node_count':len(picked)})
    return points,relations,records
