'''
lightweight, read-only napari viewer for the offline signal analyser
'''
#%%
import numpy as np
from qtpy.QtCore import Signal
from viscope.gui.napariGUI import NapariGUI


class SpotViewerGUI(NapariGUI):
    ''' shows the overview image and spot positions of a loaded dataset.
    the offline counterpart of PlasmonViewerGUI, but with no spectral graph/
    spot-identification pipeline (this data has no spectral cube) and
    read-only points (spot positions/count come from an already-fitted,
    loaded dataset, not from live identification) '''

    DEFAULT = {'nameGUI': 'SpotViewer'}

    sigUpdateData = Signal()
    sigColorChanged = Signal()
    sigSelectionChanged = Signal()

    def __init__(self, viscope, **kwargs):
        ''' initialise the class '''
        super().__init__(viscope, **kwargs)

        # PositionTrackGUI expects viewerGui.plasmonViewer to expose pointLayer/
        # sigUpdateData/sigColorChanged/sigSelectionChanged - PlasmonViewerGUI
        # delegates that to a separate PlasmonViewer object, but there is no
        # equivalent spectral-processing class here, so this GUI plays both
        # roles itself
        self.plasmonViewer = self

        SpotViewerGUI.__setWidget(self)

    def __setWidget(self):
        ''' prepare the gui '''

        self.imageLayer = self.viewer.add_image(np.zeros((2, 2)), name='overview')
        # keep the contrast limits auto-scaling to the data on every update
        self.imageLayer._keep_auto_contrast = True
        # best-effort: also press the actual 'continuous' auto-contrast
        # button so its icon in the layer controls panel matches the state
        # set above (see spotSpectraViewer.py's SViewer for the same pattern)
        try:
            controls = self.viewer.window._qt_viewer.controls.widgets[self.imageLayer]
            autoScaleBar = getattr(controls, 'autoScaleBar', None) or controls._contrast_limits_control.auto_scale_bar
            autoScaleBar._auto_btn.setChecked(True)
        except (KeyError, AttributeError):
            pass

        self.pointLayer = self.viewer.add_points(name='spots', size=5, face_color='red')
        self.pointLayer.features = {'names': []}
        self.pointLayer.text = {
            'string': '{names}',
            'size': 20,
            'color': 'green',
            'translation': np.array([-5, 0])}
        # spot positions/count come from a loaded, already-fitted dataset -
        # block interactive add/move/delete (selection stays fully functional)
        self.pointLayer.editable = False

        self.viewer.bind_key('d', lambda x: self.addDeltaSignalLayer())

        self.pointLayer._face.events.current_color.connect(lambda: self.sigColorChanged.emit())
        self.pointLayer.selected_data.events.items_changed.connect(
            lambda *_: self.sigSelectionChanged.emit())

    def addDeltaSignalLayer(self):
        ''' add delta signal layer into napari '''
        sS = self.device.spotSpectra
        sD = self.device.spotData

        _image = np.zeros(self.imageLayer.data.shape[1:])
        _image[sS.maskSpotIdx[0][~sS.outliers, :],
               sS.maskSpotIdx[1][~sS.outliers, :]] = sD.dSignal[:, None]

        _name = f'delta Signal @ {sD.evalTime + sD.dTime} s '
        self.viewer.add_image(_image, name=_name)

    def updateGui(self):
        ''' update the data in gui '''
        self.redrawViewer()

    def redrawViewer(self):
        ''' redraw the image and spot points from the device data '''
        sS = self.device.spotSpectra
        sD = self.device.spotData

        newImage = sS.image
        if newImage is not None:
            self.imageLayer.data = newImage
            # always recentre the camera on a freshly loaded dataset - the
            # user may have panned/zoomed away while looking at the
            # previous one
            self.viewer.reset_view()

        spotPosition = sS.spotPosition
        if spotPosition is not None:
            try:
                if np.any(self.pointLayer.data - spotPosition):
                    self.pointLayer.data = spotPosition
            except ValueError:
                self.pointLayer.data = spotPosition

        table = sD.table
        if table.get('name') is None:
            return

        self.pointLayer.features = {'names': table['name']}
        rgb = table['color']
        vis = table['visible']
        _color = [rgb[ii] + 'ff' if vis[ii] == 'True' else rgb[ii] + '00' for ii in range(len(rgb))]
        self.pointLayer.face_color = _color


if __name__ == "__main__":
    pass
