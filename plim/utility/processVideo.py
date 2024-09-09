''' script to process videos of hyperspectral images'''
#%%
# import and parameter definition

import numpy as np
import plim
from plim.gui.spectralViewer.plasmonViewer import PlasmonViewer
import napari

from plim.gui.signalViewer.signalWidget import SignalWidget
from plim.gui.signalViewer.flowRateWidget import FlowRateWidget

ffolder = r'F:\ondra\LPI\24-08-28 spr_variable_array\iso_h20_1to4'
ffile = r'Experiment1'
nameSet = {'flow':'_flowData.npz',
            'image': '_image.npz',
            'spot': '_spotData.npz'}

_dp = np.linspace(0.4,1,25) # spacing between the pillars

dp = np.delete(_dp,4)

#%% load the data 

# load image
container1 = np.load(ffolder + '/' + ffile + nameSet['image'])
spotPosition = container1['arr_0']
image = container1['arr_1']
w = container1['arr_2']



# load flow
container2 = np.load(ffolder + '/' + ffile + nameSet['flow'])
flow = container2['arr_0']
time = container2['arr_1']

# load spot
container3 = np.load(ffolder + '/' + ffile + nameSet['spot'])
spot = container3['arr_0']


#%% show the data 

#sViewer = PlasmonViewer(image, w)
#sViewer.pointLayer.data = spotPosition

viewer = napari.Viewer()
viewer.add_image(image)
viewer.add_points(spotPosition)

sV = SignalWidget(signal=spot,time= time)
sV.show()

fV = FlowRateWidget(signal=flow, time = time)
fV.show()

napari.run()


# %% calculate spectra
from plim.algorithm.spotSpectra import SpotSpectra

ss = SpotSpectra(wxyImage=image, spotPosition=spotPosition)
ss.setMask(pxAve=5,pxBcg=4,pxSpace=3)
ss.darkCount = 120
ss.setSpot(spotPosition[[*(np.arange(4)+15),
                         *(np.arange(5)+10),
                         *(np.arange(5)+5),
                         *(np.arange(5)+0),
                         *(np.arange(5)+19),
]])

ss.calculateSpectra()
spectra = np.array(ss.getA())

#%% post process the spectra

# restrict wavelength
ws = (w>500) * (w<720)
X = w[ws]
# normalise the spectra
Y = spectra[:,ws].T
Y = Y - np.min(Y,axis=0)
Y = Y/np.max(Y,axis=0)


# %% show the data
import matplotlib.pyplot as plt
plt.figure()
ax = plt.subplot(111)
ax.plot(X,Y+ np.arange(Y.shape[1]))

# first order diffraction
for ii,dpValue in enumerate(dp*1000*1.33):
    ax.plot([dpValue,dpValue],[ii,ii+1], 'k.-')

# second order diffraction
for ii,dpValue in enumerate(1/2*dp*1000*1.33):
    ax.plot([dpValue,dpValue],[ii,ii+1], 'k.-')

# Shrink current axis by 20%
box = ax.get_position()
ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
# Put a legend to the right of the current axis
ax.legend(np.round(dp*1000), loc='center left', bbox_to_anchor=(1, 0.5))
ax.set_title('normalised absorption')
ax.set_xlabel('wavelength')
ax.set_xlim(X[-1],X[0])

#%% get spectra from the whole video
import pathlib
import re

ffolder = r'F:\ondra\LPI\24-08-28 spr_variable_array'

# get the file name and the corresponding time
vfolder = pathlib.Path(ffolder)
fileList = list(vfolder.glob("time_*.npy"))
fileName = [x.parts[-1] for x in fileList]
fileTime = [int(re.search('\d+',x).group(0)) for x in fileName]
# sorted order of the file according their time
sortedIdx = np.argsort(fileTime)

if False:
    spectraAll =  np.empty((len(sortedIdx),*spectra.shape))
    for ii in range(len(sortedIdx)):
        _image = np.load(fileList[sortedIdx[ii]])
        ss.setImage(_image)
        ss.calculateSpectra()
        _spectra = np.array(ss.getA())
        spectraAll[ii,:,:] = _spectra
        print(f'file number {ii} out of {len(sortedIdx)}')
        np.save(ffolder + '/spectraAll.npy',spectraAll)
else:
    spectraAll = np.load(ffolder + '/spectraAll.npy')

# %% make fit and show the signal
from plim.algorithm.plasmonFit import PlasmonFit

sTime = (np.array(fileTime) - fileTime[0])/1e9

spotIdxList = [4,5,8,9,11,12,13,14]
signalAll = np.empty((len(spotIdxList),spectraAll.shape[0]))

wst = [565,550,560,575,575,575,575,575]
wsp = [690,700,700,700,700,700,700,710]
pw = [40,40,30,40,40,40,50,50]
wg = [605,630,620,625,630,635,655,660]
color = [[1,0,0,1],[0,1,0,1], [0,0,1,1], [1,1,0,1],[1,0,1,1],[0,1,1,1],[0.5,0.5,0.5,1],[1,1,1,1]]

for ii,spotIdx in enumerate(spotIdxList):
    print(f'grating period {dp[spotIdx]}')

    pF = PlasmonFit(wavelength = w, spectraList = spectraAll[:,spotIdx,:])
    pF.wavelengthStartFit = wst[ii]
    pF.wavelengthStopFit = wsp[ii]
    pF.peakWidth = pw[ii]
    pF.wavelengthGuess = wg[ii]
    pF.calculateFit()
    signalAll[ii,:] = pF.getPosition()


# %% show the signal

#plt.figure()
#ax = plt.subplot(111)
#ax.plot(sTime, signalAll.T)
print(f'grating period {dp[spotIdxList]}')
sV = SignalWidget()
sV.sD.signalColor = color
sV.setData(signal=signalAll.T,time= sTime)
sV.show()


# %% show the legend
fig, ax = plt.subplots()

xvalue = [str(int(ii)) for ii in (1000*dp[spotIdxList]).tolist()]

yvalue = np.ones(len(spotIdxList))
bar_colors = color
ax.bar(xvalue, yvalue, color=bar_colors)

# %% LoD calculation
sBase = signalAll[:,sTime<90]
sStd = np.std(sBase, axis=1)
print(f'grating period {dp[spotIdxList]}')
print(f'wavelength {signalAll[:,0]}')
print(f'std : {sStd}')

#%% conclusion

_shift = np.array([8.1,7.2,20.0,15.6,16.6,16.4,14.2,15.7])
Sb = _shift / 0.018 
print(f'bulk sensitivity {Sb}')

LoD = 3*sStd/Sb
print(f'LoD = {LoD} RIU ')


# best 700 idx= 4
# iso:h20 4:1 --> delta n = 0.018
LoD = 3*sStd[4]/(16/0.018)
print(f'LoD @700 = {LoD} RIU or {LoD*1e6} RU')

# 525 idx= 0
LoD = 3*sStd[0]/(8/0.018)
print(f'LoD @525 = {LoD} RIU or {LoD*1e6} RU')

# estimated nanoparticle
LoD = 3*0.06/100
print(f'LoD Nanoparticle = {LoD} RIU or {LoD*1e6} RU')



# %%
