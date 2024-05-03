''' camera unitest '''

import pytest


@pytest.mark.GUI
def test_TransmissionViewer():
    ''' check if gui works'''
    from plim.gui.spectralViewer.transmissionViewer import TransmissionViewer
    import numpy as np
    im = np.random.rand(10,100,100) +1
    wavelength = np.arange(im.shape[0])*1.3+ 10
    sViewer = TransmissionViewer(im, wavelength)
    sViewer.run()

@pytest.mark.GUI
def test_spotSpectraViewer():
    ''' check if gui works'''
    from plim.gui.spectralViewer.spotSpectraViewer import SpotSpectraViewer
    from plim.virtualSystem.component.sample3 import Sample3
    import numpy as np

    sample = Sample3()
    sample.setPlasmonArray()
    image = (1- sample.get())*10**3
    image += np.random.poisson(image)
    sViewer = SpotSpectraViewer(image, sample.getWavelength())
    sViewer.run()