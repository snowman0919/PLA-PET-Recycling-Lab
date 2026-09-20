"""Small geometric surrogate trained from actual sampled pin/profile distances.
NOT a model of material fracture, cutting force, throughput, wear, or safety.
"""
from pathlib import Path
import csv,json,hashlib
import numpy as np
import torch
from analyze import clearance_metric
ROOT=Path(__file__).resolve().parents[1]

def main():
 rng=np.random.default_rng(20260920);torch.manual_seed(20260920);torch.set_num_threads(1)
 X=np.column_stack((rng.uniform(72,80,256),rng.uniform(6,8,256),rng.uniform(.15,.4,256)))
 Y=[];valid=[]
 for row in X:
  a,b,ok=clearance_metric(row[0],row[1],8,row[2],720,37);Y.append([a,b]);valid.append(ok)
 Y=np.asarray(Y);mask=np.asarray(valid);X=X[mask];Y=Y[mask]
 split=rng.permutation(len(X));ntrain=int(.7*len(X));nval=int(.15*len(X));tr=split[:ntrain];va=split[ntrain:ntrain+nval];te=split[ntrain+nval:]
 xm=X[tr].mean(0);xs=X[tr].std(0);ym=Y[tr].mean(0);ys=Y[tr].std(0)
 xt=torch.tensor((X-xm)/xs,dtype=torch.float32);yt=torch.tensor((Y-ym)/ys,dtype=torch.float32)
 model=torch.nn.Sequential(torch.nn.Linear(3,32),torch.nn.Tanh(),torch.nn.Linear(32,32),torch.nn.Tanh(),torch.nn.Linear(32,2))
 opt=torch.optim.Adam(model.parameters(),lr=.008);best=1e20;weights=None
 for epoch in range(800):
  opt.zero_grad();loss=((model(xt[tr])-yt[tr])**2).mean();loss.backward();opt.step()
  with torch.no_grad():v=((model(xt[va])-yt[va])**2).mean().item()
  if v<best:best=v;weights={k:x.detach().clone() for k,x in model.state_dict().items()}
 model.load_state_dict(weights)
 with torch.no_grad():pred=model(xt[te]).numpy()*ys+ym
 err=pred-Y[te];rmse=np.sqrt(np.mean(err**2,axis=0));mae=np.mean(abs(err),axis=0)
 p=ROOT/'results/kinematic_dataset.csv'
 with p.open('w',newline='') as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(['R_pin_mm','eccentricity_mm','profile_offset_mm','min_sampled_clearance_mm','max_profile_radius_mm','split'])
  for i,(x,y) in enumerate(zip(X,Y)):w.writerow([*x,*y,'train' if i in tr else 'validation' if i in va else 'test'])
 torch.save({'state_dict':weights,'input_mean':xm.tolist(),'input_std':xs.tolist(),'output_mean':ym.tolist(),'output_std':ys.tolist(),'architecture':[3,32,32,2],'activation':'tanh'},ROOT/'results/kinematic_surrogate.pt')
 result={'scope':'KINEMATIC_GEOMETRY_ONLY','physical_training_samples':0,'DEM_samples':0,'geometry_samples_valid':len(X),'discarded_invalid_profiles':256-len(X),'train':len(tr),'validation':len(va),'test':len(te),'seed':20260920,'target_names':['min_pin_profile_clearance_mm','max_profile_radius_mm'],'test_RMSE_mm':rmse.tolist(),'test_MAE_mm':mae.tolist(),'dataset_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'coarse_geometry_samples':720,'coarse_motion_phases':37,'final_design_acceptance':'Bypass ML: recompute at2880 vertices and721 phases. Coarse labels have discretization error.','limitations':['Cannot predict cutting force or particle size','No extrapolation outside input ranges','Random holdout is not manufacturing validation','Do not load pickle-based weights from untrusted sources']}
 (ROOT/'results/kinematic_surrogate.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
