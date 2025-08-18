'''
package to fit binding kinetic data
'''

import numpy as np
from scipy.optimize import curve_fit
from scipy.special import erf
import inspect


#def functionPFO(x,x0,a,b):
#    ''' pseudo first order binding curve'''
#    res = x*0
#    xb = x>=x0
#    xa = x< x0
#    res[xa] = 0
#    if b!=0:
#        res[xb] = a*(1-np.exp(-(x[xb]-x0)/b))
#    else:
#        res[xb] = a + x[xb]*0
#    return res

def functionPFO(x,x0,a,b):
    ''' pseudo first order binding curve'''
    res = x*0
    xb = x>=x0
    xa = x< x0
    res[xa] = 0
    res[xb] = a*(1-np.exp(-(x[xb]-x0)/(b+1e-6)))
    return res

#def functionPFO(x,x0,a,b):
#    xMod = (erf((x-x0)/10)+1)/2*(x-x0)
#    res = a*(1-np.exp(-xMod*b))
#    return res



def funcP1(x,c0,c1):
    ''' linear function'''
    res = c0 + c1*x
    return res


class KineticFit:
    ''' class for fitting binding kinetics curves'''

    DEFAULT = {'fitType': 'adsorption' # type of kinetic fit
               }


    def __init__(self,**kwargs):
        ''' initialization of the parameters '''

        # data
        self.time = None # numpy 1D array
        self.signal = None # numpy array each column represent one set
        self.fitEstimate = None
        self.fitType = self.DEFAULT['fitType']

        # fitting parameters
        self.fitParam = None
        self.fitFunction = None
        self.bcgFunction = None

        self.setFitFunction()

    def setSignal(self,signal):
        ''' define '''
        self.signal = signal

    def setTime(self,time):
        ''' set the corresponding time'''
        self.time = time 

    def setFitParameter(self,time0=None,tau=None,amp=None,
                        fitType=None, fitEstimate = None):
        ''' set fitting parameters '''

        if fitType is not None: 
            self.fitType = fitType
            self.setFitFunction()
        if time0 is not None: self.fitEstimate[0] = time0
        if amp is not None: self.fitEstimate[1] = amp
        #if tau is not None: self.fitEstimate[2] = 1/tau
        if tau is not None: self.fitEstimate[2] = tau

        if fitEstimate is not None: self.fitEstimate = fitEstimate

    def setFitFunction(self):
        ''' define fit function depending on the number of polynomial parameters of background'''
        if self.fitType == 'adsorption':
            _fitFunction = functionPFO
            self.bcgFunction = funcP1
            self.fitFunction = lambda x,x0,a,b,c0,c1 : _fitFunction(x,x0,a,b) + self.bcgFunction(x,c0,c1)
            
            sig = inspect.signature(self.fitFunction)
            self.fitEstimate = np.zeros(len(sig.parameters)-1)

    def calculateFit(self):
        ''' calculate fits'''
        nFit = self.signal.shape[1]
        self.fitParam = np.zeros((nFit,len(self.fitEstimate)))
        for ii in range(nFit):
            try:
                x = self.time
                y = self.signal[:,ii]
                popt,pocv = curve_fit(self.fitFunction,x,y,p0 = self.fitEstimate.tolist())
                self.fitParam[ii,:] = popt
            except:
                print(f'did not find fit for signal {ii}')


if __name__ == "__main__":
    pass















