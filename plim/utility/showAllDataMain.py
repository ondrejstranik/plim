''' script to process videos of hyperspectral images'''
#%%
# import and parameter definition

import numpy as np
import napari

from qtpy.QtWidgets import QApplication,QMainWindow,QWidget,QToolBar,QVBoxLayout
import sys

from plim.algorithm.spotInfo import SpotInfo

from plim.gui.spectralViewer.plasmonViewer import PlasmonViewer
from plim.gui.signalViewer.signalWidget import SignalWidget
from plim.gui.signalViewer.flowRateWidget import FlowRateWidget
from plim.gui.signalViewer.infoWidget import InfoWidget


class Window(QMainWindow):
    DEFAULT = {'nameSet'  : {
                            'flow':'_flowData.npz',
                            'image': '_image.npz',
                            'spot': '_spotData.npz'
                            }}


    def __init__(self,**kwarg):
        super().__init__(parent=None)

        # data parameters
        self.spotPosition = None
        self.image = None
        self.w = None
        self.flow = None
        self.time = None
        self.signal = None
        self.sI = None

        # widget parameters
        self.viewer = None
        self.spotLayer = None
        self.sW = None
        self.fW = None
        self.iW = None

        self._createToolBar()

        self._loadData()

    def _createToolBar(self):
        tools = QToolBar()
        tools.addAction("Load", self._loadData)
        tools.addAction("Exit", self.closeAll)
        self.addToolBar(tools)

    def _loadData(self):

        ffolder = r'F:\ondra\LPI\24-08-28 spr_variable_array\iso_h20_1to4'
        ffile = r'Experiment1'
        nameSet = self.DEFAULT['nameSet']


        # load image
        container1 = np.load(ffolder + '/' + ffile + nameSet['image'])
        self.spotPosition = container1['arr_0']
        self.image = container1['arr_1']
        self.w = container1['arr_2']

        # load flow
        container2 = np.load(ffolder + '/' + ffile + nameSet['flow'])
        self.flow = container2['arr_0']
        self.time = container2['arr_1']

        # load spot
        container3 = np.load(ffolder + '/' + ffile + nameSet['spot'])
        self.signal = container3['arr_0']

        # set default spot info
        self.sI = SpotInfo(n=self.signal.shape[1])

        print(f'number of spots {self.sI.nSpot}')

        self._createWidget()

    def closeAll(self):
        self.sW.close()
        self.iW.close()
        self.fW.close()
        self.viewer.close()
        self.close()


    def updateColor(self):
        _fc = 1*self.spotLayer.face_color #  deep copy of the colors
        _fc[list(self.spotLayer.selected_data)] = self.spotLayer._face.current_color # adjust the just modified 

        _fcHex = ['#{:02x}{:02x}{:02x}{:02x}'.format( *ii.tolist()) for ii in (_fc*255).astype(int)]


        print(f'_fc {_fcHex}')



        self.sI.table['color'] = _fcHex

        self.iW.updateData()

        #self.sW.sD.signalColor = _fc
        #self.sW.drawGraph()    

    def updateWidget(self,**kwargs):
        print('updatingWidgets')
       
        try:
            # napari widget
            _sel = [x=='True' for x in self.sI.table['visible']]
            self.spotLayer.data = self.spotPosition[_sel]
            self.spotLayer.features = {
                'names': np.array(self.sI.table['name'])[_sel].tolist()
            }
            self.spotLayer.face_color = np.array(self.sI.table['color'])[_sel].tolist()        
            # signal widget
            self.sW.setData(self.signal[:,_sel],self.time)
            rgbaColor = [[int(x[1:3],16)/255,int(x[3:5],16)/255,int(x[5:7],16)/255,int(x[7:9],16)/255] for x in self.sI.table['color']]
            print(f'rgbaColor {rgbaColor}')
            self.sW.sD.signalColor = rgbaColor
            self.sW.drawGraph()
        except:
            print('error in updateWidget')

    def _createWidget(self):

        self.viewer = napari.Viewer()
        self.viewer.add_image(self.image)
        self.spotLayer = self.viewer.add_points(np.array([[0,0]]))
        self.spotLayer.features = {'names': ['0']}
        self.spotLayer.text = {
                'string': '{names}',
                'size': 20,
                'color': 'green',
                'translation': np.array([-5, 0])}
        
        self.spotLayer._face.events.current_color.connect(self.updateColor)

        self.sW = SignalWidget(signal=self.signal,time= self.time)
        self.sW.show()

        self.fW = FlowRateWidget(signal=self.flow, time = self.time)
        self.fW.show()

        self.iW = InfoWidget(self.sI)
        self.iW.show()
        self.updateWidget()
        self.iW.sigUpdateData.connect(self.updateWidget)



if __name__ == "__main__":
    app = QApplication([])
    window = Window()
    window.show()
    sys.exit(app.exec())
    #napari.run()



#%%