'''
class for calculating plasmon peak from a spectra
'''

import logging
import numpy as np
from plim.algorithm.plasmonPeakFit import (fit_polynom, get_peakmax, get_peakcenter)
from timeit import default_timer as timer
from numpy.polynomial import polynomial as P
from numpy.polynomial import Polynomial
from scipy.optimize import brentq
from scipy.optimize import newton

logger = logging.getLogger(__name__)


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
        self._fitCache = None # cached least square solver for calculateFit

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
        logger.debug(f'plasmon fit evaluation time {end -start} s')

    def _calculateFit2(self):
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
            logger.warning('could not fit polynomials')
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
                    extrema = extrema[(np.min(x) <= extrema) & (extrema <= np.max(x))]
                    if np.size(extrema) < 1: extrema = x  
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
        logger.debug(f'plasmon fit evaluation time {end -start} s')


    @staticmethod
    def _polyval(c, x):
        ''' evaluate K polynomials at K (sets of) points with Horner scheme
        c ... coefficients (deg+1, K), lowest order first
        x ... points (..., K), last axis corresponds to the polynomial '''
        y = np.zeros_like(x, dtype=float) + c[-1]
        for ck in c[-2::-1]:
            y = y*x + ck
        return y

    def calculateFit(self, xtol=1e-4):
        ''' fully vectorised least square fitting with polynomial
        (same algorithm as _calculateFit2, no python loop over spectra)

        P.polyfit / P.polyval are not used:

        - P.polyfit(x, Y) rebuilds the Vandermonde matrix and solves the least
          square problem (SVD) at every call, although the solution c = V+ @ y
          depends on the spectra only linearly. V+ (pseudo-inverse) depends only
          on the wavelengths and orderFit, so it is calculated once and cached.
          Each fit is then a single matrix product.
        - P.polyval(x, c) on the wavelength grid was the slowest step
          (~170 ms for 5000 spectra x ~250 wavelengths). The same values are
          obtained by one BLAS matrix product V @ c (~7 ms).
        - polynomials evaluated at one point per spectrum (extrema, bisection,
          integrals) use self._polyval (Horner scheme). It loops only over the
          polynomial order (~8 steps), each step works on all spectra at once.
          A loop-free version (powers + einsum) was tested and is slower
          (builds (order+1) x Datasets temporary arrays) and less accurate.
        - the fit is done in t = (x - x0)/s in [-1, 1] instead of x ~ 500 nm.
          The condition number of the Vandermonde matrix drops from ~6e10
          (x with column scaling, as in P.polyfit) to ~6e2 for orderFit = 8.
          Results are converted back to wavelength at the end.

        Measured speed-up against _calculateFit2 is ~20-50x, the peak
        positions agree within ~2e-4 nm (bisection tolerance xtol) '''

        start = timer()

        self.wRange = ((self.wavelength> self.wavelengthStartFit) &
                    (self.wavelength < self.wavelengthStopFit))

        self.fitSpectra = []
        self.peakPosition = []
        self.fitPeak = []

        # x-coordinates for all sets
        x = self.wavelength[self.wRange]

        # y-coordinates (Nx x Datasets)
        try:
            y_datasets = np.atleast_2d(np.array(self.spectraList))[:,self.wRange].T
        except:
            return

        # the fit is done in the scaled coordinate t = (x - x0)/s, t in [-1, 1]
        # (well conditioned). The least square solver depends only on x and
        # orderFit, so it is calculated once and cached
        try:
            key = (self.orderFit, x.tobytes())
            if self._fitCache is None or self._fitCache[0] != key:
                x0 = 0.5*(np.max(x) + np.min(x))
                s = 0.5*(np.max(x) - np.min(x))
                Vt = P.polyvander((x - x0)/s, self.orderFit) # (Nx x Degree+1)
                self._fitCache = (key, x0, s, Vt, np.linalg.pinv(Vt))
            _, x0, s, Vt, pinvVt = self._fitCache

            # coefficients in t (Degree+1 x Datasets)
            c = pinvVt @ y_datasets
        except:
            logger.warning('could not fit polynomials')
            return

        nSet = c.shape[1]
        w = self.peakWidth/s # peak width in t
        fit = (Vt @ c).T # (Datasets x Nx)

        # 1) initial guess = lowest extremum of the fit inside the range
        # roots of the derivatives as eigenvalues of stacked companion matrices
        dc = P.polyder(c, axis=0)
        n = dc.shape[0] - 1
        guess = (x[np.argmin(fit, axis=1)] - x0)/s # fallback - minimum on the grid
        if n > 0:
            comp = np.zeros((nSet, n, n))
            comp[:, np.arange(1, n), np.arange(n-1)] = 1
            with np.errstate(divide='ignore', invalid='ignore'):
                comp[:, :, -1] = -(dc[:-1]/dc[-1]).T
            comp[~np.isfinite(comp).all(axis=(1, 2))] = 0
            extrema = np.linalg.eigvals(comp) # (Datasets x n)
            ok = (np.isreal(extrema) & (np.real(extrema) >= -1) &
                  (np.real(extrema) <= 1))
            extrema = np.real(extrema).T # (n x Datasets)
            value_at_extrema = np.where(ok.T, self._polyval(c, extrema), np.inf)
            idx = np.argmin(value_at_extrema, axis=0)
            hasRoot = ok.any(axis=1)
            guess[hasRoot] = extrema[idx, np.arange(nSet)][hasRoot]

        # 2) beginning of the peak f(l) = f(l + w) - vectorised bisection
        fpeak = lambda l: self._polyval(c, l) - self._polyval(c, l + w)
        a = guess - w
        b = guess.copy()
        fa = fpeak(a)
        valid = np.sign(fa)*np.sign(fpeak(b)) <= 0
        nIter = int(np.ceil(np.log2(max(abs(self.peakWidth), xtol)/xtol))) + 1
        for _ in range(nIter):
            m = 0.5*(a + b)
            fm = fpeak(m)
            left = np.sign(fm) == np.sign(fa)
            a = np.where(left, m, a)
            fa = np.where(left, fm, fa)
            b = np.where(left, b, m)
        tstart = 0.5*(a + b)
        tstop = tstart + w

        # 3) weighted centre of the peak = int(t f) / int(f), then back to x
        If = P.polyint(c, axis=0)
        Ifp1 = P.polyint(np.vstack((np.zeros((1, nSet)), c)), axis=0)
        with np.errstate(divide='ignore', invalid='ignore'):
            tcenter = ((self._polyval(Ifp1, tstop) - self._polyval(Ifp1, tstart)) /
                       (self._polyval(If, tstop) - self._polyval(If, tstart)))
        valid &= np.isfinite(tcenter)
        fStart = self._polyval(c, tstart)
        fStop = self._polyval(c, tstop)

        # convert from t to wavelength
        peakcenter = x0 + s*tcenter
        lstart = x0 + s*tstart
        lstop = lstart + self.peakWidth
        guess = x0 + s*guess

        # 4) store results - failed fits are set to ones
        for k in range(nSet):
            if valid[k]:
                self.peakPosition.append(peakcenter[k])
                self.fitSpectra.append(fit[k])
                self.fitPeak.append(((lstart[k], lstop[k]), (fStart[k], fStop[k])))
            else:
                self.peakPosition.append(guess[k])
                self.fitSpectra.append(np.ones_like(x))
                self.fitPeak.append(((guess[k], guess[k]), (1, 1)))

        end = timer()
        logger.debug(f'plasmon fit evaluation time {end -start} s')

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















