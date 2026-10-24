"""Read legacy and current FlyTracker MATs, including MATLAB7.3 encoded empty arrays."""
import h5py,numpy as np
from scipy.io import loadmat

def load_track(path):
 if h5py.is_hdf5(path):
  with h5py.File(path) as f:
   g=f['trk'];names=[''.join(chr(int(c)) for c in np.asarray(f[z]).ravel()) for z in np.asarray(g['names']).ravel()]
   data=np.asarray(g['data']).transpose(2,1,0)
   # MATLAB stores an empty0x6 array as the dimension vector[0,6] plus this attribute.
   flags=np.asarray(g['flags']).T if 'flags' in g and not g['flags'].attrs.get('MATLAB_empty',0) else np.empty((0,6))
   warning=np.asarray(g['flag_frames']).ravel().astype(bool) if 'flag_frames' in g and not g['flag_frames'].attrs.get('MATLAB_empty',0) else np.zeros(data.shape[1],bool)
 else:
  g=loadmat(path,simplify_cells=True)['trk'];names=list(g['names']);data=np.asarray(g['data']);flags=np.asarray(g.get('flags',np.empty((0,6))));warning=np.asarray(g.get('flag_frames',np.zeros(data.shape[1]))).ravel().astype(bool)
 if data.ndim!=3 or data.shape[0]!=2 or data.shape[2]!=len(names) or len(set(names))!=len(names):raise ValueError('Invalid two-fly tracking schema')
 if len(warning)!=data.shape[1]:raise ValueError('Warning frame count mismatch')
 if flags.size:
  if flags.size%6:raise ValueError('Expected six-column FlyTracker warning intervals')
  for row in flags.reshape(-1,6):
   a,b=row[2:4]
   if not np.isfinite([a,b]).all() or a!=int(a) or b!=int(b) or not 1<=a<=b<=len(warning):raise ValueError('Invalid tracking warning interval')
   warning[int(a)-1:int(b)]=True
 xy=data[:,:,[names.index('pos x'),names.index('pos y')]]
 return xy,warning,data,names
