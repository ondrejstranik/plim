'''
script to test fitting of kinetics binding with mass transport limitation
'''
#%%

from plim.utility.preprocessSignal import PreprocessSignal
from plim.utility.bindingModelFitter import BindingModelFitter
import pyqtgraph as pg
import numpy as np
import matplotlib.pyplot as plt


folder = r'F:\ondra\LPI\plim\DATA\ifcBased\26-02-18 B8-BSA\processed'
fileMainName = 'Experiment1'
pS = PreprocessSignal(folder=folder, fileMainName=fileMainName)
pS.alignData((150,550))
pS.showGrid()
pS.showSignal(axis=1,idx=[1,3])


# %% show signal data difference with cut along time 

# normalise the sensitivity/coverage
signalN = pS.signalGrid/pS.signalGrid[-1,:,:]

# signal difference min
sigMin = 0.05

# add graph - line along time and x
graph = pg.plot()
graph.setTitle(f'Signal difference along rows')
graph.setLabel('left', 'Signal', units='nm')
graph.setLabel('bottom', 'column')

nTime = signalN.shape[0]
nRow = signalN.shape[1]
for jj in range(nRow):
    for ii in range(nTime):
        normSig = (signalN[ii,jj,:]-signalN[ii,jj,0])
        if normSig[-1] > sigMin:
                graph.plot(normSig+jj*0.1, pen=(jj,nRow))

#%% fitting

fitterSet = []
t_exp = pS.time 
BOUNDS = {
        "Req": (1e-6, 20),
        "C1":  (0.0,  1.0),
        "ka2": (1e-6, 1e0),
        "kap": (1e-6, 1e0),
        "t0":  (None, None),   # set dynamically from t_exp
    }

GUESS = {
        "Req": 0.9,
        "C1":  0.6,
        "ka2": 0.5,
        "kap": 0.1,
        "t0":  220, 
    }



for jj in range(pS.nRow):
    for ii in range(pS.nColumn):
        y_exp = pS.signalGrid[:,jj,ii]
        fitter = BindingModelFitter(
                t_exp, y_exp,
                fixed={},          # fix t0 at 2.0
                guess=GUESS,
                bounds= BOUNDS,
                n_starts= 15,                
            )
        fitter.fit()
        if ii==0 and jj==0:
            _fig, _ax = fitter.plot()
        else:
            fitter.plot(ax=_ax)
        fitterSet.append(fitter)
        print(f'fit position {jj}, {ii}')

# %% assign properly the parameters


t0 = np.zeros((pS.nRow,pS.nColumn))
kap = np.zeros_like(t0)
ka2 = np.zeros_like(t0)
C1 = np.zeros_like(t0)

ff = 0
for jj in range(pS.nRow):
    for ii in range(pS.nColumn):
        t0[jj,ii] =  fitterSet[ff].result_["params"]["t0"]
        C1[jj,ii] = fitterSet[ff].result_["params"]["C1"]
        kap[jj,ii] =  np.max((fitterSet[ff].result_["params"]["kap"],fitterSet[ff].result_["params"]["ka2"])) 
        ka2[jj,ii] =  np.min((fitterSet[ff].result_["params"]["kap"],fitterSet[ff].result_["params"]["ka2"])) 
        # associate C1 with kap
        if fitterSet[ff].result_["params"]["kap"]== kap[jj,ii]:
            C1[jj,ii] = C1[jj,ii]
        else:
            C1[jj,ii] = 1- C1[jj,ii]

        ff += 1

# %%

fig, ax = plt.subplots()
im = ax.imshow(dt0, cmap="viridis", origin="lower")
ax.invert_yaxis()
fig.colorbar(im, ax=ax)
plt.xlabel("x")
plt.ylabel("y")
plt.title("t0 ")
plt.tight_layout()
#plt.show()


# %%
X, Y = np.meshgrid(np.arange(pS.nColumn), np.arange(pS.nRow))

fig, ax = plt.subplots(subplot_kw={"projection": "3d"})

surf = ax.plot_surface(X, Y, t0,
    cmap="viridis",
    alpha=0.8,          # transparency
    rstride=1,          # row sampling (1 = every row)
    cstride=1,          # col sampling
)
fig.colorbar(surf, ax=ax, shrink=0.5)   # add colorbar

plt.show()
# %%

dt0 = t0[:,0:-1]- t0[:,1:]

vel = 1/dt0
# %%

velM = np.median(vel,axis=1)

# %%

vel = [] 
x = np.arange(pS.nColumn)

fig, ax = plt.subplots()

for jj in range(pS.nRow):
    coeffs = np.polyfit(x, t0[jj,:], deg=1)   # returns [slope, intercept]
    slope, intercept = coeffs
    vel.append(slope)
    ax.plot(x, t0[jj,:], label = f'{slope}')

fig.legend()
vel = np.array(vel)    
# %%

x = np.arange(pS.nRow)

fig, ax = plt.subplots()
ax.plot(x, -vel)
# %%

kapM = np.median(kap, axis=1)
fig, ax = plt.subplots()
ax.plot(x, kapM)

# %%
