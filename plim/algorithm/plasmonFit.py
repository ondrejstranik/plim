'''
class for calculating plasmon peak from a spectra
'''

import numpy as np
from plim.algorithm.plasmonPeakFit import (fit_polynom, get_peakmax, get_peakcenter)
from timeit import default_timer as timer
from numpy.polynomial import polynomial as P
from numpy.polynomial import Polynomial
from scipy.optimize import brentq
from scipy.optimize import newton


class PlasmonFit:
    ''' class for calculating plasmon peaks'''

    DEFAULT = {'orderFit': 8,
                'wavelengthGuess': 550,
                'peakWidth': 40,
                'wavelengthStartFit': 450,
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

        # calculated values
        self.fitSpectra = [] # fitted spectra for given range
        self.peakPosition = [] #  fitted peak position
        self.fitPeak = [] # fitted peak [peak_start w, peak_stop w] [value1 value2] 

    def setSpectra(self,spectraList):
        ''' define the plasmon spectra '''
        self.spectraList = spectraList

    def setWavelength(self,wavelength):
        ''' set the corresponding wavelengths to the spectra '''
        self.wavelength = wavelength 

    def setFitParameter(self,wavelengthGuess=None,peakWidth=None,orderFit=None,
            wavelengthStopFit= None, wavelengthStartFit=None):
        ''' set fitting parameters '''

        if wavelengthGuess is not None: self.wavelengthGuess = wavelengthGuess
        if peakWidth is not None: self.peakWidth = peakWidth
        if orderFit is not None: self.orderFit = orderFit
        if wavelengthStopFit is not None: self.wavelengthStopFit = wavelengthStopFit
        if wavelengthStartFit is not None: self.wavelengthStartFit = wavelengthStartFit

    def _calculateFit(self):
        ''' calculate fits - old function using plasmonPeakFit.py'''

        start = timer()

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

        end = timer()
        print(f'plasmon fit evaluation time {end -start} s')

    def calculateFit(self):
        ''' parallel least square fitting with polynomial'''

        start = timer()

        self.wRange = ((self.wavelength> self.wavelengthStartFit) &
                    (self.wavelength < self.wavelengthStopFit))

        self.fitSpectra = []
        self.peakPosition = []
        self.fitPeak = []

        # x-coordinates for all sets
        x = self.wavelength[self.wRange]

        # y-coordinates
        y_datasets = np.array(self.spectraList)
        try:
            if y_datasets.ndim >1:
                y_datasets = np.array(self.spectraList)[:,self.wRange].T
            else:
                y_datasets = np.array(self.spectraList)[self.wRange].T
        except:
            return

        
        # polyfit returns a 2D array (Degree+1 x Datasets)
        try:
            coeffs = P.polyfit(x, y_datasets, deg=self.orderFit)
        except:
            print('could not fit polynomials')
            return


        # define aux functions
        p1 = Polynomial([0, 1]) # p1(x) = x
        shift = Polynomial([self.peakWidth, 1]) # shift(x) = self.peakWidth + x 

        for c in coeffs.T:
            # define the polynomial function
            f = Polynomial(c)
            # define aux function
            fpeak = f - f(shift)
            fpeakDeriv = fpeak.deriv()
            If = f.integ()
            fp1 = f*p1
            Ifp1 = fp1.integ()

            if True:
                # get minimum of fit (f-function)in order to 
                # get better estimate than self.wavelengthGuess
                # use root function
                if True:
                    fDeriv = f.deriv()
                    extrema = fDeriv.roots()
                    # Filter out complex roots
                    extrema = extrema[np.isreal(extrema)]
                    # Get real part of root
                    extrema = np.real(extrema)
                    # Apply bounds check
                    extrema = extrema[(x[0] <= extrema) & (extrema <= x[-1])]
                # evaluate at all points
                else:
                    extrema = x
                # evaluate the extrema
                value_at_extrema = f(extrema)
                minimum_index = np.argmin(value_at_extrema)
                _wavelengthGuess = extrema[minimum_index]
            else:
                _wavelengthGuess = self.wavelengthGuess

            try:            
                # calculate the beginning of the peak - newton method
                if False:
                    # define aux function
                    fpeakDeriv = fpeak.deriv()
                    fpeakDeriv2 = fpeakDeriv.deriv()
                    lstart = newton(fpeak,_wavelengthGuess-self.peakWidth/2, 
                                    fprime=fpeakDeriv,
                                    fprime2=fpeakDeriv2, tol=1e-4)

                # calculate the beginning of the peak - brentq
                else:
                    lstart = brentq(fpeak,_wavelengthGuess-self.peakWidth,
                                    _wavelengthGuess, xtol= 1e-4)

                # get weighted centre of the peak 
                nom = Ifp1(lstart + self.peakWidth) - Ifp1(lstart)
                denom = If(lstart + self.peakWidth) - If(lstart)
                peakcenter = nom/denom

                self.peakPosition.append(peakcenter)
                self.fitSpectra.append(f(self.wavelength[self.wRange]))
                self.fitPeak.append(((lstart, lstart + self.peakWidth),
                                    (f(lstart), f(lstart + self.peakWidth))))

            except:
                # could not find the fit
                # set the fit to ones
                self.peakPosition.append(_wavelengthGuess)
                self.fitSpectra.append(np.ones_like(self.wavelength[self.wRange]))
                self.fitPeak.append(((_wavelengthGuess,_wavelengthGuess),
                                    (1, 1)))


        end = timer()
        print(f'plasmon fit evaluation time {end -start} s')


    '''
    def calculateFit2(self):

                   
        import jax
        import jax.numpy as jnp
        from jax import vmap

        # 1. Create a batch of coefficients for 1,000 polynomials
        # Each row represents one polynomial: [a, b, c, d]
        # Example: f(x) = 1x^3 - 6x^2 + 11x - 6 (Roots are 1, 2, 3)
        num_polys = 1000
        coeffs = jnp.array([[1.0, -6.0, 11.0, -6.0]] * num_polys)

        # 2. Vectorize the jnp.roots function
        # strip_zeros=False is REQUIRED for JAX transformations like vmap or jit
        vectorized_roots = vmap(lambda p: jnp.roots(p, strip_zeros=False))

        # 3. Solve all polynomials at once
        # This replaces a Python for-loop and runs in parallel
        all_roots = vectorized_roots(coeffs)

        print(f"Shape of roots: {all_roots.shape}")  # (1000, 3)
        print(f"First polynomial roots: {all_roots[0]}")

    '''

    def getFit(self):
        ''' get the fitted curves '''
        return self.fitSpectra

    def getPosition(self):
        ''' get the plasmon peak position '''
        return self.peakPosition
    
    def getWavelength(self):
        ''' get wavelengths of the fit '''
        return self.wavelength[self.wRange]
    
    def getFitPeak(self):
        ''' get the fitted peak'''
        return self.fitPeak

if __name__ == "__main__":
    pass















