#%%
# script to see spotting position images from spotter

from skimage import io
import numpy as np
from pathlib import Path
import napari

def load_jpg_stack(folder_path: str) -> np.ndarray:
    folder = Path(folder_path)
    #jpg_files = sorted(folder.glob("*.jpg")) + sorted(folder.glob("*.JPG"))

    jpg_files = sorted(folder.glob("*.jpg"))


    frames = [io.imread(str(path)) for path in jpg_files]
    
    bwFrames = np.sum(np.stack(frames, axis=0), axis=3) # shape: (Z, Y, X, 3)

    return bwFrames

def cropMiddle(stack: np.ndarray, halfSize: int= 40) -> np.ndarray:

    middle = np.array(np.shape(stack))//2

    return stack[:,middle[1]-halfSize:middle[1]+halfSize+1,
                 middle[2]-halfSize:middle[2]+halfSize+1]


def make_crosshair_label(stack: np.ndarray) -> np.ndarray:
    """
    Creates a 3D label array (Z, Y, X) with the crosshair
    burned into EVERY Z slice so it is always visible on scroll.
    """
    Z, Y, X = stack.shape[:3]
    mid_y = Y // 2
    mid_x = X // 2

    label = np.zeros((Z, Y, X), dtype=np.uint8)

    # Draw horizontal line (label value 1) across all Z slices
    label[:, mid_y, :] = 1

    # Draw vertical line (label value 2) across all Z slices
    label[:, :, mid_x] = 2

    # Intersection pixel — give it its own label so it can be colored separately
    label[:, mid_y, mid_x] = 3

    return label

def show_in_napari(folder_path: str):
    stack = load_jpg_stack(folder_path)
    #stack = cropMiddle(_stack)

    print(f"\n3D stack shape: {stack.shape}")
    print(f"dtype         : {stack.dtype}")

    viewer = napari.Viewer(title="JPG Stack — 3D Viewer")

    viewer.add_image(
        stack,
        name="jpg_stack",
        colormap="gray",
        
    )

    crosshair_label = make_crosshair_label(stack)

    viewer.add_labels(
            crosshair_label,
            name="crosshair",
            opacity=0.6,

        )



    napari.run()   # Starts the Qt event loop — blocks until the window is closed

#%%
ffolder =  r'F:\ondra\LPI\info\26-05-04 spotting postions'


show_in_napari(ffolder)