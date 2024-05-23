''' camera unitest '''

import pytest


def test_saving():
    ''' check if data are saved properly'''
    #import napari
    import numpy as np

    from plim.gui.spectralViewer.plasmonViewer import PlasmonViewer
    from plim.gui.signalViewer.signalWidget import SignalWidget
    from plim.gui.signalViewer.flowRateWidget import FlowRateWidget    
    from qtpy.QtWidgets import QApplication

    ffolder = r'G:\office\work\git\plim\plim\DATA'
    ffile = 'Experiment1'

    container = np.load(ffolder + '/' + ffile + '_image.npz')
    im = container['arr_1']
    w = container['arr_2']
    spotData = container['arr_0']

    container = np.load(ffolder + '/' + ffile + '_spotData.npz')
    signal = container['arr_0']
    sTime = container['arr_1']

    container = np.load(ffolder + '/' + ffile + '_flowData.npz')
    flow = container['arr_0']
    fTime = container['arr_1']

    app = QApplication([])
    sViewer = PlasmonViewer(im,w)
    sViewer.pointLayer.data = spotData

    sV = SignalWidget(signal,sTime)
    sV.show()

    frV = FlowRateWidget(flow,fTime)
    frV.show()

    app.exec()



