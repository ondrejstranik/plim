'''
package to fit binding kinetic data
'''

import numpy as np
from scipy.optimize import curve_fit
from scipy.special import erf
import inspect
import csv
import pickle
from lmfit import Model
from enum import Enum
import inspect

def functionPFO(x,x0,a,b):
    ''' pseudo first order binding curve'''
    res = x*0.0
    xb = x>=x0
    xa = x< x0
    res[xa] = 0.0
    #b = np.abs(b) + 1e-6
    b += 1e-6

    res[xb] = a*(1-np.exp(-(x[xb]-x0)/b))
    return res

def functionEDecay(x,x0,a,b):
    ''' exponential decay function '''
    res = x*0.0
    xb = x>=x0
    xa = x< x0
    res[xa] = a
    #b = np.abs(b) + 1e-6
    b += 1e-6

    res[xb] = a*np.exp(-(x[xb]-x0)/b)
    return res

def functionZO(x,x0,a):
    ''' Zero Order binding (linear) function - approximation of PFO'''
    res = x*0.0
    xb = x>=x0
    xa = x< x0
    res[xa] = 0
    res[xb] = a*(x[xb]-x0)
    return res


#def functionPFO(x,x0,a,b):
#    xMod = (erf((x-x0)/10)+1)/2*(x-x0)
#    res = a*(1-np.exp(-xMod*b))
#    return res

def functionP1(x,c0,c1):
    ''' linear function'''
    res = c0 + c1*x
    return res

def functionBinding(x,time0,tau,amp,p0,p1):
    return functionPFO(x,time0,amp,tau) + functionP1(x-time0,p0,p1)

def functionLinearBinding(x,time0,slope,p0,p1):
    return functionZO(x,time0,slope) + functionP1(x-time0,p0,p1)

def functionDesorption(x,time0,tau,amp,p0,p1):
    return functionEDecay(x,time0,amp,tau) + functionP1(x-time0,p0,p1)

def functionDoubleBinding(x,time0,tau1,amp1,tau2,amp2,p0,p1):
    ''' double exponential association + linear background '''
    return (functionPFO(x,time0,amp1,tau1)
            + functionPFO(x,time0,amp2,tau2)
            + functionP1(x-time0,p0,p1))


class FitType(Enum):
    ADSORPTION = ("adsorption", functionBinding)
    DESORPTION = ("desorption", functionDesorption)
    LINEAR = ("linear", functionLinearBinding)
    ADSORPTION_DOUBLE = ("adsorption_double", functionDoubleBinding)

    def __init__(self, label, fitFunction):
        self.label = label
        self.function = fitFunction
        sig = inspect.signature(fitFunction)
        self.parameters = [p for p in sig.parameters.keys() if p not in ('self', 'x')]

    @classmethod
    def from_label(cls, label_string):
        for member in cls:
            if member.label == label_string:
                return member
        raise ValueError(f"'{label_string}' it is not defined FitType.label")


