#%%
# import and parameter definition

import numpy as np
import plim
from plim.gui.spectralViewer.plasmonViewer import PlasmonViewer
import napari


ffolder = r'C:\Users\ostranik\Documents\GitHub\plim\plim\DATA\24-9-16 pfcamera\video'
ffile = r'time_1726482816858315000.npy'
wfile = 'wavelength.npy'

#%%

image = np.load(ffolder + '/' + ffile)
w = np.load(ffolder + '/' + wfile)

pViewer = PlasmonViewer(image, w)
pViewer.run()