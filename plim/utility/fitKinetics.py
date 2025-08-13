'''' script to fit binding kinetics data'''
#%%
import numpy as np

from plim.algorithm.fileData import FileData
from pathlib import Path
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.special import erf


ffile = r'Experiment1'
ffolder = r'F:\ondra\LPI\25-07-02 dna'

#%%

fData = FileData()
fData.loadAllFile(ffolder,fileMainName=ffile)


#%% pre-process

fData.spotData.time0 = fData.flowData.time[0]
fData.spotData.setOffset(alignTime=700, range=5)
time = fData.spotData.time-fData.spotData.time0
idx = np.array((68,58,50,40,34,65))
sig = fData.spotData.signal[:,idx]-fData.spotData.offset[idx]
sig = fData.spotData.signal[:,idx]-fData.spotData.offset[idx]

#%%
def func(x,x0,y0,a=1,b=1, c= 0):
    
    res = x*0
    xb = x>=x0
    xa = x< x0
    res[xa] = y0 + c*x[xa]
    res[xb] = y0 + a*(1-np.exp(-(x[xb]-x0)*b)) + c*x[xb]
    return res

def funcPFO(x,x0,a=1,b=1):
    res = x*0
    xb = x>=x0
    xa = x< x0
    res[xa] = 0
    res[xb] = a*(1-np.exp(-(x[xb]-x0)*b))
    return res

def funcP1(x,y0,c=0):
    res = y0 + c*x
    return res

def funcBK(x,x0,y0,a=1,b=1, c= 0):
    return funcP1(x,y0,c) + funcPFO(x,x0,a,b)


fTime = np.array([500,1200])
fTimeMask = (time>fTime[0]) & (time<fTime[1])

x = time[fTimeMask]

y0 = sig[fTimeMask,0]
popt0,pocv0 = curve_fit(funcBK,x,y0,p0 = (700,0,1.0,1/300,1))

y1 = sig[fTimeMask,5]
popt1,pocv1 = curve_fit(funcP1,x,y1,p0 = (0,0))



#%%

#fig, ax = plt.subplots()
ax.plot(x,y0)
ax.plot(x,y1)


ax.plot(x,funcBK(x,*popt0))
print(popt0)

ax.plot(x,funcP1(x,*popt1))
print(popt1)


# %%
