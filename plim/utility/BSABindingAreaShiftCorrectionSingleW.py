''' displaying the 1 pixel BSA adsorption'''

#%%
from plim.algorithm.fileData import FileData
import numpy as np
import numpy as np
from skimage.registration import phase_cross_correlation
from scipy.ndimage import shift as ndi_shift
from skimage.morphology import erosion, disk, square
from scipy.ndimage import gaussian_filter, sobel
import napari
from scipy.signal import correlate2d
from spectralCamera.algorithm.fileSIVideo import FileSIVideo
import matplotlib.pyplot as plt
from scipy.ndimage import fourier_shift


sFolder = r'D:\ondra\LPI\plim\DATA\ifcBased\26-03-16 highMag_BSA\singlePixel3'
fMName = 'Exp1'
norFolder = r'D:\ondra\LPI\plim\DATA\ifcBased\26-03-16 highMag_BSA\rawNorm'
savFolder =  r'D:\ondra\LPI\plim\DATA\ifcBased\26-03-16 highMag_BSA\rawShiftEachW'

#%% function

import numpy as np
from skimage.registration import phase_cross_correlation
from scipy.ndimage import shift as ndi_shift


def get_edges(data, sigma=1):
    # 1. Smooth first to reduce noise
    smoothed = gaussian_filter(data, sigma=sigma, axes=(-2,-1))
    
    # 2. Sobel edges in x and y
    edge_x = sobel(smoothed, axis=-1)
    edge_y = sobel(smoothed, axis=-2)
    
    # 3. Combine into edge magnitude
    edges = np.hypot(edge_x, edge_y)
    return edges


def normalize(img):
    return (img - img.mean()) / (img.std() + 1e-8)

def align_stack_unmasked(stack, reference_index=None, upsample_factor=4):
    """
    Align a 3D stack (z, y, x) using subpixel phase correlation (no mask).

    Returns:
        aligned_stack : same shape as input
        shifts : list of (y, x) shifts
    """
    
    stack = stack.astype(np.float32)

    # choose reference (middle is usually best)
    if reference_index is None:
        reference_index = stack.shape[0] // 2

    ref = normalize(stack[reference_index])
    #ref = stack[0,:,:]


    aligned_stack = np.zeros_like(stack)
    shifts = []

    for i in range(stack.shape[0]):
        moving = normalize(stack[i])
        #moving = stack[i]

        # 🔥 subpixel shift estimation
        shift, error, _ = phase_cross_correlation(
            ref,
            moving,
            upsample_factor=upsample_factor,
            normalization= None
        )
        #shift = detect_shiftP(ref,moving)


        # apply shift
        aligned = ndi_shift(stack[i], shift=shift, mode='constant', cval=0)


        aligned_stack[i] = aligned
        shifts.append(shift)

        print(f'shift {i} is {shift}')

    return aligned_stack, shifts

def shiftImageStack(imCube, shift):

    nImage = imCube.shape[0]
    image_corrected = 0*imCube

    for ii in range(nImage):
        #f = np.fft.fft2(imCube[ii,...])
        #image_corrected[ii,...] = np.fft.ifft2(fourier_shift(f, shift[ii])).real

        image_corrected[ii,...] = ndi_shift(imCube[ii,...], shift=shift[ii], mode='constant', cval=0)

    return image_corrected


def detect_shiftP(reference, image):
    corr = correlate2d(reference, image, mode='full')
    peak = np.unravel_index(np.argmax(corr), corr.shape)

    # Offset by center of correlation map
    shift = np.array(peak) - np.array(reference.shape) + 1
    return shift


def detect_pixel_shift(reference, image):
    """Robust integer shift using correlate2d."""
    corr = correlate2d(reference, image, mode='full')
    peak = np.unravel_index(np.argmax(corr), corr.shape)
    shift = np.array(peak) - np.array(reference.shape) + 1
    return shift

def detect_subpixel_residual(reference, image, pixel_shift):
    """Find subpixel residual after correcting integer shift."""
    # Correct integer shift first
    f = np.fft.fft2(image)
    image_corrected = np.fft.ifft2(fourier_shift(f, pixel_shift)).real

    # Now find small subpixel residual
    residual, _, _ = phase_cross_correlation(reference, image_corrected, upsample_factor=10)
    return residual

def detect_shift(reference, image):
    """Full pipeline: integer + subpixel shift."""
    # Step 1: coarse integer shift
    pixel_shift = detect_pixel_shift(reference, image)
    print(f"Pixel shift:    y={pixel_shift[0]}, x={pixel_shift[1]}")

    # Step 2: subpixel residual
    subpixel_residual = detect_subpixel_residual(reference, image, pixel_shift)
    print(f"Subpixel residual: y={subpixel_residual[0]:.3f}, x={subpixel_residual[1]:.3f}")

    # Step 3: combine
    total_shift = pixel_shift + subpixel_residual
    print(f"Total shift:    y={total_shift[0]:.3f}, x={total_shift[1]:.3f}")

    return total_shift
#%% import image and get average image
dVideo = FileSIVideo()
dVideo.setFolder(norFolder)
fileName, fileTime = dVideo.getImageInfo()

# remove the first N images. they is something wrong with them.
nStart = 10
fileName, fileTime = fileName[nStart:], fileTime[nStart:]


nFile = len(fileName)
w = dVideo.loadWavelength()


for ii, (_fn, _ft) in enumerate(zip(fileName,fileTime)):
    try:

        image = dVideo.loadImage(_fn)
        print(f'image {ii} out of {nFile}')
    except:
        print('could not load the file')
    if ii==0:
        imCube = np.zeros((len(fileName),*image.shape))
    #imCube[ii,...] = np.sum(image,axis=0)
    imCube[ii,...] = image

 

# %%
# cut sub-image so that it is in the round view of the HSI
imCubeCut = imCube[:,:,50:210,50:210]
imCubeCut[np.isnan(imCubeCut)] = 0

# get edges of the image and remove nan values
imEdge = get_edges(imCubeCut, sigma=1)

#%%

nW = imCubeCut.shape[1]
nF = imCubeCut.shape[0]

imCubeNN = imCube
imCubeNN[np.isnan(imCubeNN)] = 0
#allCube = np.zeros_like(imCube)

shiftsW = []

for ii in range(nW):
    print(f'wavelength {ii} out of {nW}')
    aligned_stack, shifts = align_stack_unmasked(imEdge[:,ii,...], upsample_factor=100)
    imCubeNN[:,ii,...] = shiftImageStack(imCubeNN[:,ii,...], shifts)
    shiftsW.append(shifts)

shiftArray = np.array(shiftsW)

#%%
viewer = napari.Viewer()
#viewer.add_image(aligned_stack)
#viewer.add_image(imCube)
viewer.add_image(imCubeNN)
#%%
viewer = napari.Viewer()
#viewer.add_image(aligned_stack)
#viewer.add_image(imCube)
viewer.add_image(shiftArray[:,:,0])
viewer.add_image(shiftArray[:,:,1])

#%%

fig, ax = plt.subplots()
ax.plot(shifts)

fig, ax = plt.subplots()
xx = np.array(shifts)
ax.plot(xx[:,1],xx[:,0])
# %% shift it back and save if for further processing

sVideo = FileSIVideo()
sVideo.setFolder(savFolder)

for ii, (_fn, _ft) in enumerate(zip(fileName,fileTime)):
    try:
        sVideo.saveImage(imCubeNN[ii,...],_ft)
    except:
        print('could not load the file')

sVideo.saveWavelength(w)

# %%
