"""Material-specific GP or deep-ensemble training on verified S2 PERFORMANCE only.
Default C2 records are empty; the CLI exits with a BLOCKED report before model import.
A trained research model is not a manufacturing qualification.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from performance import validate_record,TARGETS
from engineering import ROOT,write_json

FEATURES=('tip_mm','width_mm','eccentric_mm','gap_mm','hook_depth_mm','hooks',
          'ratio_denominator','orbit_rpm','screen_hole_mm','screen_thickness_mm',
          'screen_arc_deg','rising_fraction','shear_ratio')


def grouped_split(ids: list[str],seed: int=20260921):
    groups=sorted(set(ids))
    if len(groups)<20:raise ValueError('At least20 independent geometries required by C2 research policy')
    rng=np.random.default_rng(seed);rng.shuffle(groups)
    ntest=max(4,round(.2*len(groups)));nval=max(4,round(.2*len(groups)))
    test=set(groups[:ntest]);val=set(groups[ntest:ntest+nval]);train=set(groups[ntest+nval:])
    return {k:np.array([i for i,x in enumerate(ids) if x in g],dtype=int)
            for k,g in [('train',train),('validation',val),('test',test)]}


def fit_gp(X,y,split):
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import Matern,WhiteKernel,ConstantKernel
    import joblib
    tr,va,te=(split[k] for k in ['train','validation','test'])
    mean=X[tr].mean(0);scale=np.maximum(X[tr].std(0),1e-8)
    XX=(X-mean)/scale
    model=GaussianProcessRegressor(kernel=ConstantKernel()*Matern(nu=2.5)+WhiteKernel(1e-4),
                                   normalize_y=True,random_state=20260921,n_restarts_optimizer=2)
    model.fit(XX[tr],y[tr])
    p,std=model.predict(XX[te],return_std=True)
    pv=model.predict(XX[va])
    return dict(model=model,feature_mean=mean,feature_scale=scale),dict(
        validation_mae=np.mean(abs(pv-y[va]),axis=0).tolist(),
        test_mae=np.mean(abs(p-y[te]),axis=0).tolist(),test_mean_std=np.mean(std,axis=0).tolist())


def fit_mlp(X,y,split,epochs=1500):
    import torch
    torch.set_num_threads(1)
    tr,va,te=(split[k] for k in ['train','validation','test'])
    xm=X[tr].mean(0);xs=np.maximum(X[tr].std(0),1e-8)
    ym=y[tr].mean(0);ys=np.maximum(y[tr].std(0),1e-8)
    xt=torch.tensor((X-xm)/xs,dtype=torch.float32)
    yt=torch.tensor((y-ym)/ys,dtype=torch.float32)
    predictions=[];val_predictions=[];states=[]
    for member in range(5):
        torch.manual_seed(20260921+member)
        model=torch.nn.Sequential(torch.nn.Linear(X.shape[1],64),torch.nn.SiLU(),
                                  torch.nn.Linear(64,64),torch.nn.SiLU(),torch.nn.Linear(64,y.shape[1]))
        opt=torch.optim.AdamW(model.parameters(),lr=1e-3,weight_decay=1e-3)
        best=float('inf');best_state=None;stale=0
        for epoch in range(epochs):
            model.train();opt.zero_grad()
            loss=torch.nn.functional.mse_loss(model(xt[tr]),yt[tr]);loss.backward();opt.step()
            model.eval()
            with torch.no_grad():vl=float(torch.nn.functional.mse_loss(model(xt[va]),yt[va]))
            if vl<best-1e-7:
                best=vl;best_state={k:v.detach().clone() for k,v in model.state_dict().items()};stale=0
            else:stale+=1
            if stale>150:break
        model.load_state_dict(best_state)
        with torch.no_grad():
            predictions.append(model(xt[te]).numpy()*ys+ym)
            val_predictions.append(model(xt[va]).numpy()*ys+ym)
        states.append(best_state)
    p=np.mean(predictions,0);pv=np.mean(val_predictions,0)
    return dict(states=states,feature_mean=xm,feature_scale=xs,target_mean=ym,target_scale=ys,
                architecture=[len(FEATURES),64,64,len(TARGETS)]),dict(
        validation_mae=np.mean(abs(pv-y[va]),0).tolist(),test_mae=np.mean(abs(p-y[te]),0).tolist(),
        test_ensemble_std=np.mean(np.std(predictions,0),0).tolist())


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--records',type=Path,default=ROOT/'experiments/performance_records.json')
    p.add_argument('--backend',choices=['gp','mlp'],default='gp')
    p.add_argument('--out',type=Path,default=ROOT/'results/model_run')
    args=p.parse_args();records=json.loads(args.records.read_text())
    rows=[validate_record(r,ROOT/'experiments') for r in records]
    minimum=20 if args.backend=='gp' else 100
    counts={m:len({r['candidate_id'] for r in rows if r['material']==m}) for m in ['PLA','PET','TPU']}
    report=dict(backend=args.backend,independent_geometries=counts,minimum_policy=minimum,
                status='BLOCKED_PERFORMANCE_DATA',trained=False,models=[])
    args.out.mkdir(exist_ok=True,parents=True)
    if any(n<minimum for n in counts.values()):
        write_json(args.out/'training_status.json',report);print(json.dumps(report,indent=2));return
    candidates={r['design']['candidate_id']:r['design'] for r in json.loads((ROOT/'results/s2_candidates.json').read_text())}
    for material in ['PLA','PET','TPU']:
        group=[r for r in rows if r['material']==material]
        grades={r['material_grade'] for r in group}
        feeds={r['feed_distribution_id'] for r in group}
        if len(grades)!=1 or len(feeds)!=1:
            raise ValueError('C2 model cohort must use one grade and controlled feed distribution; add features before pooling')
        X=np.array([[candidates[r['candidate_id']][k] for k in FEATURES] for r in group])
        y=np.array([[r['outputs'][k] for k in TARGETS] for r in group])
        split=grouped_split([r['candidate_id'] for r in group])
        if args.backend=='gp':
            model,metrics=fit_gp(X,y,split)
            import joblib
            joblib.dump(model,args.out/(material+'.joblib'))
        else:
            model,metrics=fit_mlp(X,y,split)
            import torch
            torch.save(model,args.out/(material+'.pt'))
        entry=dict(material=material,grade=next(iter(grades)),features=FEATURES,targets=TARGETS,
                   metrics=metrics,split={k:[group[i]['candidate_id'] for i in v] for k,v in split.items()},
                   lot_generalization='NOT_ESTABLISHED_BY_GEOMETRY_HOLDOUT',manufacturing_qualified=False)
        report['models'].append(entry)
    report.update(status='RESEARCH_TRAINING_COMPLETE_NOT_RELEASED',trained=True)
    write_json(args.out/'training_status.json',report)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
