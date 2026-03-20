''' script to evaluate binding of BSA in high magnification IFC system'''
#%% import
import numpy as np
from spectralCamera.instrument.sCamera.sCameraFromFile import SCameraFromFile
from plim.gui.spectralViewer.plasmonViewer import PlasmonViewer
from skimage import data
from skimage.filters import threshold_otsu
from plim.algorithm.spotSpectra import SpotSpectra
import matplotlib.pyplot as plt

from skimage.morphology import erosion, disk, square
from plim.instrument.plasmonProcessor import PlasmonProcessor
from plim.algorithm.fileData import FileData
import time
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
import napari


#spectral camera system
fFolder = r'D:\ondra\LPI\plim\DATA\ifcBased\26-03-16 highMag_BSA\rawNorm'
sFolder = r'D:\ondra\LPI\plim\DATA\ifcBased\26-03-16 highMag_BSA'

# %%
# load first image
sCamera = SCameraFromFile()
sCamera.connect()
sCamera.setFolder(fFolder)

ii=10
print(f'loading file # {ii} for spot setting')
sImage = sCamera.fileSIVideo.loadImage(sCamera.fileName[ii])
t0 = sCamera.fileTime[ii]/1e9
w = sCamera.getWavelength()


# %% identify spots
image = np.sum(sImage, axis=0)
thresh = threshold_otsu(image[~np.isnan(image)])
binary = image < thresh

eroded = erosion(binary.astype(np.uint8), disk(10))

_per = 1
grid = np.zeros_like(image)
grid[::_per,::_per] = 1

_indices = np.argwhere(eroded*grid == 1)

_idxBcg = [200,100]
_idx = np.vstack((_idxBcg,_indices))

#%% show the spots and image

_im = np.zeros_like(image)
_im[_indices[:,0],_indices[:,1]] = 1
pV = PlasmonViewer(image=sImage, wavelength=w)


# set spots to the processor
pV.spotSpectra.setSpot(_idx)
pV.spotSpectra.setMask(pxAve=1,pxBcg=5, pxSpace= 1, concentric= False)
pV.redraw()


#%% set plasmon processor

sCamera.setParameter('threadingNow',True)  
pP = PlasmonProcessor()
pP.connect(sCamera=sCamera)
pP.setParameter('threadingNow',True)
sCamera.setParameter('processor',pP)

# copy the spotSpectra from pV
pP.spotSpectra = pV.spotSpectra


#set parameter for fitting
pP.pF.wavelengthStartFit = 550
pP.pF.wavelengthStopFit = 750
pP.pF.orderFit = 8
pP.pF.peakWidth =  100
pP.pF.wavelengthGuess = 620


#%% calculate spectra

#_idx = list(range(10, 50))
_idx = list(range(10, sCamera.nFile-1))
sCamera.startReadingImages(idx=_idx)

#%% wait till it is processed

app = QtWidgets.QApplication([])
win = pg.PlotWidget()
win.show()
line = win.plot(np.array([0,0]),np.array([0,0])) 
line2 = win.plot(np.array([0,0]),np.array([0,0])) 


viewer = pg.ImageView()
viewer.show()
imData = np.zeros_like(image)

def update():
    # graph
    _sig =np.mean(pP.spotData.signal[:,1:],axis=1)
    _time = pP.spotData.time - pP.spotData.time0
    #print(f'signal {_sig}')
    #print(f'time {_time}')
    try:
        line.setData(_time,_sig)
        line2.setData(_time,pP.spotData.signal[:,1])
    except:
        pass
    
    #image

    pP.spotData.setOffset()
    try:
        imData[pP.spotSpectra.spotPosition[1:,1],
                pP.spotSpectra.spotPosition[1:,0]
        ] = pP.spotData.signal[-1,1:] - pP.spotData.getOffset()[1:]
        viewer.setImage(imData)
    except:
        pass

    if not sCamera.isReading:
        timer.stop()




timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(50) 

app.exec()

pP.disconnect()

# %% save the data

_fileData = FileData(spotData=pP.spotData,
                        flowData=pP.flowData,
                        spotSpectra=pP.spotSpectra,
                        plasmonFit=pP.pF)

_fileData.saveAllFile(folder=sFolder,fileMainName='Exp1')

# %% show the whole data cube

pP.spotData.setOffset()

imCube = np.zeros((pP.spotData.signal.shape[0],imData.shape[0], imData.shape[1]))
imCube[:,
       pP.spotSpectra.spotPosition[1:,0],
       pP.spotSpectra.spotPosition[1:,1]
       ] = pP.spotData.signal[:,1:] - pP.spotData.getOffset()[1:]

myViewer = napari.Viewer()
myViewer.add_image(imCube)
myViewer.add_image(image)


napari.run()
# %%

np.save(sFolder + '/imCube',imCube)