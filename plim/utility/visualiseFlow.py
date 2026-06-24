''' script to visualise flow in chamber'''
#%%
import numpy as np
from plim.algorithm.kineticFit import KineticFit, FitType
from spectralCamera.algorithm.gridSuperPixel import GridSuperPixel

ffolder = r'F:\ondra\LPI\plim\DATA\filterBased\26-04-16 dnaBingingClean\targetDNA2uM'
ffile = '2uM_fit.pkl'
#%%

kF = KineticFit.loadFit(filePath=ffolder + '/' + ffile)

# %%

pos = np.array(kF.table['position'])
_time0 = [pp =='time0' for pp in kF.fitType.parameters]

time0 = kF.fittedParam[:,_time0]


gridSP = GridSuperPixel()
gridSP.setGridPosition(pos)
gridSP.getGridInfo()
gridSP.getPixelIndex() 

gridSP.shiftIdx00(np.min(gridSP.imIdx,axis=0))

tM = np.full(np.max(gridSP.imIdx, axis=0) + 1, np.nan)
tM[gridSP.imIdx[:, 0], gridSP.imIdx[:, 1]] = time0.flatten()

import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter

# NaN-safe Gaussian smoothing via normalised convolution
sigma = 1
_valid = (~np.isnan(tM)).astype(float)
_filled = np.where(np.isnan(tM), 0.0, tM)
tM_smooth = gaussian_filter(_filled, sigma=sigma) / gaussian_filter(_valid, sigma=sigma)
tM_smooth[_valid == 0] = np.nan

# speed = 1 / |∇t|,  velocity vector = ∇t / |∇t|²
gy, gx = np.gradient(tM_smooth)       # units: s/pixel
grad_mag = np.sqrt(gx**2 + gy**2)    # s/pixel
speed = 1.0 / grad_mag               # pixel/s
vx = gx / grad_mag**2                # velocity x-component (col direction)
vy = gy / grad_mag**2                # velocity y-component (row direction)

cols, rows = np.meshgrid(np.arange(tM.shape[1]), np.arange(tM.shape[0]))

# streamplot requires finite values
vx_plot    = np.where(np.isfinite(vx),    vx,    0.0)
vy_plot    = np.where(np.isfinite(vy),    vy,    0.0)
speed_plot = np.where(np.isfinite(speed), speed, 0.0)

fig, axes = plt.subplots(1, 4, figsize=(20, 5))

im0 = axes[0].imshow(tM, origin='upper')
fig.colorbar(im0, ax=axes[0], label='time0 (s)')
axes[0].set_title('arrival time')
axes[0].set_xlabel('col')
axes[0].set_ylabel('row')

im1 = axes[1].imshow(speed, origin='upper')
fig.colorbar(im1, ax=axes[1], label='speed (px/s)')
axes[1].set_title('speed')
axes[1].set_xlabel('col')
axes[1].set_ylabel('row')

axes[2].imshow(tM, origin='upper', alpha=0.4)
axes[2].quiver(cols, rows, vx, vy, color='white')
axes[2].set_title('flow velocity')
axes[2].set_xlabel('col')
axes[2].set_ylabel('row')

# streamplot: negate vy because origin='upper' inverts the y-axis
x = np.arange(tM.shape[1])
y = np.arange(tM.shape[0])
axes[3].imshow(tM, origin='upper', alpha=0.4)
axes[3].streamplot(x, y, vx_plot, -vy_plot,
                   color=speed_plot, cmap='hot', density=1.5, linewidth=1.5)
axes[3].set_title('streamlines')
axes[3].set_xlabel('col')
axes[3].set_ylabel('row')

plt.tight_layout()
plt.show()
# %%
