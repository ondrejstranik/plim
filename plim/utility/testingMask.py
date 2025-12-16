#%% testing mask

import numpy as np
import napari 


mask = np.random.rand(20,20) > 0.1

vec = (np.random.rand(10,2)*np.array([100,200])).astype(int)

maskIdx = np.where(mask)

im = np.zeros((100,200))

allMaskIdx = (maskIdx[0]+vec[:,0][:,None],  maskIdx[1]+vec[:,1][:,None])

ol1 = np.any((allMaskIdx[0]>99,   allMaskIdx[1]>199),axis=0)
outliers = np.any(ol1,axis=1)

allMaskIdxX = allMaskIdx[0][~outliers,:]
allMaskIdxY = allMaskIdx[1][~outliers,:]

im[allMaskIdxX,allMaskIdxY] = 1

napari.view_image(im)


# %%
