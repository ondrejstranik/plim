'''
class for calculating plasmon peak from a spectra
'''

import numpy as np
from plim.algorithm.plasmonPeakFit import (fit_polynom, get_peakmax, get_peakcenter)

class PlasmonSpectra:
    ''' class for calculating plasmon peaks'''

    DEFAULT = {'orderFit': 8,
                'wavelengthGuess': 550,
                'peakWidth': 40,
                'wavelengthStartFit': 500,
                'wavelengthStopFit': 650}



    def __init__(self,spectraList,wavelength,**kwargs):
        ''' initialization of the parameters '''

        self.spectraList = spectraList
        self.wavelength = wavelength

        # fitting parameter
        self.wavelengthStartFit = self.DEFAULT['wavelengthStartFit']
        self.wavelengthStopFit = self.DEFAULT[]
        self.orderFit = self.DEFAULT['orderFit']
        self.peakWidth = self.DEFAULT['peakWidth']
        self.wavelengthGuess = self.DEFAULT['wavelengthGuess']

        self.fitSpectra = []
        self.peakPosition = []

    def calculateFit(self):
        ''' calculate fits'''

        fitfunction = fit_polynom
        ffvar =  {'Np':self.orderFit}
        #peakfun = get_peakmax
        peakfun = get_peakcenter
        pfvar =  {'peakwidth': self.peakWidth, 'ini_guess': self.wavelengthGuess}

        wrange = ((self.wavelength> self.wavelengthStartFit) &
                    (self.wavelength < self.wavelengthStopFit))

        self.fitSpectra = []
        self.peakPosition = []

        # calculate fits
        for ii in np.arange(len(self.pointSpectra)):
            mypointSpectra = np.array(self.pointSpectra[ii])
            f = fitfunction(self.wavelength[wrange],mypointSpectra[wrange],**ffvar)
            self.fitSpectra.append(f(self.wavelength[wrange]))
            self.peakPosition.append(peakfun(f,**pfvar))


    def getFit(self):
        ''' get the fitted curves '''
        return self.fitSpectra

    def getPosition(self):
        ''' get the plasmon peak position '''
        return self.peakPosition


if __name__ == "__main__":

        # load the image
        container = np.load(os.getcwd() + '\\code\\Data\\plasmonicArray.npz')
        wxyImage = container['arr_0']
        w = container['arr_1']
        mySpot = [[118,113], [151,108]]

        mySS = SpotSpectra(wxyImage,spotPosition=mySpot)

        # show images
        import napari
        viewer = napari.Viewer()
        viewer.add_image(np.sum(wxyImage, axis=0))
        viewer.add_image(mySS.maskImage)
        napari.run()


        # show spectra
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.plot(w, np.array(mySS.spectraSpot).T)
        ax.set_title('Spectra')

        fig, ax = plt.subplots()
        ax.plot(w, np.array(mySS.spectraRawSpot).T)
        ax.plot(w, np.array(mySS.spectraRawBcg).T)

        ax.set_title('Raw Spectra')




        plt.show()















