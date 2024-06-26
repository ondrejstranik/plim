''' script to identify splasmon spots from hyperspectral image'''
#%%
# import and parameter definition

import numpy as np
import napari
from plim.algorithm.spotIdentification import SpotIdentification
import plim

container = np.load(plim.dataFolder + '/' + 'spot_0.npy.npz')
image = container['image']

#%% identify the spots

sI = SpotIdentification(image)
myPosition = sI.getPosition()
myRadius = sI.getRadius()

#%% show images
viewer = napari.Viewer()
viewer.add_image(image)
viewer.add_points(myPosition)
napari.run()
# %%
