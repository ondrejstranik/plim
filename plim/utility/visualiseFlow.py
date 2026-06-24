''' script to visualise flow in chamber'''
#%%
import numpy as np
from plim.algorithm.kineticFit import KineticFit, FitType
from spectralCamera.algorithm.gridSuperPixel import GridSuperPixel
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter

ffolder = r'F:\ondra\LPI\plim\DATA\filterBased\26-04-16 dnaBingingClean\targetDNA2uM'
ffile = '2uM_fit.pkl'
#%%

kF = KineticFit.loadFit(filePath=ffolder + '/' + ffile)

# %% re-create the spatial matrix with time0

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
tM = tM - np.nanmin(tM)


sigma  = 1
_valid = (~np.isnan(tM)).astype(float)
_filled = np.where(np.isnan(tM), 0.0, tM)
tM_smooth = gaussian_filter(_filled, sigma=sigma) / gaussian_filter(_valid, sigma=sigma)
tM_smooth[_valid == 0] = np.nan


#%%
fig, axes = plt.subplots(1, 1, figsize=(16, 5))

im0 = axes.imshow(tM, origin='upper')
fig.colorbar(im0, ax=axes, label='time0 (s)')
axes.set_title('arrival time ')
axes.set_xlabel('position along channel')
axes.set_ylabel('position across channel')


plt.tight_layout()



# %% linear fit per row: for each x position (row i) fit t vs y, speed = 1/|slope|
spacing_um = 300  # µm between spots
x_um = np.arange(tM.shape[0]) * spacing_um   # x positions in µm
y_um = np.arange(tM.shape[1]) * spacing_um   # y positions in µm

speed_per_row = np.full(tM.shape[0], np.nan)
speed_err     = np.full(tM.shape[0], np.nan)
fit_lines     = {}   # store (m, offset) per row for plotting

for i in range(tM.shape[0]):
    row   = tM[i, :]
    valid = np.isfinite(row)
    if valid.sum() < 3:
        continue
    (m, offset), cov = np.polyfit(y_um[valid], row[valid], 1, cov=True)
    sigma_m           = np.sqrt(cov[0, 0])               # std error of slope
    speed_per_row[i]  = 1.0 / abs(m)                     # µm/s
    speed_err[i]      = sigma_m / m**2                   # error propagation
    fit_lines[i]      = (m, offset)

# parabolic fit of speed vs x
valid_rows  = np.isfinite(speed_per_row)
p           = np.polyfit(x_um[valid_rows], speed_per_row[valid_rows], 2)
speed_parab = np.polyval(p, x_um)
print(f'speed parabola: {p[0]:.4g}·x² + {p[1]:.4g}·x + {p[2]:.4g}  [µm/s]')

# figure 1: linear fits + scatter
fig_fits, ax_fits = plt.subplots()
for i, (m, offset) in fit_lines.items():
    t_line = m * y_um + offset
    color  = ax_fits.plot(y_um, t_line, alpha=0.6)[0].get_color()
    row    = tM[i, :]
    valid  = np.isfinite(row)
    ax_fits.scatter(y_um[valid], row[valid], color=color, s=20, zorder=5)
ax_fits.set_xlabel('position along channel (µm)')
ax_fits.set_ylabel('arrival time (s)')
ax_fits.set_title('linear fits per row')
plt.tight_layout()


# figure 2: speed profile + parabolic fit
fig_spd, ax_spd = plt.subplots()
ax_spd.errorbar(x_um, speed_per_row, yerr=speed_err, fmt='o', capsize=4, label='speed per row')
ax_spd.plot(x_um, speed_parab, '-', label='parabolic fit')
ax_spd.set_xlabel('position across channel (µm)')
ax_spd.set_ylabel('speed (µm/s)')
ax_spd.set_title('flow speed + parabolic fit')
ax_spd.legend()
plt.tight_layout()


# %% reconstruct arrival time surface from parabolic speed fit
tM_new = np.full_like(tM, np.nan)
for i, (m, offset) in fit_lines.items():
    tM_new[i, :] = np.sign(m) * y_um / speed_parab[i] + offset

# plot reconstructed surface
fig_new, ax_new = plt.subplots()
im_new = ax_new.imshow(tM_new, origin='upper',
                       extent=[y_um[0], y_um[-1], x_um[-1], x_um[0]])
fig_new.colorbar(im_new, ax=ax_new, label='arrival time (s)')
ax_new.set_xlabel('position along channel (µm)')
ax_new.set_ylabel('position across channel (µm)')
ax_new.set_title('reconstructed time0 (parabolic fit)')
plt.tight_layout()

#%%
# spread (max - min) for each column (fixed y)
col_spread = np.nanmax(tM_new, axis=0) - np.nanmin(tM_new, axis=0)

fig_cs, ax_cs = plt.subplots()
ax_cs.plot(y_um, col_spread, 'o-')
ax_cs.set_xlabel('position along channel (µm)')
ax_cs.set_ylabel('time spread (s)')
ax_cs.set_title('arrival time spread per column (max - min across x)')
plt.tight_layout()


# spread (max - min) for each column (fixed y, across x) from smoothed data
col_spread_smooth = np.nanmax(tM_smooth, axis=0) - np.nanmin(tM_smooth, axis=0)

fig_rs, ax_rs = plt.subplots()
ax_rs.plot(y_um, col_spread_smooth, 'o-')
ax_rs.set_xlabel('position along channel (µm)')
ax_rs.set_ylabel('time spread (s)')
ax_rs.set_title('arrival time spread per column (max - min across x)')
plt.tight_layout()
plt.show()
