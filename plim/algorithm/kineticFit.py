'''
package to fit binding kinetic data
'''

import numpy as np
from scipy.optimize import curve_fit

def functionPFO(x,x0,a,b):
    ''' pseudo first order binding curve'''
    res = x*0
    xb = x>=x0
    xa = x< x0
    res[xa] = 0
    res[xb] = a*(1-np.exp(-(x[xb]-x0)/b))
    return res

def functionBcgPFO(x,x0,a,b,polyPar):
    ''' pseudo first order with polynomial background'''
    return functionBcgPFO(x,x0,a,b) + np.poly1d(polyPar)(x)


class KineticFit:
    ''' class for fitting binding kinetics curves'''

    DEFAULT = {'polyCoef': np.array([0,0]), # estimated coefficients for polynomial to fit background 
               'fitType': 'adsorption' # type of kinetic fit
               }


    def __init__(self,**kwargs):
        ''' initialization of the parameters '''

        # data
        self.time = None # numpy 1D array
        self.signal = None # numpy array each column represent one set

        # calculated values
        self.bcgFit = None # numpy array each column represent one set
        self.kineticFit = None # numpy array each column represent one set

        # fitting parameters
        self.time0 = None
        self.tau = None
        self.amp = None
        self.polyCoef = self.DEFAULT['polyCoef']
        self.fitType = self.DEFAULT['fitType']

    def setSignal(self,signal):
        ''' define '''
        self.signal = signal

    def setTime(self,time):
        ''' set the corresponding time'''
        self.time = time 

    def setFitParameter(self,time0=None,tau=None,amp=None,polyCoef=None,fitType=None):
        ''' set fitting parameters '''
        if time0 is not None: self.time0 = time0
        if tau is not None: self.tau = tau
        if polyCoef is not None: self.polyCoef = polyCoef
        if amp is not None: self.amp = amp
        if fitType is not None: self.fitType = fitType


    def calculateFit(self):
        ''' calculate fits'''

        


        if self.fitType == 'adsorption':
            func = functionBcgPFO

        for ii in range(self.signal.shape[0]-1):
            try:
                x = self.time
                y = self.signal[:,ii]
                popt,pocv = curve_fit(func,x,y,p0 = (self.time0,self.amp,self.tau,*self.polyCoef))
            except:
                print(f'did not find fit for signal {ii}')

        tauList.append(1/popt[3])
        sigList.append(popt[2])


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
    


if __name__ == "__main__":
    pass















