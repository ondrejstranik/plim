''' code to evaluate the sensitivity'''
#%% import
from plim.algorithm.spotSpectra import SpotSpectra
import napari
import numpy as np
from spectralCamera.instrument.sCamera.sCameraFromFile import SCameraFromFile
from plim.algorithm.fileData import FileData
import matplotlib.pyplot as plt


#spectral camera system
rFolder = r'F:\ondra\LPI\plim\DATA\filterBased\26-03-13 sensitivity\raw2'
dFolder = r'F:\ondra\LPI\plim\DATA\filterBased\26-03-13 sensitivity'
dMName = 'Experiment2'

rFolder = r'F:\ondra\LPI\plim\DATA\ifcBased\26-03-13 sensitivity_ebeam\raw2'
dFolder = r'F:\ondra\LPI\plim\DATA\ifcBased\26-03-13 sensitivity_ebeam'
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

# %% show noise
nPoint = 20
nPoint = 40

sigMean = np.mean(sD.signal[:nPoint,:], axis=0)
sigStd = np.std(sD.signal[:nPoint,:], axis=0)
sigStdAve = np.mean(sigStd)

data = (sD.signal[:nPoint,:]-sigMean)
n_traj, n_steps = data.shape
t = np.arange(n_steps)

# Build 2D histogram: time on x-axis, value on y-axis
hist, xedges, yedges = np.histogram2d(
    np.repeat(t, n_traj),          # time indices repeated for each trajectory
    data.T.ravel(),                 # all values flattened
    bins=[n_steps, 100]
)

plt.imshow(hist, origin='lower', aspect='auto',
           extent=[yedges[0], yedges[-1], 0, n_steps],
           cmap='inferno')
plt.colorbar(label='Count')
plt.ylabel('Spot #')
plt.xlabel('signal /nm')
plt.title('2D histogram of signal')
plt.show()

print(f"Instrument noise: {sigStdAve:.1e}")
# %%

sD.setOffset()

y = sD.signal -sD.getOffset()
x = sD.time -sD.time[0]

fig, ax = plt.subplots()
ax.plot(x,y)
plt.xlabel('time / s')
plt.ylabel('signal /nm')
plt.title('Sensitivity calibration')
plt.show()

# %%

t = np.array([50,240, 400, 550])

t = np.array([50,180,310, 470])


t = t + sD.time[0] 


n = 4.5e-3
nn = np.array([0, n/4, n/2, n])
s = np.array([sD.getDSignal(evalTime=t[0],dTime=_t-t[0]) for _t in t])

y = np.mean(s,axis=1)
slope, intercept = np.polyfit(nn, y, 1)  # 1 = linear
print(f"Slope: {slope:.4f}")

fig, ax = plt.subplots()
ax.plot(nn,s)
plt.xlabel(' $\Delta$ n / RIU')
plt.ylabel('signal /nm')
plt.title(f'Sensitivity {slope:.0f} nm/RIU')
plt.show()

print(f"Instrument limit: {sigStdAve/slope:.1e}")

# %%


