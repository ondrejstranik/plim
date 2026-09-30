''' code to evaluate the surface sensitivity with BSA'''
#%% import
from plim.algorithm.spotSpectra import SpotSpectra
import napari
import numpy as np
from spectralCamera.instrument.sCamera.sCameraFromFile import SCameraFromFile
from plim.algorithm.fileData import FileData
import matplotlib.pyplot as plt

# save text as text
plt.rcParams['svg.fonttype'] = 'none'

#spectral camera system
rFolder = r'F:\ondra\LPI\plim\DATA\filterBased\26-02-03 G4_BSA_spotted\raw'
dFolder = r'F:\ondra\LPI\plim\DATA\filterBased\26-02-03 G4_BSA_spotted'
dMName = 'Experiment2'



#%% load data
# load first image
sCamera = SCameraFromFile()
sCamera.connect()
sCamera.setFolder(rFolder)

ii=50
print(f'loading file # {ii} for spot setting')
sImage = sCamera.fileSIVideo.loadImage(sCamera.fileName[ii])
t0 = sCamera.fileTime[ii]/1e9
w = sCamera.getWavelength()


fD = FileData()
fD.loadAllFile(dFolder,fileMainName=dMName)
sS = fD.spotSpectra
sD = fD.spotData
pF = fD.pF
sS.setMask()
im = sS.getImage()
sS.spectraSigma = 1
sS.calculateSpectra()


# %% show plasmon spectra

y = np.array(sS.getSpectra())
x = w

fig1, ax1 = plt.subplots()
ax1.plot(x,y.T)
ax1.set_xlabel('wavelength / nm')
ax1.set_ylabel('Transmission')

# %% show the image with a mask

mask = sS.getMask()
mask[mask==2]=0

viewer = napari.Viewer()
viewer.add_image(im)
viewer.add_image(mask, opacity=0.08)
viewer.add_image(np.sum(sImage, axis=0))

# %% show bsa adsorption

sD.time0 = sD.time[0]
sD.setOffset(alignTime=950, useOffset=True)

y = sD.signal -sD.getOffset()
x = sD.time -sD.time[0]

fig2, ax2 = plt.subplots()
ax2.plot(x,y)
ax2.set_xlabel('time / s')
ax2.set_ylabel('signal /nm')
ax2.set_xlim([920,1500])
ax2.set_ylim([-1,9])
ax2.set_title('Surface Sensitivity calibration')

# %% calculate sensitivity

t = np.array([1000,1400])
s = np.array(sD.getDSignal(evalTime=t[0],dTime=t[1]-t[0]))
y = np.mean(s)
ystd = np.std(s)

print(f"shift for BSA monolayer: {y:.1f} +- {ystd:.1f} nm")


# %%
plt.show()


