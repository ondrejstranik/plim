'''
lightweight, read-only napari viewer for the offline signal analyser
'''
#%%
import numpy as np
import logging
from qtpy.QtCore import Signal
from viscope.gui.napariGUI import NapariGUI

logger = logging.getLogger(__name__)


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
        # sigUpdateData/sigColorChanged/sigSelectionChanged/table/
        # syncPointsFromTable() - PlasmonViewerGUI delegates that to a
        # separate PlasmonViewer (SViewer subclass) object, but there is no
        # equivalent spectral-processing class here, so this GUI plays both
        # roles itself
        self.plasmonViewer = self

        # per-spot metadata, shape-compatible with plim.algorithm.spotData.
        # SpotData.table. Replaced-by-alias (spotViewerGui.table =
        # positionTrack.sD.table) by PositionTrackGUI.interconnectGui() once
        # a real SpotData exists; this default just keeps the GUI usable
        # stand-alone (mirrors SViewer.__init__ in spectralCamera)
        self.table = {'name': [], 'color': [], 'visible': []}

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
        # block interactive add/move/delete, but selecting a point (to
        # recolor it) must keep working. editable=False can't be used for
        # that: napari forces PAN_ZOOM mode whenever a layer isn't editable
        # (Layer._set_mode), which blocks selection too, not just editing.
        # block add/move/delete individually instead, and default into
        # select mode so a click selects right away, no mode switch needed
        self.pointLayer.mode = 'select'
        self.pointLayer.add = lambda *a, **kw: None
        self.pointLayer._move = lambda *a, **kw: None
        self.pointLayer.remove_selected = lambda *a, **kw: None

        # 'v' toggles visibility of the currently selected spot(s) - bound
        # on self.viewer, not pointLayer, so it fires regardless of which
        # layer is currently active (see SViewer for the same pattern/the
        # reasoning on why viewer-level, not layer-level)
        self.viewer.bind_key('v', lambda viewer: self.toggleVisibility(), overwrite=True)

        # record a colour picked via napari's own UI into self.table (kept
        # separate from sigColorChanged so it always runs before anything
        # reacting to that signal sees the change)
        self.pointLayer._face.events.current_color.connect(self.colorChanged)
        self.pointLayer._face.events.current_color.connect(lambda: self.sigColorChanged.emit())
        self.pointLayer.selected_data.events.items_changed.connect(
            lambda *_: self.sigSelectionChanged.emit())

    def updateGui(self):
        ''' update the data in gui '''
        self.redrawViewer()

    def redrawViewer(self):
        ''' redraw the image and spot points from the device data '''
        sS = self.device.spotSpectra

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

        self.syncPointsFromTable()

    def syncPointsFromTable(self):
        ''' push self.table['color']/['visible']/['name'] onto pointLayer.
        Mirrors SViewer.syncPointsFromTable() (spectralCamera) - kept as a
        separate copy here since this GUI isn't an SViewer subclass. '''
        rgb = self.table.get('color')
        if not rgb:
            return
        vis = self.table['visible']
        _color = [rgb[ii] + 'ff' if vis[ii] == 'True' else rgb[ii] + '00' for ii in range(len(rgb))]

        # defensive guard in case this bulk push ever fires current_color as
        # a side effect - prevents it being misread as a genuine colour pick
        # made in the viewer, which would otherwise re-enter colorChanged()
        with self.pointLayer._face.events.current_color.blocker():
            self.pointLayer.face_color = _color

        try:
            self.pointLayer.features = {'names': list(self.table['name'])}
        except Exception:
            logger.exception('error updating point annotations from table')

    def colorChanged(self):
        ''' record a colour picked via napari's own UI into self.table
        (aliased to SpotData.table once wired up by PositionTrackGUI) for
        the currently selected point(s). Mirrors SViewer.colorChanged(),
        minus the "cumbersome" spectral-graph redraw dance - there is no
        spectral graph in this GUI to keep in sync. '''
        idx = list(self.pointLayer.selected_data)
        try:
            hexColor = '#{:02x}{:02x}{:02x}'.format(
                *(np.asarray(self.pointLayer._face.current_color[:3]) * 255).astype(int))
            for ii in idx:
                self.table['color'][ii] = hexColor
        except Exception:
            logger.exception('error updating table color from current_color')

    def toggleVisibility(self):
        ''' toggle visibility of the currently selected spot(s) - bound to
        the 'v' key. Mirrors SViewer.toggleVisibility(). '''
        idx = list(self.pointLayer.selected_data)
        if not idx:
            return
        for ii in idx:
            self.table['visible'][ii] = 'False' if self.table['visible'][ii] == 'True' else 'True'
        self.syncPointsFromTable()
        self.sigUpdateData.emit()


if __name__ == "__main__":
    pass
