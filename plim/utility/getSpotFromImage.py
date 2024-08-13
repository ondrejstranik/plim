''' script to identify splasmon spots from hyperspectral image'''
#%%
# import and parameter definition

import numpy as np
import napari
from plim.algorithm.spotIdentification import SpotIdentification
import plim

ffolder = r'Experiment1_4to1_h2o_iso'
ffile = r'Experiment1_4to1_h2o_iso_image.npz'
container = np.load(plim.dataFolder + '/' + ffolder + '/' + ffile)
image = container['arr_1']

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
