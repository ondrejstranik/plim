'''
Load/Save/Export panel for the offline signal analyser, paired with a FileDataProcessor device
'''
#%%
from pathlib import Path

from qtpy.QtWidgets import QFileDialog, QWidget, QVBoxLayout, QLabel, QPushButton
import pyqtgraph.exporters

from viscope.gui.baseGUI import BaseGUI


class FileDataProcessorGUI(BaseGUI):
    ''' Load/Save/Export panel paired 1:1 with a FileDataProcessor device, the same
    way SCameraFromFileGUI is paired with SCameraFromFile. Replaces SaveDataGUI for
    this app - device.fileData already *is* the persistent FileData instance, so
    there is no need to wrap device attributes into a fresh one on every save. '''

    DEFAULT = {'nameGUI': 'Data'}

    def __init__(self, viscope, **kwargs):
        ''' initialise the class '''
        super().__init__(viscope, **kwargs)

        self.folder = None
        self.fileMainName = None
        self.ptGui = None
        self.spotViewerGui = None

        FileDataProcessorGUI.__setWidget(self)

    def __setWidget(self):
        ''' prepare the gui '''

        self.fileLabel = QLabel('')

        loadBtn = QPushButton('Load')
        loadBtn.clicked.connect(self.selectAndLoad)

        saveBtn = QPushButton('Save')
        saveBtn.clicked.connect(self.save)

        exportBtn = QPushButton('Export')
        exportBtn.clicked.connect(self.export)

        self.dataGui = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.fileLabel)
        layout.addWidget(loadBtn)
        layout.addWidget(saveBtn)
        layout.addWidget(exportBtn)
        self.dataGui.setLayout(layout)

        self.vWindow.addParameterGui(self.dataGui, name=self.DEFAULT['nameGUI'])

    def interconnectGui(self, ptGui, spotViewerGui):
        ''' connect with the other GUIs of the signal analyser - needed for the
        post-load refresh and for Export's graph/viewer access '''
        self.ptGui = ptGui
        self.spotViewerGui = spotViewerGui

    def _updateFileLabel(self):
        ''' update the displayed folder/filename '''
        self.fileLabel.setText(f'{self.folder}\n{self.fileMainName}')

    def _selectFile(self):
        ''' select a saved dataset with a native file dialog
        return (folder, fileMainName) or (None, None) if cancelled '''
        dialog = QFileDialog()
        dialog.setDirectory(str(self.viscope.dataFolder))
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter("Numpy arrays (*.npz)")
        dialog.setViewMode(QFileDialog.ViewMode.List)
        filenames = []
        if dialog.exec():
            filenames = dialog.selectedFiles()

        if filenames:
            p = Path(filenames[0])
            fileMainName = '_'.join(p.stem.split('_')[:-1])
            return str(p.parent), fileMainName
        return None, None

    def selectAndLoad(self):
        ''' prompt for a dataset via the native file dialog and load it if one was
        chosen. return True if a dataset was chosen and loaded, False if the dialog
        was cancelled '''
        folder, fileMainName = self._selectFile()
        if fileMainName is None:
            return False

        self.folder = folder
        self.fileMainName = fileMainName
        self.device.loadFile(folder, fileMainName)
        self._updateFileLabel()

        # no live device tick to rely on - refresh everything explicitly.
        # spotViewerGui must go first: it populates pointLayer.data to match
        # the newly loaded spot count, which the sigUpdateData emit below
        # relies on - it triggers PositionTrackGUI.updatePlasmonViewer()
        # pushing the (new) table length into pointLayer.features, and that
        # raises if pointLayer.data hasn't been resized to match yet
        if self.spotViewerGui is not None:
            self.spotViewerGui.updateGui()
        if self.ptGui is not None:
            self.ptGui.updateGui()
            # updateGui() only redraws the graph - resync SignalWidget's own
            # displayed magicgui fields too, and notify other GUIs (e.g. the
            # plasmon viewer) that the underlying data changed
            self.ptGui.positionTrack.redrawWidget()
            self.ptGui.positionTrack.sigUpdateData.emit()

        return True

    def save(self):
        ''' write back to the currently loaded folder/fileMainName, no dialog '''
        if self.fileMainName is None:
            print('no dataset loaded yet - nothing to save')
            return
        self.device.fileData.saveAllFile(self.folder, self.fileMainName)
        print('saving data')

    def export(self):
        ''' export a viewer screenshot, the signal/flow graphs and the info table '''
        dialog = QFileDialog()
        dialog.setDirectory(str(self.viscope.dataFolder))
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        folder = None
        if dialog.exec():
            folder = dialog.selectedFiles()

        if not folder:
            return
        folder = folder[0]

        viewer = self.spotViewerGui.viewer
        viewer.theme = 'light'
        viewer.screenshot(path=folder + '/image.png')
        viewer.theme = 'dark'
        print('viewer image exported')

        exporter = pyqtgraph.exporters.ImageExporter(self.ptGui.positionTrack.graph.plotItem)
        exporter.export(folder + '/signal.png')
        print('signal graph exported')

        exporter = pyqtgraph.exporters.ImageExporter(self.ptGui.flowTrack.graph.plotItem)
        exporter.export(folder + '/flow.png')
        print('flow graph exported')

        self.device.spotData.saveInfoFile(folder, 'infoTable.txt')
        print('info data exported')


if __name__ == "__main__":
    pass
