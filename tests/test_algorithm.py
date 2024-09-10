''' algorithm check '''

import pytest

def generateSample():
    ''' generate plasmon spot sample '''
    from plim.virtualSystem.component.sample3 import Sample3
    import numpy as np
    sample = Sample3()
    sample.setPlasmonArray()
    image = (1- sample.get())*10**3
    image += np.random.poisson(image)
    w = sample.getWavelength()

    return (image, w)

@pytest.mark.GUI
def test_spotIdentification():
    ''' check if spots are identified '''
    import napari
    from plim.algorithm.spotIdentification import SpotIdentification

    image , w = generateSample()

   # identify the spots
    sI = SpotIdentification(image)
    myPosition = sI.getPosition()
    myRadius = sI.getRadius()

    # show images
    viewer = napari.Viewer()
    viewer.add_image(image)
    viewer.add_points(myPosition)
    napari.run()

@pytest.mark.GUI
def test_spotSpectra():
    ''' check if spectra are properly calculated'''
    from plim.algorithm.spotSpectra import SpotSpectra
    from plim.algorithm.spotIdentification import SpotIdentification
    import numpy as np

    image , w = generateSample()

   # identify the spots
    sI = SpotIdentification(image)
    myPosition = sI.getPosition().astype(int)
    myRadius = int(sI.getRadius())

    print(f'position {myPosition}')
    print(f'radius {myRadius}')

    # calculate spectra
    sS = SpotSpectra(image,myPosition,pxAve=int(myRadius), 
                     sphere= False, ratio= 1.4, angle=25)

    # show images
    import napari
    viewer = napari.Viewer()
    viewer.add_image(image)
    viewer.add_image(sS.maskImage)
    napari.run()

    # show spectra
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.plot(w, np.array(sS.getA()).T)
    ax.set_title('Spectra')
    plt.show()


@pytest.mark.GUI
def test_plamonFit():
    ''' check if spectra are fitted'''
    import numpy as np
    from plim.algorithm.spotIdentification import SpotIdentification
    from plim.algorithm.spotSpectra import SpotSpectra
    from plim.algorithm.plasmonFit import PlasmonFit

    image , w = generateSample()

    # identify the spots
    sI = SpotIdentification(image)
    myPosition = sI.getPosition()
    myRadius = sI.getRadius()

    # calculate spectra
    sS = SpotSpectra(image,spotPosition=myPosition)

    # fit plasmon peak
    pF = PlasmonFit(spectraList=sS.getA(),wavelength=w)
    pF.calculateFit()

    # show spectra
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.plot(w, np.array(sS.getA()).T,'*k')
    ax.set_title('Spectra and Fits')
    ax.plot(pF.getWavelength(), np.array(pF.getFit()).T,'-b')

    fig, ax = plt.subplots()
    ax.plot(pF.getPosition(),'*k')
    ax.set_title('Position')
    
    plt.show()

def test_spotData():
    from plim.algorithm.spotData import SpotData
    import numpy as np

    sD = SpotData()

    sD.setData(np.random.rand(50,5))
    sD.addDataValue(np.random.rand(5))
    (signal, time) = sD.getData()
    print(f'signal {signal}')
    print(f'time {time}')

    assert signal.shape[0]==51

def test_flowData():
    from plim.algorithm.flowData import FlowData
    import numpy as np

    fD = FlowData()

    fD.addDataValue([1],1)
    fD.addDataValue(np.random.rand(1),np.random.rand(1))
    fD.setData(np.random.rand(50))
 
    (signal, time) = fD.getData()
    print(f'signal {signal}')
    print(f'time {time}')

    assert signal.shape[0]==50