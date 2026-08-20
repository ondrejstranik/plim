"""
file data processor - "device" wrapping a saved dataset for offline review

@author: ostranik
"""
#%%

from viscope.instrument.base.baseProcessor import BaseProcessor
from plim.algorithm.fileData import FileData


class FileDataProcessor(BaseProcessor):
    ''' "device" for the offline signal analyser: wraps a FileData instance and exposes
    it as a device (.name, .spotData, .flowData, .spotSpectra, .pF, .injectionData) - the
    same shape the live scripts get from PlasmonProcessor - so PositionTrackGUI/
    SpotViewerGUI/FileDataProcessorGUI's setDevice() pattern can be reused unchanged for
    offline review. No live loop is started (nothing to poll), so .worker stays None. '''
    DEFAULT = {'name': 'FileDataProcessor'}

    def __init__(self, name=None, **kwargs):
        ''' initialisation '''

        if name is None: name = FileDataProcessor.DEFAULT['name']
        super().__init__(name=name, **kwargs)

        self.fileData = FileData()

    @property
    def spotData(self): return self.fileData.spotData
    @property
    def flowData(self): return self.fileData.flowData
    @property
    def spotSpectra(self): return self.fileData.spotSpectra
    @property
    def pF(self): return self.fileData.pF
    @property
    def injectionData(self): return self.fileData.injectionData

    def loadFile(self, folder, fileMainName):
        ''' load a previously saved dataset and recompute all derived fields needed for
        display. loadAllFile() only writes raw fields via its sub-loaders (e.g.
        loadSpotFile() sets spotData.signal/.time directly, bypassing SpotData.setData()),
        so getDSignal/getNoise/offset/reference/table are stale until recomputed here -
        the offline equivalent of what PlasmonProcessor.processData() does per live
        frame, but for a whole pre-recorded dataset at once. '''
        self.fileData.loadAllFile(folder, fileMainName)

        sD, sS, fD = self.spotData, self.spotSpectra, self.flowData
        if sD.signal is not None:
            sD.time0 = sD.time[0]
            sD.setOffset()
            sD.setReference()
            sD.getDSignal()
            sD.getNoise()
            sD.setTable(table=sD.table)
            if fD.signal is not None:
                sD.time0 = fD.time[0]
        if sS.image is not None:
            sS.setMask()


#%%
if __name__ == "__main__":
    pass
