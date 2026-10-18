from pathlib import Path
import json,numpy as np
from scipy.io import loadmat
root=Path(__file__).resolve().parents[1];rows=[]
for i in range(1,6):
 rec=f'movie{i}';folder=root/'data'/rec
 expected=loadmat(folder/'matlab-augmentation-reference.mat')['expected'];actual=loadmat(folder/'features36.mat',simplify_cells=True)['feat']['data']
 np.testing.assert_array_equal(np.isnan(actual),np.isnan(expected));np.testing.assert_allclose(actual,expected,rtol=0,atol=1e-12,equal_nan=True)
 rows.append({'recording':rec,'shape':list(actual.shape),'max_finite_absolute_difference':float(np.nanmax(np.abs(actual-expected))),'nan_values':int(np.isnan(actual).sum()),'official_matlab_augmentation_parity':True})
(root/'reports/augmentation-verification.json').write_text(json.dumps({'status':'PASS','tolerance_absolute':1e-12,'records':rows},indent=2));print(json.dumps(rows,indent=2))
