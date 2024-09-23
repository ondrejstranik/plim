''' script to process videos of hyperspectral images'''
#%%
# import and parameter definition

import numpy as np
import plim
from plim.gui.spectralViewer.plasmonViewer import PlasmonViewer
from spectralCamera.algorithm.calibratePFImage import CalibratePFImage
import napari
from tifffile import imread

ffolder = r'G:\office\work\git\plim\plim\DATA\nanodisc'
ffile = r'nanodisc.tif'

#%% load the data 

# load image
rImage = imread(ffolder + '/' + ffile)


#%% show the data 

viewer = napari.Viewer()
viewer.add_image(rImage)
napari.run()

#%%
sCal = CalibratePFImage(darkValue=200)

image = sCal.getSpectralImage(rawImage=rImage)
w = sCal.getWavelength()


sViewer = PlasmonViewer(image, w)

sViewer.run()
# %%

