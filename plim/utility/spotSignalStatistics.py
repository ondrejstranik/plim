''' make statistics of the spots signals'''

#%%
import numpy as np
import csv
from pathlib import Path
from plim.algorithm.spotData import SpotData

# %% set parameters
#ffolder = r'D:\ondra\LPI\25-07-02 dna\results\redDot'
ffolder = r'F:\ondra\LPI\25-07-02 dna\results\redDotEnd'
ffile = r'infoTable.txt'

myPath = Path(ffolder)

colorRef = '#ffffff'
colorNdm = '#ff0000'

#color = colorNdm
#color = colorRef
colorSel = colorNdm

#%% process

sD = SpotData()

name, color, dSignal, noise = sD.loadInfoFile(ffolder,ffile)

_sel= [True if ii==colorSel else False for ii in color]

dSignal = dSignal[_sel]
noise = noise[_sel]

print(f'dSignal {dSignal}')

meanDSignal = np.mean(dSignal)
meanNoise = np.mean(noise)

print(f'mean dSignal {meanDSignal} nm')
print(f'mean noise {meanNoise} nm')
print(f'spot signal variation{np.std(dSignal)} nm')
print(f'spot noise variation{np.std(noise)} nm')
print(f'number of spots {dSignal.shape[0]}')



# %%
