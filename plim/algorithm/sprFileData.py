"""
SprFileData - convert SPR sensorgrams (excel sheet) into the plim data format

each sheet (tab) of the excel file is one measurement. Columns come in pairs
(time [min], signal) - one pair for each SPR channel, e.g.
    Time (min) | ch1_Target 1 uM in buffer SSC 5x | Time (min) | ch2_Reference_buffer SSC 5x | ...

each sheet is saved as one dataset of FileData (6 files: <sheetName>_spotData.npz,
_image.npz, _fit.npz, _flowData.npz, _info.dat, _injectionData.txt), which can be
opened in runSignalAnalyser.
- the channels (columns) are the 'spots', the column headers are their names
- the image is synthetic: each channel is a square, which is exactly the spot of the
  square mask (spotSpectra circle=False, ratio=1) with the saved pxAve. The squares are
  placed vertically (ch1 on the top), the gap leaves space for the background mask.

reading the excel file needs pandas + openpyxl

@author: ostranik
"""
#%%

import re
import logging
import datetime
from pathlib import Path
import numpy as np

from plim.algorithm.fileData import FileData

logger = logging.getLogger(__name__)


class SprFileData:
    ''' class to convert SPR sensorgrams from an excel file into plim data files (FileData) '''

    DEFAULT = {'pxAve': 5, # spot mask: half width of the square [px]
               'pxSpace': 1, # mask: space between spot and background [px]
               'pxBcg': 3, # mask: thickness of the background [px]
               'distance': 10, # [px] free space between the background masks of neighbouring channels
               'border': 10, # [px] free space between the background masks and the image edge
               'intensityBcg': 1000, # intensity of the image outside the channels
               'intensityChannel': 500, # intensity of the channels
               'referenceKey': 'reference', # channel name containing this key is the reference
               'referenceColor': '#ff0000', # color of the reference channels (= default reference color of SpotData)
               'channelColor': '#ffffff'
               }

    def __init__(self, fileName=None, time0=None, **kwargs):
        ''' initialisation
        fileName ... excel file
        time0 ... start of the measurement [s from epoch] (only formally needed,
                  the analyser works with the time relative to the start)
                  None ... date from the file name (yyyymmdd...) or now
        '''
        for key, value in self.DEFAULT.items():
            setattr(self, key, kwargs.get(key, value))

        self.fileName = None
        self.time0 = time0
        self.sheet = {} # sheetName -> {'name': [nChannel], 'time': (nTime,) [s], 'signal': (nTime, nChannel)}

        if fileName is not None: self.loadExcel(fileName)

    @staticmethod
    def _getTime0FromName(fileName):
        ''' start of the day from the file name (yyyymmdd...), now if not possible '''
        m = re.match(r'(\d{8})', Path(fileName).name)
        if m is not None:
            try:
                return datetime.datetime.strptime(m.group(1), '%Y%m%d').timestamp()
            except ValueError:
                pass
        return datetime.datetime.now().timestamp()

    def loadExcel(self, fileName):
        ''' read all sheets of the excel file '''
        import pandas as pd

        self.fileName = Path(fileName)
        if self.time0 is None: self.time0 = self._getTime0FromName(self.fileName)

        self.sheet = {}
        for sheetName, df in pd.read_excel(self.fileName, sheet_name=None).items():
            data = self._readSheet(df)
            if data is None:
                logger.warning(f'sheet {sheetName}: no (time, signal) column pairs - skipped')
                continue
            self.sheet[sheetName] = data

    @staticmethod
    def _readSheet(df):
        ''' get channel names, common time [s] and signal (nTime, nChannel) from one sheet.
        each channel has its own time column (it can be shorter or slightly shifted),
        the signals are interpolated to the longest time axis '''
        name, tList, yList = [], [], []
        for i in range(0, df.shape[1] - 1, 2):
            t = _toFloat(df.iloc[:, i])
            y = _toFloat(df.iloc[:, i + 1])
            ok = np.isfinite(t) & np.isfinite(y)
            if ok.sum() < 2: continue
            # pandas makes duplicate column names unique ('name.1') - remove the suffix
            name.append(re.sub(r'\.\d+$', '', str(df.columns[i + 1]).strip()))
            tList.append(t[ok] * 60) # min -> s
            yList.append(y[ok])

        if len(name) == 0: return None

        time = tList[int(np.argmax([len(t) for t in tList]))]
        signal = np.zeros((len(time), len(name)))
        for ii, (t, y) in enumerate(zip(tList, yList)):
            idx = np.argsort(t)
            # outside its own time span the channel keeps its edge value
            signal[:, ii] = np.interp(time, t[idx], y[idx])

        return {'name': name, 'time': time, 'signal': signal}

    def getImage(self, nChannel):
        ''' synthetic image (1, ny, nx) with the channels as squares (= spot of the square mask)
        and spot positions (nChannel, 2) [row, col] in the centre of the squares '''
        # square mask in SpotSpectra (circle=False, ratio=1): spot |dx|, |dy| < pxAve
        h = self.pxAve - 1 # half size of the square [px]
        m = h + self.pxSpace + self.pxBcg # half size with the background mask

        # channels placed vertically (ch1 on the top)
        nx = 2*(m + self.border) + 1
        ny = nChannel*(2*m + 1) + (nChannel - 1)*self.distance + 2*self.border

        image = np.full((1, ny, nx), float(self.intensityBcg))
        spotPosition = np.zeros((nChannel, 2))
        x0 = self.border + m
        for ii in range(nChannel):
            y0 = self.border + m + ii*(2*m + 1 + self.distance)
            image[0, y0 - h:y0 + h + 1, x0 - h:x0 + h + 1] = self.intensityChannel
            spotPosition[ii] = [y0, x0]

        return image, spotPosition

    def getFileData(self, sheetName):
        ''' FileData filled with the data of one sheet '''
        data = self.sheet[sheetName]
        nChannel = len(data['name'])
        time = self.time0 + data['time']

        fD = FileData()

        # spots = channels
        image, spotPosition = self.getImage(nChannel)
        fD.spotSpectra.image = image
        fD.spotSpectra.spotPosition = spotPosition
        fD.spotSpectra.pxAve = int(self.pxAve)
        fD.spotSpectra.pxSpace = int(self.pxSpace)
        fD.spotSpectra.pxBcg = int(self.pxBcg)
        fD.spotSpectra.circle = False
        fD.spotSpectra.ratio = 1
        fD.pF.wavelength = np.array([0.0]) # no spectral information

        # signal
        fD.spotData.setData(data['signal'], time)
        isReference = [self.referenceKey.lower() in n.lower() for n in data['name']]
        fD.spotData.setTable({
            'name': list(data['name']),
            'color': [self.referenceColor if r else self.channelColor for r in isReference],
            'visible': ['True']*nChannel})
        fD.spotData.alignTime = 0
        fD.spotData.evalTime = 0
        fD.spotData.dTime = float(np.floor(data['time'][-1]*0.95)) # [s] signal change over the measurement

        # no pump - flow data are empty
        fD.flowData.signal = None
        fD.flowData.time = None

        # injection info
        text = f'source: {self.fileName.name}\n' if self.fileName is not None else ''
        text += f'0s {sheetName}\n' + ''.join(f'    channel {i}: {n}\n' for i, n in enumerate(data['name']))
        fD.injectionData.setData(text, time[0])

        return fD

    def save(self, folder=None, sheetName=None):
        ''' save each sheet (only sheetName if given) as one plim dataset (6 files)
        folder ... output folder, None = folder of the excel file
        the sheet name is the fileMainName
        return list of fileMainNames '''
        folder = Path(folder) if folder is not None else self.fileName.parent
        folder.mkdir(parents=True, exist_ok=True)

        sheetNames = list(self.sheet.keys()) if sheetName is None else [sheetName]
        fileMainNames = []
        for s in sheetNames:
            fileMainName = re.sub(r'[\\/:*?"<>|]', '-', s).strip()
            self.getFileData(s).saveAllFile(str(folder), fileMainName)
            logger.info(f'sheet {s} saved as {folder / fileMainName}_*')
            fileMainNames.append(fileMainName)
        return fileMainNames


def _toFloat(column):
    ''' column of a pandas dataframe as float numpy array (non numbers -> nan) '''
    import pandas as pd
    return pd.to_numeric(column, errors='coerce').to_numpy(dtype=float)


#%%

if __name__ == '__main__':
    fileName = r'F:\ondra\LPI\plim\DATA\sprBased\2026-10-14 DNA-OXA48\20261014_DNA oxa_SPR.xlsx'
    sprData = SprFileData(fileName)
    for name in sprData.save():
        print(f'saved {name}')
