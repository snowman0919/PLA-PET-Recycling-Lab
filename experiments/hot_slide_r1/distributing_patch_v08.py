"""Work-conjugate weighted rigid-section fit and statically exact surface resultants."""
import numpy as np

def cross_matrix(r):
    x,y,z=r
    return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])

def rigid_fit_coefficients(points,weights,origin):
    ids=list(weights)
    if len(ids)<3 or any(not np.isfinite(weights[n]) or weights[n]<=0 for n in ids):raise ValueError('invalid patch weights')
    origin=np.asarray(origin,float)
    blocks={n:np.column_stack((np.eye(3),-cross_matrix(np.asarray(points[n])-origin))) for n in ids}
    gram=sum(weights[n]*blocks[n].T@blocks[n] for n in ids)
    if not np.isfinite(gram).all() or np.linalg.matrix_rank(gram)<6:raise ValueError('degenerate patch')
    inverse=np.linalg.inv(gram)
    return {n:inverse@(weights[n]*blocks[n].T) for n in ids}

def resultant_loads(points,weights,force,moment,origin):
    force=np.asarray(force,float);moment=np.asarray(moment,float);origin=np.asarray(origin,float)
    if not np.isfinite(np.concatenate([force,moment,origin])).all():raise ValueError('nonfinite resultant')
    coefficients=rigid_fit_coefficients(points,weights,origin)
    generalized=np.concatenate([force,moment])
    return {n:c.T@generalized for n,c in coefficients.items()}
