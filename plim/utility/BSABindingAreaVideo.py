''' displaying the 1 pixel BSA adsorption'''

#%%
from plim.algorithm.fileData import FileData
import numpy as np
import numpy as np
from scipy.ndimage import shift as ndi_shift
from skimage.morphology import erosion, disk, square
from scipy.ndimage import gaussian_filter, sobel
import napari
from scipy.signal import correlate2d


sFolder = r'F:\ondra\LPI\plim\DATA\ifcBased\26-03-16 highMag_BSA\singlePixel'
fMName = 'Exp1'

#%% function

def shiftImageStack(imCube, shift):

    nImage = imCube.shape[0]
    image_corrected = 0*imCube

    for ii in range(nImage):
        #f = np.fft.fft2(imCube[ii,...])
        #image_corrected[ii,...] = np.fft.ifft2(fourier_shift(f, shift[ii])).real

        image_corrected[ii,...] = ndi_shift(imCube[ii,...], shift=shift[ii], mode='constant', cval=0)

    return image_corrected



#%% import
fD = FileData()
fD.loadAllFile(sFolder,fileMainName=fMName)
sS = fD.spotSpectra
sD = fD.spotData
sS.setMask()
im = sS.getImage()

shifts = np.load(sFolder + '/shifts.npy')
# correct the number of files
shifts = shifts[1:,:]

#%% get the 3D stack of signals

imCube = np.zeros((sD.signal.shape[0],im.shape[1], im.shape[2]))

imCube[:,sS.maskSpotIdx[0][~sS.outliers,:],
                sS.maskSpotIdx[1][~sS.outliers,:]] = sD.signal[:,:,None]

#%% get aligned 3D stack of signals

imCubeNN = imCube*1
imCubeNN[np.isnan(imCubeNN)] = 0
allCube = shiftImageStack(imCubeNN, shifts)

#%% remove the edges
from scipy.ndimage import binary_erosion

mask = np.zeros((im.shape[1], im.shape[2]), dtype=np.uint8)
mask[sS.maskSpotIdx[0][~sS.outliers,:],
                sS.maskSpotIdx[1][~sS.outliers,:]] = 1
eroded = binary_erosion(mask, structure=disk(10), border_value=0)

CubeOffset = (allCube- allCube[140,...])*eroded


#%%

viewer = napari.Viewer()
viewer.add_image(CubeOffset, name='shifted')
#viewer.add_image(imCube)
#%%

