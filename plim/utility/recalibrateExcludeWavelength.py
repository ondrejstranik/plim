'''
re-calibrate recorded photonfocus spectral cubes without some bands (e.g. 700 nm)
and compare the plasmon signal of the original and the new calibration

the recorded files (raw/time_*.npy) are already spectral cubes:
    cube[w,y,x] = sum_p (rawPixel[p,y,x] - dark) * C[p,w]     C = coef_pixels (25x25)
the unmixing is linear, so the raw super-pixel values are recovered with inv(C)
and the cube is recalculated with the new calibration - exactly the same as
CalibratePFImage(excludeWavelength=[...]) does on a live image:
    - the row of the raw filter pixel with transmission peak closest to the
      excluded wavelength is set to zero (it does not leak into the other bands)
    - the band closest to the excluded wavelength is removed
    cubeNew = cube @ inv(C) @ Cnew[:, bandMask]   (one 25 x 24 matrix)

the signal of both calibrations is then calculated with the same spot positions /
fit parameters as the recording (Experiment1_image.npz, Experiment1_fit.npz)

output (in dataFolder/recalibrated_<tag>):
    raw/time_*.npy, raw/wavelength.npy  ... re-calibrated spectral cubes
    <name>_orig_spotData.npz            ... signal original calibration (offline)
    <name>_<tag>_spotData.npz           ... signal new calibration
    <name>_<tag>_image.npz/_fit.npz     ... spots/fit parameter with new wavelengths
                                            (for loading in the signal analyser)
    calibrationComparison.png
'''
#%% parameters
import sys
from pathlib import Path
import shutil
import numpy as np
import matplotlib.pyplot as plt

dataFolder = Path(r'F:\ondra\LPI\plim\DATA\filterBased\26-10-27 cabraDNA')
if len(sys.argv) > 1 and Path(sys.argv[1]).is_dir(): # data folder from the command line
    dataFolder = Path(sys.argv[1])
fileMainName = 'Experiment1'
excludeWavelength = [700] # [nm]
saveCube = True # save the re-calibrated cubes

# spot-spectra parameters which are not stored in the _fit.npz file
# (values from runRealMSC.py used for the recording)
spectraSigma = 1
circle = False

tag = 'no' + '_'.join(str(w) for w in excludeWavelength)
rawFolder = dataFolder / 'raw'
outFolder = dataFolder / ('recalibrated_' + tag)
outRawFolder = outFolder / 'raw'

#%% calibration matrices
try:
    import PFPyCameraLib
except Exception:
    # camera SDK is not needed to read the calibration xml
    from unittest.mock import MagicMock
    sys.modules['PFPyCameraLib'] = MagicMock()
from spectralCamera.instrument.camera.pfCamera.photonFocus import Photonfocus

pf = Photonfocus()
pf.GetCalibrationData()
C = pf.pixelChar['coef_pixels']
wv = pf.pixelChar['wv']

wvRecorded = np.load(rawFolder / 'wavelength.npy')
if not np.allclose(wvRecorded, wv):
    raise ValueError('recorded wavelengths do not match the calibration file')

bandMask = np.ones(len(wv), dtype=bool)
for w in excludeWavelength:
    bandMask[np.argmin(np.abs(wv - w))] = False

filterPeak = pf.pixelChar['w'][np.argmax(pf.pixelChar['filterchar'], axis=0)]
Cnew = C.copy()
for w in excludeWavelength:
    p = np.argmin(np.abs(filterPeak - w))
    Cnew[p] = 0
    print(f'excluded band {wv[~bandMask]} nm, raw filter pixel #{p} (peak {filterPeak[p]:.0f} nm)')

M = np.linalg.inv(C) @ Cnew[:, bandMask] # (25, nBandNew)
wvNew = wv[bandMask]
print(f'cond(C) = {np.linalg.cond(C):.0f}')

def recalibrate(cube):
    ''' cube (25,Y,X) -> cube (nBandNew,Y,X) '''
    return np.tensordot(M, cube, axes=(0, 0))

#%% spot / fit parameters of the recording
from plim.algorithm.fileData import FileData

def getProcessor(wavelength, image):
    ''' spotSpectra and plasmonFit set as in the recording '''
    fd = FileData()
    fd.loadImageFile(folder=str(dataFolder), fileMainName=fileMainName)
    fd.loadFitFile(folder=str(dataFolder), fileMainName=fileMainName)
    sS, pF = fd.spotSpectra, fd.pF
    sS.spectraSigma = spectraSigma
    sS.setImage(image)
    sS.setMask(circle=circle)
    sS.setWavelength(wavelength)
    pF.setWavelength(wavelength)
    return sS, pF

def getSignal(sS, pF, image):
    sS.setImage(image)
    sS.calculateSpectra()
    pF.setSpectra(sS.getSpectra())
    pF.calculateFit()
    return np.array(pF.getPosition())

#%% process all files
fileList = sorted(rawFolder.glob('time_*.npy'), key=lambda f: int(f.stem.split('_')[1]))
nFile = len(fileList)
fileTime = np.array([int(f.stem.split('_')[1]) for f in fileList]) / 1e9 # [s]

if saveCube:
    outRawFolder.mkdir(parents=True, exist_ok=True)
    np.save(outRawFolder / 'wavelength.npy', wvNew)

