'''
script to test fitting of kinetics binding with mass transport limitation
'''
#%%

from plim.utility.preprocessSignal import PreprocessSignal
from plim.utility.bindingModelSetFitter import GlobalLocalFitter
import pyqtgraph as pg
import numpy as np
import matplotlib.pyplot as plt


folder = r'F:\ondra\LPI\plim\DATA\ifcBased\26-02-18 B8-BSA\processed'
fileMainName = 'Experiment1'
pS = PreprocessSignal(folder=folder, fileMainName=fileMainName)
pS.alignData((150,550))
pS.showGrid()
pS.showSignal(axis=1,idx=[1,3])

#%% fitting

fitterSet = []
t_exp = pS.time 
BOUNDS = {
        "Req": (1e-6, 20),
        "C1":  (0.0,  1.0),
        "ka2": (1e-3, 1e-1),
        "kap": (1e-2, 1e0),
        "t0":  (200, 250),   # set dynamically from t_exp
    }

GUESS = {
        "Req": 0.9,
        "C1":  0.6,
        "ka2": 0.01,
        "kap": 0.3,
        "t0":  220, 
    }

 
datasets = []
for ii in range(pS.nColumn):
    for jj in range(pS.nRow):
        datasets.append((pS.time, pS.signalGrid[:,jj,ii]))

fitter = GlobalLocalFitter(
    datasets=datasets,
    global_params=["ka2"],   # shared across all curves
    local_params=["kap", "Req", "t0", "C1"],            # fitted per curve
    fixed={},
    bounds= BOUNDS,
    guess= GUESS,
)

fitter.fit()
fitter.summary()
fitter.plot()

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
        # identify uniquely kap and ka2
        if C1[jj,ii] >0.5:
            kap[jj,ii] =  fitterSet[ff].result_["params"]["kap"]
            ka2[jj,ii] =  fitterSet[ff].result_["params"]["ka2"]
        else:
            kap[jj,ii] =  fitterSet[ff].result_["params"]["ka2"]
            ka2[jj,ii] =  fitterSet[ff].result_["params"]["kap"]
            C1[jj,ii] = 1- C1[jj,ii]

        ff += 1

# %%

fig, ax = plt.subplots()
im = ax.imshow(t0, cmap="viridis", origin="lower")
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
