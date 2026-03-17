''' script to evaluate binding of BSA in high magnification IFC system'''
#%% import
import numpy as np
from spectralCamera.instrument.sCamera.sCameraFromFile import SCameraFromFile
from plim.gui.spectralViewer.plasmonViewer import PlasmonViewer
from skimage import data
from skimage.filters import threshold_otsu
from plim.algorithm.spotSpectra import SpotSpectra
import matplotlib.pyplot as plt

from skimage.morphology import erosion, disk, square


#spectral camera system
fFolder = r'F:\ondra\LPI\plim\DATA\ifcBased\26-03-16 highMag_BSA\rawNorm'


# %%
# load first image
sCamera = SCameraFromFile()
sCamera.connect()
sCamera.setFolder(fFolder)

ii=10
print(f'processing file # {ii}')
sImage = sCamera.fileSIVideo.loadImage(sCamera.fileName[ii])
t0 = sCamera.fileTime[ii]/1e9
w = sCamera.getWavelength()

pV = PlasmonViewer(image=sImage, wavelength=w)


# %% identify spots
image = np.sum(sImage, axis=0)
thresh = threshold_otsu(image[~np.isnan(image)])
binary = image < thresh

eroded = erosion(binary.astype(np.uint8), disk(2))

_indices = np.argwhere(eroded == 1)[::100,:]

_idxBcg = [200,100]
_idx = np.vstack((_idxBcg,_indices))
sS = SpotSpectra(sImage,wavelength=w)
sS.setSpot(_idx)

#%% calculate spectra

sS.setMask(pxAve=1,pxBcg=1, pxSpace= 1, concentric= False)

sS.calculateSpectra()

# %% show spots

_im = np.zeros_like(image)
_im[_indices[:,0],_indices[:,1]] = 1
pV.viewer.add_image(_im)
# %%

fig, ax = plt.subplots()

ax.plot(np.array(sS.spectraSpot)[::100,:].T)


# %%
