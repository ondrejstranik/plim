''' script to normalise the spectral images'''
#%% import
from spectralCamera.algorithm.fileSIVideo import FileSIVideo
import numpy as np
from plim.gui.spectralViewer.plasmonViewer import PlasmonViewer

datFolder = r'D:\ondra\LPI\plim\DATA\ifcBased\26-03-16 highMag_BSA\raw'
norFolder = r'D:\ondra\LPI\plim\DATA\ifcBased\26-03-16 highMag_BSA\raw_flatfielding'
savFolder =  r'D:\ondra\LPI\plim\DATA\ifcBased\26-03-16 highMag_BSA\rawNorm'


#%% get flatfielding image
nVideo = FileSIVideo()

nVideo.setFolder(norFolder)

fileName, _ = nVideo.getImageInfo()
nFile = len(fileName)

# average
for ii,_fn in enumerate(fileName):
    if ii==0:
        image = np.load(norFolder + '/'+ _fn)
    else:
        image += np.load(norFolder + '/'+ _fn)
    print(f'image number {ii}')

image /= ii+1

norImage = image/np.max(image,axis=(1,2))[:,None,None]


#%% 


dVideo = FileSIVideo()
dVideo.setFolder(datFolder)
fileName, fileTime = dVideo.getImageInfo()
nFile = len(fileName)
w = dVideo.loadWavelength()

sVideo = FileSIVideo()
sVideo.setFolder(savFolder)

#%%
for ii, (_fn, _ft) in enumerate(zip(fileName,fileTime)):
    try:
        image = dVideo.loadImage(_fn)
        nImage = image/norImage
        sVideo.saveImage(nImage,_ft)
        #np.save(datFolder + '/' + sVideo.DEFAULT['nameSet']['image'].format(_ft),nImage)
        print(f'image {ii} out of {nFile}')
    except:
        print('could not save the file')

sVideo.saveWavelength(w)


sViewer = PlasmonViewer(image/norImage, w)
sViewer.run()


# %%
