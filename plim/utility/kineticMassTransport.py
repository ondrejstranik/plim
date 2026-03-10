'''
script to test fitting of kinetics binding with mass transport limitation
'''

#%%
from plim.algorithm.spotData import SpotData
from plim.algorithm.fileData import FileData
from spectralCamera.algorithm.gridSuperPixel import GridSuperPixel
import pyqtgraph as pg

import napari
import numpy as np

import matplotlib.pyplot as plt

folder = r'F:\ondra\LPI\plim\DATA\ifcBased\26-02-18 B8-BSA\processed'
fileMainName = r'Experiment1'

#%%
# load data
_fileData = FileData()
_fileData.loadAllFile(folder=folder,fileMainName=fileMainName)

# transfer data
spotPosition = _fileData.spotSpectra.spotPosition
image = _fileData.spotSpectra.image
w = _fileData.pF.wavelength

# set time0 to the beginning
_fileData.spotData.time0 = _fileData.spotData.time[0]
(signal, time) = _fileData.spotData.getData()

# off set the data
_fileData.spotData.setOffset(200)
signal = signal - _fileData.spotData.getOffset()

# reduce the range
_timeRange = np.all([time>150,time<550],axis=0)
time = time[_timeRange]
signal = signal[_timeRange]



# %%
# characterize the grid
gridSP = GridSuperPixel()
gridSP.setGridPosition(spotPosition)
gridSP.getGridInfo()
gridSP.getPixelIndex()

# move the origin to the top left
_x0 = np.min(gridSP.imIdx[:,0])
_y0 = np.min(gridSP.imIdx[:,1])
gridSP.shiftIdx00([_x0,_y0])

# %%

# prepare a sub selected  points
pointsSelect = (gridSP.imIdx[:,0]%1 == 0 ) & (gridSP.imIdx[:,1]%1 == 0 ) & gridSP.inside
points = gridSP.position[pointsSelect,:]

features = {'pointIndex0': gridSP.imIdx[pointsSelect,0],
            'pointIndex1': gridSP.imIdx[pointsSelect,1]
            }
text = {'string': '[{pointIndex0},{pointIndex1}]',
        'translation': np.array([-5, 0])
        }

# display the images
viewer = napari.Viewer()
viewer.add_image(image)
viewer.add_points(points,features=features,text=text, size= 5, opacity=0.5)

# %%
# normalise the sensitivity/coverage

signalN = signal/signal[-1,:]

#%%


# set signal into a regular grid x- along channel
signalGrid = np.zeros((signal.shape[0],
                      np.max(gridSP.imIdx[:,0])+1,
                       np.max(gridSP.imIdx[:,1])+1)
                       )

for ii in range(signal.shape[1]):
    signalGrid[:,gridSP.imIdx[ii,0],gridSP.imIdx[ii,1].astype(int)] = signalN[:,ii]


# %%
# add graph - line along time and x
graph = pg.plot()
graph.setTitle(f'Signal difference along rows')
graph.setLabel('left', 'Signal', units='nm')
graph.setLabel('bottom', 'column')

nTime = signalGrid.shape[0]
nRow = signalGrid.shape[1]
for jj in range(nRow):
    for ii in range(nTime):
        normSig = (signalGrid[ii,jj,:]-signalGrid[ii,jj,0])
        if normSig[-1] > 0.05:
                graph.plot(normSig+jj*0.1, pen=(jj,nRow))

    print(f'showing {ii} line ')
#%%

# add graph - line along y
graph = pg.plot()
graph.setTitle(f'Fits')
graph.setLabel('left', 'Signal', units='nm')
graph.setLabel('bottom', 'time', units= 's')

nColumn = signalGrid.shape[2]
nRow = signalGrid.shape[1]
for jj in range(nRow):
    for ii in range(nColumn):
        graph.plot(time,signalGrid[:,jj,ii], pen=(ii,nColumn))
        print(f'showing {ii} line ')



# %%
# show some data slice

t_exp = time
y_exp = signalGrid[:,3,0]
plt.figure(figsize=(7, 4))
plt.scatter(t_exp, y_exp, label="Experimental data", color="steelblue", zorder=5)

# %%

from plim.utility.bindingModelFitter import BindingModelFitter

fitterSet = []
t_exp = time 

nColumn = signalGrid.shape[2]
nRow = signalGrid.shape[1]

for jj in range(nRow):
    for ii in range(nColumn):
        y_exp = signalGrid[:,jj,ii]
        fitter = BindingModelFitter(
                t_exp, y_exp,
                fixed={},          # fix t0 at 2.0
                guess={"Req": 0.9, "C1": 0.6, "t0":220},
            )

        fitter.fit()
        #fitter.plot()

        fitterSet.append(fitter)

# Access results programmatically
    #print("ka2 =", fitter.result_["params"]["t0"])
# %%

t0 = np.zeros((nRow,nColumn))
kap = np.zeros((nRow,nColumn))
ka2 = np.zeros((nRow,nColumn))
C1 = np.zeros((nRow,nColumn))


ff = 0
for jj in range(nRow):
    for ii in range(nColumn):
        t0[jj,ii] =  fitterSet[ff].result_["params"]["t0"]
        kap[jj,ii] =  np.max((fitterSet[ff].result_["params"]["kap"], fitterSet[ff].result_["params"]["ka2"]))
        ka2[jj,ii] =  np.min((fitterSet[ff].result_["params"]["ka2"], fitterSet[ff].result_["params"]["ka2"]))
        C1[jj,ii] = fitterSet[ff].result_["params"]["C1"]
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
im = ax.imshow(kap, cmap="viridis", origin="lower")
ax.invert_yaxis()
fig.colorbar(im, ax=ax)
plt.xlabel("x")
plt.ylabel("y")
plt.title("t0 ")
plt.tight_layout()
#plt.show()


# %%
X, Y = np.meshgrid(np.arange(nColumn), np.arange(nRow))

fig, ax = plt.subplots(subplot_kw={"projection": "3d"})

surf = ax.plot_surface(X, Y, kap,
    cmap="viridis",
    alpha=0.8,          # transparency
    rstride=1,          # row sampling (1 = every row)
    cstride=1,          # col sampling
)
fig.colorbar(surf, ax=ax, shrink=0.5)   # add colorbar

plt.show()
# %%
