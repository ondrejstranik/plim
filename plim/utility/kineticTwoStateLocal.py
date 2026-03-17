'''
script to test fitting of kinetics binding (two exponential fit)
assumes two state model with  with mass transport limitation
'''


#%%

from plim.algorithm.preprocessSignal import PreprocessSignal
from plim.algorithm.bindingModelFitter import BindingModelFitter
import pyqtgraph as pg
import numpy as np
import matplotlib.pyplot as plt


folder = r'F:\ondra\LPI\plim\DATA\ifcBased\26-02-18 B8-BSA\processed'
fileMainName = 'Experiment1'
pS = PreprocessSignal(folder=folder, fileMainName=fileMainName)
pS.alignData((150,550))
pS.showGrid()
pS.showSignal(axis=0,idx=[0,4])


# %% show signal data difference with cut along time 
'''
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
'''
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
        "t0":  250, 
    }



for jj in range(pS.nRow):
    for ii in range(pS.nColumn):
        y_exp = pS.signalGrid[:,jj,ii]
        fitter = BindingModelFitter(
                t_exp, y_exp,
                fixed={},          
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

# %% assign proper the parameters (slow and quick rate)


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

# %% false color plot

Z = 1*t0
# remove the bad fits
Z[5,0:3] = np.nan

fig, ax = plt.subplots()
im = ax.imshow(Z, cmap="viridis", origin="lower")
ax.invert_yaxis()
fig.colorbar(im, ax=ax)
plt.xlabel("column")
plt.ylabel("row")
plt.title(r"$t_0 /s$")
plt.tight_layout()
#plt.show()


# %% 3D surface plot
X, Y = np.meshgrid(np.arange(pS.nColumn), np.arange(pS.nRow))

fig, ax = plt.subplots(subplot_kw={"projection": "3d"})

surf = ax.plot_surface(X, Y, Z,
    cmap="viridis",
    alpha=0.8,          # transparency
    rstride=1,          # row sampling (1 = every row)
    cstride=1,          # col sampling
)
fig.colorbar(surf, ax=ax, shrink=0.5)   # add colorbar


# %% 3D bar graph

Z = 1*t0
Z[5,0:3] = np.min(Z)

# x/y axis values (replace with your actual values)
x_vals = np.arange(pS.nColumn)   # or e.g. np.array([0.1, 0.5, 1.0])
y_vals = np.arange(pS.nRow)   # or e.g. np.array([10, 20, 30])

# ── Build bar positions ───────────────────────────────────────────────────────
x_idx, y_idx = np.meshgrid(x_vals, y_vals)
xpos = x_idx.flatten()
ypos = y_idx.flatten()
zpos = np.zeros_like(xpos) + np.min(Z)   # bars start at z=0
dz   = Z.flatten()- np.nanmin(Z)           # bar heights

# bar width/depth — set to ~80% of spacing to leave a gap
dx = 0.8 * (x_vals[1] - x_vals[0]) if len(x_vals) > 1 else 0.8
dy = 0.8 * (y_vals[1] - y_vals[0]) if len(y_vals) > 1 else 0.8

# ── Color by height ───────────────────────────────────────────────────────────
norm   = plt.Normalize(np.nanmin(dz), np.nanmax(dz))
colors = plt.cm.viridis(norm(dz))

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(subplot_kw={"projection": "3d"}, figsize=(8, 6))

ax.bar3d(xpos, ypos, zpos, dx, dy, dz, color=colors, shade=True)

# colorbar
sm = plt.cm.ScalarMappable(cmap="viridis", norm=norm)
fig.colorbar(sm, ax=ax, shrink=0.5, label="Value")

ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Value")
ax.set_title("3D Bar Graph")
ax.set_zlim(bottom=np.nanmin(Z))

# set tick labels to actual axis values
ax.set_xticks(x_vals)
ax.set_yticks(y_vals)

ax.view_init(elev=25, azim=-60)
plt.tight_layout()


# %% fit the average time to cross the array

slope = [] 
x = np.arange(pS.nColumn)

y = 1*t0
y[5,0:3] = np.nan

fig, ax = plt.subplots()

for jj in range(pS.nRow):
    # remove nan
    _number = ~np.isnan(y[jj,:])
    _x = x[_number]
    _y = y[jj,_number]
    coeffs = np.polyfit(_x, _y, deg=1)   # returns [slope, intercept]
    _slope, intercept = coeffs
    slope.append(_slope)
    ax.plot(x, y[jj,:], label = f'{jj} row')
    ax.plot(x, _slope*x + intercept)

ax.set_xlabel("column")
ax.set_ylabel("t0 [s]")
ax.set_title(" linear fit for each row")



fig.legend()
#slope = np.array(slope)    
# %% graph of the passing time 

x = np.arange(pS.nRow)

fig, ax = plt.subplots()
ax.plot(x, -np.array(slope)*(pS.nColumn-1),'*-')

ax.set_xlabel("row")
ax.set_ylabel("time [s]")
ax.set_title(" flow time over chip")

