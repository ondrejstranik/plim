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

        # calculated values
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
        ''' set fitting parameters '''

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

    '''
    def calculateFit2(self):


        # parallel least square fitting
        import numpy as np
        from numpy.polynomial import polynomial as P

        # 1. Share the same x-coordinates for all sets
        x = np.linspace(0, 10, 100)

        # 2. Define multiple datasets in a 2D array (Shape: Points x Datasets)
        # Example: 500 different datasets, each with 100 points
        y_datasets = np.random.rand(100, 500)

        # 3. Fit all 500 datasets to a 3rd-degree polynomial in one call
        # polyfit returns a 2D array (Degree+1 x Datasets)
        coeffs = P.polyfit(x, y_datasets, deg=3)

        print(coeffs.shape)  # Output: (4, 500) -> 4 coefficients for each of the 500 fits



            
                    
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


if __name__ == "__main__":
    pass















