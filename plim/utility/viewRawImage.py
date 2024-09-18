#%%
# import and parameter definition

import numpy as np
import plim
from plim.gui.spectralViewer.plasmonViewer import PlasmonViewer
import napari
from tifffile import  imread
from spectralCamera.algorithm.calibratePFImage import CalibratePFImage
#from spectralCamera.instrument.sCamera.sCamera import SCamera

ffolder = r'C:\Users\ostranik\Documents\GitHub\plim\plim\DATA\24-9-16 pfcamera'
ffile = r'nanodisc.tif'
wfile = 'wavelength.npy'

#%%

rImage = imread(ffolder +'/' + ffile)

#viewer = napari.Viewer()
#viewer.add_image(rImage)

#napari.run()

#%%

sCal = CalibratePFImage(darkValue= 200)






#pViewer = PlasmonViewer(image, w)
#pViewer.run()
# %%
