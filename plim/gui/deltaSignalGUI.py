'''
class for pushing a delta-signal image layer into a live spectral viewer
'''
#%%
import numpy as np
from qtpy.QtWidgets import QWidget, QVBoxLayout, QPushButton, QCheckBox

from viscope.gui.baseGUI import BaseGUI


class DeltaSignalGUI(BaseGUI):
    ''' dockable panel with 'new Image'/'live Image' buttons that paint
    each spot's current dSignal value into its mask pixels and push the
    result into a connected viewer's napari window (PlasmonViewerGUI, or
    any GUI shaped the same way - exposing .viewer). This GUI has no
    napari view of its own, so it needs setDevice() for the data
    (spotSpectra/spotData, e.g. from PlasmonProcessor) and
    interconnectGui() for a viewer to draw into - the same two-step wiring
    used by PositionTrackGUI/FitGUI.

    For the live acquisition path only - expects device.worker to exist
    (e.g. PlasmonProcessor), which both drives periodic 'live Image'
    updates and provides the rate-limited path used for manual
    evalTime/dTime edits (see interconnectGui()). For the offline signal
    analyser (FileDataProcessor, which never starts a worker thread), use
    DeltaSignal2GUI instead.

    The 'dtime update' tick controls how 'live Image' picks its window:
    checked (default) grows dTime to keep tracking the latest recorded
    time; unchecked just follows whatever evalTime/dTime SignalWidget's
    own vLine markers currently sit at, so the live layer mirrors the
    graph instead of auto-advancing past it. '''

    DEFAULT = {'nameGUI': 'DeltaSignal'}

    def __init__(self, viscope, **kwargs):
        ''' initialise the class '''
        super().__init__(viscope, **kwargs)

        self.device = None
        self.viewerGui = None
        self.ptGui = None
        self.liveLayer = None  # the reusable 'liveDelta' napari image layer

        DeltaSignalGUI.__setWidget(self)

    def __setWidget(self):
        ''' prepare the gui '''

        plotBtn = QPushButton('new Image')
        plotBtn.clicked.connect(self.plotDeltaSignal)

        self.liveBtn = QPushButton('live Image')
        self.liveBtn.setCheckable(True)
        self.liveBtn.toggled.connect(self._onLiveToggled)

        # checked (default) = auto-grow dTime to the latest recorded time;
        # unchecked = follow SignalWidget's own evalTime/dTime as-is
        self.dTimeUpdateCheck = QCheckBox('dtime update')
        self.dTimeUpdateCheck.setChecked(True)

        self.widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(plotBtn)
        layout.addWidget(self.liveBtn)
        layout.addWidget(self.dTimeUpdateCheck)
        self.widget.setLayout(layout)

        self.vWindow.addParameterGui(self.widget, name=self.DEFAULT['nameGUI'])

    def interconnectGui(self, viewerGui, ptGui=None):
        ''' connect with the viewer GUI (e.g. PlasmonViewerGUI) whose
        napari window the delta-signal layer(s) get added into, and
        optionally with PositionTrackGUI so live updates also move
        SignalWidget's evalTime/dTime graph lines - without it, live mode
        falls back to leaving sD.evalTime/dTime/the graph untouched.

        Also, when ptGui is given, refreshes 'liveDelta' (via
        guiUpdateTimed(), the same rate-limited path the device's own
        worker tick uses) whenever SignalWidget's own lineParameter fires
        sigUpdateData - which it does unconditionally on every
        evalTime/dTime edit (among other things). Routing a manual edit
        through the shared rate limiter is safe here: the worker keeps
        ticking regardless, so if an edit happens to land inside
        guiUpdateTimed's throttle window, the very next worker tick picks
        it up anyway - a bounded, imperceptible delay, and it coalesces
        rapid edits with the worker's own updates instead of doing a
        redundant extra redraw. '''
        self.viewerGui = viewerGui
        self.ptGui = ptGui
        if self.ptGui is not None:
            self.ptGui.positionTrack.sigUpdateData.connect(self.guiUpdateTimed)

    def setDevice(self, device):
        ''' the device is a processor exposing spotSpectra/spotData
        (e.g. PlasmonProcessor) with an active worker thread '''
        super().setDevice(device)
        if self.device.worker is not None:
            self.device.worker.yielded.connect(self.guiUpdateTimed)

    def _buildDeltaImage(self, dSignal):
        ''' paint the given per-spot dSignal values into their mask pixels,
        skipping spots hidden via the 'visible' column (same table SignalWidget
        uses to show/hide graph lines - see its table['visible'] == 'True'
        checks) as well as out-of-bounds outlier spots '''
        sS = self.device.spotSpectra
        sD = self.device.spotData

        if sS.image is None or sS.maskSpotIdx is None or dSignal is None:
            return None

        visible = np.array([v == 'True' for v in sD.table['visible']])
        mask = visible & ~sS.outliers

        _image = np.zeros(sS.image.shape[1:])
        _image[sS.maskSpotIdx[0][mask, :],
               sS.maskSpotIdx[1][mask, :]] = dSignal[mask, None]
        return _image

    def plotDeltaSignal(self):
        ''' add a new, timestamped delta-signal snapshot layer, drawn into
        the interconnected viewer. Uses sD.evalTime/dTime/dSignal exactly
        as the user currently has them set (e.g. via SignalWidget) - unlike
        the live path below, this doesn't move anything. '''
        if self.viewerGui is None or self.device is None:
            return
        sD = self.device.spotData
        _image = self._buildDeltaImage(sD.dSignal)
        if _image is None:
            return
        _name = f'delta Signal @ {sD.evalTime + sD.dTime} s '
        self.viewerGui.viewer.add_image(_image, name=_name, colormap='turbo')

    def _onLiveToggled(self, checked):
        ''' give immediate feedback on turning 'live Image' on, instead of
        waiting for the next (rate-limited) update from the device '''
        if checked:
            self._updateLiveDelta()

    def updateGui(self):
        ''' called (rate-limited) on every new frame from the device - only
        does the live-delta update while 'live Image' is checked '''
        if not self.liveBtn.isChecked() or self.viewerGui is None or self.device is None:
            return
        self._updateLiveDelta()

    def _updateLiveDelta(self):
        ''' push the current delta signal into the reusable 'liveDelta'
        layer. Which window is used depends on the 'dtime update' tick:

        - checked (default): grow the delta window to reach the most
          recently recorded time, keeping evalTime (the baseline) fixed.
          When a PositionTrackGUI is connected (see interconnectGui()),
          this moves the SHARED sD.dTime (via getDSignal(), the stateful
          method) and immediately resyncs SignalWidget's own cached
          evalTime/dTime/dSignal widget values + redraws its graph, so the
          vLine[1] marker visibly tracks the live window while vLine[0]
          (evalTime, the baseline) stays put. The resync is the essential
          part: SignalWidget's evalTime/dTime spinboxes are auto_call=True,
          so if their cached value were left stale (not matching the
          sD.dTime we just set), the next unrelated widget event (a colour
          change, a visibility toggle, anything) would see a mismatch,
          mistake it for a real user edit, and silently write the stale
          value back - undoing this update and yanking the line back.
          Resyncing right here closes that window every time. Without a
          connected PositionTrackGUI, falls back to computeDSignal() (a
          pure computation) so live mode still works but leaves
          sD.evalTime/dTime/the graph completely alone.

        - unchecked: just follow whatever evalTime/dTime SignalWidget's own
          vLine markers currently sit at (a pure computeDSignal() read, no
          mutation) - the live layer mirrors the graph instead of
          auto-advancing past it, so dragging the lines in SignalWidget is
          what drives the update. '''
        sD = self.device.spotData
        if sD.time is None or len(sD.time) == 0:
            return

        if self.dTimeUpdateCheck.isChecked():
            # evalTime/dTime are relative to sD.time0 (the first recorded
            # timestamp), not raw/absolute time - see SpotData.getRange()
            # ("self.time - self.time0 - time") and getData() (returns
            # "self.time - self.time0" for the graph's x-axis). sD.time
            # itself stores whatever PlasmonProcessor fed it, which is an
            # absolute wall-clock timestamp (sCamera.t0) - using it
            # directly here produced a value far outside the dTime
            # widget's [0, 1e6] range, raising inside redrawWidget() and
            # aborting this method before ever reaching the image-building
            # code below (that's why neither Plot nor live were producing
            # any image at all).
            latestRelativeTime = sD.time[-1] - sD.time0
            # clamp to 0: if the baseline (evalTime) is at or after the
            # latest recorded time (e.g. right at the start of a run), a
            # negative dTime would be equally out of the dTime widget's
            # [0, 1e6] range and raise the same way
            dTime = max(0.0, latestRelativeTime - sD.evalTime)

            if self.ptGui is not None:
                sD.getDSignal(dTime=dTime)
                self.ptGui.positionTrack.redrawWidget()
                self.ptGui.positionTrack.drawGraph()
                dSignal = sD.dSignal
            else:
                dSignal = sD.computeDSignal(sD.evalTime, dTime)
        else:
            dSignal = sD.computeDSignal(sD.evalTime, sD.dTime)

        _image = self._buildDeltaImage(dSignal)
        if _image is None:
            return

        if self.liveLayer is None or self.liveLayer not in self.viewerGui.viewer.layers:
            self.liveLayer = self.viewerGui.viewer.add_image(_image, name='liveDelta', colormap='turbo')
        else:
            self.liveLayer.data = _image


if __name__ == "__main__":
    pass
