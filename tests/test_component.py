''' camera unitest '''

import pytest


@pytest.mark.GUI
def test_Sample3():
    ''' check if sample is good'''
    import napari
    from plim.virtualSystem.component.sample3 import Sample3
    from plim.gui.spectralViewer.transmissionViewer import TransmissionViewer
    sample = Sample3()
    sample.setPlasmonArray()

    viewer = TransmissionViewer(sample.get(),sample.getWavelength())
    viewer.run()

