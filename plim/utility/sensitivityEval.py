''' code to evaluate the sensitivity'''
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
rFolder = r'F:\ondra\LPI\plim\DATA\filterBased\26-03-13 sensitivity\raw2'
dFolder = r'F:\ondra\LPI\plim\DATA\filterBased\26-03-13 sensitivity'
dMName = 'Experiment2'

#rFolder = r'F:\ondra\LPI\plim\DATA\ifcBased\26-03-13 sensitivity_ebeam\raw2'
#dFolder = r'F:\ondra\LPI\plim\DATA\ifcBased\26-03-13 sensitivity_ebeam'
#dMName = 'Experiment2'

#dFolder = r'F:\ondra\LPI\plim\DATA\ifcBased\26-03-13 Au80 sensitivity\processed'
#dFolder = r'F:\ondra\LPI\plim\DATA\ifcBased\26-03-13 sensitivity_ebeam\raw2'


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

# %% show noise
nPoint0 = 20
nPoint1 = 40

sigMean = np.mean(sD.signal[nPoint0:nPoint1,:], axis=0)
sigStd = np.std(sD.signal[nPoint0:nPoint1,:], axis=0)
sigStdAve = np.mean(sigStd)

data = (sD.signal[nPoint0:nPoint1,:]-sigMean)
n_traj, n_steps = data.shape
t = np.arange(n_steps)

# Build 2D histogram: time on x-axis, value on y-axis
hist, xedges, yedges = np.histogram2d(
    np.repeat(t, n_traj),          # time indices repeated for each trajectory
    data.T.ravel(),                 # all values flattened
    bins=[n_steps, 100]
)

fig2, ax2 = plt.subplots()
im2 = ax2.imshow(hist, origin='lower', aspect='auto',
                  extent=[yedges[0], yedges[-1], 0, n_steps],
                  cmap='inferno')
fig2.colorbar(im2, ax=ax2, label='Count')
ax2.set_ylabel('Spot #')
ax2.set_xlabel('signal /nm')
ax2.set_title('2D histogram of signal')

print(f"Instrument noise: {sigStdAve:.1e}")
# %% show sensitivity calibration

sD.setOffset(useOffset=True, alignTime=75)

y = sD.signal -sD.getOffset()
x = sD.time -sD.time[0]

fig3, ax3 = plt.subplots()
ax3.plot(x,y)
ax3.set_xlabel('time / s')
ax3.set_ylabel('signal /nm')
ax3.set_title('Sensitivity calibration')

# %% calculate sensitivity

t = np.array([50,240, 400, 550])

t = np.array([50,180,310, 470])


t = t + sD.time[0] 


n = 4.5e-3
nn = np.array([0, n/4, n/2, n])
s = np.array([sD.getDSignal(evalTime=t[0],dTime=_t-t[0]) for _t in t])

y = np.mean(s,axis=1)
slope, intercept = np.polyfit(nn, y, 1)  # 1 = linear
print(f"Slope: {slope:.4f}")

fig4, ax4 = plt.subplots()
ax4.plot(nn,s)
ax4.set_xlabel(' $\Delta$ n / RIU')
ax4.set_ylabel('signal /nm')
ax4.set_title(f'Sensitivity {slope:.0f} nm/RIU')

print(f"Instrument limit: {sigStdAve/slope:.1e}")

# %%
plt.show()


