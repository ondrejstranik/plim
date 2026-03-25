''' displaying the 1 pixel BSA adsorption'''

#%%
from plim.algorithm.fileData import FileData
import numpy as np
import numpy as np
from scipy.ndimage import shift as ndi_shift
from skimage.morphology import erosion, disk, square
from scipy.ndimage import gaussian_filter, sobel
import napari
from scipy.signal import correlate2d


sFolder = r'F:\ondra\LPI\plim\DATA\ifcBased\26-03-16 highMag_BSA\singlePixel2'
fMName = 'Exp1'


#%% import
fD = FileData()
fD.loadAllFile(sFolder,fileMainName=fMName)
sS = fD.spotSpectra
sD = fD.spotData
sS.setMask()
im = sS.getImage()

#%% get the 3D stack of signals

imCube = np.zeros((sD.signal.shape[0],im.shape[1], im.shape[2]))
imCube[:,sS.maskSpotIdx[0][~sS.outliers,:],
                sS.maskSpotIdx[1][~sS.outliers,:]] = sD.signal[:,:,None]

#%% get aligned 3D stack of signals

viewer = napari.Viewer()
viewer.add_image(imCube, name='shifted')
#viewer.add_image(imCube)
#%%

import numpy as np
import matplotlib.pyplot as plt

# Shape: (n_trajectories, n_timesteps)
# data = np.load('your_data.npy')

sD.time0 = sD.time[0]
sD.setOffset(480)
data = (sD.signal - sD.getOffset()).T

n_traj, n_steps = data.shape
t = sD.time - sD.time0


# Build 2D histogram: time on x-axis, value on y-axis
hist, xedges, yedges = np.histogram2d(
    np.repeat(t, n_traj),          # time indices repeated for each trajectory
    data.T.ravel(),                 # all values flattened
    bins=[n_steps, 100]
)

plt.imshow(hist.T, origin='lower', aspect='auto',
           extent=[0, n_steps, yedges[0], yedges[-1]],
           cmap='inferno')
plt.colorbar(label='Count')
plt.xlabel('Time step')
plt.ylabel('Value')
plt.title('Trajectory Density over Time')
plt.show()

# %%
mean = np.mean(data, axis=0)
p5, p25, p75, p95 = np.percentile(data, [5, 25, 75, 95], axis=0)

plt.fill_between(t, p5, p95, alpha=0.2, label='5–95%')
plt.fill_between(t, p25, p75, alpha=0.4, label='25–75%')
plt.plot(t, mean, lw=2, label='Mean')
plt.legend()
plt.xlabel('Time / s')
plt.ylabel('signal / nm')
plt.title('BSA adsorption')
plt.xlim(300, )
plt.show()
# %%
