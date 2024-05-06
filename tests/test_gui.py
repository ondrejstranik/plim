''' camera unitest '''

import pytest

@pytest.mark.GUI
def test_TViewerGUI():
    ''' testing the viewer with webcam'''

    from viscope.main import Viscope
    from viscope.gui.allDeviceGUI import AllDeviceGUI
    from spectralCamera.instrument.sCamera.sCameraGenerator import RGBWebCamera

    from plim.gui.tViewerGUI import TViewerGui

    #spectral camera system
    scs = RGBWebCamera()
    camera = scs.camera
    sCamera = scs.sCamera

    # add gui
    viscope = Viscope()
    viewer  = AllDeviceGUI(viscope)
    viewer.setDevice(camera)
    newGUI  = TViewerGui(viscope)
    newGUI.setDevice(sCamera)

    # main event loop
    viscope.run()

    camera.disconnect()
    sCamera.disconnect()

@pytest.mark.GUI
def test_STViewerGUI():
    ''' testing the viewer with webcam'''

    from viscope.main import Viscope
    from viscope.gui.allDeviceGUI import AllDeviceGUI
    from spectralCamera.instrument.sCamera.sCameraGenerator import RGBWebCamera

    from plim.gui.stViewerGUI import STViewerGUI

    #spectral camera system
    scs = RGBWebCamera()
    camera = scs.camera
    sCamera = scs.sCamera

    # add gui
    viscope = Viscope()
    viewer  = AllDeviceGUI(viscope)
    viewer.setDevice(camera)
    newGUI  = STViewerGUI(viscope)
    newGUI.setDevice(sCamera)

    # main event loop
    viscope.run()

    camera.disconnect()
    sCamera.disconnect()

@pytest.mark.GUI
def test_plasmonViewerGUI():
    ''' testing the viewer with webcam'''

    from viscope.main import Viscope
    from viscope.gui.allDeviceGUI import AllDeviceGUI
    from spectralCamera.instrument.sCamera.sCameraGenerator import RGBWebCamera

    from plim.gui.plasmonViewerGUI import PlasmonViewerGUI

        #spectral camera system
    scs = RGBWebCamera()
    camera = scs.camera
    sCamera = scs.sCamera

    # add gui
    viscope = Viscope()
    viewer  = AllDeviceGUI(viscope)
    viewer.setDevice(camera)
    newGUI  = PlasmonViewerGUI(viscope)
    newGUI.setDevice(sCamera)

    # main event loop
    viscope.run()

    camera.disconnect()
    sCamera.disconnect()