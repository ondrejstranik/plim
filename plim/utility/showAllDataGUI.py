''' script to process videos of hyperspectral images'''
#%%
# import and parameter definition

import numpy as np
import napari

from plim.gui.spectralViewer.plasmonViewer import PlasmonViewer
from plim.gui.signalViewer.signalWidget import SignalWidget
from plim.gui.signalViewer.flowRateWidget import FlowRateWidget
from plim.gui.signalViewer.infoWidget import InfoWidget


ffolder = r'F:\ondra\LPI\24-08-28 spr_variable_array\iso_h20_1to4'
ffile = r'Experiment1'
nameSet = {'flow':'_flowData.npz',
            'image': '_image.npz',
            'spot': '_spotData.npz'}

_dp = np.linspace(0.4,1,25) # spacing between the pillars

dp = np.delete(_dp,4)

#%% load the data 

# load image
container1 = np.load(ffolder + '/' + ffile + nameSet['image'])
spotPosition = container1['arr_0']
image = container1['arr_1']
w = container1['arr_2']



# load flow
container2 = np.load(ffolder + '/' + ffile + nameSet['flow'])
flow = container2['arr_0']
time = container2['arr_1']

# load spot
container3 = np.load(ffolder + '/' + ffile + nameSet['spot'])
spot = container3['arr_0']


#%% show the data 

def colorChange():
    _fc = 1*sViewer.pointLayer.face_color #  deep copy of hte colors
    _fc[list(sViewer.pointLayer.selected_data)] = sViewer.pointLayer._face.current_color # adjust the just modified 
    sV.sD.signalColor = _fc
    sV.drawGraph()

def printAhoj():
    print('Ahoj')


sViewer = PlasmonViewer(image, w)
sViewer.pointLayer.data = spotPosition

sViewer.pointLayer._face.events.current_color.connect(colorChange)


#viewer = napari.Viewer()
#viewer.add_image(image)
#viewer.add_points(spotPosition)

sV = SignalWidget(signal=spot,time= time)
colorChange()
sV.show()

fV = FlowRateWidget(signal=flow, time = time)
fV.show()

iV = InfoWidget()
iV.show()

iV.infoBox.changed.connect(printAhoj)


napari.run()

