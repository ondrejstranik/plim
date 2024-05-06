''' camera unitest '''

import pytest


@pytest.mark.GUI
def test_TransmissionViewer():
    ''' check if gui works'''
    from plim.gui.spectralViewer.transmissionViewer import TransmissionViewer
    from plim.virtualSystem.component.sample3 import Sample3
    import numpy as np
        
    sample = Sample3()
    sample.setPlasmonArray()
    image = (1- sample.get())*10**3
    image += np.random.poisson(image)
    w = sample.getWavelength()

    sViewer = TransmissionViewer(image, w)
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

@pytest.mark.GUI
def test_plasmonViewer():
    from plim.gui.spectralViewer.plasmonViewer import PlasmonViewer
    from plim.virtualSystem.component.sample3 import Sample3
    import numpy as np
        
    sample = Sample3()
    sample.setPlasmonArray()
    image = (1- sample.get())*10**3
    image += np.random.poisson(image)
    w = sample.getWavelength()

    sViewer = PlasmonViewer(image, w)
    sViewer.run()