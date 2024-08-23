''' script to show recorded plasmon data'''
#%%
# import and parameter definition

import numpy as np
import plim
from plim.gui.spectralViewer.plasmonViewer import PlasmonViewer
import napari

from plim.gui.signalViewer.signalWidget import SignalWidget
from plim.gui.signalViewer.flowRateWidget import FlowRateWidget


ffolder = r'Experiment1_4to1_h2o_iso'
ffile = r'Experiment1_4to1_h2o_iso'

ffolder = 'Experiment2_4to1_h2o_iso'
ffile = 'Experiment2'

ffolder = 'Experiment3_4to1_h2o_iso'
ffile = 'Experiment_noCorr_ave_32'

nameSet = {'flow':'_flowData.npz',
            'image': '_image.npz',
            'spot': '_spotData.npz'}


#%% load the data 

# load image
container1 = np.load(plim.dataFolder + '/' + ffolder + '/' + ffile + nameSet['image'])
spotPosition = container1['arr_0']
image = container1['arr_1']
w = container1['arr_2']

# load flow
container2 = np.load(plim.dataFolder + '/' + ffolder + '/' + ffile + nameSet['flow'])
flow = container2['arr_0']
time = container2['arr_1']

# load spot
container3 = np.load(plim.dataFolder + '/' + ffolder + '/' + ffile + nameSet['spot'])
spot = container3['arr_0']


#%% show the data 

#sViewer = PlasmonViewer(image, w)
#sViewer.pointLayer.data = spotPosition

viewer = napari.Viewer()
viewer.add_image(image)
viewer.add_points(spotPosition)

sV = SignalWidget(signal=spot,time= time)
sV.show()

fV = FlowRateWidget(signal=flow, time = time)
fV.show()

napari.run()


# %%
