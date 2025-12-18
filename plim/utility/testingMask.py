#%% testing mask

import numpy as np
import napari 


mask = np.random.rand(21,21) > 0.1

vec = (np.random.rand(10,2)*np.array([100,200])).astype(int)

maskIdx = np.where(mask)

im = np.zeros((100,200))
imSum = np.zeros((100,200))
imVal = np.random.rand(100,200)
imSpec = np.random.rand(10,100,200)



allMaskIdx = (maskIdx[0]+vec[:,0][:,None]-10,  maskIdx[1]+vec[:,1][:,None]-10)

ol1 = np.any((allMaskIdx[0]<0, allMaskIdx[0]>99, allMaskIdx[1]<0, allMaskIdx[1]>199),axis=0)
outliers = np.any(ol1,axis=1)

allMaskIdxX = allMaskIdx[0][~outliers,:]
allMaskIdxY = allMaskIdx[1][~outliers,:]

im[allMaskIdxX,allMaskIdxY] = 1

spec = np.sum(imSpec[:,allMaskIdxX,allMaskIdxY],axis=2).T

sumValue = np.sum(imVal[allMaskIdxX,allMaskIdxY],axis=1)
imSum[vec[~outliers,:][:,0],vec[~outliers,:][:,1]] = sumValue
viewer = napari.Viewer()
viewer.add_image(im)
viewer.add_image(imSum)
viewer.add_image(imVal)

# %%
