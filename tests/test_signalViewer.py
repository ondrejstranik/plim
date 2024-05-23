''' test spectral viewer '''

import pytest


@pytest.mark.GUI
def test_SignalWidget():
    ''' check if gui works'''
    from plim.gui.signalViewer.signalWidget import SignalWidget

    from qtpy.QtWidgets import QApplication
    import numpy as np

    app = QApplication([])

    sV = SignalWidget(np.random.rand(50,4))
    sV.show()
    app.exec()

