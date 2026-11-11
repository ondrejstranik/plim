'''
write bandOffset.npy into folders with recorded photonfocus spectral images

new recordings save bandOffset.npy automatically (SCamera.startRecording),
older recordings need it once. With bandOffset.npy in the folder, SCameraFromFile
provides it and PlasmonProcessor/SpotSpectra use the band dependent fractional mask.

the offset is calculated from the camera calibration (unmixing matrix) and is
written only if the recorded wavelengths match the calibration

usage: python writeBandOffset.py <imageFolder> [<imageFolder> ...]
       (imageFolder = folder with time_*.npy and wavelength.npy, e.g. ...\\raw)
'''
#%%
import sys
from pathlib import Path
import numpy as np

try:
    import PFPyCameraLib
except Exception:
    # camera SDK is not needed to read the calibration file
    from unittest.mock import MagicMock
    sys.modules['PFPyCameraLib'] = MagicMock()
from spectralCamera.algorithm.calibratePFImage import CalibratePFImage
from spectralCamera.algorithm.fileSIVideo import FileSIVideo


def writeBandOffset(folder, overwrite=False):
    ''' write bandOffset.npy into the folder, return True if written '''
    fileVideo = FileSIVideo(folder=str(folder))
    wavelength = fileVideo.loadWavelength()
    if wavelength is None:
        print(f'{folder}: no wavelength.npy - skipped')
        return False
    if fileVideo.loadBandOffset() is not None and not overwrite:
        print(f'{folder}: bandOffset.npy exists - skipped')
        return False

    # calibration with the same bands as the recording (all or with excluded bands)
    sCal = CalibratePFImage()
    wvCal = sCal.wavelength
    if len(wavelength) != len(wvCal):
        excluded = [w for w in wvCal if np.min(np.abs(wavelength - w)) > 1]
        sCal = CalibratePFImage(excludeWavelength=excluded)
    if len(wavelength) != len(sCal.wavelength) or not np.allclose(wavelength, sCal.wavelength):
        print(f'{folder}: wavelengths do not match the photonfocus calibration - skipped')
        return False

    fileVideo.saveBandOffset(sCal.getBandOffset())
    print(f'{folder}: bandOffset.npy written')
    return True


if __name__ == '__main__':
    folders = sys.argv[1:] if len(sys.argv) > 1 else [
        r'F:\ondra\LPI\plim\DATA\filterBased\26-10-27 cabraDNA\raw',
        r'F:\ondra\LPI\plim\DATA\filterBased\26-10-08 SAM_DNA\raw']
    for f in folders:
        writeBandOffset(Path(f))
