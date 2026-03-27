''' code to evaluate the surface sensitivity with BSA'''
#%% import
from plim.algorithm.spotSpectra import SpotSpectra
import napari
import numpy as np
from spectralCamera.instrument.sCamera.sCameraFromFile import SCameraFromFile
from plim.algorithm.fileData import FileData
import matplotlib.pyplot as plt


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

fig, ax = plt.subplots()
ax.plot(x,y.T)
plt.xlabel('wavelength / nm')
plt.ylabel('Transmission')
plt.show()

# %% show the image with a mask

mask = sS.getMask()
mask[mask==2]=0

viewer = napari.Viewer()
viewer.add_image(im)
viewer.add_image(mask, opacity=0.08)
viewer.add_image(np.sum(sImage, axis=0))

# %% show bsa adsorption

sD.time0 = sD.time[0]
sD.setOffset(950)

y = sD.signal -sD.getOffset()
x = sD.time -sD.time[0]

fig, ax = plt.subplots()
ax.plot(x,y)
plt.xlabel('time / s')
plt.ylabel('signal /nm')
plt.xlim([920,1500])
plt.ylim([-1,9])

plt.title('Surface Sensitivity calibration')
plt.show()

# %% calculate sensitivity

t = np.array([1000,1400])
s = np.array(sD.getDSignal(evalTime=t[0],dTime=t[1]-t[0]))
y = np.mean(s)
ystd = np.std(s)

print(f"shift for BSA monolayer: {y:.1f} +- {ystd:.1f} nm")


# %%