class KineticFit:
    ''' class for fitting binding kinetics curves'''

    DEFAULT = {'fitType': FitType.ADSORPTION # type of kinetic fit 
               }


    def __init__(self,**kwargs):
        ''' initialization of the parameters '''

        # data
        self.time = None # numpy 1D array
        self.signal = None # numpy array each column represent one set

        # info about the data
        self.table = {'name': None}

        # fitting parameters
        self.fittedParam = None
        self.fitType = self.DEFAULT['fitType']
        self.model = None
        self.modelParams = None

        self.setFitFunction()

    def setSignal(self,signal):
        ''' define '''
        self.signal = signal

    def setTime(self,time):
        ''' set the corresponding time'''
        self.time = time

    def setTable(self,table):
        ''' set additional info about the fitting data '''
        self.table = table         

    def setFitParameter(self, name=None, value=None, fixed=None, fitType=None, min=None, max=None):
        ''' set fitting parameters'''
        if fitType is not None: self.setFitFunction(fitType)
        if name is not None:
            self.modelParams[name].set(
                **({} if value is None else {'value': value}),
                **({} if fixed is None else {'vary': not fixed}),
                **({} if min   is None else {'min':   min}),
                **({} if max   is None else {'max':   max}),
            )

    def setFitFunction(self, fitType:FitType =None):
        ''' define fit function '''
        if fitType is not None:
            self.fitType = fitType
            self.model = Model(fitType.function)
            self.modelParams = self.model.make_params()

    def calculateFit(self):
        ''' calculate fits'''
        nFit = self.signal.shape[1]
        self.fittedParam = np.zeros((nFit,len(self.modelParams)))

        for ii in range(nFit):
            try:
                result = self.model.fit(self.signal[:,ii],self.modelParams, x= self.time)
                self.fittedParam[ii,:] = np.array([result.best_values[_name]
                                                for _name in result.best_values.keys()])
                # for double exponential ensure tau1 <= tau2
                if self.fitType == FitType.ADSORPTION_DOUBLE:
                    if self.fittedParam[ii, 1] > self.fittedParam[ii, 3]:
                        (self.fittedParam[ii, 1], self.fittedParam[ii, 3]) = (self.fittedParam[ii, 3], self.fittedParam[ii, 1])
                        (self.fittedParam[ii, 2], self.fittedParam[ii, 4]) = (self.fittedParam[ii, 4], self.fittedParam[ii, 2])
            except:
                print(f'could not fit signal{ii}')
        print(f'model parameters {self.modelParams}')


    def getFittedSignal(self,idx):
        return self.model.func(self.time,*self.fittedParam[idx,:])

    def getCleanDataFit(self):
        '''Return signal and fit with background subtracted for all curves.

        Returns
        -------
        clean_signal : ndarray (n_time, n_curves)  Raw signal minus background.
        clean_fit    : ndarray (n_time, n_curves)  Fitted curve minus background.
        '''
        nFit = self.signal.shape[1]
        clean_signal = np.empty_like(self.signal)
        clean_fit    = np.empty((len(self.time), nFit))
        for ii in range(nFit):
            bg = self.getFittedBackground(ii)
            clean_signal[:, ii] = self.signal[:, ii] - bg
            clean_fit[:, ii]    = self.getFittedSignal(ii) - bg
        return clean_signal, clean_fit


    def getFittedBackground(self,idx):
        _param = self.fittedParam[idx,:]*1.0
        if self.fitType == FitType.LINEAR:
            _param[1]= 0 # set slope of binding to zero
        if self.fitType == FitType.ADSORPTION:
            _param[2]= 0 # set amplitude of binding to zero
        if self.fitType == FitType.DESORPTION:
            _param[2]= 0 # set amplitude of desorption to zero
        if self.fitType == FitType.ADSORPTION_DOUBLE:
            _param[2]= 0 # amp1
            _param[4]= 0 # amp2
        return self.model.func(self.time,*_param)
        

    def saveFitInfo(self, folder, fileName):
        ''' save fits info into .txt file'''
        _dataDict = {}
        if self.table:
            for key, val in self.table.items():
                _dataDict[key] = val
        for index, param in enumerate(self.fitType.parameters):
            _dataDict[param + '_param'] = self.fittedParam[:, index]

        with open(folder + "/" + fileName, "w", newline='') as outfile:
            outfile.write(self.fitType.label + '\n')
            writer = csv.writer(outfile, delimiter=',')
            writer.writerow(_dataDict.keys())
            writer.writerows(zip(*_dataDict.values()))
        print('fit info exported')

    def saveFit(self, filePath):
        '''Save the full KineticFit state to a file.'''
        state = {
            'time':        self.time,
            'signal':      self.signal,
            'table':       self.table,
            'fittedParam': self.fittedParam,
            'fitType':     self.fitType,
            'modelParams': self.modelParams,
        }
        with open(filePath, 'wb') as f:
            pickle.dump(state, f)

    @classmethod
    def loadFit(cls, filePath):
        '''Load a KineticFit instance from a file saved with saveFit.'''
        with open(filePath, 'rb') as f:
            state = pickle.load(f)
        obj = cls()
        obj.setFitFunction(state['fitType'])
        obj.time        = state['time']
        obj.signal      = state['signal']
        obj.table       = state['table']
        obj.fittedParam = state['fittedParam']
        obj.modelParams = state['modelParams']
        return obj

    def loadFitInfo(self, folder, fileName):
        ''' load fit info
         return
          fitTypeLabel (string)
          table (dict of lists, columns without _param suffix)
          fittedParam (2D numpy array, columns with _param suffix) '''
        with open(folder + "/" + fileName) as infile:
            fitTypeLabel = infile.readline().strip()
            reader = csv.DictReader(infile, delimiter=',')

            table_cols = {key: [] for key in reader.fieldnames if not key.endswith('_param')}
            param_cols = {key: [] for key in reader.fieldnames if key.endswith('_param')}

            for row in reader:
                for key in table_cols:
                    table_cols[key].append(row[key])
                for key in param_cols:
                    param_cols[key].append(float(row[key]))

            table = table_cols
            fittedParam = np.array(list(param_cols.values()), dtype=float).T

        return (fitTypeLabel, table, fittedParam)

if __name__ == "__main__":
    pass