cube = np.load(fileList[0])
sSo, pFo = getProcessor(wv, cube)
sSn, pFn = getProcessor(wvNew, recalibrate(cube))
nSpot = len(sSo.spotPosition)

signalOrig = np.zeros((nFile, nSpot))
signalNew = np.zeros((nFile, nSpot))

for ii, f in enumerate(fileList):
    cube = np.load(f)
    cubeNew = recalibrate(cube)
    if saveCube:
        np.save(outRawFolder / f.name, cubeNew)
    signalOrig[ii] = getSignal(sSo, pFo, cube)
    signalNew[ii] = getSignal(sSn, pFn, cubeNew)
    if ii % 50 == 0:
        print(f'{ii} / {nFile}', flush=True)

#%% save signals and parameters
outFolder.mkdir(parents=True, exist_ok=True)
for name, sig, sS, pF in [('orig', signalOrig, sSo, pFo), (tag, signalNew, sSn, pFn)]:
    fd = FileData(spotSpectra=sS, plasmonFit=pF)
    fd.spotData.signal = sig
    fd.spotData.time = fileTime
    fd.saveSpotFile(folder=str(outFolder), fileMainName=f'{fileMainName}_{name}')
    fd.saveImageFile(folder=str(outFolder), fileMainName=f'{fileMainName}_{name}')
    fd.saveFitFile(folder=str(outFolder), fileMainName=f'{fileMainName}_{name}')
for suffix in ['_flowData.npz', '_injectionData.txt', '_info.dat']:
    src = dataFolder / (fileMainName + suffix)
    if src.is_file():
        shutil.copy(src, outFolder / (f'{fileMainName}_{tag}' + suffix))

#%% comparison
def noise(sig):
    ''' frame-to-frame noise per spot [nm] (robust, insensitive to slow binding) '''
    d = np.diff(sig, axis=0)
    return 1.4826 * np.median(np.abs(d - np.median(d, axis=0)), axis=0) / np.sqrt(2)

ok = np.all(np.isfinite(signalOrig) & np.isfinite(signalNew), axis=0)
diff = signalNew - signalOrig
offset = np.median(diff, axis=0)
relSig = lambda s: s - np.median(s[:20], axis=0) # signal relative to the start
dRel = relSig(signalNew) - relSig(signalOrig)
nO, nN = noise(signalOrig), noise(signalNew)

print(f'spots valid: {ok.sum()} / {nSpot}')
print(f'offset new-orig [nm]: median {np.median(offset[ok]):.3f}, range {offset[ok].min():.3f} .. {offset[ok].max():.3f}')
print(f'change of the relative signal (shift from start) [nm]: rms {np.sqrt(np.mean(dRel[:, ok]**2)):.4f}, max {np.abs(dRel[:, ok]).max():.4f}')
print(f'noise [nm] orig: median {np.median(nO[ok]):.4f}   {tag}: median {np.median(nN[ok]):.4f}   ratio {np.median(nN[ok]/nO[ok]):.3f}')

# check: offline original calibration vs. live recorded signal
live = FileData()
live.loadSpotFile(folder=str(dataFolder), fileMainName=fileMainName)
if live.spotData.signal is not None and len(live.spotData.signal):
    liveInterp = np.array([np.interp(fileTime, live.spotData.time, s) for s in live.spotData.signal.T]).T
    m = (fileTime > live.spotData.time[0]) & (fileTime < live.spotData.time[-1])
    print(f'check offline orig vs live signal [nm]: median |diff| {np.median(np.abs(signalOrig[m] - liveInterp[m])):.4f}')

# figure
t = (fileTime - fileTime[0]) / 60
iSpot = np.where(ok)[0][np.argsort(np.abs(relSig(signalOrig)[-1, ok]))[-3:]] # 3 spots with largest shift
fig, ax = plt.subplots(2, 2, figsize=(13, 8))
for k, s in enumerate(iSpot):
    ax[0, 0].plot(t, relSig(signalOrig)[:, s], color=f'C{k}', label=f'spot {s} orig')
    ax[0, 0].plot(t, relSig(signalNew)[:, s], '--', color=f'C{k}', label=f'spot {s} {tag}')
ax[0, 0].set(xlabel='time [min]', ylabel='shift from start [nm]', title='signal')
ax[0, 0].legend(fontsize=7)
ax[0, 1].plot(t, dRel[:, ok], lw=0.5, alpha=0.4)
ax[0, 1].set(xlabel='time [min]', ylabel=f'{tag} - orig [nm]', title='difference of the relative signal (all spots)')
ax[1, 0].hist(offset[ok], 40)
ax[1, 0].set(xlabel=f'absolute offset {tag} - orig [nm]', ylabel='spots', title='peak position offset')
ax[1, 1].plot(nO[ok], nN[ok], '.')
lim = [0, max(nO[ok].max(), nN[ok].max()) * 1.05]
ax[1, 1].plot(lim, lim, 'k--', lw=0.8)
ax[1, 1].set(xlim=lim, ylim=lim, xlabel='noise orig [nm]', ylabel=f'noise {tag} [nm]', title='frame-to-frame noise per spot')
fig.tight_layout()
fig.savefig(outFolder / 'calibrationComparison.png', dpi=120)
print(f'results in {outFolder}')
plt.show()
