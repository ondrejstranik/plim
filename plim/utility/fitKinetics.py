'''' script to fit binding kinetics data'''
#%%
import numpy as np

from plim.algorithm.fileData import FileData
from pathlib import Path
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.special import erf
from plim.algorithm.kineticFit import KineticFit



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
'''
def funcPFO(x,x0,a=1,b=1):
    res = x*0
    xb = x>=x0
    xa = x< x0
    res[xa] = 0
    res[xb] = a*(1-np.exp(-(x[xb]-x0)*b))
    return res
'''

def funcPFO(x,x0,a=1,b=1):
    xMod = (erf((x-x0)/10)+1)/2*(x-x0)
    res = a*(1-np.exp(-xMod*b))
    return res    


def funcP1(x,y0,c=0):
    res = y0 + c*x
    return res

def funcBK(x,x0,y0,a=1,b=1, c= 0):
    return funcP1(x,y0,c) + funcPFO(x,x0,a,b)


fTime = np.array([200,1800])
fTimeMask = (time>fTime[0]) & (time<fTime[1])

x = time[fTimeMask]

y0 = sig[fTimeMask,0]
popt0,pocv0 = curve_fit(funcBK,x,y0,p0 = (700,0,1.0,1/300,1))

y1 = sig[fTimeMask,5]
popt1,pocv1 = curve_fit(funcP1,x,y1,p0 = (0,0))



#%%

fig, ax = plt.subplots()
ax.plot(x,y0)
#ax.plot(x,y1)


ax.plot(x,funcBK(x,*popt0))
print(popt0)
ax.plot(x,funcP1(x,popt0[1],popt0[4]))
print(popt0)


#ax.plot(x,funcP1(x,*popt1))
#print(popt1)
ax.set_xlabel('time /s')
ax.set_ylabel('signal /nm')
ax.set_title(f'idx ={idx[0]}, tau = {1/popt0[3]:.1f} s , sig = {popt0[2]:.2f} nm')


# %%

tauList = []
sigList = []


fig, ax = plt.subplots()

for ii in range(len(idx)-1):
    y = sig[fTimeMask,ii]
    popt,pocv = curve_fit(funcBK,x,y,p0 = (700,0,1.0,1/300,0))
    tauList.append(1/popt[3])
    sigList.append(popt[2])

    ax.plot(x,y)
    ax.plot(x,funcBK(x,*popt))
    ax.plot(x,funcP1(x,popt[1],popt[4]))

ax.set_xlabel('time /s')
ax.set_ylabel('signal /nm')



ax.set_title(f'tau = {np.array(tauList).mean():.1f} +- {np.array(tauList).std():.1f} s')

plt.show()
# %%

kFit = KineticFit()
kFit.setSignal(sig[fTimeMask,:-1])
kFit.setTime(time[fTimeMask])
kFit.setFitParameter(fitEstimate=(700,1,300,0,0))

kFit.calculateFit()

fig, ax = plt.subplots()

# plot result

for ii in range(kFit.fitParam.shape[0]):
    ax.plot(kFit.time,kFit.signal[:,ii])
    ax.plot(kFit.time,kFit.bcgFunction(kFit.time,*kFit.fitParam[ii,-2:]))
    ax.plot(kFit.time,kFit.fitFunction(kFit.time,*kFit.fitParam[ii,:]))

ax.set_xlabel('time /s')
ax.set_ylabel('signal /nm')

ax.set_title(f'tau = {kFit.fitParam[:,2].mean():.1f} +- {kFit.fitParam[:,2].std():.1f} s')

plt.show()




# %%
