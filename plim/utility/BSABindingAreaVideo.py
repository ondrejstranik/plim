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


sFolder = r'F:\ondra\LPI\plim\DATA\ifcBased\26-03-16 highMag_BSA\singlePixel'
fMName = 'Exp1'

#%% function

import numpy as np
from skimage.registration import phase_cross_correlation
from scipy.ndimage import shift as ndi_shift


def get_edges(data, sigma=1):
    # 1. Smooth first to reduce noise
    smoothed = gaussian_filter(data, sigma=sigma, axes=(1,2))
    
    # 2. Sobel edges in x and y
    edge_x = sobel(smoothed, axis=2)
    edge_y = sobel(smoothed, axis=1)
    
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

    #ref = normalize(stack[reference_index])
    ref = stack[0,:,:]


    aligned_stack = np.zeros_like(stack)
    shifts = []

    for i in range(stack.shape[0]):
        #moving = normalize(stack[i])
        moving = stack[i]

        # 🔥 subpixel shift estimation
        #shift, error, _ = phase_cross_correlation(
        #    ref,
        #    moving,
        #    upsample_factor=upsample_factor
        #)
        shift = detect_shiftP(ref,moving)



        # apply shift
        aligned = ndi_shift(stack[i], shift=shift, mode='constant', cval=0)


        aligned_stack[i] = aligned
        shifts.append(shift)

    return aligned_stack, shifts


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
#%% import
fD = FileData()
fD.loadAllFile(sFolder,fileMainName=fMName)
sS = fD.spotSpectra
sD = fD.spotData
sS.setMask()
im = sS.getImage()

#%% get the 3D stack of signals

imCube = np.zeros((sD.signal.shape[0],im.shape[1], im.shape[2]))

imCube[:,sS.maskSpotIdx[0][~sS.outliers,:],
                sS.maskSpotIdx[1][~sS.outliers,:]] = sD.signal[:,:,None]

#%% get aligned 3D stack of signals

# stack shape: (z, y, x)
# mask shape: (y, x), boolean

imCubeSmall = imCube[:,100:140, 135:170]

mask = np.zeros_like(im[0,...], dtype= bool)

mask[sS.maskSpotIdx[0][~sS.outliers,:],
                sS.maskSpotIdx[1][~sS.outliers,:]] = True

erodedMask = erosion(mask.astype(np.uint8), disk(10))


aligned_stack, shifts = align_stack_unmasked(imCubeSmall)

print("Shifts:")
for i, s in enumerate(shifts):
    print(f"Slice {i}: {s}")


#%%

imCubeSmall = imCube[:,100:140, 135:170]
imEdge = get_edges(imCubeSmall, sigma=3)
imEdge2 = imEdge[3:-3,3:-3]

aligned_stack, shifts = align_stack_unmasked(imEdge2, reference_index=10)


viewer = napari.Viewer()
viewer.add_image(aligned_stack)
#viewer.add_image(imEdge)

print(np.array(shifts))

# %%

import napari

viewer = napari.Viewer()
viewer.add_image(imCubeSmall)
viewer.add_image(aligned_stack)
# %%
from scipy.ndimage import fourier_shift

imCubeSmall = imCube[:,100:140, 135:170]
imEdge = get_edges(imCubeSmall, sigma=3)

idx = 200

shift, error, _ = phase_cross_correlation(
    imEdge[0,...], imEdge[idx,...],upsample_factor=100)
print(shift)
print(error)


shiftP = detect_shiftP(imEdge[0,...], imEdge[idx,...])
print(shiftP)

total_shift = detect_shift(imEdge[0,...], imEdge[idx,...])
print(total_shift)

adv_shift = detect_subpixel_residual(imEdge[0,...], imEdge[idx,...],pixel_shift=np.array([0,0]))

print(adv_shift)


#aligned = ndi_shift(imEdge[idx,...], shift=total_shift, mode='constant', cval=0)

f_shifted = fourier_shift(np.fft.fft2(imEdge[idx,...]), adv_shift)
shifted = np.fft.ifft2(f_shifted).real

viewer = napari.Viewer()
edgeStack = np.array((imEdge[idx,...], shifted,imEdge[0,...]))
viewer.add_image(edgeStack)


# %%
