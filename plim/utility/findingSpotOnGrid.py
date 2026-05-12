#%%
'''script to test finding spots on a grid
'''

from plim.virtualSystem.component.sample3 import Sample3
import numpy as np
from plim.algorithm.spotIdentification import SpotIdentification
from spectralCamera.algorithm.gridSuperPixel import GridSuperPixel
import napari


sample = Sample3()
sample.setPlasmonArray()
image = (1- sample.get())*10**3
image += np.random.poisson(image)

#%%
sI = SpotIdentification(image)
myPosition = sI.getPosition(contrastChannel=15)
myRadius = sI.getRadius()
print(f'detected radius: {myRadius}')


#%%
# restrict the spot on grid
gridSP = GridSuperPixel()
gridSP.setGridPosition(myPosition)
gridSP.getGridInfo()
gridSP.getPixelIndex()          

#%%
I, J = np.meshgrid(np.arange(np.min(gridSP.imIdx[:,0]),np.max(gridSP.imIdx[:,0])+1),
                   np.arange(np.min(gridSP.imIdx[:,1]),np.max(gridSP.imIdx[:,1])+1),
                   indexing='ij')  # shape (nRow, nColumn)
positionGrid = (I[:, :, None] * gridSP.xVec + 
                J[:, :, None] * gridSP.yVec) + gridSP.xy00
# set the properly defined 
positionGrid[gridSP.imIdx[:,0]-min(gridSP.imIdx[:,0]),
                gridSP.imIdx[:,1]-min(gridSP.imIdx[:,1]),:] = gridSP.position
myPosition2 = np.reshape(positionGrid,(-1,2))

#myPosition = gridSP.position

print(f'xy00 is {gridSP.xy00}')
print(f'xVec is {gridSP.xVec}')
print(f'yVec is {gridSP.yVec}')
#print(f'positionGrid is {positionGrid}')
#print(f'shape of I {I.shape}')
#print(f'shape of positionGrid {positionGrid.shape}')


# restrict to the spots, whose whole mask is in the image
#self.spotSpectra.pxAve = int(myRadius)
#self.spotSpectra.setSpot(myPosition)
#self.spotSpectra.setMask()
#myPosition = myPosition[~self.spotSpectra.outliers]

#%%
viewer = napari.Viewer()

viewer.add_image(image)

viewer.add_points(myPosition)
viewer.add_points(myPosition2)


# %%
