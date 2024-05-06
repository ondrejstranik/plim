'''
class for calculating plasmon peak from a spectra
'''

import numpy as np
from plim.algorithm.plasmonPeakFit import (fit_polynom, get_peakmax, get_peakcenter)

class PlasmonFit:
    ''' class for calculating plasmon peaks'''

    DEFAULT = {'orderFit': 8,
                'wavelengthGuess': 550,
                'peakWidth': 40,
                'wavelengthStartFit': 500,
                'wavelengthStopFit': 650}



    def __init__(self,**kwargs):
        ''' initialization of the parameters '''

        self.spectraList = kwargs['spectraList'] if 'spectraList' in kwargs else [] 
        self.wavelength = kwargs['wavelength'] if 'wavelength' in kwargs else np.array([])

        # fitting parameter
        self.wavelengthStartFit = self.DEFAULT['wavelengthStartFit']
        self.wavelengthStopFit = self.DEFAULT['wavelengthStopFit']
        self.orderFit = self.DEFAULT['orderFit']
        self.peakWidth = self.DEFAULT['peakWidth']
        self.wavelengthGuess = self.DEFAULT['wavelengthGuess']
        self.wRange = None

        # caluclated values
        self.fitSpectra = []
        self.peakPosition = []

    def setSpectra(self,spectraList):
        ''' define the plasmon spectra '''
        self.spectraList = spectraList

    def setWavelength(self,wavelength):
        ''' set the corresponding wavelengths to the spectra '''
        self.wavelength = wavelength 

    def setFitParameter(self,wavelengthGuess=None,peakWidth=None,orderFit=None,
            wavelengthStopFit= None, wavelengthStartFit=None):
        ''' set fiting parameters '''

        if wavelengthGuess is not None: self.wavelengthGuess = wavelengthGuess
        if peakWidth is not None: self.peakWidth = peakWidth
        if orderFit is not None: self.orderFit = orderFit
        if wavelengthStopFit is not None: self.wavelengthStopFit = wavelengthStopFit
        if wavelengthStartFit is not None: self.wavelengthStartFit = wavelengthStartFit

    def calculateFit(self):
        ''' calculate fits'''

        fitfunction = fit_polynom
        ffvar =  {'Np':self.orderFit}
        #peakfun = get_peakmax
        peakfun = get_peakcenter
        pfvar =  {'peakwidth': self.peakWidth, 'ini_guess': self.wavelengthGuess}

        self.wRange = ((self.wavelength> self.wavelengthStartFit) &
                    (self.wavelength < self.wavelengthStopFit))

        self.fitSpectra = []
        self.peakPosition = []

        # calculate fits
        for ii in np.arange(len(self.spectraList)):
            mypointSpectra = np.array(self.spectraList[ii])
            f = fitfunction(self.wavelength[self.wRange],mypointSpectra[self.wRange],**ffvar)
            self.fitSpectra.append(f(self.wavelength[self.wRange]))
            self.peakPosition.append(peakfun(f,**pfvar))


    def getFit(self):
        ''' get the fitted curves '''
        return self.fitSpectra

    def getPosition(self):
        ''' get the plasmon peak position '''
        return self.peakPosition
    
    def getWavelength(self):
        ''' get wavelengths of the fit '''
        return self.wavelength[self.wRange]


if __name__ == "__main__":

    pass















