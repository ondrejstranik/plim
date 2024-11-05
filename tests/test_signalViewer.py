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
