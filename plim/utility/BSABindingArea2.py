''' script to evaluate binding of BSA in high magnification IFC system'''
#%% import
import numpy as np
from spectralCamera.instrument.sCamera.sCameraFromFile import SCameraFromFile
from plim.gui.spectralViewer.plasmonViewer import PlasmonViewer
from skimage import data
from skimage.filters import threshold_otsu
from plim.algorithm.spotSpectra import SpotSpectra
import matplotlib.pyplot as plt

from scipy.ndimage import binary_erosion

from skimage.morphology import erosion, disk, square
from plim.instrument.plasmonProcessor import PlasmonProcessor
from plim.algorithm.fileData import FileData
import time
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
import napari


#spectral camera system
fFolder = r'F:\ondra\LPI\plim\DATA\ifcBased\26-03-16 highMag_BSA\rawShift'
sFolder = r'F:\ondra\LPI\plim\DATA\ifcBased\26-03-16 highMag_BSA\singlePixel2'

# %%
# load first image
sCamera = SCameraFromFile()
sCamera.connect()
sCamera.setFolder(fFolder)

ii=1
print(f'loading file # {ii} for spot setting')
sImage = sCamera.fileSIVideo.loadImage(sCamera.fileName[ii])
t0 = sCamera.fileTime[ii]/1e9
w = sCamera.getWavelength()


# %% identify spots
image = np.sum(sImage, axis=0)
image[image<1] = np.nan
thresh = threshold_otsu(image[~np.isnan(image)])
#thresh = threshold_otsu(image[image>1])

binary = image < thresh

#eroded = erosion(binary.astype(np.uint8), disk(10))

eroded = binary_erosion(binary.astype(np.uint8), structure=disk(10), border_value=0)



_per = 1
grid = np.zeros_like(image)
grid[::_per,::_per] = 1

_indices = np.argwhere(eroded*grid == 1)

_idxBcg = [200,100]
_idx = np.vstack((_idxBcg,_indices))

#%% show the spots and image

_im = np.zeros_like(image)
_im[_indices[:,0],_indices[:,1]] = 1
pV = PlasmonViewer(image=sImage, wavelength=w)


# set spots in the viewer
pV.spotSpectra.setSpot(_idx)
pV.spotSpectra.setMask(pxAve=1,pxBcg=5, pxSpace= 1, concentric= False)
pV.redraw()


#%% set plasmon processor

sCamera.setParameter('threadingNow',True)  
pP = PlasmonProcessor()
pP.connect(sCamera=sCamera)
pP.setParameter('threadingNow',True)
sCamera.setParameter('processor',pP)

# copy the spotSpectra from pV
pP.spotSpectra = pV.spotSpectra


#set parameter for fitting
pP.pF.wavelengthStartFit = 550
pP.pF.wavelengthStopFit = 750
pP.pF.orderFit = 8
pP.pF.peakWidth =  100
pP.pF.wavelengthGuess = 620


#%% calculate spectra
sCamera.startReadingImages(idx=[10])
# %% show the whole data cube

aa = np.array(pP.pF.spectraList)


import numpy as np
import matplotlib.pyplot as plt

# Shape: (n_trajectories, n_timesteps)
# data = np.load('your_data.npy')

data = np.array(pP.pF.spectraList)

n_traj, n_steps = data.shape

t = w

mean = np.mean(data, axis=0)
p5, p25, p75, p95 = np.percentile(data, [5, 25, 75, 95], axis=0)

plt.fill_between(t, p5, p95, alpha=0.2, label='5–95%')
plt.fill_between(t, p25, p75, alpha=0.4, label='25–75%')
plt.plot(t, mean, lw=2, label='Mean')
plt.legend()
plt.xlabel('wavelenght / nm')
plt.ylabel('Transmission ')
plt.title('Plasmon resonance')
plt.xlim(500, )
plt.show()


# %%
