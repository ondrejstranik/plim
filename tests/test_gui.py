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

    from viscope.main import viscope
    from viscope.gui.allDeviceGUI import AllDeviceGUI
    from spectralCamera.instrument.sCamera.sCameraGenerator import RGBWebCamera

    from plim.gui.stViewerGUI import STViewerGUI

    #spectral camera system
    scs = RGBWebCamera()
    camera = scs.camera
    sCamera = scs.sCamera

    # add gui
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

    from spectralCamera.instrument.sCamera.sCameraGenerator import RGBWebCamera
    from plim.instrument.plasmonProcessor import PlasmonProcessor

    from viscope.main import viscope
    from viscope.gui.allDeviceGUI import AllDeviceGUI
    from plim.gui.plasmonViewerGUI import PlasmonViewerGUI

    #spectral camera system
    scs = RGBWebCamera()
    camera = scs.camera
    sCamera = scs.sCamera

    # plasmon processor 
    pP = PlasmonProcessor()
    pP.connect(sCamera=sCamera)
    pP.setParameter('threadingNow',True)

    # add gui
    viewer  = AllDeviceGUI(viscope)
    viewer.setDevice(camera)
    newGUI  = PlasmonViewerGUI(viscope)
    newGUI.setDevice(pP)

    # main event loop
    viscope.run()

    camera.disconnect()
    sCamera.disconnect()


@pytest.mark.GUI
def test_positionTrackGUI():
    ''' testing the viewer with webcam'''

    from viscope.main import viscope
    from viscope.gui.allDeviceGUI import AllDeviceGUI
    from plim.gui.plasmonViewerGUI import PlasmonViewerGUI
    from plim.gui.positionTrackGUI import PositionTrackGUI

    from spectralCamera.instrument.sCamera.sCameraGenerator import RGBWebCamera
    from plim.instrument.plasmonProcessor import PlasmonProcessor
    from viscope.instrument.virtual.virtualPump import VirtualPump

    #spectral camera system
    scs = RGBWebCamera()
    camera = scs.camera
    sCamera = scs.sCamera

    # pump
    pump = VirtualPump()
    pump.connect()

    # plasmon processor 
    pP = PlasmonProcessor()
    pP.connect(sCamera=sCamera, pump= pump)
    pP.setParameter('threadingNow',True)

    # add gui
    viewer  = AllDeviceGUI(viscope)
    viewer.setDevice([camera,pump])
    newGUI  = PlasmonViewerGUI(viscope)
    newGUI.setDevice(pP)
    _vWindow = viscope.addViewerWindow()
    newGUI  = PositionTrackGUI(viscope,vWindow=_vWindow)
    newGUI.setDevice(pP)

    # main event loop
    viscope.run()

    camera.disconnect()
    sCamera.disconnect()
    pump.disconnect()