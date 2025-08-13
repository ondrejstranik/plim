''' make statistics of the spots signals'''

#%%
import numpy as np
import csv
from pathlib import Path

# %% set parameters
#ffolder = r'D:\ondra\LPI\25-07-02 dna\results\redDot'
ffolder = r'D:\ondra\LPI\25-07-02 dna\results\redDotEnd'
ffile = r'infoTable.txt'

myPath = Path(ffolder)

colorRef = '#ffffff'
colorNdm = '#ff0000'

#color = colorNdm
#color = colorRef
color = colorNdm

#%% process

dSignal = []
noise = []

with open(myPath / ffile) as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')
    for row in spamreader:
        if row == []: continue
        if (row[1]==color) and row[2]=='True':
            dSignal.append(float(row[3]))
            noise.append(float(row[4]))

dSignal = np.array(dSignal)
noise = np.array(noise)

meanDSignal = np.mean(dSignal)
meanNoise = np.mean(noise)

print(f'mean dSignal {meanDSignal} nm')
print(f'mean noise {meanNoise} nm')
print(f'spot signal variation{np.std(dSignal)} nm')
print(f'spot noise variation{np.std(noise)} nm')
print(f'number of spots {dSignal.shape[0]}')



# %%
