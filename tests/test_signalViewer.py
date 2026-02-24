''' test spectral viewer '''

import pytest


@pytest.mark.GUI
def test_SignalWidget():
    ''' check if gui works'''
    from plim.gui.signalViewer.signalWidget import SignalWidget

    from qtpy.QtWidgets import QApplication
    import numpy as np

    app = QApplication([])

    sV = SignalWidget(np.random.rand(50,4),np.arange(50))
    sV.show()
    app.exec()

@pytest.mark.GUI
def test_InfoWidget():
    ''' check if gui works'''
    from plim.gui.signalViewer.infoWidget import InfoWidget

    from qtpy.QtWidgets import QApplication
    import numpy as np

    app = QApplication([])

    sV = InfoWidget()
    sV.show()
    app.exec()

def test_FitWidget():
    ''' check if gui works'''
    import numpy as np
    from plim.algorithm.kineticFit import functionBinding
    from plim.algorithm.kineticFit import KineticFit
    from plim.gui.signalViewer.fitWidget import FitWidget
    from qtpy.QtWidgets import QApplication

    # generate data set    
    time = np.arange(1000)
    nFit = 5
    # trueParam .... time0,tau,amp,p0,p1
    trueParam = np.array((100,50,10,20,1e-3))
    signal = np.zeros((len(time),nFit))
    for ii in range(nFit):
        _Param = trueParam + (ii,ii,ii,ii,0)
        signal[:,ii] = functionBinding(time,*_Param) + np.random.rand(len(time))*5

    kF = KineticFit()
    kF.setSignal(signal)
    kF.setTime(time)
    kF.setTable({'name':['a','b','c','d','e']})

    app = QApplication([])

    fW = FitWidget(kineticFit=kF)
    fW.drawGraph(onlyData=True)
    fW.fitParameter.time0.value = 150
    fW.fitParameter.tau.value = 50
    fW.fitParameter.amp.value = 20
    fW.show()
    app.exec()

@pytest.mark.GUI
def test_InjectionWidget():
    ''' check if gui works'''
    from plim.gui.signalViewer.injectionWidget import InjectionWidget

    from qtpy.QtWidgets import QApplication
    import numpy as np

    app = QApplication([])

    iV = InjectionWidget()
    iV.show()
    app.exec()

