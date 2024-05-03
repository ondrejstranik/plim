''' camera unitest '''

import pytest


@pytest.mark.GUI
def test_Sample3():
    ''' check if sample is good'''
    import napari
    from plim.virtualSystem.component.sample3 import Sample3
    sample = Sample3()
    sample.setPlasmonArray()
    # load multichannel image in one line
    viewer = napari.view_image(sample.get())
    napari.run()

